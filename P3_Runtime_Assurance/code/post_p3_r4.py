"""Fourth-revision numbers for P3 -> macros.

Reads p3_r4.json (exp_p3_r4.py): why infeasible city instances are infeasible; the first rule broken by the
one-hot annealer's unsafe top samples; and the bit-flip annealer under penalty weights x0.25, x1, x4 and a
cost-scaled temperature schedule on the 108-instance subset. Every claim in the text is asserted.
Called from post_p3.py.
"""
import json
from collections import Counter

import numpy as np


def extend(put, work):
    d = json.loads((work / "p3_r4.json").read_text(encoding="utf-8"))
    R = d["rows"]
    inf = Counter(r["infeas"] for r in R if not r["feasible"])
    n_inf = sum(inf.values())
    put("InfN", str(n_inf))
    put("InfEmpty", str(inf["empty_row"]))
    put("InfComb", str(inf["combinatorial"]))
    assert inf["aggregate"] == 0 and inf["empty_row"] + inf["combinatorial"] == n_inf
    oh = Counter(x["cls"] for r in R for x in r["onehot"] if x["cls"] != "valid")
    n_oh = sum(oh.values())
    assert oh.get("onehot", 0) == 0, "one-hot annealer never breaks a row"
    put("OhClsBlind", f"{100 * oh['blind'] / n_oh:.0f}")
    put("OhClsForb", f"{100 * oh['forbidden'] / n_oh:.0f}")
    assert oh["blind"] > oh["forbidden"] > oh.get("pair", 0), "text: mostly penalty-free overloads, then forbidden pairs"
    F = [r for r in R if r["feasible"]]
    words = {8: "Eight", 16: "Sixteen", 32: "ThirtyTwo"}
    for G, w in words.items():
        vals = []
        for c in d["configs"]:
            rr = [r for r in F if r["G"] == G and c in r]
            vals.append(100 * np.mean([x["found"] for r in rr for x in r[c]]))
        put(f"SwMin{w}", f"{min(vals):.1f}")
        put(f"SwMax{w}", f"{max(vals):.1f}")
    put("SwN", str(sum(1 for r in R if "m1" in r)))
    big = [r for r in F if r["G"] == 32 and "m1" in r]
    assert len({round(100 * np.mean([x["found"] for r in big for x in r[c]]), 6) for c in d["configs"]}) == 1, \
        "text: no setting changed the valid rate at 32 groups"
