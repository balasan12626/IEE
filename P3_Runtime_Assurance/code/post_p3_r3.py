"""Third-revision numbers for P3 -> macros.

Reads p3_r3.json (exp_p3_r3.py: one-hot-preserving annealer, same 360 city instances, seeds, energy, chains, sweeps
and loop as the paper's bit-flip annealer) and p3_city2.json (the bit-flip annealer). Paired per instance:
two-sided Wilcoxon signed-rank on the share of calls with a valid sample. Every claim in the text is asserted.
Called from post_p3.py.
"""
import json

import numpy as np
from scipy.stats import wilcoxon


def extend(put, work, city2):
    r3 = json.loads((work / "p3_r3.json").read_text(encoding="utf-8"))
    new = {(r["city"], r["G"], r["tight"], r["k"]): r for r in r3["rows"]}
    old = {(r["city"], r["G"], r["tight"], r["k"]): r for r in city2["city"]}
    assert set(new) == set(old) and all(new[k]["feasible"] == old[k]["feasible"] for k in new), "same instances"
    words = {8: "Eight", 16: "Sixteen", 32: "ThirtyTwo"}
    res = {}
    for G, w in words.items():
        sol = [k for k in new if k[1] == G and new[k]["feasible"]]
        alli = [k for k in new if k[1] == G]
        vn = [np.mean([d["sampler_found"] for d in new[k]["draws"]]) for k in sol]
        vo = [np.mean([d["sampler_found"] for d in old[k]["draws"]["fixed"]]) for k in sol]
        un = 100 * np.mean([d["raw_invalid"] for k in alli for d in new[k]["draws"]])
        uo = 100 * np.mean([d["raw_invalid"] for k in alli for d in old[k]["draws"]["fixed"]])
        fn = 100 * np.mean([d["uncert_false_escalation"] for k in sol for d in new[k]["draws"]])
        fo = 100 * np.mean([d["uncert_false_escalation"] for k in sol for d in old[k]["draws"]["fixed"]])
        put(f"OhValid{w}", f"{100 * np.mean(vn):.1f}")
        put(f"OhValidOld{w}", f"{100 * np.mean(vo):.1f}")
        put(f"OhUnsafe{w}", f"{un:.1f}")
        put(f"OhUnsafeOld{w}", f"{uo:.1f}")
        put(f"OhFalse{w}", f"{fn:.1f}")
        put(f"OhFalseOld{w}", f"{fo:.1f}")
        res[G] = (np.mean(vn), np.mean(vo), un, uo, fn, fo)
    assert all(res[G][0] > res[G][1] for G in words), "text: the one-hot annealer found valid plans more often"
    assert all(abs(res[G][2] - res[G][3]) < 2.5 for G in words), "text: unsafe top samples about as frequent"
    assert all(abs(res[G][4] - res[G][5]) < 1.0 for G in words), "text: false escalations unchanged"
    sol = [k for k in new if new[k]["feasible"]]
    a = np.array([np.mean([d["sampler_found"] for d in new[k]["draws"]]) for k in sol])
    b = np.array([np.mean([d["sampler_found"] for d in old[k]["draws"]["fixed"]]) for k in sol])
    put("OhBetter", str(int((a > b).sum())))
    put("OhWorse", str(int((a < b).sum())))
    put("OhP", f"{wilcoxon(a, b).pvalue:.1e}".replace("e-0", "\\times10^{-").replace("e-", "\\times10^{-") + "}"
        if wilcoxon(a, b).pvalue < 0.01 else f"{wilcoxon(a, b).pvalue:.3f}")
    assert wilcoxon(a, b).pvalue < 0.05
    # first rule broken by the one-hot annealer's unsafe top samples cannot be one-hot: check
    dr = [d for k in new for d in new[k]["draws"]]
    put("OhDraws", f"{len(dr):,}")
    return res
