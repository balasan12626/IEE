"""P1 fifth revision: exact capacity penalty and an integer-programming baseline -> <work>/p1_r5.json.

Runs without the twin backend, on the 50 feasible OpenStreetMap city instances (frozen snapshot
shared_code/city_snapshot_2026-10-13, rebuilt with exp_p1_cities.build and checked against p1_cities.json).

Encodings of the capacity constraint, both with the ring-XY mixer on the 3^G one-hot plans:
  pair  the paper's pairwise penalty: one term x_gs x_hs for every pair (g, h) that overloads shelter s
  hubo  one product term prod_{g in T} x_gs for every minimal overloading set T of shelter s (sum of sizes
        > remaining seats, every proper subset fits); the pairs are the minimal sets of size two. A shelter
        is overloaded exactly when its groups contain a minimal overloading set, so penalty-free <=> feasible.
        This is also checked exhaustively on every instance.
Same penalty weight mu, scaling (divide by mu - 1), training procedure (exp_p1_v2.train: COBYLA <= 250
evaluations per start, depths 1..4, 2 random starts + INTERP, seed of the instance) and fixed 12-qubit angle
sets (p1_r3.json, rules popt = eq. 7 and energy) for both encodings.
Gate counts per layer (all-to-all): each distinct Z-string of weight w >= 2 in the expanded cost costs 2(w - 1)
CNOTs; the ring-XY mixer costs 2 CNOTs per XY term (3 per group). Slack encoding size: ceil(log2(R_s + 1))
qubits per shelter with seats left. Classical: exhaustive search (qaoa_sim.exact_solve) and the integer
program solved by HiGHS (scipy.optimize.milp), both timed (median of 5 runs).
usage: python exp_p1_r5.py <work>
"""
import itertools
import json
import math
import sys
import time
import types
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

HERE = Path(__file__).resolve().parent
SHARED = HERE.parents[1] / "shared_code"
sys.path[:0] = [str(SHARED), str(HERE)]
if "exp_p1" not in sys.modules:  # exp_p1 imports the twin backend; only its training code is needed here
    try:
        import exp_p1  # noqa: F401
    except ImportError:
        sys.modules["exp_p1"] = types.SimpleNamespace(disrupted=None)
import qaoa_sim as Q  # noqa: E402
import exp_p1_cities as C  # noqa: E402
from exp_p1_v2 import train  # noqa: E402

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
C.CITY_DIR = SHARED / "city_snapshot_2026-10-13" / "backend" / "data" / "cities"
RULES = ("popt", "energy")


def minimal_overload_sets(inst):
    """(T, s): minimal sets T of groups allowed at shelter s whose total size exceeds its remaining seats."""
    out = []
    for s in range(inst["S"]):
        ok = [g for g in range(inst["G"]) if not inst["forb"][g, s]]
        for k in range(2, len(ok) + 1):
            for T in itertools.combinations(ok, k):
                tot = sum(int(inst["sizes"][g]) for g in T)
                if tot > inst["rem"][s] and all(tot - int(inst["sizes"][g]) <= inst["rem"][s] for g in T):
                    out.append((T, s))
    return out


def hubo_diag(inst, sd):
    """Copy of the subspace diagonal with the pairwise capacity terms replaced by the minimal-set terms."""
    A = sd["plans"]
    rows = np.arange(inst["G"])
    lin_s = Q.shifted_cost(inst)[rows, A].sum(axis=1)
    forb_viol = inst["forb"][rows, A].sum(axis=1).astype(float)
    viol = np.zeros(len(A))
    sets = minimal_overload_sets(inst)
    for T, s in sets:
        viol += np.all(A[:, list(T)] == s, axis=1)
    d = dict(sd)
    d["h_xy"] = lin_s + sd["P"] * (forb_viol + viol)
    return d, sets


def cnot_per_layer(inst, sets):
    """CNOTs of one cost layer plus one ring-XY layer, all-to-all connectivity."""
    terms = set()
    for T, s in sets:
        q = [3 * g + s for g in T]
        for w in range(2, len(q) + 1):
            terms.update(itertools.combinations(sorted(q), w))
    return sum(2 * (len(t) - 1) for t in terms) + 2 * 3 * inst["G"], len(terms)


def milp_solve(inst):
    G, S = inst["G"], inst["S"]
    c = (inst["cost"] + inst["stab"]).ravel()
    A_one = np.zeros((G, G * S))
    for g in range(G):
        A_one[g, g * S:(g + 1) * S] = 1
    A_cap = np.zeros((S, G * S))
    for s in range(S):
        for g in range(G):
            A_cap[s, g * S + s] = inst["sizes"][g]
    ub = np.where(inst["forb"].ravel(), 0, 1)
    cons = [LinearConstraint(A_one, 1, 1), LinearConstraint(A_cap, -np.inf, inst["rem"])]
    r = milp(c, constraints=cons, integrality=np.ones(G * S), bounds=Bounds(0, ub))
    return r


def timed(fn, reps=5):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        out = fn()
        ts.append((time.perf_counter() - t0) * 1000)
    return out, float(np.median(ts))


def main():
    fixed = json.loads((WORK / "p1_r3.json").read_text(encoding="utf-8"))["fixed"]
    stored = json.loads((WORK / "p1_cities.json").read_text(encoding="utf-8"))["rows"]
    graphs, rows = {}, []
    for r in stored:
        if not r["feasible_instance"]:
            continue
        city = r["city"]
        if city not in graphs:
            c = json.loads((C.CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
            graphs[city] = (c, C.city_graph(c))
        inst = C.build(*graphs[city], r["seed"])
        ex, ex_ms = timed(lambda: Q.exact_solve(inst))
        sd = Q.subspace_diag(inst)
        opt = sd["obj"] <= ex["obj"] + 1e-6
        assert abs(opt.sum() / 81 - r["uniform"]) < 1e-12 and int(sd["feas"].sum()) == r["n_feasible"], \
            "city instance rebuilt identically"
        hd, sets = hubo_diag(inst, sd)
        lin = Q.shifted_cost(inst)[np.arange(inst["G"]), sd["plans"]].sum(axis=1)
        pen_free = {"pair": np.isclose(sd["h_xy"], lin), "hubo": np.isclose(hd["h_xy"], lin)}
        assert np.array_equal(pen_free["hubo"], sd["feas"]), "minimal-set penalty is exact on this instance"
        mi, mi_ms = timed(lambda: milp_solve(inst))
        assert mi.status == 0 and abs(mi.fun - ex["obj"]) < 1e-6, "HiGHS finds the exhaustive optimum"
        row = {"city": city, "seed": r["seed"], "binding": r["binding"], "n_feas": int(sd["feas"].sum()),
               "exact_ms": ex_ms, "milp_ms": mi_ms, "n_sets": len(sets),
               "n_sets_big": sum(len(T) > 2 for T, _ in sets),
               "slack_qubits": int(sum(math.ceil(math.log2(R + 1)) for R in inst["rem"] if R > 0))}
        pairs = [(T, s) for T, s in sets if len(T) == 2]
        assert len(pairs) == len(Q.overload_pairs(inst)), "pairwise terms are the size-two minimal sets"
        for enc, d, ss in (("pair", sd, pairs), ("hubo", hd, sets)):
            row[f"{enc}:pen_free_infeas"] = int((pen_free[enc] & ~sd["feas"]).sum())
            row[f"{enc}:minimiser_opt"] = bool(opt[int(np.argmin(d["h_xy"]))])
            row[f"{enc}:cnot"], row[f"{enc}:zterms"] = cnot_per_layer(inst, ss)
            qa = Q.SubQaoa(inst, "xy", d)
            tr = train(qa, opt, sd["feas"], r["seed"])
            row[f"{enc}:trained"] = tr[-1]["popt"]
            row[f"{enc}:trained_feas"] = tr[-1]["pfeas"]
            row[f"{enc}:nfev"] = sum(x["nfev"] for x in tr)
            for rule in RULES:
                pr = np.abs(Q.SubQaoa(inst, "xy", d).state(np.asarray(fixed[f"xy:1.0:4:{rule}"]))) ** 2
                row[f"{enc}:{rule}"] = float(pr[opt].sum())
                row[f"{enc}:{rule}_feas"] = float(pr[sd["feas"]].sum())
        assert abs(row["pair:popt"] - r["xy:1.0:4"]["fixed"]) < 1e-9, "pairwise fixed angles reproduce p1_cities.json"
        rows.append(row)
        print(f"{city} {r['seed']} sets={len(sets)} pair={row['pair:trained']:.3f}/{row['pair:trained_feas']:.3f} "
              f"hubo={row['hubo:trained']:.3f}/{row['hubo:trained_feas']:.3f} fixO {row['pair:popt']:.3f}->"
              f"{row['hubo:popt']:.3f}", flush=True)
    (WORK / "p1_r5.json").write_text(json.dumps({"rows": rows}, indent=0), encoding="utf-8")


if __name__ == "__main__":
    main()
