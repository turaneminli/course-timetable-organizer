import json
from typing import Dict, List, Any

from timetable.models import Room, Timeslot, Course, Session, Instance


def _parse_timeslots(raw: Any) -> List[Timeslot]:
    if isinstance(raw, list):
        if not raw:
            return []
        if isinstance(raw[0], dict):
            return [Timeslot(t["id"], t["label"]) for t in raw]
        if isinstance(raw[0], str):
            return [Timeslot(tid, tid) for tid in raw]
        raise TypeError("Unsupported timeslots list format.")
    if isinstance(raw, dict):
        return [Timeslot(k, v) for k, v in raw.items()]
    raise TypeError("Unsupported timeslots format.")


def _parse_rooms(raw: Any) -> Dict[str, Room]:
    if isinstance(raw, list):
        rooms: Dict[str, Room] = {}
        for r in raw:
            if not isinstance(r, dict):
                raise TypeError("rooms list must contain objects.")
            rooms[r["id"]] = Room(r["id"], int(r["capacity"]), r["type"])
        return rooms

    if isinstance(raw, dict):
        rooms: Dict[str, Room] = {}
        for rid, rv in raw.items():
            if isinstance(rv, dict):
                cap = int(rv["capacity"])
                rtype = rv.get("type", "normal")
            elif isinstance(rv, (int, float)):
                cap = int(rv)
                rtype = "normal"
            else:
                raise TypeError(
                    "rooms dict values must be objects or numbers.")
            rooms[rid] = Room(rid, cap, rtype)
        return rooms

    raise TypeError("Unsupported rooms format.")


def _sessions_from_courses(data: dict) -> List[Session]:
    courses: List[Course] = []
    for c in data["courses"]:
        courses.append(Course(
            id=c["id"],
            teacher=c["teacher"],
            groups=list(c["groups"]),
            size=int(c["size"]),
            sessions_per_week=int(c["sessions_per_week"]),
            room_type=c.get("room_type", "normal"),
        ))

    sessions: List[Session] = []
    for c in courses:
        for k in range(c.sessions_per_week):
            sid = f"{c.id}_S{k+1}"
            sessions.append(Session(
                id=sid,
                course=c.id,
                teacher=c.teacher,
                groups=tuple(c.groups),
                size=c.size,
                rtype=c.room_type,
            ))
    return sessions


def _sessions_from_sessions(data: dict) -> List[Session]:
    raw_sessions = data["sessions"]
    if not isinstance(raw_sessions, list) or not raw_sessions:
        raise ValueError("'sessions' must be a non-empty list.")

    sessions: List[Session] = []
    for s in raw_sessions:
        if not isinstance(s, dict):
            raise TypeError("Each session must be an object.")
        sessions.append(Session(
            id=str(s.get("id") or s.get("session_id")),
            course=str(s.get("course") or s.get("course_id") or "UNKNOWN"),
            teacher=str(s.get("teacher") or s.get("instructor") or "UNKNOWN"),
            groups=tuple(s.get("groups", [])),
            size=int(s.get("size", s.get("students", 0))),
            rtype=str(s.get("rtype", s.get("room_type", "normal"))),
        ))
    return sessions


def load_instance(path: str) -> Instance:
    data = json.load(open(path, "r", encoding="utf-8"))

    timeslots = _parse_timeslots(data["timeslots"])
    rooms = _parse_rooms(data["rooms"])

    teacher_av_raw: Dict[str, List[str]] = data.get("teacher_availability", {})
    teacher_availability = {t: set(v) for t, v in teacher_av_raw.items()}

    preferences = data.get("preferences", {})

    if "sessions" in data:
        sessions = _sessions_from_sessions(data)
    elif "courses" in data:
        sessions = _sessions_from_courses(data)
    else:
        raise KeyError("Instance must contain either 'courses' or 'sessions'.")

    return Instance(
        timeslots=timeslots,
        rooms=rooms,
        sessions=sessions,
        teacher_availability=teacher_availability,
        preferences=preferences,
    )
