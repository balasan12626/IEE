"""P3 fourth revision (city scale, no twin backend needed) -> <work>/p3_r4.json.

  infeas   why each of the 360 city instances has no valid plan: a group with no allowed shelter (empty row),
           total group size above the seats of all open shelters (aggregate), or neither (combinatorial).
  sweep    bit-flip annealer of exp_p3_v2 on the 108-instance subset of the paper's 400-sweep check (k < 3 per city,
           size and demand) with the penalty weight scaled by m in {0.25, 1, 4} and, for m in {1, 4}, a temperature
           schedule ending at 5 % of the median nonzero shifted cost instead of 0.2 % of P; 64 chains, 40 sweeps,
           10 draws, same seeds. Per draw: valid sample found, and the first rule broken by the top sample
           (exp_p3_viol.classify).
  onehot   the one-hot annealer of exp_p3_r3 on all 360 instances, with the class of every unsafe top sample.
usage: python exp_p3_r4.py <work>
"""
import json
import sys
import time
import zlib
from multiprocessing import Pool
from pathlib import Path

import networkx as nx
import numpy as np

import exp_p3_r3 as R3  # stubs the twin backend and sets E.ROOT to the city snapshot
from exp_p3_r3 import E, onehot_sa

sys.argv = sys.argv[:2] + ["x"]  # exp_p3_viol reads sys.argv[1] at import
from exp_p3_viol import classify  # noqa: E402

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
CONFIGS = (("m0.25", 0.25, False), ("m1", 1.0, False), ("m4", 4.0, False), ("m1T", 1.0, True), ("m4T", 4.0, True))


def build(city, G, tight, k):
    c = json.loads((E.ROOT / "backend" / "data" / "cities" / f"{city}.json").read_text(encoding="utf-8"))
    g = E.city_graph(c)
    nodes = list(g.nodes)
    seed = zlib.crc32(f"{city}|{G}|{tight}|{k}".encode())
    rng = np.random.default_rng(seed)
    S = len(c["shelters"])
    zn = [E.nearest(c, z["lat"], z["lon"], nodes) for z in c["zones"]]
    sn = [E.nearest(c, s["lat"], s["lon"], nodes) for s in c["shelters"]]
    cap = np.array([float(s["capacity"]) for s in c["shelters"]])
    rem = cap * (1 - rng.uniform(0.15, 0.45, S))
    closed = sorted({d["rid"] for _, _, d in g.edges(data=True)}, key=lambda rid: -max(
        d["flood"] for _, _, d in g.edges(data=True) if d["rid"] == rid))[:3]
    h = g.copy()
    h.remove_edges_from([(u, v) for u, v, d in g.edges(data=True) if d["rid"] in closed])
    rem[int(rng.integers(S))] = 0
    gz = rng.integers(len(zn), size=G)
    sizes = rng.uniform(0.5, 1.5, G)
    sizes = np.maximum(1, np.round(sizes / sizes.sum() * tight * rem.sum())).astype(float)
    dist = {z: nx.single_source_dijkstra_path_length(h, zn[z], weight="w") for z in set(gz.tolist())}
    cost = np.zeros((G, S))
    forb = np.zeros((G, S), dtype=bool)
    for gi in range(G):
        for s in range(S):
            dd = dist[gz[gi]].get(sn[s])
            if dd is None or rem[s] <= 0 or sizes[gi] > rem[s]:
                forb[gi, s] = True
            else:
                cost[gi, s] = dd / 25.0 * 60.0
    return cost, forb, sizes, rem, seed


def qubo_w(cost, forb, sizes, rem, m):
    """exp_p3_v2.qubo with every penalty term scaled by m; returns lin, Qs, P_used, cs."""
    lin, Qs, P = E.qubo(cost, forb, sizes, rem)
    G, S = cost.shape
    big = np.where(forb, np.inf, cost)
    lo = np.where(np.isfinite(big.min(axis=1)), big.min(axis=1), 0.0)
    cs = np.where(forb, 0.0, cost - lo[:, None]).ravel()
    return cs + m * (lin - cs), m * Qs, m * P, cs


def sa_sched(lin, Qs, T0, Tend, shots, rng, sweeps=40):
    """exp_p3_v2.sa_sample with an explicit geometric schedule from T0 to Tend."""
    n = len(lin)
    x = rng.integers(0, 2, size=(shots, n)).astype(np.float64)
    h = x @ Qs
    for sw in range(sweeps):
        T = T0 * (Tend / T0) ** (sw / max(sweeps - 1, 1)) + 1e-9
        for i in rng.permutation(n):
            d = (1 - 2 * x[:, i]) * (lin[i] + h[:, i])
            acc = (d <= 0) | (rng.random(shots) < np.exp(-np.clip(d, 0, None) / T))
            flip = np.where(acc, 1 - 2 * x[:, i], 0.0)
            x[:, i] += flip
            h += np.outer(flip, Qs[i])
    return x.astype(np.int8)


def top_class(samples, forb, sizes, rem):
    cnt = {}
    for a in samples:
        cnt[a] = cnt.get(a, 0) + 1
    return classify(max(cnt, key=cnt.get), forb, sizes, rem)


def job(args):
    city, G, tight, k = args
    cost, forb, sizes, rem, seed = build(city, G, tight, k)
    a_m, obj_m, ms_m, status = E.milp_solve(cost, forb, sizes, rem)
    feasible = a_m is not None
    empty = bool((forb.all(axis=1)).any())
    aggregate = bool(sizes.sum() > rem[rem > 0].sum() + 1e-9)
    out = {"city": city, "G": G, "tight": tight, "k": k, "feasible": feasible,
           "infeas": None if feasible else ("empty_row" if empty else "aggregate" if aggregate else "combinatorial")}
    oh = []
    for dr in range(E.DRAWS):
        rr = np.random.default_rng(seed + 7919 * dr)
        smp = onehot_sa(cost, forb, sizes, rem, E.SHOTS, rr)
        valid = [a for a in smp if E.verify(a, forb, sizes, rem)]
        oh.append({"found": bool(valid), "cls": top_class(smp, forb, sizes, rem)})
    out["onehot"] = oh
    if k < 3:
        cs_nz = None
        for name, m, sched in CONFIGS:
            lin, Qs, P, cs = qubo_w(cost, forb, sizes, rem, m)
            if cs_nz is None:
                pos = cs[cs > 0]
                cs_nz = float(np.median(pos)) if len(pos) else 1.0
            T0 = max(P, 1.0)
            Tend = 0.05 * cs_nz if sched else 0.002 * T0
            res = []
            for dr in range(E.DRAWS):
                rr = np.random.default_rng(seed + 7919 * dr)
                smp = E.decode(sa_sched(lin, Qs, T0, Tend, E.SHOTS, rr), G, cost.shape[1])
                valid = [a for a in smp if E.verify(a, forb, sizes, rem)]
                res.append({"found": bool(valid), "cls": top_class(smp, forb, sizes, rem)})
            out[name] = res
    return out


if __name__ == "__main__":
    jobs = [(c, G, t, k) for c in E.CITIES for G in (8, 16, 32) for t in (0.6, 0.9) for k in range(10)]
    out, t0 = [], time.time()
    with Pool(3) as pool:
        for r in pool.imap_unordered(job, jobs):
            out.append(r)
            if len(out) % 30 == 0:
                print(f"{len(out)}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    (WORK / "p3_r4.json").write_text(json.dumps({"configs": [c[0] for c in CONFIGS], "rows": out}), encoding="utf-8")
