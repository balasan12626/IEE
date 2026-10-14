"""Sixth-revision numbers for P1 -> macros and tab_dis.tex.

Reads only p1_r6.json (exp_p1_r6.py): the 12-qubit angle sets fixed on the twin (rules popt = eq. 7, energy, cvar)
against per-instance training on city instances with three other disruption patterns (two roads closed; a shelter
failed; a 70 % seat cut). Tests: two-sided Wilcoxon signed-rank on per-instance P_opt and on success@32, Holm over
the 9 pattern x rule P_opt tests; per-city sign test of the pooled mean differences. Called from post_p1.py.
"""
import json

import numpy as np
from scipy.stats import binomtest, wilcoxon

from post_p1_r3 import holm, s32  # noqa: E402
from post_p1_v2 import sci  # noqa: E402

PAT = (("roads", "2 roads", "Roads"), ("shelter", "Shelter out", "Shelter"),
       ("cut", "Seats $-70\\%$", "Cut"))
RULES = (("popt", "O"), ("energy", "E"), ("cvar", "C"))


def extend(put, work, out):
    d = json.loads((work / "p1_r6.json").read_text(encoding="utf-8"))
    rows = d["rows"]
    R = {}
    tests, data = [], {}
    for pat, _, _ in PAT:
        g = [r for r in rows if r["pattern"] == pat]
        data[pat] = {k: np.array([r[k] for r in g]) for k in ("trained", "popt", "energy", "cvar", "uniform",
                                                               "trained_feas", "popt_feas")}
        data[pat]["bind"] = int(sum(r["binding"] for r in g))
        data[pat]["cities"] = [r["city"] for r in g]
        for rule, _ in RULES:
            tests.append((pat, rule))
    raw = [wilcoxon(data[p][rule], data[p]["trained"]).pvalue for p, rule in tests]
    adj = dict(zip(tests, holm(raw)))
    put("DsFamily", str(len(tests)))
    put("DsNTotal", str(len(rows)))
    put("DsTried", str(sum(d["tried"].values())))
    lines = []
    for pat, label, tg in PAT:
        x = data[pat]
        t = x["trained"]
        put(f"Ds{tg}N", str(len(t)))
        put(f"Ds{tg}Bind", str(x["bind"]))
        put(f"Ds{tg}Trained", f"{t.mean():.3f}")
        put(f"Ds{tg}TrainedSucc", f"{s32(t):.1f}")
        cells = [label, f"{t.mean():.3f}"]
        for rule, rt in RULES:
            f = x[rule]
            p = adj[(pat, rule)]
            R[(pat, rule)] = dict(f=f, t=t, p=p, wins=int((f > t).sum()), med=float(np.median(f - t)))
            put(f"Ds{tg}{rt}", f"{f.mean():.3f}")
            put(f"Ds{tg}{rt}P", sci(p))
            put(f"Ds{tg}{rt}Wins", str(int((f > t).sum())))
            put(f"Ds{tg}{rt}Succ", f"{s32(f):.1f}")
            if rule in ("popt", "energy"):
                cells += [f"{f.mean():.3f}", f"${sci(p)}$"]
        cells += [f"{s32(t):.1f}", f"{s32(x['popt']):.1f}"]
        lines.append(" & ".join(cells) + "\\\\")
    # pooled over the three patterns, with a per-city sign test (instances cluster by city)
    T = np.concatenate([data[p]["trained"] for p, _, _ in PAT])
    cities = sorted(set(sum((data[p]["cities"] for p, _, _ in PAT), [])))
    allc = sum((data[p]["cities"] for p, _, _ in PAT), [])
    for rule, rt in RULES:
        F = np.concatenate([data[p][rule] for p, _, _ in PAT])
        pos = sum(np.mean([F[i] - T[i] for i in range(len(T)) if allc[i] == c]) > 0 for c in cities)
        put(f"DsAll{rt}", f"{F.mean():.3f}")
        put(f"DsAll{rt}Pos", str(int(pos)))
        put(f"DsAll{rt}SignP", f"{binomtest(int(pos), len(cities)).pvalue:.2f}")
        put(f"DsAll{rt}Succ", f"{s32(F):.1f}")
        put(f"DsAll{rt}SuccP", sci(wilcoxon(1 - (1 - F) ** 32, 1 - (1 - T) ** 32).pvalue))
        R[("all", rule)] = dict(f=F, t=T, pos=int(pos), n_cities=len(cities))
    put("DsAllTrained", f"{T.mean():.3f}")
    put("DsAllTrainedSucc", f"{s32(T):.1f}")
    put("DsCities", str(len(cities)))
    assert all(not (R[k]["f"].mean() > R[k]["t"].mean() and R[k]["p"] < 0.05) for k in R if k[0] != "all"), \
        "text: no fixed set raised P_opt significantly under any pattern"
    assert R[("shelter", "popt")]["p"] < 0.05 and R[("shelter", "popt")]["f"].mean() < R[("shelter", "popt")]["t"].mean()
    assert R[("roads", "energy")]["p"] < 0.05 and R[("roads", "energy")]["f"].mean() < R[("roads", "energy")]["t"].mean()
    assert all(s32(R[("all", r)]["f"]) > s32(R[("all", r)]["t"]) for r, _ in RULES), "text: success@32 rose pooled"
    (out / "tab_dis.tex").write_text("\n".join(lines), encoding="utf-8")
    return R, adj
