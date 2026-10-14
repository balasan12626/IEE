"""P1 sixth revision: fixed angles under other disruption patterns on the city road networks -> <work>/p1_r6.json.

Runs without the twin backend. City instances as in exp_p1_cities.build (same cities, seeds 1000 (c + 1) + k,
k = 0..9, G = 4 groups, 3 shelters, 12 qubits), but with three disruption patterns that the paper's main study
does not use:
  roads    the two most flood-exposed roads on any zone->shelter path close; no shelter surge
  shelter  the most flood-exposed road closes and the first shelter fails (no seats)
  cut      the most flood-exposed road closes and the second shelter loses 70 % of its remaining seats
Per feasible instance: the 12-qubit angle sets fixed on the twin's development set (p1_r3.json, rules popt = eq. 7,
energy and cvar; XY mixer, mean objective, p = 4) applied unchanged, against per-instance training with the main
procedure (exp_p1_v2.train, seed of the instance), all on the paper's pairwise QUBO, simulated on the 3^G one-hot
amplitudes (qaoa_sim.SubQaoa).
usage: python exp_p1_r6.py <work>
"""
import json
import sys
import types
from pathlib import Path

import networkx as nx
import numpy as np

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
PATTERNS = ("roads", "shelter", "cut")
RULES = ("popt", "energy", "cvar")
G, S = C.G, C.S


def build(c, g, seed, pattern):
    """exp_p1_cities.build with another disruption (same random draws for zones, shelters, seats and sizes)."""
    rng = np.random.default_rng(seed)
    comp = max(nx.connected_components(g), key=len)
    nodes = list(comp)
    zones = [c["zones"][k] for k in rng.choice(len(c["zones"]), G, replace=False)]
    shel = [c["shelters"][k] for k in rng.choice(len(c["shelters"]), S, replace=False)]
    zn = [C.nearest(c, z["lat"], z["lon"], nodes) for z in zones]
    sn = [C.nearest(c, s["lat"], s["lon"], nodes) for s in shel]
    cap = np.array([120, 90, 70])
    rem = (cap * (1 - rng.uniform(0.15, 0.45, S))).astype(int)
    sizes = rng.integers(8, 23, G)
    used = {}
    for a in zn:
        for b in sn:
            if a != b:
                p = nx.shortest_path(g, a, b, weight="w")
                for u, v in zip(p, p[1:]):
                    used[g[u][v]["rid"]] = g[u][v]["flood"]
    ranked = sorted(used, key=used.get, reverse=True)
    closed = set(ranked[:2] if pattern == "roads" else ranked[:1])
    h = g.copy()
    h.remove_edges_from([(u, v) for u, v, d in g.edges(data=True) if d["rid"] in closed])
    failed = np.zeros(S, dtype=bool)
    if pattern == "shelter":
        failed[0] = True
        rem[0] = 0
    elif pattern == "cut":
        rem[1] = int(rem[1] * 0.3)
    cost = np.zeros((G, S))
    forb = np.zeros((G, S), dtype=bool)
    for gi, a in enumerate(zn):
        for si, b in enumerate(sn):
            if failed[si]:
                forb[gi, si] = True
                continue
            try:
                p = nx.shortest_path(h, a, b, weight="w") if a != b else [a]
            except nx.NetworkXNoPath:
                forb[gi, si] = True
                continue
            km = sum(h[u][v]["km"] for u, v in zip(p, p[1:]))
            wkm = sum(h[u][v]["w"] for u, v in zip(p, p[1:]))
            haz = sum(h[u][v]["km"] * h[u][v]["flood"] for u, v in zip(p, p[1:])) / km if km > 0 else 0.0
            cost[gi, si] = wkm / 25.0 * 60.0 + 5.0 * haz
            if sizes[gi] > rem[si]:
                forb[gi, si] = True
    return {"G": G, "S": S, "sizes": sizes, "rem": rem, "cost": cost, "forb": forb, "stab": np.zeros((G, S))}


def main():
    fixed = json.loads((WORK / "p1_r3.json").read_text(encoding="utf-8"))["fixed"]
    rows, tried = [], {p: 0 for p in PATTERNS}
    for ci, city in enumerate(C.CITIES):
        c = json.loads((C.CITY_DIR / f"{city}.json").read_text(encoding="utf-8"))
        g = C.city_graph(c)
        for pattern in PATTERNS:
            for k in range(C.SEEDS_PER_CITY):
                seed = 1000 * (ci + 1) + k
                inst = build(c, g, seed, pattern)
                tried[pattern] += 1
                ex = Q.exact_solve(inst)
                if not np.isfinite(ex["obj"]):
                    continue
                sd = Q.subspace_diag(inst)
                opt = sd["obj"] <= ex["obj"] + 1e-6
                naive = tuple(int(np.argmin(np.where(inst["forb"][gg], np.inf, inst["cost"][gg]))) for gg in range(G))
                row = {"city": city, "seed": seed, "pattern": pattern, "binding": naive != ex["assign"],
                       "uniform": float(opt.sum() / 3 ** G), "n_feas": int(sd["feas"].sum())}
                for rule in RULES:
                    pr = np.abs(Q.SubQaoa(inst, "xy", sd).state(np.asarray(fixed[f"xy:1.0:4:{rule}"]))) ** 2
                    row[rule] = float(pr[opt].sum())
                    row[rule + "_feas"] = float(pr[sd["feas"]].sum())
                tr = train(Q.SubQaoa(inst, "xy", sd), opt, sd["feas"], seed)
                row["trained"] = tr[-1]["popt"]
                row["trained_feas"] = tr[-1]["pfeas"]
                row["nfev"] = sum(x["nfev"] for x in tr)
                rows.append(row)
                print(f"{pattern} {city} {seed} trained={row['trained']:.3f} popt={row['popt']:.3f} "
                      f"energy={row['energy']:.3f}", flush=True)
    (WORK / "p1_r6.json").write_text(json.dumps({"tried": tried, "rows": rows}), encoding="utf-8")


if __name__ == "__main__":
    main()
