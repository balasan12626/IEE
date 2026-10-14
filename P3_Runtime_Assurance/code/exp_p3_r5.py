"""P3 fifth revision (city scale, no twin backend needed) -> <work>/p3_r5.json.

  raw      the paper's bit-flip annealer (exp_p3_v2.sa_sample, 64 chains, 40 sweeps, same seeds, fixed budget) on all
           360 city instances, scored on the raw bit vectors instead of decoded plans. exp_p3_v2.decode maps every
           vector that is not one-hot to one outcome (None), so the "most frequent sample" pooled all broken vectors.
           Here: the most frequent raw vector (ties broken by lower QUBO energy), the lowest-energy raw vector, the
           share of one-hot vectors, and whether any vector occurred twice.
  deadline the MILP of exp_p3_v2.milp_solve with a real time limit of 0.5, 1, 2 and 5 s on every instance: status,
           whether an incumbent was returned, and whether it is valid and optimal (against the 60 s solve).
  recheck  every instance the 60 s solve called infeasible, solved again with presolve off.
usage: python exp_p3_r5.py <work>
"""
import json
import time
from multiprocessing import Pool

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

import exp_p3_r3 as R3  # stubs the twin backend and sets E.ROOT to the city snapshot
from exp_p3_r3 import E
from exp_p3_r4 import build

WORK = R3.WORK
LIMITS = (0.5, 1.0, 2.0, 5.0)


def solve(cost, forb, sizes, rem, limit, presolve=True):
    G, S = cost.shape
    n = G * S
    A_one = np.zeros((G, n))
    for g in range(G):
        A_one[g, g * S:(g + 1) * S] = 1
    A_cap = np.zeros((S, n))
    for g in range(G):
        for s in range(S):
            A_cap[s, g * S + s] = sizes[g]
    t0 = time.perf_counter()
    r = milp(np.where(forb, 0.0, cost).ravel(), constraints=[LinearConstraint(A_one, 1, 1),
                                                             LinearConstraint(A_cap, -np.inf, rem)],
             integrality=np.ones(n), bounds=Bounds(np.zeros(n), np.where(forb.ravel(), 0.0, 1.0)),
             options={"time_limit": limit, "presolve": presolve})
    s = time.perf_counter() - t0
    a = None
    if r.x is not None:
        x = np.round(r.x).reshape(G, S)
        a = tuple(int(np.argmax(x[g])) for g in range(G)) if (x.sum(axis=1) == 1).all() else None
    return int(r.status), a, (float(r.fun) if r.x is not None else None), s


def job(args):
    city, G, tight, k = args
    cost, forb, sizes, rem, seed = build(city, G, tight, k)
    st, a_m, obj_m, s_m = solve(cost, forb, sizes, rem, 60.0)
    feasible = a_m is not None
    out = {"city": city, "G": G, "tight": tight, "k": k, "feasible": feasible, "status60": st, "s60": s_m}
    lin, Qs, P = E.qubo(cost, forb, sizes, rem)
    S = cost.shape[1]
    raw = []
    for dr in range(E.DRAWS):
        rr = np.random.default_rng(seed + 7919 * dr)
        x = E.sa_sample(lin, Qs, P, E.SHOTS, rr, sweeps=40).astype(float)
        en = x @ lin + 0.5 * np.einsum("ij,jk,ik->i", x, Qs, x)
        keys = [row.tobytes() for row in x.astype(np.int8)]
        cnt = {}
        for kk in keys:
            cnt[kk] = cnt.get(kk, 0) + 1
        best = {}
        for i, kk in enumerate(keys):
            best[kk] = min(best.get(kk, np.inf), en[i])
        top = min(cnt, key=lambda kk: (-cnt[kk], best[kk]))
        i_top = keys.index(top)
        i_low = int(np.argmin(en))
        dec = E.decode(x.astype(np.int8), G, S)
        raw.append({"top_unsafe": not E.verify(dec[i_top], forb, sizes, rem),
                    "low_unsafe": not E.verify(dec[i_low], forb, sizes, rem),
                    "top_count": int(cnt[top]), "onehot_share": float(np.mean([d is not None for d in dec])),
                    "decoded_top_none": max({d: dec.count(d) for d in set(dec)}.items(), key=lambda t: t[1])[0] is None})
    out["raw"] = raw
    dl = {}
    for lim in LIMITS:
        st, a, obj, s = solve(cost, forb, sizes, rem, lim)
        dl[str(lim)] = {"status": st, "s": s, "incumbent": a is not None,
                        "valid": bool(a is not None and E.verify(a, forb, sizes, rem)),
                        "optimal": bool(a is not None and feasible and abs(obj - obj_m) <= 1e-6 * max(1.0, abs(obj_m)))}
    out["deadline"] = dl
    if not feasible:
        st2, a2, _, _ = solve(cost, forb, sizes, rem, 600.0, presolve=False)
        out["recheck_status"] = st2
    return out


if __name__ == "__main__":
    jobs = [(c, G, t, k) for c in E.CITIES for G in (8, 16, 32) for t in (0.6, 0.9) for k in range(10)]
    out, t0 = [], time.time()
    with Pool(3) as pool:
        for r in pool.imap_unordered(job, jobs):
            out.append(r)
            if len(out) % 30 == 0:
                print(f"{len(out)}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    (WORK / "p3_r5.json").write_text(json.dumps({"limits": LIMITS, "rows": out}), encoding="utf-8")
