"""Fifth-revision numbers for P1 -> macros and tab_exact.tex.

Reads only p1_r5.json (exp_p1_r5.py): pairwise vs minimal-set (exact) capacity penalty on the 50 city
instances, ring-XY, p = 4, per-instance training and the fixed set of rule (7); exhaustive search and HiGHS.
Tests: two-sided Wilcoxon signed-rank on per-instance values, Holm over the 4 tests of Table VI
(P_opt and P_feas, trained and fixed); per-city sign test for feasibility. Every claim in the text is asserted.
Called from post_p1.py.
"""
import json

import numpy as np
from scipy.stats import binomtest, wilcoxon

from post_p1_r3 import holm, s32  # noqa: E402
from post_p1_v2 import sci  # noqa: E402


def extend(put, work, out):
    R = json.loads((work / "p1_r5.json").read_text(encoding="utf-8"))["rows"]

    def g(k):
        return np.array([r[k] for r in R], dtype=float)

    n = len(R)
    put("ExN", str(n))
    put("ExMissInst", str(sum(r["pair:pen_free_infeas"] > 0 for r in R)))
    put("ExMissPlans", str(int(g("pair:pen_free_infeas").sum())))
    assert g("hubo:pen_free_infeas").sum() == 0, "text: minimal-set penalty exact on every instance"
    put("ExMinPair", f"{100 * g('pair:minimiser_opt').mean():.0f}")
    put("ExMinHubo", f"{100 * g('hubo:minimiser_opt').mean():.0f}")
    assert g("hubo:minimiser_opt").all()
    put("ExSetsBig", str(sum(r["n_sets_big"] > 0 for r in R)))
    put("ExCnotPair", f"{g('pair:cnot').mean():.0f}")
    put("ExCnotHubo", f"{g('hubo:cnot').mean():.0f}")
    put("ExCnotHuboMax", f"{g('hubo:cnot').max():.0f}")
    put("ExSlackMin", str(int(g("slack_qubits").min())))
    put("ExSlackMax", str(int(g("slack_qubits").max())))
    put("ExExactMs", f"{np.median(g('exact_ms')):.2f}")
    put("ExMilpMs", f"{np.median(g('milp_ms')):.1f}")
    assert np.median(g("milp_ms")) > np.median(g("exact_ms")), "text: HiGHS slower than enumeration at this size"

    keys = [("trained", "trained"), ("trained_feas", "trained_feas"), ("popt", "popt"), ("popt_feas", "popt_feas")]
    raw = [wilcoxon(g("hubo:" + k), g("pair:" + k)).pvalue for k, _ in keys]
    adj = dict(zip([k for k, _ in keys], holm(raw)))
    for k, tag in (("trained", "TrOpt"), ("trained_feas", "TrFeas"), ("popt", "FxOpt"), ("popt_feas", "FxFeas")):
        put(f"Ex{tag}Pair", f"{g('pair:' + k).mean():.3f}")
        put(f"Ex{tag}Hubo", f"{g('hubo:' + k).mean():.3f}")
        put(f"Ex{tag}P", sci(adj[k]))
    assert adj["trained_feas"] < 0.01 and g("hubo:trained_feas").mean() > g("pair:trained_feas").mean()
    assert adj["popt_feas"] < 0.01 and g("hubo:popt_feas").mean() > g("pair:popt_feas").mean()
    assert adj["trained"] > 0.05 and g("hubo:trained").mean() < g("pair:trained").mean(), \
        "text: trained P_opt lower with the exact penalty, not significantly"
    assert adj["popt"] < 0.05 and g("hubo:popt").mean() < g("pair:popt").mean(), \
        "text: the fixed (pairwise-trained) set loses P_opt on the exact penalty"
    cond = {e: (g(f"{e}:trained") / g(f"{e}:trained_feas")).mean() for e in ("pair", "hubo")}
    put("ExCondPair", f"{cond['pair']:.2f}")
    put("ExCondHubo", f"{cond['hubo']:.2f}")
    assert cond["hubo"] < cond["pair"]
    sp, sh = s32(g("pair:trained")), s32(g("hubo:trained"))
    p_s = wilcoxon(1 - (1 - g("hubo:trained")) ** 32, 1 - (1 - g("pair:trained")) ** 32).pvalue
    put("ExSuccPair", f"{sp:.1f}")
    put("ExSuccHubo", f"{sh:.1f}")
    put("ExSuccP", sci(p_s))
    assert p_s > 0.05, "text: success@32 not significantly different"
    cities = sorted({r["city"] for r in R})
    up = sum(np.mean([r["hubo:trained_feas"] for r in R if r["city"] == c]) >
             np.mean([r["pair:trained_feas"] for r in R if r["city"] == c]) for c in cities)
    put("ExFeasCities", str(up))
    put("ExFeasSignP", f"{binomtest(up, len(cities)).pvalue:.2f}")
    assert up == len(cities)
    b = g("binding").astype(bool)
    put("ExNBind", str(int(b.sum())))
    for e, tg in (("pair", "Pair"), ("hubo", "Hubo")):
        put(f"ExBind{tg}", f"{g(e + ':trained')[b].mean():.3f}")
        put(f"ExNonBind{tg}", f"{g(e + ':trained')[~b].mean():.3f}")
    assert g("hubo:trained")[b].mean() > g("pair:trained")[b].mean(), "text: exact penalty helps binding instances"
    assert g("hubo:trained")[~b].mean() < g("pair:trained")[~b].mean(), "text: and hurts the others"

    rows = []
    for e, name in (("pair", "Pairwise"), ("hubo", "Exact")):
        rows.append(f"{name} & {int((g(e + ':pen_free_infeas') > 0).sum())} & {100 * g(e + ':minimiser_opt').mean():.0f} & "
                    f"{g(e + ':cnot').mean():.0f} & {g(e + ':trained_feas').mean():.3f} & {g(e + ':trained').mean():.3f} & "
                    f"{g(e + ':popt_feas').mean():.3f} & {g(e + ':popt').mean():.3f}\\\\")
    rows.append(f"Holm $p$ & & & & ${sci(adj['trained_feas'])}$ & ${sci(adj['trained'])}$ & "
                f"${sci(adj['popt_feas'])}$ & ${sci(adj['popt'])}$\\\\")
    (out / "tab_exact.tex").write_text("\n".join(rows), encoding="utf-8")
