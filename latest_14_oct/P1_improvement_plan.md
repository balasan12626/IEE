# P1 improvement plan (research first, writing last)

Paper: One-Hot-Preserving QAOA for Flood Shelter Assignment: Pairwise Capacity Encoding and Angle Transfer.
Target: an IEEE conference, 6 pages. Scope: new experiments and one algorithmic addition, no new system features.

## Where the paper stands (14 Oct 2026)

Several items in the outside advice are already in the paper:

| Advice | Status in P1 now |
|---|---|
| Exhaustive search, simulated annealing, greedy baseline | Done (Section VI-F). SA comes in two forms: bit flip and one-hot moves. |
| Report oracle-assisted selection separately | Done. Table II has a "Needs optima" column, and the abstract says rule (7) uses development-set optima. |
| Seeds and uncertainty intervals | Done for the mixer study (5 seeds, two-level bootstrap, Holm). Grover is still one run. |
| Ablation of the energy scale | Done (no scaling 0.029, std scaling 0.282, ours 0.306). |
| Real road networks | Done (50 instances, 6 cities, per-city sign test). |
| Larger instances | Done (150 instances, 15 to 27 qubits). |
| Statevector, noise model or hardware stated per experiment | Done. Everything is classical simulation; the noise study is labelled. |
| Scripts that regenerate tables and figures | Done inside the repo (`exp_*.py` write JSON, `post_*.py` write every number and assert every claim). Not yet public. |

What is missing, in order of how much it would change a reviewer's score:

1. Capacity is only approximate. The pairwise penalty misses overloads by three or more groups, and at 24 to 27 qubits under 6% of the probability lands on feasible plans.
2. No integer-programming baseline and no runtime comparison at equal budget.
3. One disruption pattern only.
4. Angle selection uses development data for both training and selection; there is no separate validation split, and no optimum-free rule has been tested on new scenarios.
5. Code and data are not public.

## Phase A. Fix the capacity constraint (critical)

Three encodings, compared on the same instances:

| Encoding | Exact? | Extra qubits at G = 4 | Simulation cost |
|---|---|---|---|
| Pairwise penalty (current) | No | 0 | 3^G amplitudes |
| Higher-order penalty: one product term for every minimal set of groups that overloads a shelter | Yes, by construction | 0 | 3^G amplitudes (only the diagonal changes) |
| Slack variables, binary-coded remaining seats | Yes | about 7 per shelter, about 21 in all | 81 x 2^21 amplitudes, about 2.7 GB; too much for the Core i3 laptop |

The higher-order penalty is the main new method. Why it is exact: a shelter is overloaded exactly when the groups sent there contain a minimal overloading set, so a plan has zero capacity penalty exactly when it is feasible. Even so, we will check it exhaustively on every instance before writing "exact", as the reviewer asks. Its cost is in gates: a product of k binary variables expands to 2^k - 1 Pauli Z terms, and a k-qubit Z term needs 2(k - 1) CNOTs. We report the CNOT count per layer next to ring-XY's 28.

Slack encoding: run it on a reduced set (smaller seat counts, or coarser seat units) and report it as a reference, with its qubit and CNOT counts. If even that will not fit, report its qubit count only and say why it was not simulated.

Measures for each encoding: share of penalty-free plans that are infeasible, P_feas, P_opt, P_opt / P_feas, success@32, qubits, CNOTs per layer.

Expected result to test, not to assume: the higher-order penalty raises P_feas at 21 to 27 qubits, where capacity binds on every instance.

## Phase B. Stronger classical comparison (critical)

1. Integer program solved with HiGHS (`scipy.optimize.milp`, already installed). OR-Tools is not installed and adds nothing at this size.
2. For every method, on the same instances and with the same feasibility check, report the best cost, the gap to the optimum and the wall-clock time. For QAOA, also report the number of shots needed to reach success@N = 0.95.
3. State plainly that exhaustive search and HiGHS solve every instance exactly in milliseconds. The paper then reads as a study of constraint handling and angle transfer, which it already is.

## Phase C. More realistic scenarios (high impact)

The generator for three other disruption patterns is already written (`exp_p1_r4.py dis`: two roads closed; shelter B failed plus a road closed; shelter C capacity cut by 30% or 70% plus a road closed). Add:

- three flood levels (low, medium, severe), set by the flood index on closed roads and the size of the capacity cut;
- group sizes drawn from two other ranges.

Report results split by capacity-binding and non-binding instances, as the held-out test already does.

## Phase D. Cleaner angle transfer (high impact)

Split the 60 twin seeds three ways: 30 for training, 10 for validation, 20 for testing.

1. Train per instance on the training seeds only.
2. Choose the angle set, and anything else tuned, on the validation seeds only.
3. Report the final numbers once, on the test seeds and on the Phase C scenarios.

Report two rules side by side: the optimum-free energy rule as the main result, and rule (7) as an oracle reference. If the energy rule still loses to per-instance training, the paper says so; that is already the current finding.

## Phase E. Reproducibility

- Public repository after the review decision (README asks to keep it private until then). In the blind PDF: "Code and stored results will be released after review."
- Add a `requirements.txt`, the fixed seeds, the optimizer settings and one command that rebuilds every table from the stored JSON. The Linux build used on 14 Oct already does this for P1.

## Phase F. Rewrite and format (last)

Only after Phases A to D, because the abstract, title and contribution list depend on their results.

- Possible title if Phase A works: "Exact Capacity Penalties and Angle Transfer for One-Hot-Preserving QAOA in Flood Shelter Assignment".
- Abstract: problem, method, three main numbers, the main limit, no quantum advantage.
- Related work: compare directly with higher-order and slack encodings and with constrained-QAOA transfer work.
- Discussion: keep shown results apart from hypotheses.
- Edit the prose by hand to plain academic English (CLAUDE.md rule), with every number from the post scripts.
- Page budget: Table V (size) and the noise paragraph can shrink to make room for a Table VI comparing the encodings.

## Where each phase can run

| Phase | Needs | Runs where |
|---|---|---|
| A, B on city instances | frozen city snapshot (in this repo) plus a small shim, because `exp_p1_v2.py` imports the twin backend | here, in the cloud session |
| A, B, C, D on twin instances | `backend.simulation.hqrl_demo` from the main AquaSentinel repo | main repo, or here once that repo is attached |
| Slack encoding at full seat resolution | about 3 GB of memory per state | not on the laptop |

Run long jobs one at a time and in the background, as CLAUDE.md asks.

## Order and rough cost

1. Phase A on the 50 city instances (here). About one day of work and an hour of compute.
2. Phase B on the same instances. Half a day.
3. Attach or copy the main repo, then run Phases A and B on the twin and size instances, and Phase C. Two to three days, mostly compute.
4. Phase D. One day.
5. Phase F rewrite and rebuild. One day.

## What this can do to the score

Current estimate (ours, not a review): about 4.0 to 4.1 out of 5.

If Phase A shows a clear feasibility gain and Phases B to D hold up, originality and significance should both rise, and 4.3 to 4.5 is a reasonable aim. That depends on the results, and only the conference reviewers give the real score. If the higher-order penalty does not help, the paper still gains an exact baseline and a fairer comparison, and the title stays as it is.

## Knock-on effect on P5

P5 reuses P1. Any change to P1's numbers or claims must also go into P5's P1 summary (macro prefix `Qa`), and P5 must be rebuilt.
