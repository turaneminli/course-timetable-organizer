from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass(frozen=True)
class Room:
    id: str
    capacity: int
    rtype: str


@dataclass(frozen=True)
class Timeslot:
    id: str
    label: str


@dataclass(frozen=True)
class Course:
    id: str
    teacher: str
    groups: List[str]
    size: int
    sessions_per_week: int
    room_type: str


@dataclass(frozen=True)
class Session:
    id: str
    course: str
    teacher: str
    groups: Tuple[str, ...]
    size: int
    rtype: str


@dataclass(frozen=True)
class Instance:
    timeslots: List[Timeslot]
    rooms: Dict[str, Room]
    sessions: List[Session]
    teacher_availability: Dict[str, set[str]]
    preferences: Dict


Assignment = Tuple[str, str]
Individual = List[Assignment]


@dataclass(frozen=True)
class Penalty:
    total: int
    hard: int
    soft: int
    details: Dict[str, int]
