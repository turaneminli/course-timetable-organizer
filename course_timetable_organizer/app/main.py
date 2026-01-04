from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from threading import Lock

from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from timetable.fitness import evaluate
from timetable.ga import GAConfig, solve
from timetable.loader import load_instance

HistoryRow = Tuple[int, int, int, int]


@dataclass
class InstanceRecord:
    id: str
    path: str
    name: str
    created_at: float


@dataclass
class Job:
    id: str
    status: str
    created_at: float
    started_at: Optional[float]
    finished_at: Optional[float]
    error: Optional[str]
    cfg: Dict[str, Any]
    history: List[HistoryRow]
    result: Optional[Dict[str, Any]]
    instance_id: str
    instance_name: str
    lock: Lock


RUNS_DIR = ".runs"
INST_DIR = os.path.join(RUNS_DIR, "instances")
os.makedirs(INST_DIR, exist_ok=True)

INSTANCES: Dict[str, InstanceRecord] = {}
JOBS: Dict[str, Job] = {}

app = FastAPI(title="Timetable Solver API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


def _job_view(j: Job) -> Dict[str, Any]:
    with j.lock:
        return {
            "id": j.id,
            "status": j.status,
            "created_at": j.created_at,
            "started_at": j.started_at,
            "finished_at": j.finished_at,
            "error": j.error,
            "cfg": j.cfg,
            "history": j.history,
            "instance_id": j.instance_id,
            "instance_name": j.instance_name,
            "has_result": j.result is not None,
        }


def _instance_view(inst) -> Dict[str, Any]:
    rooms = [{"id": rid, "capacity": r.capacity, "rtype": r.rtype}
             for rid, r in inst.rooms.items()]
    timeslots = [{"id": t.id, "label": t.label} for t in inst.timeslots]
    sessions = [
        {
            "id": s.id,
            "course": s.course,
            "teacher": s.teacher,
            "groups": list(s.groups),
            "size": s.size,
            "rtype": s.rtype,
        }
        for s in inst.sessions
    ]

    teachers = sorted({s.teacher for s in inst.sessions})
    groups = sorted({g for s in inst.sessions for g in s.groups})
    courses = sorted({s.course for s in inst.sessions})

    teacher_availability = {k: sorted(list(v))
                            for k, v in inst.teacher_availability.items()}
    preferences = inst.preferences or {}

    return {
        "summary": {
            "sessions": len(inst.sessions),
            "rooms": len(inst.rooms),
            "timeslots": len(inst.timeslots),
            "teachers": len(teachers),
            "groups": len(groups),
            "courses": len(courses),
        },
        "rooms": rooms,
        "timeslots": timeslots,
        "sessions": sessions,
        "teachers": teachers,
        "groups": groups,
        "courses": courses,
        "teacher_availability": teacher_availability,
        "preferences": preferences,
    }


def _build_schedule_rows(ind, inst) -> List[Dict[str, Any]]:
    tlabel = {t.id: t.label for t in inst.timeslots}
    out: List[Dict[str, Any]] = []
    for i, (ts_id, room_id) in enumerate(ind):
        s = inst.sessions[i]
        out.append(
            {
                "timeslot_id": ts_id,
                "timeslot_label": tlabel.get(ts_id, ts_id),
                "room": room_id,
                "session_id": s.id,
                "course": s.course,
                "teacher": s.teacher,
                "groups": list(s.groups),
                "size": s.size,
                "room_type": s.rtype,
            }
        )
    return out


def _build_group_rows(ind, inst) -> List[Dict[str, Any]]:
    tlabel = {t.id: t.label for t in inst.timeslots}
    out: List[Dict[str, Any]] = []
    for i, (ts_id, room_id) in enumerate(ind):
        s = inst.sessions[i]
        for g in s.groups:
            out.append(
                {
                    "group": g,
                    "timeslot_id": ts_id,
                    "timeslot_label": tlabel.get(ts_id, ts_id),
                    "room": room_id,
                    "course": s.course,
                    "teacher": s.teacher,
                    "session_id": s.id,
                }
            )
    return out


def _day_of(ts_id: str) -> str:
    if "_" in ts_id:
        return ts_id.split("_")[0]
    if "," in ts_id:
        return ts_id.split(",")[0]
    return ts_id


def _slot_num(ts_id: str) -> int:
    if "_" in ts_id:
        p = ts_id.split("_", 1)[1]
        try:
            return int(p)
        except Exception:
            return 0
    return 0


def _validate(ind, inst, limit: int = 30) -> Dict[str, Any]:
    room_occ: Dict[Tuple[str, str], List[str]] = {}
    teacher_occ: Dict[Tuple[str, str], List[str]] = {}
    group_occ: Dict[Tuple[str, str], List[str]] = {}

    cap_bad: List[Dict[str, Any]] = []
    type_bad: List[Dict[str, Any]] = []
    avail_bad: List[Dict[str, Any]] = []

    for i, (ts_id, room_id) in enumerate(ind):
        s = inst.sessions[i]
        sid = s.id

        room_occ.setdefault((ts_id, room_id), []).append(sid)
        teacher_occ.setdefault((ts_id, s.teacher), []).append(sid)
        for g in s.groups:
            group_occ.setdefault((ts_id, g), []).append(sid)

        room = inst.rooms[room_id]
        if room.capacity < s.size:
            cap_bad.append({"session_id": sid, "need": s.size,
                           "capacity": room.capacity, "room": room_id, "timeslot": ts_id})
        if room.rtype != s.rtype:
            type_bad.append({"session_id": sid, "need": s.rtype,
                            "room_type": room.rtype, "room": room_id, "timeslot": ts_id})

        av = inst.teacher_availability.get(s.teacher)
        if av is not None and ts_id not in av:
            avail_bad.append(
                {"session_id": sid, "teacher": s.teacher, "timeslot": ts_id})

    room_coll = [{"timeslot": k[0], "room": k[1], "sessions": v}
                 for k, v in room_occ.items() if len(v) > 1]
    teacher_coll = [{"timeslot": k[0], "teacher": k[1], "sessions": v}
                    for k, v in teacher_occ.items() if len(v) > 1]
    group_coll = [{"timeslot": k[0], "group": k[1], "sessions": v}
                  for k, v in group_occ.items() if len(v) > 1]

    gaps_by_group: Dict[str, int] = {}
    group_slots: Dict[str, List[str]] = {}
    for i, (ts_id, _) in enumerate(ind):
        s = inst.sessions[i]
        for g in s.groups:
            group_slots.setdefault(g, []).append(ts_id)

    total_gaps = 0
    for g, slots in group_slots.items():
        per_day: Dict[str, List[int]] = {}
        for t in slots:
            per_day.setdefault(_day_of(t), []).append(_slot_num(t))

        g_gaps = 0
        for _, nums in per_day.items():
            nums.sort()
            for a, b in zip(nums, nums[1:]):
                if b - a > 1:
                    g_gaps += (b - a - 1)

        gaps_by_group[g] = g_gaps
        total_gaps += g_gaps

    hard_count = (
        sum(len(x["sessions"]) - 1 for x in room_coll)
        + sum(len(x["sessions"]) - 1 for x in teacher_coll)
        + sum(len(x["sessions"]) - 1 for x in group_coll)
        + len(cap_bad)
        + len(type_bad)
        + len(avail_bad)
    )

    return {
        "hard_total": hard_count,
        "hard": {
            "room_collisions": room_coll[:limit],
            "teacher_collisions": teacher_coll[:limit],
            "group_collisions": group_coll[:limit],
            "capacity_violations": cap_bad[:limit],
            "room_type_violations": type_bad[:limit],
            "availability_violations": avail_bad[:limit],
            "counts": {
                "room_collisions": len(room_coll),
                "teacher_collisions": len(teacher_coll),
                "group_collisions": len(group_coll),
                "capacity": len(cap_bad),
                "room_type": len(type_bad),
                "availability": len(avail_bad),
            },
        },
        "soft": {
            "total_gaps": total_gaps,
            "gaps_by_group_top": sorted(
                [{"group": k, "gaps": v} for k, v in gaps_by_group.items()],
                key=lambda x: -x["gaps"],
            )[:20],
        },
    }


def _save_uploaded_json(file: UploadFile) -> Tuple[str, str, str]:
    if not (file.filename or "").lower().endswith(".json"):
        raise HTTPException(
            status_code=400, detail="Instance must be a .json file")

    data = file.file.read()
    try:
        json.loads(data.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    inst_id = str(uuid.uuid4())
    name = os.path.basename(file.filename)
    path = os.path.join(INST_DIR, f"{inst_id}_{name}")

    with open(path, "wb") as f:
        f.write(data)

    return inst_id, name, path


def _run_job(job_id: str):
    j = JOBS[job_id]
    with j.lock:
        j.status = "running"
        j.started_at = time.time()
        j.error = None
        j.history = []
        j.result = None

    try:
        inst_rec = INSTANCES.get(j.instance_id)
        if inst_rec is None:
            raise RuntimeError("Instance not found for job.")
        inst = load_instance(inst_rec.path)

        cfg = GAConfig(
            pop_size=int(j.cfg["pop"]),
            generations=int(j.cfg["gen"]),
            seed=int(j.cfg["seed"]),
            use_repair=bool(j.cfg["repair"]),
            log_every=int(j.cfg["log_every"]),
            workers=int(j.cfg["workers"]),
            repair_attempts_per_gene=int(j.cfg["repair_attempts_per_gene"]),
            repair_max_rounds=int(j.cfg["repair_max_rounds"]),
        )

        def on_progress(row: HistoryRow) -> None:
            with j.lock:
                j.history.append(row)
                # prevent unbounded growth if someone runs 50k generations
                if len(j.history) > 5000:
                    j.history = j.history[-5000:]

        best, pen, hist = solve(inst, cfg, progress_cb=on_progress)

        rows = _build_schedule_rows(best, inst)
        group_rows = _build_group_rows(best, inst)

        verify_pen = evaluate(best, inst)
        validation = _validate(best, inst)

        with j.lock:
            # keep final history from solve (it may have more points than emitted cadence)
            j.history = hist

            j.result = {
                "penalty": {"total": pen.total, "hard": pen.hard, "soft": pen.soft, "details": pen.details},
                "verify_penalty": {"total": verify_pen.total, "hard": verify_pen.hard, "soft": verify_pen.soft, "details": verify_pen.details},
                "validation": validation,
                "history": hist,
                "schedule": rows,
                "by_group": group_rows,
                "instance": _instance_view(inst),
            }

            j.status = "done"
            j.finished_at = time.time()

    except Exception as e:
        with j.lock:
            j.status = "error"
            j.error = str(e)
            j.finished_at = time.time()


@api.get("/health")
def health():
    return {"ok": True}


@api.post("/instances/preview")
async def preview_instance(instance: UploadFile = File(...)):
    inst_id, name, path = _save_uploaded_json(instance)
    inst = load_instance(path)
    INSTANCES[inst_id] = InstanceRecord(
        id=inst_id, path=path, name=name, created_at=time.time())
    return {"instance_id": inst_id, "name": name, "instance": _instance_view(inst)}


@api.get("/instances/{instance_id}")
def get_instance(instance_id: str):
    rec = INSTANCES.get(instance_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Instance not found")
    inst = load_instance(rec.path)
    return {"instance_id": rec.id, "name": rec.name, "instance": _instance_view(inst)}


@api.post("/jobs")
async def create_job(
    instance_id: str = Form(""),
    instance: UploadFile = File(None),
    pop: int = Form(120),
    gen: int = Form(600),
    seed: int = Form(42),
    repair: bool = Form(True),
    workers: int = Form(4),
    log_every: int = Form(10),
    repair_attempts_per_gene: int = Form(15),
    repair_max_rounds: int = Form(2),
):
    inst_id = instance_id.strip()

    if inst_id:
        if inst_id not in INSTANCES:
            raise HTTPException(
                status_code=404, detail="instance_id not found")
        inst_name = INSTANCES[inst_id].name
    else:
        if instance is None:
            raise HTTPException(
                status_code=400, detail="Provide instance_id or upload instance file")

        new_id, name, path = _save_uploaded_json(instance)
        load_instance(path)
        INSTANCES[new_id] = InstanceRecord(
            id=new_id, path=path, name=name, created_at=time.time())
        inst_id = new_id
        inst_name = name

    job_id = str(uuid.uuid4())
    j = Job(
        id=job_id,
        status="queued",
        created_at=time.time(),
        started_at=None,
        finished_at=None,
        error=None,
        cfg={
            "pop": pop,
            "gen": gen,
            "seed": seed,
            "repair": repair,
            "workers": workers,
            "log_every": log_every,
            "repair_attempts_per_gene": repair_attempts_per_gene,
            "repair_max_rounds": repair_max_rounds,
        },
        history=[],
        result=None,
        instance_id=inst_id,
        instance_name=inst_name,
        lock=Lock(),
    )
    JOBS[job_id] = j

    t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    t.start()

    return _job_view(j)


@api.get("/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_view(JOBS[job_id])


@api.get("/jobs/{job_id}/result")
def get_result(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    j = JOBS[job_id]
    if j.status == "error":
        raise HTTPException(status_code=400, detail=j.error or "Job failed")
    if j.status != "done" or j.result is None:
        raise HTTPException(status_code=409, detail="Job not finished")
    return j.result


app.include_router(api)


@app.get("/__routes")
def __routes():
    return sorted([getattr(r, "path", "") for r in app.routes])
