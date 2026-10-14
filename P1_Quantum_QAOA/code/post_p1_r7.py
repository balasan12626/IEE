"""Seventh-revision numbers for P1 -> macros.

Reads p1_r7.json (exp_p1_r7.py): the 30 development-trained angle sets on the city instances of all four disruption
patterns. Leave one city out: a rule picks one set from the other five cities' instances and is scored on the
held-out city against per-instance training. Rules: vcost (expected cost of the cheapest verified plan among 32
shots relative to the greedy plan; needs no optimum), energy (needs no optimum), popt (needs the optima; reference).
Tests: two-sided Wilcoxon signed-rank on per-instance P_opt and success@32 over all held-out instances, Holm over
the 6 tests of the two oracle-free rules; per-city sign test. Every claim in the text is asserted. Called from post_p1.py.
"""
import json

import numpy as np
from scipy.stats import binomtest, spearmanr, wilcoxon

from post_p1_r3 import holm, s32  # noqa: E402
from post_p1_v2 import sci  # noqa: E402


def extend(put, work):
    fx = json.loads((work / "p1_r3.json").read_text(encoding="utf-8"))["fixed"]
    assert np.allclose(fx["xy:0.1:4:popt"], fx["xy:0.1:4:cvar"]), "text: Table II note, same set for XY CVaR"
    d = json.loads((work / "p1_r7.json").read_text(encoding="utf-8"))
    R = d["rows"]
    cities = sorted({r["city"] for r in R})
    put("LcN", str(len(R)))
    put("LcCand", str(d["n_candidates"]))
    res, raw, keys = {}, [], []
    for rule, sign in (("vcost", 1), ("energy", 1), ("popt", -1)):
        F, T, picks, pos_s = [], [], [], 0
        for c in cities:
            tr = [r for r in R if r["city"] != c]
            te = [r for r in R if r["city"] == c]
            k = int(np.argmin(sign * np.mean([r[rule] for r in tr], axis=0)))
            picks.append(k)
            f = np.array([r["popt"][k] for r in te])
            t = np.array([r["trained"] for r in te])
            F.append(f)
            T.append(t)
            pos_s += s32(f) > s32(t)
        F, T = np.concatenate(F), np.concatenate(T)
        res[rule] = dict(F=F, T=T, picks=picks, pos_s=pos_s,
                         p_opt=wilcoxon(F, T).pvalue,
                         p_s=wilcoxon(1 - (1 - F) ** 32, 1 - (1 - T) ** 32).pvalue)
        if rule != "popt":
            raw += [res[rule]["p_opt"], res[rule]["p_s"]]
            keys += [(rule, "opt"), (rule, "s")]
    adj = dict(zip(keys, holm(raw)))
    v, e, o = res["vcost"], res["energy"], res["popt"]
    assert v["picks"] == o["picks"], "text: the verified-cost rule picked the set the city optima pick, every fold"
    ch = json.loads((work / "p1_r3.json").read_text(encoding="utf-8"))["variants"]["xy:1.0"]["4"]["choice"]
    assert set(v["picks"]) == {ch["energy"]["from_instance"]} and ch["popt"]["from_instance"] != ch["energy"]["from_instance"], \
        "text: the picked set is the twin energy rule's set, not the twin rule-(8) set"
    pv = wilcoxon(1 - (1 - v["F"]) ** 32, 1 - (1 - e["F"]) ** 32).pvalue
    put("LcVvsEP", sci(pv))
    assert pv < 0.01, "text: verified-cost choice above the energy rule re-applied on cities"
    assert all(a != b for a, b in zip(e["picks"], v["picks"])), "text: the energy rule re-applied picked other sets"
    assert int(v["pos_s"]) == len(cities), "text: success@32 higher in all cities"
    cj = [r for r in json.loads((work / "p1_cities.json").read_text(encoding="utf-8"))["rows"] if r["feasible_instance"]]
    cv = np.array([r["xy:0.1:4"]["trained"] for r in cj])
    put("CityCvarTrainedSucc", f"{s32(cv):.1f}")
    base_v = [r["popt"][v["picks"][0]] for r in R if r["pattern"] == "base"]
    put("LcVBaseSucc", f"{s32(base_v):.1f}")
    assert s32(base_v) > s32(cv), "text: the chosen set beats per-instance CVaR training in success@32 on the base cities"
    k = v["picks"][0]
    for pat, tg in (("base", "Base"), ("roads", "Roads"), ("shelter", "Shelter"), ("cut", "Cut")):
        rr = [r for r in R if r["pattern"] == pat]
        put(f"LcV{tg}Opt", f"{np.mean([r['popt'][k] for r in rr]):.3f}")
        put(f"LcV{tg}Trained", f"{np.mean([r['trained'] for r in rr]):.3f}")
    put("LcSame", str(sum(a == b for a, b in zip(v["picks"], o["picks"]))))
    put("LcFolds", str(len(cities)))
    for rule, tg in (("vcost", "V"), ("energy", "E")):
        x = res[rule]
        put(f"Lc{tg}Opt", f"{x['F'].mean():.3f}")
        put(f"Lc{tg}OptP", sci(adj[(rule, 'opt')]))
        put(f"Lc{tg}Succ", f"{s32(x['F']):.1f}")
        put(f"Lc{tg}SuccP", sci(adj[(rule, 's')]))
        put(f"Lc{tg}SuccCities", str(int(x["pos_s"])))
    put("LcTrained", f"{v['T'].mean():.3f}")
    put("LcTrainedSucc", f"{s32(v['T']):.1f}")
    put("LcVSuccSignP", f"{binomtest(int(v['pos_s']), len(cities)).pvalue:.2f}")
    assert adj[("vcost", "opt")] > 0.05, "text: P_opt not significantly different from per-instance training"
    assert adj[("vcost", "s")] < 0.01 and s32(v["F"]) > s32(v["T"]), "text: success@32 higher"
    assert e["F"].mean() < e["T"].mean(), "text: the energy rule's set had a lower mean P_opt"
    assert s32(v["F"]) > s32(e["F"]), "text: verified-cost rule above the energy rule in success@32"
    fs = json.loads((work / "p1_r7b.json").read_text(encoding="utf-8"))  # finite-shot selection (exp_p1_r7b.py)
    S, n_same, n_all = [], 0, 0
    for c, pk in fs["picks"].items():
        te = [r for r in R if r["city"] == c]
        for kk in pk:
            S.append(s32([r["popt"][kk] for r in te]))
            n_same += kk == v["picks"][0]
            n_all += 1
    put("FsReps", f"{n_all:,}")
    put("FsSame", f"{100 * n_same / n_all:.0f}")
    put("FsSucc", f"{np.mean(S):.1f}")
    put("FsSuccFive", f"{np.percentile(S, 5):.1f}")
    assert np.percentile(S, 5) > s32(v["T"]) + 10, "text: finite-shot picks still far above per-instance training"
    mv = np.mean([r["vcost"] for r in R], axis=0)
    mp = np.mean([r["popt"] for r in R], axis=0)
    me = np.mean([r["energy"] for r in R], axis=0)
    rv, re_ = spearmanr(-mv, mp)[0], spearmanr(-me, mp)[0]
    put("LcRhoV", f"{rv:.2f}")
    put("LcRhoE", f"{re_:.2f}")
    assert rv > re_
    return res
