from __future__ import annotations
from typing import DefaultDict, Tuple

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Sequence, Set, Tuple

from timetable.models import Instance, Individual


@dataclass(frozen=True)
class _MoveToken:
    idx: int
    old_ts: str
    old_room: str


class HardConstraintTracker:
    """
    Incremental tracker for HARD constraint penalties:
      - capacity
      - room type
      - teacher availability
      - collisions: room, teacher, group

    hard_penalty = unary_total + room_collision_total + teacher_collision_total + group_collision_total
    where each collision group contributes sum(max(0, count-1)).
    """

    def __init__(self, ind: Individual, inst: Instance):
        self.inst = inst
        self.ind = ind[:]  # mutable working copy

        self._room_count: DefaultDict[Tuple[str, str], int] = defaultdict(int)
        self._teacher_count: DefaultDict[Tuple[str, str], int] = defaultdict(
            int)
        self._group_count: DefaultDict[Tuple[str, str], int] = defaultdict(int)

        self._room_coll = 0
        self._teacher_coll = 0
        self._group_coll = 0

        self._unary_by_idx: List[int] = [0] * len(inst.sessions)
        self._unary_total = 0

        for i, (ts, room) in enumerate(self.ind):
            self._add_collision(i, ts, room)
            u = self._unary_for(i, ts, room)
            self._unary_by_idx[i] = u
            self._unary_total += u

    def hard(self) -> int:
        return self._unary_total + self._room_coll + self._teacher_coll + self._group_coll

    def unary_for_idx(self, idx: int) -> int:
        return self._unary_by_idx[idx]

    def assignment(self, idx: int) -> Tuple[str, str]:
        return self.ind[idx]

    def move(self, idx: int, new_ts: str, new_room: str) -> _MoveToken:
        old_ts, old_room = self.ind[idx]
        if old_ts == new_ts and old_room == new_room:
            return _MoveToken(idx=idx, old_ts=old_ts, old_room=old_room)

        self._remove_collision(idx, old_ts, old_room)
        self._add_collision(idx, new_ts, new_room)

        old_u = self._unary_by_idx[idx]
        new_u = self._unary_for(idx, new_ts, new_room)
        self._unary_by_idx[idx] = new_u
        self._unary_total += (new_u - old_u)

        self.ind[idx] = (new_ts, new_room)
        return _MoveToken(idx=idx, old_ts=old_ts, old_room=old_room)

    def undo(self, token: _MoveToken) -> None:
        idx = token.idx
        cur_ts, cur_room = self.ind[idx]
        if cur_ts == token.old_ts and cur_room == token.old_room:
            return
        self.move(idx, token.old_ts, token.old_room)

    def _unary_for(self, idx: int, ts: str, room_id: str) -> int:
        s = self.inst.sessions[idx]
        room = self.inst.rooms[room_id]
        u = 0

        if room.capacity < s.size:
            u += 1
        if room.rtype != s.rtype:
            u += 1

        av = self.inst.teacher_availability.get(s.teacher)
        if av is not None and ts not in av:
            u += 1

        return u

    @staticmethod
    def _penalty_from_count(c: int) -> int:
        return c - 1 if c > 1 else 0

    def _bump_count(self, mp: DefaultDict[Tuple[str, str], int], key: Tuple[str, str], delta: int, which: str) -> None:
        before = mp[key]
        after = before + delta
        if after < 0:
            raise ValueError("Count underflow for key=%s" % (key,))

        pb = self._penalty_from_count(before)
        pa = self._penalty_from_count(after)

        if which == "room":
            self._room_coll += (pa - pb)
        elif which == "teacher":
            self._teacher_coll += (pa - pb)
        elif which == "group":
            self._group_coll += (pa - pb)
        else:
            raise ValueError("Unknown collision type")

        if after == 0:
            del mp[key]
        else:
            mp[key] = after

    def _add_collision(self, idx: int, ts: str, room_id: str) -> None:
        s = self.inst.sessions[idx]
        self._bump_count(self._room_count, (ts, room_id), +1, "room")
        self._bump_count(self._teacher_count, (ts, s.teacher), +1, "teacher")
        for g in s.groups:
            self._bump_count(self._group_count, (ts, g), +1, "group")

    def _remove_collision(self, idx: int, ts: str, room_id: str) -> None:
        s = self.inst.sessions[idx]
        self._bump_count(self._room_count, (ts, room_id), -1, "room")
        self._bump_count(self._teacher_count, (ts, s.teacher), -1, "teacher")
        for g in s.groups:
            self._bump_count(self._group_count, (ts, g), -1, "group")


def hard_penalty(ind: Individual, inst: Instance) -> int:
    hard = 0
    occ_room: DefaultDict[Tuple[str, str], int] = defaultdict(int)
    occ_teacher: DefaultDict[Tuple[str, str], int] = defaultdict(int)
    occ_group: DefaultDict[Tuple[str, str], int] = defaultdict(int)

    for i, (ts_id, room_id) in enumerate(ind):
        s = inst.sessions[i]
        room = inst.rooms[room_id]

        occ_room[(ts_id, room_id)] += 1
        occ_teacher[(ts_id, s.teacher)] += 1
        for g in s.groups:
            occ_group[(ts_id, g)] += 1

        if room.capacity < s.size:
            hard += 1
        if room.rtype != s.rtype:
            hard += 1

        av = inst.teacher_availability.get(s.teacher)
        if av is not None and ts_id not in av:
            hard += 1

    for c in occ_room.values():
        if c > 1:
            hard += (c - 1)
    for c in occ_teacher.values():
        if c > 1:
            hard += (c - 1)
    for c in occ_group.values():
        if c > 1:
            hard += (c - 1)

    return hard


def _conflicting_indices(ind: Individual, inst: Instance) -> Set[int]:
    bad: Set[int] = set()

    occ_room: DefaultDict[Tuple[str, str], List[int]] = defaultdict(list)
    occ_teacher: DefaultDict[Tuple[str, str], List[int]] = defaultdict(list)
    occ_group: DefaultDict[Tuple[str, str], List[int]] = defaultdict(list)

    for i, (ts_id, room_id) in enumerate(ind):
        s = inst.sessions[i]
        occ_room[(ts_id, room_id)].append(i)
        occ_teacher[(ts_id, s.teacher)].append(i)
        for g in s.groups:
            occ_group[(ts_id, g)].append(i)

        room = inst.rooms[room_id]
        if room.capacity < s.size:
            bad.add(i)
        if room.rtype != s.rtype:
            bad.add(i)

        av = inst.teacher_availability.get(s.teacher)
        if av is not None and ts_id not in av:
            bad.add(i)

    for idxs in occ_room.values():
        if len(idxs) > 1:
            bad.update(idxs)
    for idxs in occ_teacher.values():
        if len(idxs) > 1:
            bad.update(idxs)
    for idxs in occ_group.values():
        if len(idxs) > 1:
            bad.update(idxs)

    return bad


def repair(
    ind: Individual,
    inst: Instance,
    attempts_per_gene: int = 20,
    max_rounds: int = 3,
) -> Individual:
    """
    Repair focuses on reducing HARD penalty quickly using incremental scoring.
    It does not try to optimize SOFT penalties; GA will do that.
    """
    timeslot_ids = [t.id for t in inst.timeslots]
    room_ids = list(inst.rooms.keys())

    # Precompute feasibility sets to avoid wasting candidate trials
    feasible_rooms: List[List[str]] = []
    feasible_timeslots: List[List[str]] = []

    for s in inst.sessions:
        rs = [rid for rid in room_ids if inst.rooms[rid].capacity >=
              s.size and inst.rooms[rid].rtype == s.rtype]
        feasible_rooms.append(rs if rs else room_ids)

        av = inst.teacher_availability.get(s.teacher)
        feasible_timeslots.append(list(av) if av else timeslot_ids)

    out = ind[:]
    tracker = HardConstraintTracker(out, inst)

    for _ in range(max_rounds):
        bad = list(_conflicting_indices(tracker.ind, inst))
        if not bad:
            break

        random.shuffle(bad)

        for idx in bad:
            base_hard = tracker.hard()
            old_ts, old_room = tracker.assignment(idx)

            best_ts, best_room = old_ts, old_room
            best_hard = base_hard

            ts_choices = feasible_timeslots[idx]
            room_choices = feasible_rooms[idx]

            for _k in range(attempts_per_gene):
                cand_ts = random.choice(ts_choices)
                cand_room = random.choice(room_choices)
                if cand_ts == old_ts and cand_room == old_room:
                    continue

                token = tracker.move(idx, cand_ts, cand_room)
                h = tracker.hard()
                if h < best_hard:
                    best_hard = h
                    best_ts, best_room = cand_ts, cand_room
                    tracker.undo(token)
                    if best_hard == 0:
                        break
                else:
                    tracker.undo(token)

            tracker.move(idx, best_ts, best_room)

            if tracker.hard() == 0:
                return tracker.ind[:]

    return tracker.ind[:]
