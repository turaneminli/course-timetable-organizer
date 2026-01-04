from __future__ import annotations
import csv
from collections import defaultdict
from typing import Dict, List
from timetable.models import Instance, Individual


def export_csv(path: str, ind: Individual, inst: Instance):
    ts_label = {t.id: t.label for t in inst.timeslots}

    rows = []
    for i, (ts_id, room_id) in enumerate(ind):
        s = inst.sessions[i]
        rows.append({
            "timeslot_id": ts_id,
            "timeslot_label": ts_label.get(ts_id, ts_id),
            "room": room_id,
            "session_id": s.id,
            "course": s.course,
            "teacher": s.teacher,
            "groups": ",".join(s.groups),
            "size": s.size,
            "room_type": s.rtype
        })

    rows.sort(key=lambda r: (r["timeslot_id"], r["room"], r["course"]))

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        w.writeheader()
        w.writerows(rows)


def export_group_view_csv(path: str, ind: Individual, inst: Instance):
    ts_label = {t.id: t.label for t in inst.timeslots}
    by_group = defaultdict(list)

    for i, (ts_id, room_id) in enumerate(ind):
        s = inst.sessions[i]
        for g in s.groups:
            by_group[g].append((ts_id, ts_label.get(
                ts_id, ts_id), room_id, s.course, s.teacher, s.id))

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "timeslot_id", "timeslot_label",
                   "room", "course", "teacher", "session_id"])
        for g in sorted(by_group.keys()):
            items = sorted(by_group[g], key=lambda x: (x[0], x[2], x[3]))
            for ts_id, label, room, course, teacher, sid in items:
                w.writerow([g, ts_id, label, room, course, teacher, sid])
