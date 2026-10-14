"""Fifth-revision numbers for P3 -> macros. Reads p3_r5.json (exp_p3_r5.py), city scale only.

  raw       the bit-flip annealer scored on raw bit vectors: most frequent raw vector (ties by energy), lowest-energy
            raw vector, share of one-hot vectors, share of draws in which the decoded "most frequent sample" was the
            pooled bucket of all non-one-hot vectors.
  deadline  MILP alone with a real time limit (second computer): optimal, valid incumbent, or nothing, on solvable
            instances; infeasibility proofs within the limit.
  recheck   every infeasible instance solved again with presolve off.
Every claim in the text is asserted. Called from post_p3.py.
"""
import json

import numpy as np


def pct(x):
    return 100 * float(np.mean(x))


def extend(put, work):
    d = json.loads((work / "p3_r5.json").read_text(encoding="utf-8"))
    R = d["rows"]
    F = [r for r in R if r["feasible"]]
    I = [r for r in R if not r["feasible"]]
    dr_f = [x for r in F for x in r["raw"]]
    dr_a = [x for r in R for x in r["raw"]]
    put("RwNone", f"{pct([x['decoded_top_none'] for x in dr_a]):.1f}")
    put("RwOneHot", f"{pct([x['onehot_share'] for x in dr_a]):.1f}")
    put("RwRepeat", f"{pct([x['top_count'] > 1 for x in dr_a]):.1f}")
    put("RwTopUnsafe", f"{pct([x['top_unsafe'] for x in dr_a]):.1f}")
    put("RwTopUnsafeSol", f"{pct([x['top_unsafe'] for x in dr_f]):.1f}")
    put("RwLowUnsafeSol", f"{pct([x['low_unsafe'] for x in dr_f]):.1f}")
    for G, tg in ((8, "Eight"), (16, "Sixteen"), (32, "ThirtyTwo")):
        put(f"RwTopUnsafeSol{tg}", f"{pct([x['top_unsafe'] for r in F if r['G'] == G for x in r['raw']]):.1f}")
    put("RwTopUnsafeEight", f"{pct([x['top_unsafe'] for r in R if r['G'] == 8 for x in r['raw']]):.1f}")
    put("RwN", str(len(R)))
    put("RwInf", str(len(I)))
    put("RwRecheckSame", str(sum(r.get("recheck_status") == 2 for r in I)))
    assert all(r.get("recheck_status") == 2 for r in I), "text: presolve-off re-solve confirmed every infeasible case"
    out = {}
    for lim in d["limits"]:
        k = str(lim)
        tg = {0.5: "Half", 1.0: "One", 2.0: "Two", 5.0: "Five"}[lim]
        opt = pct([r["deadline"][k]["optimal"] for r in F])
        val = pct([r["deadline"][k]["valid"] for r in F])
        none = pct([not r["deadline"][k]["incumbent"] for r in F])
        inf_ok = sum(r["deadline"][k]["status"] == 2 for r in I)
        bad = sum(r["deadline"][k]["incumbent"] and not r["deadline"][k]["valid"] for r in R)
        assert bad == 0, "every incumbent the solver returned was valid"
        put(f"RdOpt{tg}", f"{opt:.1f}")
        put(f"RdVal{tg}", f"{val:.1f}")
        put(f"RdNone{tg}", f"{none:.1f}")
        put(f"RdInf{tg}", str(inf_ok))
        out[lim] = (opt, val, none, inf_ok)
    put("RdSolvable", str(len(F)))
    return dict(out=out, F=F, I=I, dr_f=dr_f, dr_a=dr_a)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    m = {}
    extend(lambda k, v: m.__setitem__(k, v), Path(sys.argv[1]))
    for k, v in m.items():
        print(k, v)
