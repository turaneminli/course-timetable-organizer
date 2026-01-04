from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

from timetable.models import Instance, Individual, Penalty
from timetable.fitness import evaluate
from timetable.repair import repair

HistoryRow = Tuple[int, int, int, int]  # (generation, total, hard, soft)
ProgressCb = Callable[[HistoryRow], None]

_WORKER_INST: Instance | None = None
_WORKER_USE_REPAIR: bool = False
_WORKER_ATTEMPTS: int = 20
_WORKER_ROUNDS: int = 3


def _init_worker(inst: Instance, use_repair: bool, attempts_per_gene: int, max_rounds: int) -> None:
    global _WORKER_INST, _WORKER_USE_REPAIR, _WORKER_ATTEMPTS, _WORKER_ROUNDS
    _WORKER_INST = inst
    _WORKER_USE_REPAIR = use_repair
    _WORKER_ATTEMPTS = attempts_per_gene
    _WORKER_ROUNDS = max_rounds


def _repair_and_eval_worker(ind: Individual) -> Tuple[Individual, Penalty]:
    inst = _WORKER_INST
    if inst is None:
        raise RuntimeError("Worker instance not initialised.")

    out = ind
    if _WORKER_USE_REPAIR:
        out = repair(out, inst, attempts_per_gene=_WORKER_ATTEMPTS,
                     max_rounds=_WORKER_ROUNDS)

    pen = evaluate(out, inst)
    return out, pen


def _repair_and_evaluate_population(
    pop: List[Individual],
    inst: Instance,
    pool,
    *,
    use_repair: bool,
    attempts_per_gene: int,
    max_rounds: int,
    workers: int,
) -> Tuple[List[Individual], List[Penalty]]:
    if pool is None:
        new_pop: List[Individual] = []
        penalties: List[Penalty] = []
        for ind in pop:
            out = ind
            if use_repair:
                out = repair(
                    out, inst, attempts_per_gene=attempts_per_gene, max_rounds=max_rounds)
            new_pop.append(out)
            penalties.append(evaluate(out, inst))
        return new_pop, penalties

    chunksize = max(1, len(pop) // (workers * 4))
    results = pool.map(_repair_and_eval_worker, pop, chunksize=chunksize)
    new_pop = [ind for ind, _ in results]
    penalties = [pen for _, pen in results]
    return new_pop, penalties


@dataclass(frozen=True)
class GAConfig:
    pop_size: int = 250
    generations: int = 600
    elite: int = 12
    tournament_k: int = 3
    cx_rate: float = 0.9
    mut_rate: float = 0.12
    seed: int = 42
    use_repair: bool = True
    log_every: int = 25
    workers: int = 1
    repair_attempts_per_gene: int = 15
    repair_max_rounds: int = 2


def _tournament(pop: Sequence[Individual], scores: Sequence[int], k: int) -> Individual:
    if not pop:
        raise ValueError("Population is empty.")
    if len(pop) != len(scores):
        raise ValueError("Population and scores length mismatch.")
    if k <= 0:
        raise ValueError("Tournament size k must be > 0.")

    best_idx = random.randrange(len(pop))
    for _ in range(k - 1):
        i = random.randrange(len(pop))
        if scores[i] < scores[best_idx]:
            best_idx = i
    return pop[best_idx]


def _crossover(a: Individual, b: Individual, rate: float) -> Tuple[Individual, Individual]:
    if random.random() > rate:
        return a[:], b[:]

    n = len(a)
    i = random.randrange(n)
    j = random.randrange(n)
    if i > j:
        i, j = j, i

    c1 = a[:i] + b[i:j] + a[j:]
    c2 = b[:i] + a[i:j] + b[j:]
    return c1, c2


def solve(
    inst: Instance,
    cfg: GAConfig,
    *,
    progress_cb: Optional[ProgressCb] = None,
) -> Tuple[Individual, Penalty, List[HistoryRow]]:
    if cfg.pop_size <= 0:
        raise ValueError("pop_size must be > 0.")
    if cfg.generations <= 0:
        raise ValueError("generations must be > 0.")
    if cfg.elite < 0 or cfg.elite >= cfg.pop_size:
        raise ValueError("elite must be in [0, pop_size-1].")
    if cfg.log_every < 0:
        raise ValueError("log_every must be >= 0.")
    if cfg.workers <= 0:
        raise ValueError("workers must be >= 1.")

    random.seed(cfg.seed)

    timeslot_ids = [t.id for t in inst.timeslots]
    room_ids = list(inst.rooms.keys())
    n_sessions = len(inst.sessions)

    def random_individual() -> Individual:
        return [(random.choice(timeslot_ids), random.choice(room_ids)) for _ in range(n_sessions)]

    def mutate(ind: Individual) -> Individual:
        out = ind[:]
        for idx in range(len(out)):
            if random.random() < cfg.mut_rate:
                ts_id, room_id = out[idx]
                if random.random() < 0.5:
                    ts_id = random.choice(timeslot_ids)
                else:
                    room_id = random.choice(room_ids)
                out[idx] = (ts_id, room_id)
        return out

    pool = None
    if cfg.workers > 1:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        pool = ctx.Pool(
            processes=cfg.workers,
            initializer=_init_worker,
            initargs=(inst, cfg.use_repair,
                      cfg.repair_attempts_per_gene, cfg.repair_max_rounds),
        )

    def emit(row: HistoryRow) -> None:
        if progress_cb is not None:
            progress_cb(row)

    try:
        pop: List[Individual] = [random_individual()
                                 for _ in range(cfg.pop_size)]

        pop, penalties = _repair_and_evaluate_population(
            pop,
            inst,
            pool,
            use_repair=cfg.use_repair,
            attempts_per_gene=cfg.repair_attempts_per_gene,
            max_rounds=cfg.repair_max_rounds,
            workers=cfg.workers,
        )
        totals: List[int] = [p.total for p in penalties]

        best_idx = min(range(len(pop)), key=totals.__getitem__)
        best = pop[best_idx]
        best_pen = penalties[best_idx]

        history: List[HistoryRow] = [
            (0, best_pen.total, best_pen.hard, best_pen.soft)]
        emit(history[-1])

        if cfg.log_every > 0:
            print(
                f"gen=0 best_total={best_pen.total} hard={best_pen.hard} soft={best_pen.soft}", flush=True)

        for gen in range(1, cfg.generations + 1):
            ranked = sorted(range(len(pop)), key=totals.__getitem__)
            new_pop: List[Individual] = [pop[i] for i in ranked[:cfg.elite]]

            while len(new_pop) < cfg.pop_size:
                p1 = _tournament(pop, totals, cfg.tournament_k)
                p2 = _tournament(pop, totals, cfg.tournament_k)
                c1, c2 = _crossover(p1, p2, cfg.cx_rate)
                c1 = mutate(c1)
                c2 = mutate(c2)
                new_pop.append(c1)
                if len(new_pop) < cfg.pop_size:
                    new_pop.append(c2)

            pop, penalties = _repair_and_evaluate_population(
                new_pop,
                inst,
                pool,
                use_repair=cfg.use_repair,
                attempts_per_gene=cfg.repair_attempts_per_gene,
                max_rounds=cfg.repair_max_rounds,
                workers=cfg.workers,
            )
            totals = [p.total for p in penalties]

            cur_idx = min(range(len(pop)), key=totals.__getitem__)
            cur_pen = penalties[cur_idx]
            if cur_pen.total < best_pen.total:
                best = pop[cur_idx]
                best_pen = cur_pen

            row = (gen, best_pen.total, best_pen.hard, best_pen.soft)
            history.append(row)

            # emit at same cadence as log_every (and always emit the last generation)
            if cfg.log_every > 0 and (gen % cfg.log_every == 0 or gen == cfg.generations):
                emit(row)
                print(
                    f"gen={gen} best_total={best_pen.total} hard={best_pen.hard} soft={best_pen.soft}", flush=True)

            if best_pen.hard == 0 and best_pen.soft == 0:
                emit(row)
                break

        return best, best_pen, history

    finally:
        if pool is not None:
            pool.close()
            pool.join()
