from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
import random

from timetable.models import Instance, Individual, Penalty
from timetable.fitness import evaluate
from timetable.ga import GAConfig, solve

HistoryRow = Tuple[int, int, int, int]


@dataclass(frozen=True)
class BaselineResult:
    best: Individual
    penalty: Penalty
    tries: int
    seed: int


@dataclass(frozen=True)
class GAResult:
    best: Individual
    penalty: Penalty
    history: List[HistoryRow]
    config: GAConfig


def random_baseline(inst: Instance, tries: int, seed: int = 123) -> BaselineResult:
    if tries <= 0:
        raise ValueError("tries must be > 0")

    rng = random.Random(seed)
    timeslot_ids = [t.id for t in inst.timeslots]
    room_ids = list(inst.rooms.keys())

    if not timeslot_ids:
        raise ValueError("Instance has no timeslots.")
    if not room_ids:
        raise ValueError("Instance has no rooms.")
    if not inst.sessions:
        raise ValueError("Instance has no sessions.")

    best_ind: Optional[Individual] = None
    best_pen: Optional[Penalty] = None
    n_sessions = len(inst.sessions)

    for _ in range(tries):
        ind = [(rng.choice(timeslot_ids), rng.choice(room_ids))
               for _ in range(n_sessions)]
        pen = evaluate(ind, inst)
        if best_pen is None or pen.total < best_pen.total:
            best_ind = ind
            best_pen = pen

    assert best_ind is not None and best_pen is not None
    return BaselineResult(best=best_ind, penalty=best_pen, tries=tries, seed=seed)


def run_ga(inst: Instance, cfg: GAConfig) -> GAResult:
    best, pen, hist = solve(inst, cfg)
    history: List[HistoryRow] = [
        (int(g), int(t), int(h), int(s)) for (g, t, h, s) in hist]
    return GAResult(best=best, penalty=pen, history=history, config=cfg)


def plot_history_png(
    path: str,
    history: List[HistoryRow],
    *,
    show_components: bool = False
) -> None:
    if not history:
        raise ValueError("history is empty; nothing to plot.")

    import matplotlib.pyplot as plt

    xs = [g for g, _, _, _ in history]
    total = [t for _, t, _, _ in history]
    hard = [h for _, _, h, _ in history]
    soft = [s for _, _, _, s in history]

    plt.figure()
    plt.plot(xs, total, label="total", marker="o")

    if show_components:
        hard_scaled = [h * 1000 for h in hard]
        plt.plot(xs, hard_scaled, label="hard (x1000)", marker="o")
        plt.plot(xs, soft, label="soft", marker="o")

    plt.xlabel("Generation")
    plt.ylabel("Penalty (lower is better)")
    plt.legend()

    if len(xs) == 1:
        x = xs[0]
        plt.xlim(x - 1, x + 1)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def summarize_history(history: List[HistoryRow]) -> dict:
    if not history:
        return {}

    start = history[0]
    end = history[-1]
    best = min(history, key=lambda x: x[1])

    return {
        "start": {"gen": start[0], "total": start[1], "hard": start[2], "soft": start[3]},
        "end": {"gen": end[0], "total": end[1], "hard": end[2], "soft": end[3]},
        "best": {"gen": best[0], "total": best[1], "hard": best[2], "soft": best[3]},
        "generations": len(history),
    }
