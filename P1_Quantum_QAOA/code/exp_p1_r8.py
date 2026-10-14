"""P1 eighth revision: confirmatory test on fresh city instances, CVaR baseline, linear-ramp schedule -> <work>/p1_r8.json.

Runs without the twin backend. Nothing here was used to choose anything in exp_p1_r7.py.
  ramp     training-free linear-ramp angles gamma_k = s_g (k - 1/2)/p, beta_k = s_b (1 - (k - 1/2)/p), p = 4, on a
           grid of (s_g, s_b); the scale is chosen by the verified-cost rule (no optima) on the 197 city instances
           of exp_p1_r7.py, then frozen.
  fresh    new city instances, seeds 1000 (c + 1) + k with k = 10..19, all four disruption patterns (main study's and
           exp_p1_r6.py's), never seen by any selection. Per feasible instance: the set chosen in exp_p1_r7.py (the
           verified-cost choice), the frozen ramp, per-instance training with the mean objective and with CVaR
           (alpha = 0.1), both with the main procedure (exp_p1_v2.train, seed of the instance).
usage: python exp_p1_r8.py <work>
"""
import json
import sys
import types
from multiprocessing import Pool
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
from exp_p1_r7 import vcost  # noqa: E402
from exp_p1_v2 import train  # noqa: E402

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
C.CITY_DIR = SHARED / "city_snapshot_2026-10-13" / "backend" / "data" / "cities"
P = 4
SG = (0.5, 1.0, 2.0, 4.0, 8.0)
SB = (0.25, 0.5, 1.0)


def ramp(sg, sb):
    t = (np.arange(1, P + 1) - 0.5) / P
    return np.concatenate([sg * t, sb * (1 - t)])


def build(city, seed, pattern, cache={}):
    if city not in cache:
        c = json.loads((C.CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
        cache[city] = (c, C.city_graph(c))
    c, g = cache[city]
    return C.build(c, g, seed) if pattern == "base" else R6.build(c, g, seed, pattern)


def prep(inst):
    sd = Q.subspace_diag(inst)
    ex = Q.exact_solve(inst)
    opt = sd["obj"] <= ex["obj"] + 1e-6
    gr = Q.greedy(inst, sorted(range(inst["G"]), key=lambda q: -inst["sizes"][q]))
    gcost = float(sum(inst["cost"][q, s] for q, s in enumerate(gr))) if gr else float(np.max(sd["cost"][sd["feas"]]))
    return sd, opt, gcost


def fresh_job(args):
    city, seed, pattern, theta_set, theta_ramp = args
    inst = build(city, seed, pattern)
    if not np.isfinite(Q.exact_solve(inst)["obj"]):
        return None
    sd, opt, _ = prep(inst)
    row = {"city": city, "seed": seed, "pattern": pattern, "uniform": float(opt.sum() / len(opt))}
    for name, th in (("set", theta_set), ("ramp", theta_ramp)):
        pr = np.abs(Q.SubQaoa(inst, "xy", sd).state(np.asarray(th))) ** 2
        row[name] = float(pr[opt].sum())
    for name, a in (("trained", 1.0), ("trained_cvar", 0.1)):
        tr = train(Q.SubQaoa(inst, "xy", sd, alpha=a), opt, sd["feas"], seed)
        row[name] = tr[-1]["popt"]
        row[name + "_nfev"] = sum(x["nfev"] for x in tr)
    return row


def main():
    v2 = json.loads((WORK / "p1_v2.json").read_text(encoding="utf-8"))
    runs = sorted([r for r in v2["results"] if r["task"] == "seed:xy:1.0:0" and r["feasible_instance"]],
                  key=lambda r: r["i"])
    r7 = json.loads((WORK / "p1_r7.json").read_text(encoding="utf-8"))["rows"]
    # the verified-cost choice of exp_p1_r7.py (same set in every fold): lowest mean vcost over all 197 instances
    k_set = int(np.argmin(np.mean([r["vcost"] for r in r7], axis=0)))
    theta_set = runs[k_set]["runs"][3]["theta"]
    # ramp scale chosen by the same rule on the same 197 instances
    grid = [(sg, sb) for sg in SG for sb in SB]
    score = np.zeros(len(grid))
    for r in r7:
        inst = build(r["city"], r["seed"], r["pattern"])
        sd, opt, gcost = prep(inst)
        qa = Q.SubQaoa(inst, "xy", sd)
        for j, (sg, sb) in enumerate(grid):
            score[j] += vcost(np.abs(qa.state(ramp(sg, sb))) ** 2, sd, gcost)
    j = int(np.argmin(score))
    theta_ramp = ramp(*grid[j]).tolist()
    print("set", k_set, "ramp", grid[j], flush=True)
    jobs = [(city, 1000 * (ci + 1) + k, pattern, theta_set, theta_ramp)
            for ci, city in enumerate(C.CITIES) for pattern in ("base",) + R6.PATTERNS for k in range(10, 20)]
    rows = []
    with Pool(3) as pool:
        for r in pool.imap_unordered(fresh_job, jobs):
            if r:
                rows.append(r)
                if len(rows) % 20 == 0:
                    print(len(rows), flush=True)
    (WORK / "p1_r8.json").write_text(json.dumps({"set_index": k_set, "ramp": list(grid[j]), "ramp_theta": theta_ramp,
                                                 "tried": len(jobs), "rows": rows}), encoding="utf-8")


if __name__ == "__main__":
    main()
