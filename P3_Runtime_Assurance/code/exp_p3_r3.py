"""P3 third revision: a one-hot-preserving annealer inside the same loop at city scale -> <work>/p3_r3.json.

Runs without the twin backend (only the city code path of exp_p3_v2 is used; its backend imports are stubbed).
Same 360 city instances, seeds, energy (exp_p3_v2.qubo: shifted cost + P (one-hot + forbidden + pairwise
capacity)), 64 chains, 40 sweeps, temperature schedule and draws as the paper's bit-flip annealer, but each move
reassigns one group to another shelter, so every chain stays one-hot. The returned plans go through the same
loop (exp_p3_v2.run_loop: exact verification, greedy fallback, MILP certificate), fixed budget of 64 shots.
usage: python exp_p3_r3.py <work>
"""
import json
import sys
import time
import types
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SHARED = HERE.parents[1] / "shared_code"
sys.path[:0] = [str(SHARED), str(HERE)]
for name in ("backend", "backend.simulation"):
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules.setdefault("backend.simulation.hqrl_demo", types.SimpleNamespace(HqrlConfig=None, HqrlEngine=None))
sys.modules.setdefault("exp_p3", types.SimpleNamespace(apply_event=None, state_key=None))
import exp_p3_v2 as E  # noqa: E402

E.ROOT = SHARED / "city_snapshot_2026-10-13"
WORK = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SWEEPS = 40


def onehot_sa(cost, forb, sizes, rem, shots, rng, sweeps=SWEEPS):
    """Annealing over one-hot plans on the energy of exp_p3_v2.qubo; returns one plan per chain."""
    G, S = cost.shape
    big = np.where(forb, np.inf, cost)
    lo = np.where(np.isfinite(big.min(axis=1)), big.min(axis=1), 0.0)
    cs = np.where(forb, 0.0, cost - lo[:, None])
    P = 1.0 + cs.max(axis=1).sum()
    unary = cs + P * forb  # per (group, shelter)
    ov = np.zeros((S, G, G))  # pairwise capacity term, as in exp_p3_v2.qubo
    for s in range(S):
        for g in range(G):
            for h in range(G):
                if g != h and not forb[g, s] and not forb[h, s] and sizes[g] + sizes[h] > rem[s]:
                    ov[s, g, h] = P
    a = rng.integers(0, S, size=(shots, G))
    ch = np.arange(shots)
    T0 = max(P, 1.0)
    for sw in range(sweeps):
        T = T0 * 0.002 ** (sw / max(sweeps - 1, 1)) + 1e-9
        for g in rng.permutation(G):
            old = a[:, g]
            new = (old + 1 + rng.integers(0, S - 1, size=shots)) % S
            # pair penalty of g at a shelter = sum over other groups h placed there
            pen_old = np.einsum("ch,ch->c", ov[old, g, :], (a == old[:, None]).astype(float))
            pen_new = np.einsum("ch,ch->c", ov[new, g, :], (a == new[:, None]).astype(float))
            d = unary[g, new] - unary[g, old] + pen_new - pen_old
            acc = (d <= 0) | (rng.random(shots) < np.exp(-np.clip(d, 0, None) / T))
            a[ch[acc], g] = new[acc]
    return [tuple(int(x) for x in row) for row in a]


def job(args):
    city, G, tight, k = args
    E.sa_sample = lambda lin, Qs, P, shots, rng, sweeps=40: None  # not used here
    import zlib
    import networkx as nx
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
    failed = int(rng.integers(S))
    rem[failed] = 0
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
    a_m, obj_m, ms_m, status = E.milp_solve(cost, forb, sizes, rem)
    feasible = a_m is not None
    draws = []
    t_sa = []
    for dr in range(E.DRAWS):
        rr = np.random.default_rng(seed + 7919 * dr)
        t0 = time.perf_counter()
        smp = onehot_sa(cost, forb, sizes, rem, E.SHOTS, rr)
        t_sa.append((time.perf_counter() - t0) * 1000)
        draws.append(E.run_loop(smp, cost, forb, sizes, rem, obj_m if feasible else np.inf, feasible, False))
    return {"city": city, "G": G, "tight": tight, "k": k, "feasible": feasible, "milp_status": status,
            "sa_ms": float(np.median(t_sa)), "draws": draws}


if __name__ == "__main__":
    jobs = [(c, G, t, k) for c in E.CITIES for G in (8, 16, 32) for t in (0.6, 0.9) for k in range(10)]
    out, t0 = [], time.time()
    with Pool(3) as pool:
        for r in pool.imap_unordered(job, jobs):
            out.append(r)
            if len(out) % 30 == 0:
                print(f"{len(out)}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    (WORK / "p3_r3.json").write_text(json.dumps({"sweeps": SWEEPS, "rows": out}), encoding="utf-8")
