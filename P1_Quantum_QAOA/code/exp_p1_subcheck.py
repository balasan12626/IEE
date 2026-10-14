"""Check of the one-hot subspace simulator used for the size test (exp_p1_r4.py) -> <work>/p1_subcheck.json.

Runs without the twin backend: random instances in the format of qaoa_sim.instance_from_engine (three shelters,
group sizes 8-22, remaining seats from capacities 120/90/70 at 15-45 % occupancy with half of the first shelter's
capacity added, costs 5-60, about 10 % forbidden pairs). For G = 4 and 5 (12 and 15 qubits) the ring-XY circuit
is simulated on the full 2^(3G) statevector (qaoa_sim.Qaoa) and on the 3^G one-hot amplitudes (qaoa_sim.SubQaoa)
at random angles, p = 4; the largest absolute amplitude difference is stored.
usage: python exp_p1_subcheck.py <work>
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "shared_code"), str(HERE)]
import qaoa_sim as Q  # noqa: E402

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
N_INST, N_ANGLES, P = 5, 4, 4


def random_instance(G, rng):
    cap = np.array([120, 90, 70])
    occ = np.round(cap * rng.uniform(0.15, 0.45, 3)).astype(int)
    occ[0] = min(cap[0], occ[0] + cap[0] // 2)
    rem = cap - occ
    sizes = rng.integers(8, 23, G)
    cost = rng.uniform(5, 60, (G, 3))
    forb = (rng.random((G, 3)) < 0.1) | (sizes[:, None] > rem[None, :])
    return {"G": G, "S": 3, "sids": ["SA", "SB", "SC"], "sizes": sizes, "rem": rem, "cost": cost, "forb": forb,
            "stab": np.zeros((G, 3))}


def main():
    rng = np.random.default_rng(2026)
    worst, runs = 0.0, 0
    for G in (4, 5):
        for _ in range(N_INST):
            inst = random_instance(G, rng)
            sd = Q.subspace_diag(inst)
            full = Q.Qaoa(inst, "xy", Q.diagonals(inst, Q.bit_table(3 * G)))
            sub = Q.SubQaoa(inst, "xy", sd)
            for _ in range(N_ANGLES):
                th = np.concatenate([rng.uniform(0, np.pi, P), rng.uniform(0, np.pi / 2, P)])
                worst = max(worst, float(np.abs(full.state(th)[sd["full_index"]] - sub.state(th)).max()))
                runs += 1
    assert worst < 1e-10, worst
    out = {"sizes": [4, 5], "instances_per_size": N_INST, "angles_per_instance": N_ANGLES, "p": P,
           "runs": runs, "max_abs_amplitude_diff": worst}
    (WORK / "p1_subcheck.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
