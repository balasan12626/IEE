"""Eighth-revision numbers for P1 -> macros.

Reads p1_r8.json (exp_p1_r8.py): fresh city instances (seeds never used in any selection), all four disruption
patterns. Compares the set chosen by the verified-cost rule in exp_p1_r7.py and a training-free linear ramp (scale
chosen by the same rule) with per-instance training under the mean and the CVaR objective. Tests: two-sided Wilcoxon
signed-rank on per-instance P_opt and success@32, Holm over the family below; per-city sign test. Every claim in the
text is asserted. Called from post_p1.py.
"""
import json

import numpy as np
from scipy.stats import binomtest, wilcoxon

from post_p1_r3 import holm, s32  # noqa: E402
from post_p1_v2 import sci  # noqa: E402


def sv(x):
    return 1 - (1 - np.asarray(x)) ** 32


def extend(put, work):
    d = json.loads((work / "p1_r8.json").read_text(encoding="utf-8"))
    R = d["rows"]
    r7 = json.loads((work / "p1_r7.json").read_text(encoding="utf-8"))
    assert {(r["city"], r["seed"]) for r in R}.isdisjoint({(r["city"], r["seed"]) for r in r7["rows"]}), \
        "text: fresh instances share no seed with the selection instances"
    cities = sorted({r["city"] for r in R})
    A = {k: np.array([r[k] for r in R]) for k in ("set", "ramp", "trained", "trained_cvar", "uniform")}
    put("FrN", str(len(R)))
    put("FrTried", str(d["tried"]))
    put("FrCities", str(len(cities)))
    put("FrRampG", f"{d['ramp'][0]:g}")
    put("FrRampB", f"{d['ramp'][1]:g}")
    for k, tg in (("set", "Set"), ("ramp", "Ramp"), ("trained", "Trained"), ("trained_cvar", "Cvar"), ("uniform", "Uni")):
        put(f"Fr{tg}Opt", f"{A[k].mean():.3f}")
        put(f"Fr{tg}Succ", f"{s32(A[k]):.1f}")
    tests = [("set", "trained", "opt"), ("set", "trained", "s"), ("set", "trained_cvar", "opt"),
             ("set", "trained_cvar", "s"), ("set", "ramp", "opt"), ("set", "ramp", "s")]
    raw = []
    for a, b, m in tests:
        x, y = (A[a], A[b]) if m == "opt" else (sv(A[a]), sv(A[b]))
        raw.append(wilcoxon(x, y).pvalue)
    adj = dict(zip(tests, holm(raw)))
    put("FrFamily", str(len(tests)))
    for (a, b, m), p in adj.items():
        put("FrP" + {"trained": "T", "trained_cvar": "C", "ramp": "R"}[b] + ("Opt" if m == "opt" else "Succ"), sci(p))
    pos = {}
    for b in ("trained", "trained_cvar"):
        pos[b] = sum(s32([r["set"] for r in R if r["city"] == c]) > s32([r[b] for r in R if r["city"] == c])
                     for c in cities)
    put("FrPosT", str(pos["trained"]))
    put("FrPosC", str(pos["trained_cvar"]))
    put("FrPosTSignP", f"{binomtest(pos['trained'], len(cities)).pvalue:.2f}")
    put("FrNfev", f"{np.mean([r['trained_nfev'] for r in R]):.0f}")
    assert d["set_index"] == int(np.argmin(np.mean([r["vcost"] for r in r7["rows"]], axis=0))), "set of the rule"
    assert s32(A["set"]) > s32(A["trained_cvar"]) > s32(A["trained"]), "text: success@32 order set > CVaR > mean"
    assert adj[("set", "trained", "s")] < 0.01 and adj[("set", "trained_cvar", "s")] < 0.01, "text: both significant"
    assert pos["trained"] == pos["trained_cvar"] == len(cities), "text: higher success@32 in every city"
    assert 0 < A["set"].mean() - A["trained"].mean() < 0.02 and adj[("set", "trained", "opt")] < 0.05, \
        "text: slightly higher P_opt than per-instance training"
    assert A["trained_cvar"].mean() < A["trained"].mean(), "text: CVaR training lowered mean P_opt"
    assert A["ramp"].mean() < A["uniform"].mean() and s32(A["ramp"]) < s32(A["uniform"]), \
        "text: the linear ramp stayed below uniform one-hot sampling"
    assert d["ramp"][0] == min(0.5, 1.0, 2.0, 4.0, 8.0), "text: best ramp scale at the edge of the grid"
    return dict(A=A, adj=adj, pos=pos, cities=cities)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    out = {}
    res = extend(lambda k, v: out.__setitem__(k, v), Path(sys.argv[1]))
    for k, v in out.items():
        print(k, v)
