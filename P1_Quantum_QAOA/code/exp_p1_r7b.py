"""P1 seventh revision, finite-shot check of the verified-cost rule -> <work>/p1_r7b.json.

exp_p1_r7.py scores each candidate set by the exact expected cost of the cheapest verified plan among 32 shots.
A device only sees shots. Here, in every leave-one-city-out fold, each candidate is scored on the training cities
from one draw of 32 shots per instance (cheapest verified plan, the greedy plan if none, divided by the greedy
cost), the lowest mean is picked, and this is repeated for REPS independent draws. Same 30 candidates, same 197
city instances (four disruption patterns) as exp_p1_r7.py.
usage: python exp_p1_r7b.py <work>
"""
import json
import sys
import types
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SHARED = HERE.parents[1] / "shared_code"
sys.path[:0] = [str(SHARED), str(HERE)]
if "exp_p1" not in sys.modules:
    try:
        import exp_p1  # noqa: F401
    except ImportError:
        sys.modules["exp_p1"] = types.SimpleNamespace(disrupted=None)
import qaoa_sim as Q  # noqa: E402
import exp_p1_cities as C  # noqa: E402
import exp_p1_r6 as R6  # noqa: E402

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
C.CITY_DIR = SHARED / "city_snapshot_2026-10-13" / "backend" / "data" / "cities"
N, REPS = 32, 200


def main():
    v2 = json.loads((WORK / "p1_v2.json").read_text(encoding="utf-8"))
    runs = sorted([r for r in v2["results"] if r["task"] == "seed:xy:1.0:0" and r["feasible_instance"]],
                  key=lambda r: r["i"])
    cands = [np.asarray(r["runs"][3]["theta"]) for r in runs]
    r7 = json.loads((WORK / "p1_r7.json").read_text(encoding="utf-8"))["rows"]
    keys = [(r["pattern"], r["city"], r["seed"]) for r in r7]
    insts = []
    for ci, city in enumerate(C.CITIES):
        c = json.loads((C.CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
        g = C.city_graph(c)
        for pattern, cc, seed in keys:
            if cc != city:
                continue
            inst = C.build(c, g, seed) if pattern == "base" else R6.build(c, g, seed, pattern)
            sd = Q.subspace_diag(inst)
            gr = Q.greedy(inst, sorted(range(inst["G"]), key=lambda q: -inst["sizes"][q]))
            gcost = float(sum(inst["cost"][q, s] for q, s in enumerate(gr))) if gr else float(np.max(sd["cost"][sd["feas"]]))
            qa = Q.SubQaoa(inst, "xy", sd)
            probs = np.array([np.abs(qa.state(th)) ** 2 for th in cands])
            cost = np.where(sd["feas"], sd["cost"], np.inf)
            insts.append({"city": city, "probs": probs / probs.sum(axis=1, keepdims=True), "cost": cost, "g": gcost})
    rng = np.random.default_rng(2026)
    cities = sorted({x["city"] for x in insts})
    picks = {c: [] for c in cities}
    for c in cities:
        tr = [x for x in insts if x["city"] != c]
        for _ in range(REPS):
            score = np.zeros(len(cands))
            for x in tr:
                for k in range(len(cands)):
                    shots = rng.choice(len(x["cost"]), size=N, p=x["probs"][k])
                    best = np.min(x["cost"][shots])
                    score[k] += (best if np.isfinite(best) else x["g"]) / x["g"]
            picks[c].append(int(np.argmin(score)))
        print(c, np.bincount(picks[c], minlength=len(cands)).argmax(), flush=True)
    (WORK / "p1_r7b.json").write_text(json.dumps({"N": N, "reps": REPS, "picks": picks}), encoding="utf-8")


if __name__ == "__main__":
    main()
