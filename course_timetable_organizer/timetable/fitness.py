from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

from timetable.models import Instance, Individual, Penalty


def evaluate(individual: Individual, inst: Instance) -> Penalty:
    hard = 0
    soft = 0
    details: Dict[str, int] = defaultdict(int)

    occ_room = defaultdict(int)
    occ_teacher = defaultdict(int)
    occ_group = defaultdict(int)

    # Preferences
    late_slots = set(inst.preferences.get("late_slots", []))
    avoid_days_for_course = inst.preferences.get("avoid_days_for_course", {})

    # Cache day/slot parsing to avoid repeated split/int conversions
    day_cache: Dict[str, str] = {}
    slot_cache: Dict[str, int] = {}

    def day_of(ts_id: str) -> str:
        d = day_cache.get(ts_id)
        if d is None:
            d = ts_id.split("_", 1)[0]
            day_cache[ts_id] = d
        return d

    def slot_num(ts_id: str) -> int:
        n = slot_cache.get(ts_id)
        if n is None:
            n = int(ts_id.split("_", 1)[1])
            slot_cache[ts_id] = n
        return n

    # Hard + some soft; and counts for collisions
    for i, (ts_id, room_id) in enumerate(individual):
        s = inst.sessions[i]
        room = inst.rooms[room_id]

        occ_room[(ts_id, room_id)] += 1
        occ_teacher[(ts_id, s.teacher)] += 1
        for g in s.groups:
            occ_group[(ts_id, g)] += 1

        if room.capacity < s.size:
            hard += 1
            details["hard_capacity"] += 1

        if room.rtype != s.rtype:
            hard += 1
            details["hard_room_type"] += 1

        av = inst.teacher_availability.get(s.teacher)
        if av is not None and ts_id not in av:
            hard += 1
            details["hard_teacher_availability"] += 1

        if ts_id in late_slots:
            soft += 1
            details["soft_late_slot"] += 1

        avoid_days = avoid_days_for_course.get(s.course)
        if avoid_days:
            if day_of(ts_id) in avoid_days:
                soft += 2
                details["soft_avoid_day"] += 2

    # Convert counts to collision penalties (same as len(list)-1)
    for _, c in occ_room.items():
        if c > 1:
            v = c - 1
            hard += v
            details["hard_room_collision"] += v

    for _, c in occ_teacher.items():
        if c > 1:
            v = c - 1
            hard += v
            details["hard_teacher_collision"] += v

    for _, c in occ_group.items():
        if c > 1:
            v = c - 1
            hard += v
            details["hard_group_collision"] += v

    # Soft: group gaps
    group_slots = defaultdict(list)
    for i, (ts_id, _) in enumerate(individual):
        s = inst.sessions[i]
        for g in s.groups:
            group_slots[g].append(ts_id)

    for _, slots in group_slots.items():
        per_day = defaultdict(list)
        for ts_id in slots:
            per_day[day_of(ts_id)].append(slot_num(ts_id))

        for _, nums in per_day.items():
            nums.sort()
            for a, b in zip(nums, nums[1:]):
                if b - a > 1:
                    gap = b - a - 1
                    soft += gap
                    details["soft_gaps"] += gap

    total = hard * 1000 + soft
    return Penalty(total=total, hard=hard, soft=soft, details=dict(details))
