"""P1 seventh revision: angle-set selection without optima, leave one city out -> <work>/p1_r7.json.

Runs without the twin backend. Candidates: the 30 angle sets trained per instance on the twin's development set
(p1_v2.json, task seed:xy:1.0:0, p = 4; the sets from which rule (7) and the energy rule chose, see p1_r3.json).
Instances: the 50 feasible city instances of the main study (exp_p1_cities.build) and the feasible city instances
of the three other disruption patterns (exp_p1_r6.build). For every instance and candidate, on the paper's pairwise
QUBO (3^G one-hot amplitudes, qaoa_sim.SubQaoa) we store:
  popt     probability of an optimal plan (needs the optimum: oracle, reference only)
  energy   <E>/Delta (estimable on a device)
  vcost    expected cost of the cheapest verified plan among N = 32 shots, the greedy plan when no shot is valid,
           divided by the greedy plan's cost (estimable on a device: needs only the verifier and the greedy rule)
plus the uniform-sampling value of vcost. Selection and testing are done in post_p1_r7.py.
usage: python exp_p1_r7.py <work>
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
N = 32


def vcost(pr, sd, greedy_cost):
    """E[cost of cheapest verified plan among N shots, greedy plan if none] / greedy cost."""
    feas = np.where(sd["feas"])[0]
    order = feas[np.argsort(sd["cost"][feas], kind="stable")]
    q = pr[order]
    cum = np.concatenate([[0.0], np.cumsum(q)])
    p_best = (1 - cum[:-1]) ** N - (1 - cum[1:]) ** N
    p_none = (1 - cum[-1]) ** N
    return float((p_best @ sd["cost"][order] + p_none * greedy_cost) / greedy_cost)


def main():
    v2 = json.loads((WORK / "p1_v2.json").read_text(encoding="utf-8"))
    runs = sorted([r for r in v2["results"] if r["task"] == "seed:xy:1.0:0" and r["feasible_instance"]],
                  key=lambda r: r["i"])
    cands = [np.asarray(r["runs"][3]["theta"]) for r in runs]
    r3 = json.loads((WORK / "p1_r3.json").read_text(encoding="utf-8"))
    assert np.allclose(cands[r3["variants"]["xy:1.0"]["4"]["choice"]["popt"]["from_instance"]],
                       r3["fixed"]["xy:1.0:4:popt"]), "candidate list reproduces the stored rule (7) set"
    trained = {(r["city"], r["seed"]): r["xy:1.0:4"]["trained"]
               for r in json.loads((WORK / "p1_cities.json").read_text(encoding="utf-8"))["rows"] if r["feasible_instance"]}
    r6 = {(r["pattern"], r["city"], r["seed"]): r for r in json.loads((WORK / "p1_r6.json").read_text(encoding="utf-8"))["rows"]}
    rows = []
    for ci, city in enumerate(C.CITIES):
        c = json.loads((C.CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
        g = C.city_graph(c)
        for pattern in ("base",) + R6.PATTERNS:
            for k in range(C.SEEDS_PER_CITY):
                seed = 1000 * (ci + 1) + k
                if pattern == "base":
                    if (city, seed) not in trained:
                        continue
                    inst, tr = C.build(c, g, seed), trained[(city, seed)]
                else:
                    if (pattern, city, seed) not in r6:
                        continue
                    inst, tr = R6.build(c, g, seed, pattern), r6[(pattern, city, seed)]["trained"]
                ex = Q.exact_solve(inst)
                sd = Q.subspace_diag(inst)
                opt = sd["obj"] <= ex["obj"] + 1e-6
                gr = Q.greedy(inst, sorted(range(inst["G"]), key=lambda q: -inst["sizes"][q]))
                if gr is None:  # greedy fails: fall back to the costliest feasible plan as the device's last resort
                    gcost = float(np.max(sd["cost"][sd["feas"]]))
                else:
                    gcost = float(sum(inst["cost"][q, s] for q, s in enumerate(gr)))
                qa = Q.SubQaoa(inst, "xy", sd)
                row = {"city": city, "seed": seed, "pattern": pattern, "trained": float(tr),
                       "greedy_ok": gr is not None,
                       "uniform_vcost": vcost(np.full(len(opt), 1 / len(opt)), sd, gcost),
                       "popt": [], "energy": [], "vcost": []}
                for th in cands:
                    pr = np.abs(qa.state(th)) ** 2
                    row["popt"].append(float(pr[opt].sum()))
                    row["energy"].append(float(pr @ qa.hn))
                    row["vcost"].append(vcost(pr, sd, gcost))
                rows.append(row)
        print(city, len(rows), flush=True)
    (WORK / "p1_r7.json").write_text(json.dumps({"n_candidates": len(cands), "N": N, "rows": rows}), encoding="utf-8")


if __name__ == "__main__":
    main()
