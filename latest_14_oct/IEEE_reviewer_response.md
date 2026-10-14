# IEEE Reviewer Comments and Responses: Papers 1 and 2

Revision of 13–14 October 2026. Files in this folder:

| Paper | Upload for review (blind) | After acceptance |
|---|---|---|
| P1: One-Hot-Preserving QAOA with Transferable Angles for Flood Shelter Assignment | `P1_SUBMIT_blind_review.pdf` | `P1_camera_ready_with_authors.pdf` |
| P2: Rules Decide, Language Models Narrate: Fail-Closed Numeric Grounding of LLM Narration in a Flood-Response Pipeline | `P2_SUBMIT_blind_review.pdf` | `P2_camera_ready_with_authors.pdf` |

Both are 6 pages, pass every build check (numbers checked against the experiment data, references, fonts, page count), and the blind copies have no author names.

Status key: ✅ done · ⚠️ partly done (reason given) · ❌ not done (reason given)

---

## Paper 2: response to the reviewer

Original recommendation: Weak Accept, 3.4 / 5.

### Major comments

| # | Reviewer comment | Status | What we changed |
|---|---|---|---|
| 1 | Strongest baseline missing: let the LLM write placeholders and let the program fill every number. Also run "forbid arrival times in the prompt". | ✅ | Both designs were run live on gpt-oss-20b and gpt-oss-120b (first 120 states; the run was stopped there to limit API use). Unsupported replies: production prompt 28.0%; with the no-arrival-time rule 3.4%; placeholders only 1.7%, with 2.1% template fallbacks. Token use and words per reply are reported (new Table II). |
| 2 | Qualitative over-claims ("flood confirmed", "has breached") are the real residual risk; report miss rate per guard or narrow the claim. | ✅ | New section "Qualitative Over-Claims": 43 replies (14.3%) over-claim, and the deployed guard passes 27 of 43. The claim is narrowed to *numeric* grounding (new title). A frozen check on assertion words is added. We also report that our own prompt rule ("flood occurred") and our fallback template ("Flood has occurred") cause part of the problem. |
| 3 | Reference labels are not independent of the checkers; use a second blind annotator and Cohen's kappa. | ⚠️ | Every result is now also reported under the script-only labels, which were made before any manual reading. The second-annotator package is ready (`../../P2_Agentic_AI/second_annotator/`: blind sheet, facts, protocol, kappa script) but needs a co-author to fill in. The paper states this as the main open item. |
| 4 | Held-out result does not show v2 is better; use McNemar; report the 18 failed ALLaM-2 calls. | ✅ | McNemar p = 0.62 (recall) and p = 0.25 (false rejections), so the paper now says neither guard is shown to be better. All 18 failed calls were in the automated band (18 of 123 calls there, 0 of 27 elsewhere), and this is reported. |
| 5 | Judge comparison unfair: 23 failed judge calls counted as rejections; report with and without. | ✅ | Judge false rejections are 14.1% with the failures counted and 6.8% without them (277 answered replies). Both rows are in Table I. "Caught all it checked" is removed. |
| 6 | 2,807 is a grid count, not exposure; give a proof; discuss what the pure-function check misses. | ✅ | 2,807 = 401 probabilities × 7 failed-health combinations, i.e. one equivalence class. Because the probability is only compared with 0.40/0.50/0.60, which all lie on the grid, the grid check is a proof for the extracted functions. Exposure: 119 of 604 sweep settings were in the unsafe state. Asynchronous limits are discussed (stale flags, an override racing a tick, a real task-cancellation bug that only running the system found). |
| 7 | Gate: report recall of errors, a cost comparison, a no-gate baseline and a calibrated single model, with CIs. | ✅ | New Table V. The deployed gate catches 40.3% of errors (CI 34–47); the straddle rule only 15.9%, and it would let 55 more errors through (CI 42–69). We withdrew the earlier "replace with straddle" recommendation. When a missed dispatch costs 5×, a calibrated single model with no gate is cheapest. |
| 8 | Classifiers not described. | ✅ | INDOFLOODS, 4,548 events at 155 gauges, target = severe flood (35.8%), 55 numeric + 4 categorical inputs, stratified 80/20 split, ROC-AUC 0.818 / 0.806. The sweep extrapolates: 37% of its settings exceed the 99th percentile of training rainfall. |
| 9 | Narrow model coverage; say the rates are specific to the setup. | ⚠️ | The abstract and limits now say the rates are specific to our prompt, models and states. No new model family was tested, because API calls were stopped. |
| 10 | "Multi-agent" and "formal" overstated; compare with CAP and NeMo Guardrails. | ✅ | New title; the system is described as "a rule-based pipeline with an LLM narrator". Common Alerting Protocol is cited; NeMo's fact-checking rail is matched to our LLM-judge baseline. |

### Minor comments

| Reviewer comment | Status | What we changed |
|---|---|---|
| Table II repeats columns | ✅ | Merged into one Table I |
| 97% vs "almost all" | ✅ | Both now say 106 of 109 (97%) |
| 64% vs Fig. 2 (68%) | ✅ | Same categories used throughout: 39% of all ALLaM-2 replies, 67% of its unsupported ones |
| Table III header and judge CIs | ✅ | Sample sizes in the header; judge Wilson CIs at most ±14 points |
| ×100 rule sensitivity | ✅ | Recall unchanged on the development replies (89.0%); false rejections 5.8% → 6.3% |
| Give the δ value | ✅ | δ95 = 0.28; the sweep stops holding agreeing cases at δ = 0.31 |
| Explain 16,032 vs 32,032 | ✅ | 1,002 × 8 × 2 = 16,032 and 1,001 × 8 × 2 × 2 = 32,032 (also added to the companion paper P5) |
| Template-fallback rate per model | ✅ | 38.7% (gpt-oss-20b), 33.3% (gpt-oss-120b), 63.3% (ALLaM-2) |
| How excerpts were chosen | ✅ | The excerpt table was removed for space; two examples are quoted in the text, with how they were chosen stated |
| Overlap with the companion paper | ✅ | Stated in the introduction (no citation, because the review is double-blind) |
| Check refs [16], [17] | ✅ | RvLLM: NeurIPS 38, pp. 89374–89394, doi 10.52202/085713-2693. AgentSpec: ICSE 2026, pp. 2938–2950 (checked with Crossref) |
| Blind copy without names | ✅ | Checked |

### Answers to the reviewer's questions

1. **Slots only?** The narrator left a digit or number word in 2.1% of replies, and those go to the template. One reply that passed still carried an unsupported number.
2. **Fallback share in practice?** The measured rates are 33–63% of calls per model with the deployed guard, but 2.1–2.6% with the improved prompts.
3. **Straddle instead of the gap rule?** 55 more errors would reach dispatch (CI 42–69). Cost per 100 events is in Table V.

---

## Paper 1: response to the reviewer

Original recommendation: Weak Accept. The pasted review was cut off after major comment 5, so the comments below are the ones that were visible.

| # | Reviewer comment | Status | What we changed |
|---|---|---|---|
| 1 | The mixer preserves one-hot, not capacity; title overstates; compare with a mixer on the feasible subspace. | ✅ | Title changed to "One-Hot-Preserving QAOA". A mixer confined to fully feasible plans reaches P_opt 0.444 against 0.215 for ring-XY (better on 26 of 30 instances, p = 4.4e-06). The paper states that preparing its start state needs the feasible set, so it is a bound, not a practical circuit. |
| 2 | The "shared energy scale" explanation is not tested. | ✅ | With the scaling switched off, the transferred angles collapse to 0.029. A different normalisation gives 0.282, close to our 0.306. So transfer needs a common scale, not our particular one. |
| 3 | "0 evaluations" hides the offline cost; give the break-even. | ✅ | One-time cost: 78,992 evaluations, which per-instance training would spend on about 32 disruptions. |
| 4 | The per-instance baseline is weak; add equal-budget, warm-start and stronger-optimizer baselines. | ✅ | Fixed angles 0.306 vs best of 5 COBYLA seeds 0.242 and L-BFGS-B 0.225. A warm start from the fixed angles with a full budget improves to 0.385 (p = 0.0019). |
| 5 | "Statistically indistinguishable from Grover" is not equivalence. | ✅ | Reworded. The data lean towards XY: ahead on 20 of 30 instances, mean difference 0.076 (CI 0.018–0.141), unadjusted p = 0.047, not significant after Holm. |
| 6+ | (rest of the review was cut off) | — | Please paste the remainder if it exists. |

Other fixes:
- The city map files had been rebuilt after the first run, so the city test was re-run on a frozen copy of the data. Delhi, Chennai, Mumbai and Kolkata reproduce exactly; Guwahati and Patna changed slightly. Updated result: success within 32 shots rises from 74.9% to 89.9% (p ≈ 0.01).
- The position table, the scaling table and Algorithm 1 were folded into the text to stay at 6 pages.

### Round 3 (14 Oct 2026)

New title: "One-Hot-Preserving QAOA for Flood Shelter Assignment: Pairwise Capacity Encoding and Angle Transfer". All new numbers come from stored results (`p1_r3.json`, `p1_r3_cities.json`, `p1_r3_cand.json`, written by `exp_p1_r3.py`) through `post_p1_r3.py`, which asserts every comparison in the text. On the user's instruction (slow machine) no new training runs were made for M2, M3 and M7; those items are handled in the text and listed below as not done.

| # | Comment | Status | What changed (measured numbers) |
|---|---|---|---|
| M1 | theta* chosen with oracle P_opt; best-of-5 also chosen by P_opt | ✅ done, claim weakened | Text now says Eq. (7) uses the exact optima of the development set. Two oracle-free rules added (min. mean energy, min. mean CVaR) over the same 30 trained sets. Held-out P_opt (XY, mean, p=4): P_opt rule 0.306, energy rule 0.264, CVaR rule 0.234, per-instance training 0.163 (Holm p 8.5e-4, 3.8e-3, 0.039). Leave-one-out on the development set: P_opt rule 0.292, energy rule 0.082, CVaR rule 0.164, per-instance training 0.215. So the oracle-free rules are not reliable, and the abstract, contributions, discussion and conclusion say so. Best of 5 now chosen by lowest training energy: 0.203 (was 0.242 by P_opt). Per-instance training reaches lower energy than the fixed set (0.300 vs 0.530, lower on 24 of 30), and energy ranks P_opt poorly across candidate sets (Spearman 0.33). |
| M2 | "new disruption instances" overstates | ⚠️ renamed only | Now "held-out seeds of one disruption pattern" everywhere; varied disruptions listed as a limitation. A generator for three other patterns is in `exp_p1_r3.py` (phase `dis`) but was not run. |
| M3 | scaling evidence thin | ⚠️ text only | Rewrite 8 applied ("fixed angles remain usable at 15 and 18 qubits; it does not establish a gain"); minimum fixed P_opt is 36x and 34x uniform one-hot. A one-hot subspace simulator was added to `qaoa_sim.py` (agrees with the full statevector to 1.8e-16 at G=4, 5) and `exp_p1_sub.py` is ready, but the run (G=5..10, 30 instances) was stopped and is listed as future work. |
| M4 | "tuned" SA weak; uniform-over-feasible baseline | ✅ | "tuned" dropped. SA with one-hot moves ends at the optimum in 93.3% (the encoding's limit) vs 80.0% for bit-flip SA; both visit the optimum every time, so with a verifier both reach 100%. Uniform sampling over feasible plans gives P_opt 0.049; the feasible-subspace mixer's 0.444 is 9.0x that. |
| M5 | statistics: unadjusted p, city clustering, unnamed test, seeds ignored | ✅ | Holm per family (4 depths; 7 transfer rows; 4 city tests). Median paired differences in Table II (+0.195, +0.131, +0.102 for XY mean). Per-city table: fixed set ahead in P_opt in only 3 of 6 cities (sign test p = 1.00); success@32 higher in all 6 (sign test p = 0.03; Holm Wilcoxon p = 0.042). Wilcoxon signed-rank named for success@N. Two-level bootstrap (instances, then seeds): XY mean 0.188, CI 0.127-0.257. |
| M6 | success@N vs verifier; best-of-N gap | ✅ | New Table III: expected gap of the cheapest verified plan among N = 8/32/128 samples. N=8: fixed 0.09%, per-instance 1.49%, uniform one-hot 6.7%; N=128: per-instance 0.10%. Text states the sampler is optimal whenever the optimum is drawn. |
| M7 | hardware cost not quantified | ✅ partly | CNOT counts per layer (Table I): X 28, ring-XY 28, Grover 150 (two W-state layers of 12 CNOTs + 122-CNOT multi-controlled phase with 10 ancillas, Nielsen & Chuang construction); one-time W-state preparation 12 CNOTs (3 per group, checked numerically). XY gate = 2 CNOTs (Vatan & Williams 2004). eps = 0.01 per gate ~ 0.5% per CNOT, compared with Sycamore's 0.36% / 0.62% two-qubit Pauli errors (Arute et al. 2019, checked in the supplement). Noise was not re-run per CNOT (limitation). |
| M8 | novelty and contributions | ✅ | Contributions rewritten around the pairwise encoding and its exactness, the mixer comparison with CNOT counts, transfer with three selection rules and the energy-scale ablation, and the verifier. "Matches or outperforms ... at no per-instance cost" removed. Positioning paragraph added (ring-XY is from [7]; differences from [18]-[20]). Angle concentration: a set's development P_opt predicts its held-out P_opt (Spearman 0.98); only 7 of 30 trained sets beat per-instance training (median set 0.062). Binding vs non-binding: per-instance training 0.106 vs 0.228, fixed set 0.312 vs 0.298, so the gain comes mostly from capacity-binding instances. |
| Minor | macros, p format, tables, notation, refs | ✅ | Macro spacing checked in the PDF text; one p-value format ($8.5\times10^{-4}$, three decimals between 0.01 and 0.1). Table I: "seeds" column removed, Evals and CNOT explained. Penalty renamed mu; group size m_g; optimal set X*. Lemma -> Remark, noting that lambda < 1 breaks the bound. Fig. 1 caption notes different y-axes. Noise table dropped for space (numbers kept in text). Punctuation after equations fixed; "Training never uses the optimal plan" and per-variant training stated. Refs checked: [13], [14] on arXiv (no journal version), Farhi 2014 and Brandao 2018 have no journal version (arXiv pages checked); added Vatan & Williams, Nielsen & Chuang, Arute et al. (Crossref checked). "Mean cost 47 minutes per pair" dropped. 93.3% vs "every instance has an infeasible zero-penalty plan" explained (such plans usually cost more than the optimum). |
| Rewrites 1-10 | | ✅ | All ten applied or rephrased to the same effect (9: "Threats to validity" merged into Limitations; 10: ratio given, 36x and 34x uniform; 6 rephrased as "Stronger optimizers stayed below"). |

Build: `build_series.py p1` -> 6 pages (blind and camera), REFERENCES OK, ALL CHECKS PASSED, no Type 3 fonts. Style: 4,618 words, burstiness 0.58, no em dashes in prose, tell words: "significant" (statistical use only). Old P1 PDFs are in `_before_revision3/`.

### Round 4 (14 Oct 2026, size test from stored results)

No new training was run. The size data in `p1_r4_sub.json` (written by `exp_p1_r4.py sub` in the main repository) were already stored but not yet in the paper. `post_p1_r4.py` now reads them, writes the macros and table, and asserts every claim below. The disruption run (`exp_p1_r4.py dis`, file `p1_r4_dis.json`) was never made; the script now skips it when the file is missing.

| # | Comment | Status | What changed (measured numbers) |
|---|---|---|---|
| M3 | scaling evidence thin (10 instances, 15 and 18 qubits) | ✅ | New Table V: 30 new twin instances for each of G = 5..9 (15 to 27 qubits, 150 in all), simulated exactly on the 3^G one-hot amplitudes. The 12-qubit set of rule (7) beat per-instance training at every size (Holm p <= 0.027 over 10 tests; 15 qubits 0.192 vs 0.111, 27 qubits 0.003 vs 0.001). The energy-rule set won on at least 22 of 30 at every size but was significant only at 21 and 24 qubits. Per-instance training fell below P_opt = 0.01 on at least 28 of 30 instances from 21 qubits on. |
| M3 | (new caveat, added by us) | ✅ claim narrowed | The absolute values are reported as a limit: P_opt of the fixed set fell about 2.9-fold per added group; from 24 qubits every instance was capacity-binding and at most 0.053 of the probability lay on feasible plans. Abstract, discussion and conclusion say so, and the discussion names a capacity-aware mixer or slack encoding as the next step. |
| M3 | subspace simulator validated? | ✅ | New `exp_p1_subcheck.py` (no backend needed): 40 random 12- and 15-qubit circuits, ring-XY, p = 4; largest amplitude difference to the full statevector 1.6e-16 (`p1_subcheck.json`). |
| M2 | varied disruptions | ❌ not done | Needs the main repository's twin backend, which is not in this snapshot. Still listed as a limitation. |
| Minor | Table II 9 pt too wide | ✅ | Column spacing reduced; no overfull boxes. |

Other changes: the global depolarising model is now one sentence (no equation); captions and several paragraphs were shortened to keep 6 pages. The oracle caveat on rule (7) stays in the abstract and in Section IV-A.

Standalone build: this repository has no `backend/`, so `post_p1.py` and `post_p1_r3.py` take nine circuit-size macros (ZZX, ZZXY, OvPairs, CnotX, CnotXY, CnotGM, CnotW, CnotMCP, NAnc) from `p1_backend_macros.json`, a verbatim copy of the delivered round-3 `nums.tex`. With the backend present they are recomputed as before. All other 419 round-3 macros were regenerated from the stored JSON and match the delivered `nums.tex` exactly.

Build (Linux, TeX Live 2023): blind and camera copies 6 pages, references in first-citation order, no undefined references, no overfull boxes, all fonts embedded, no Type 3 fonts, no author names in the blind copy. Round-3 PDFs are in `_before_revision4/`.

### Round 4b (14 Oct 2026, open items of the first review and hand edit of the prose)

| Comment (first review) | Status | What changed |
|---|---|---|
| Compare conditional on feasibility | ✅ | New sentence in Section VI-A: P_opt / P_feas at p = 4 is 0.28 for XY against 0.08 for X (mean over 5 seeds and 30 instances; macros CondXY, CondX from `post_p1_r3.py`, asserted). X from the one-hot subspace: not run (needs the main repo). |
| Define P_opt precisely | ✅ | Section V: an optimal plan is a feasible plan of lowest true cost, not always the QUBO minimiser (checked in `qaoa_sim.diagonals`: `obj` is set only on feasible plans). |
| CVaR alpha tuned? | ✅ | "the only level we tried; it was not tuned" (the scripts only run alpha in {1.0, 0.1}). |
| Noise: which angles | ✅ | "With angles trained per instance" added (`exp_p1_noise.py` retrains per instance). |
| Abstract has too many numbers | ✅ | Abstract cut from about 15 numbers to 9, about 195 words. |
| No code repository cited | ⚠️ please confirm | Added "code and stored results will be released after review". Remove it if the authors do not want to promise this. |
| Open-Meteo in Acknowledgment, weather not described | ⚠️ open | Not changed: this snapshot has no backend code to show how the twin uses Open-Meteo. Authors: either add one clause on what weather data the twin uses or drop Open-Meteo from the Acknowledgment. |
| Penalty sweep below 0.25, Grover over seeds, other disruptions | ❌ | Need new runs in the main repository. |

Prose was edited by hand to plain academic English (no humanizer tool, per CLAUDE.md): staged phrases removed ("tells a different story", "Why does a fixed set work?", "The absolute values temper this result", "The study has limits.", "not our particular one"), one-word last lines tightened. No em dashes in prose, no listed tell words. Build: blind and camera 6 pages, no overfull boxes, references in order, fonts embedded, blind copy anonymous.

### Round 5 (14 Oct 2026, exact capacity penalty and integer programming)

New experiment `exp_p1_r5.py` (runs without the twin backend, about 7 minutes) on the 50 feasible city instances, rebuilt from the frozen snapshot and checked against `p1_cities.json`. Numbers through `post_p1_r5.py`, which asserts every claim. Stored result: `p1_r5.json`.

| Item | Result |
|---|---|
| Exact capacity encoding without slack qubits | New Eq. (4): one product term per minimal overloading set. Exact on all 50 instances (checked over all 81 one-hot plans). The pairwise penalty admitted 262 infeasible penalty-free plans in 47 instances; its minimiser was optimal in 74% (exact penalty: 100%). |
| Feasibility vs optimality (new Table IV) | Trained ring-XY: P_feas 0.601 -> 0.922 (Holm p = 1.5e-6, higher in all 6 cities), P_opt 0.219 -> 0.169 (p = 0.081, not significant), success@32 75.6% -> 81.2% (p = 0.91). Helps capacity-binding instances (0.061 -> 0.125), hurts the others (0.342 -> 0.203). |
| Gate cost | 66 CNOTs per layer on average (up to 120) against 28. A slack encoding would add 15 to 19 qubits. |
| Integer programming | HiGHS (scipy.optimize.milp) returns the optimum on every instance in 2.6 ms; exhaustive search 0.39 ms. New reference [26] (Huangfu and Hall, 2018). |

To stay at 6 pages: the per-city table (old Table IV) and the best-of-N gap table (old Table III) were folded into the text (all their claims and tests remain), contribution 4 merged into contribution 1, and the Discussion and Conclusion were shortened. Build: blind and camera 6 pages, no overfull boxes, 28 references in order, blind copy anonymous.

### Rounds 6-7 (14 Oct 2026, two independent strict internal reviews: 3.4 before, 3.5 after)

New experiments that run without the twin backend, on the city road networks (results in the snapshot, every claim asserted in `post_p1_r6.py` / `post_p1_r7.py`):

| Item | Result |
|---|---|
| Other disruptions (`exp_p1_r6.py`, 147 feasible instances: two roads closed; shelter failed; 70% seat cut) | No fixed set raised P_opt significantly; three lost it (rule (8) with a failed shelter, energy and CVaR sets with two roads closed). Pooled success@32 still rose (74.9-75.1% to 91.7-96.0%). |
| Angle choice without optima (`exp_p1_r7.py`, leave one city out, 197 instances) | Expected cost of the best verified plan among 32 shots (needs no optima) ranks sets like P_opt (Spearman 0.87 vs 0.45 for energy) and picked the city optima's set in 6/6 folds (this is the twin energy rule's set, not the rule-(8) set). Held out: P_opt 0.256 vs 0.277 (n.s.; lower with two roads closed), success@32 75.1% -> 96.2%. |
| Finite-shot version (`exp_p1_r7b.py`, one draw of 32 shots per instance, 1,200 repetitions) | Same set in 43%; held-out success@32 of the picks 96.2% on average, 5th percentile 92.9%. |
| Review fixes | Seed basis of every comparison stated; P_opt/P_feas defined; binding shift between development and held-out seeds; exact-penalty and capacity-share wording ("about half", 52% on a log scale); noiseless noise reference; American spelling; Table I/II/IV notes; intro claim cited. |

Both reviewers judged 4.5 not reachable for this work without new science (a capacity-preserving mixer that helps at 21-27 qubits, or a hardware run); their realistic target is about 4.0 as an honest benchmark paper.

### P1 round 8 (14 Oct 2026, after a strict internal review scored 3.0 to 3.3)

| Comment | Status | Change |
|---|---|---|
| The no-optima rule was chosen and tested on the same 197 city instances | Done | `exp_p1_r8.py`: 195 fresh feasible city instances (240 built, seeds never used in any selection, all four patterns). The chosen set kept P_opt about equal to per-instance training (0.246 vs 0.237, Holm p = 0.049) and raised success@32 from 80.1% to 96.8%, in all 6 cities. |
| No CVaR baseline for success@32 | Done | Per-instance CVaR training on the same fresh instances: 90.6% success@32 at P_opt 0.122; the fixed set stays ahead (Holm p = 8.0e-14). |
| No training-free schedule baseline | Done | Linear ramp with its scale chosen by the same rule: P_opt 0.006, below uniform one-hot sampling (0.012); the best scale lay at the edge of the grid. Reported as is. |
| Discussion said the no-optima rule "made the same choice" as rule (8) | Fixed | It picked the twin energy-rule set; text corrected and asserted in `post_p1_r7.py`. |
| Conclusion lacked the oracle caveat and the p = 4 limit | Fixed | Both added. |
| Missing related work on inequality penalties and weighted parameter setting | Fixed | Montanez-Barrera et al. (QST 2024) and Sureshbabu et al. (Quantum 2024), checked by web search. |
| Wording: "bounds", "at most", Sycamore error, "a device can apply", "ours is not special" | Fixed | Reference point, mean probability, two-qubit Pauli error, "needs no optima", reworded. |
| Page limit | Done | Exact-penalty table folded into text (all its numbers stay in the text); both copies 6 pages, all build checks pass. |

## Paper 3: round 3 (14 Oct 2026, internal review, no new experiments)

An internal reviewer (scored 2.9 / 5) found the problems below. All numbers come from stored results (`p3_city2.json`, `p3_v2.json`, `p3_r2.json`) through `post_p3.py` / `post_p3_r2.py`, which assert each new claim.

| Comment | Status | Change |
|---|---|---|
| Banned word "showcase"; run-ups, rhetorical questions, closers | ✅ | Rewritten by hand. |
| Abstract about 300 words | ✅ | 242 words; "faster in median time". |
| Text vs Table VI (Chennai vs Kolkata) | ✅ | "Among the other five cities, Chennai..."; unsafe range 12.7 to 100.0% instead of "at least 12.7%". |
| "A weak search is part of the story" contradicted by data | ✅ | Now "More search did not help": 400 sweeps better on 1 instance, worse on 5 (asserted); the limit is the encoding and penalty weight. |
| Two values for twin MILP / QAOA times | ✅ | The second set is labelled "a separate timing run". |
| City plan quality of the verified loop missing | ✅ | 2,570 calls on solvable instances: optimal 37.0%, median gap 4.4%, P90 28.7%; plans from greedy 1,516, sampler 940, MILP 114. |
| Penalty-free overload looks like an artifact of the encoding | ✅ | Section III-A states that exact encodings exist (slack variables, minimal-set penalty) and why the pairwise form is kept. |
| "Certificate" too strong | ✅ | Holds within the solver's feasibility tolerance and default MIP gap. |
| Single 5 s deadline looks post hoc | ✅ | Deadline curve: 1/2/5/10/30 s stop 45/22/7/2/1 instances, all with valid plans (asserted). |
| Stale table footnote, missing space "twin,97.7%" | ✅ | Fixed. |
| Self-citation of the P1 overlap; enumeration cross-check of infeasibility | ❌ | Not done (double-blind; enumeration cross-check not in the stored data). |

Build: 6 pages (blind and camera), 21 references, no overfull boxes, blind copy anonymous. Old PDFs in `_before_P3_revision3_2026-10-14/`.

### P3 round 4 (14 Oct 2026, after a fresh strict internal review scored 3.0)

New city-only experiments (no twin backend needed; numbers asserted in `post_p3_r2.py`, `post_p3_r3.py`, `post_p3_r4.py`):

| Item | Result |
|---|---|
| Loop calls the MILP last although results favour it first | Offline replay of a solver-first loop with a deadline and the sampler/greedy as fallback: optimal plans 74.3 / 82.5 / 91.4 / 97.3% for 0.5 / 1 / 2 / 5 s, against 37.0% sampler-first; uncertified escalations of solvable cases at most 0.78%. In the abstract and Section V-D. |
| Is the annealer mis-tuned? (`exp_p3_r4.py`, 108 instances) | Penalty weight x0.25 to x4 and a cost-scaled temperature: valid rate 71.1-78.9 / 33.1-39.3 / 13.3% at 8 / 16 / 32 groups; no setting changed it at 32 groups. |
| One-hot annealer's failures (`exp_p3_r3.py`, `exp_p3_r4.py`) | Valid plans more often (41 instances better, 4 worse), but 77% of its unsafe top samples are penalty-free overloads and 23% forbidden pairs: the encoding's blind spot limits it. |
| Value of the certificate | Of 103 infeasible city instances, 53 have a group with no allowed shelter; 50 have no trivial cause, so only the MILP shows that no plan exists. |
| Text items | Typed "90 shots" now a macro; one set of twin timings; mixed denominators stated; Table notes; repeated sentences cut; unsupported "radio cycle" removed; hedge on novelty; staged phrasing rewritten; trace table folded into text. |

Build: 6 pages, abstract 248 words, no overfull boxes.

### P3 round 5 (14 Oct 2026, after a strict internal review scored 3.0)

| Comment | Status | Change |
|---|---|---|
| City "most frequent sample" pools every non-one-hot vector into one outcome | Done | `exp_p3_r5.py` re-scores the bit-flip annealer on raw vectors (same seeds): top sample unsafe in 42.9 / 77.9 / 83.0% of solvable calls at 8 / 16 / 32 groups; over all 8-group calls 70.5% raw against 71.2% pooled, so the picture is unchanged. Stated in Sec. V. |
| Deadline replay ignores the incumbent of a stopped solver | Done | Re-solved every instance with real limits of 0.5/1/2/5 s on a second computer: valid plan on every solvable instance within 0.5 s, optimum on 96.1% (98.4% within 1 s), all 103 infeasible proved. Replay now called "offline replay from measured solve times". |
| "Certified" overstates a solver result | Fixed | Defined as a solver proof, not an independently checked one; a presolve-off re-solve agreed on all 103 infeasible instances. |
| Retuning "did not help" was false at 8 groups (78.9 vs 72.1) | Fixed | "helped only at small sizes"; at 32 groups every setting succeeded on the same 4 instances (asserted). |
| "Always optimal", "did not repair", "18.4 shots", "three groups" | Fixed | Reworded; adaptive shots now 18.0 (QAOA) and 18.7 (annealing). |
| ReAct / Toolformer / AgentSpec references off topic | Fixed | Replaced by Montanez-Barrera et al. 2024 (inequality penalties) and Hobbs et al. 2023 (runtime-assurance tutorial), both checked by web search. |
| Unused macros, Algorithm 1 fixed vs adaptive budget | Fixed | Macros deleted; Algorithm 1 line 1 states both budgets. |
| Page limit | Done | Event table folded into its text; both copies 6 pages, all checks pass. |

## Paper 4: round 2 finished (14 Oct 2026, internal review, no new experiments)

The round-2 source was never built into a PDF (the old PDF of 10 Oct had the round-1 text). It is now built from stored results; `models/flood_evaluation_v4.json` and `flood_model_metadata_v4.json` (from the main repository) are copied into the results snapshot. The basin folds are already in `p4_r2.json`. An internal reviewer scored the round-2 text 3.0 / 5; changes, each asserted in `post_p4.py` / `post_p4_r2.py`:

| Comment | Change |
|---|---|
| Calibration blamed on the monsoon | The no-class-weight refit (raw ECE 0.008, BA 0.902, onset 0.863 against 0.898 / 0.852 with the weight) shows that the weighting caused the over-confidence and bought no skill; marked post hoc. "The miscalibration is a monsoon problem" removed. |
| "there the LSTM led" (onset) | The difference interval (-0.045 to 0.011) includes zero; abstract, results and conclusion now say "not significantly different". |
| "neither unusually easy nor hard"; "did not carry the result" | The primary refit is at the top of the split range; two basin folds fall below every random split; gain over persistence 0.119-0.136 (splits) vs 0.094-0.186 (basins). |
| "less than 0.005" (false) | "at most 0.0051 (removing rainfall raised it)". |
| "an onset is announced by the weather" | Removed; the no-flow variant is less precise (0.239) and onset counts reward frequent alarms. |
| Leakage overread | "a temporal split matters at least as much" replaced by a note that the test sets differ. |
| Regulation selective | Reservoir index added (rho 0.20, p = 0.23); attribute tests not corrected for multiple comparisons. |
| Bootstrap too narrow | Limitation added (gauges share storms; per-year BA range). |
| "single use of the test set" | Later test-set diagnostics are marked post hoc. |
| Section "Robustness" (banned stem), seed text, run-ups, keywords, Brier DOI | Renamed "Sensitivity to Split and Level"; seeds corrected; prose edited by hand; keywords alphabetical; DOI added. |
| 7 pages | Position table, gain-importance figure, catchment figure, lead-day table and deployment figure folded into the text (their numbers stay). |

Build: 6 pages (blind and camera), 18 references, no overfull boxes. Old PDFs in `_before_P4_revision2_2026-10-14/`.

---

### P4 round 3 (14 Oct 2026, after a strict internal review scored 3.0)

| Comment | Status | Change |
|---|---|---|
| "one of these 1 gauges" (wrong macro) | Fixed | Uses the 49 unseen gauges. |
| Protocol gap called an "inflation" by "the same model" | Fixed | Now "a refit scored on a random row split ... on its own test set"; the discussion says the test sets and flood rates differ, so not all of the gap is leakage. |
| Per-year skill quoted for full years only | Fixed | Adds the partial years 2019 and 2020 (0.783 and 0.767), asserted lower. |
| "Above a flow-trend rule" without an interval | Fixed | Dropped from abstract and conclusion. |
| "Clearly better", "beat climatology", "both needed" | Fixed | Softened to what the numbers support. |
| "Test once", table label "all rows" | Fixed | "test on"; "selected refit". |
| Prose items | Fixed | Rewrites from the review. |
| Not done | Open | Prevalence-normalised PR-AUC, block bootstrap over years, CSI/F1 and Brier skill (needs re-analysis), forecast-rain inputs (new experiment). |

## Paper 5: rebuilt (14 Oct 2026)

| Item | Status | Change |
|---|---|---|
| P1 summary lacked the oracle caveat | Fixed | States that rule (8) uses development optima, that energy/CVaR sets fell below per-instance training in leave-one-out, adds the no-optima rule's fresh-city result and the three disruption losses. |
| P3 summary used removed time-out macros | Fixed | Now reports the 1 s deadline (45 instances stopped, all solvable) and the solver-first result (82.5% vs 37.0% optimal). |
| P2 wording "caught" for guards | Fixed | "flagged", with labelled errors where recall is meant. |
| Reuse of companion papers not stated | Fixed | One sentence in the Introduction. Submit P5 or the separate papers, never both. |
| Unclosed quote in Sec. VII, build path in this repo | Fixed | `post_p5.py` finds the companion folders here; P2 post uses stored labels when the backend is absent. |
| Page limit | Done | Duplicate P1 figure dropped; abstract rewritten (under 250 words); 6 pages, all checks pass. |

## Our own score estimate (not a real review)

| Criterion (out of 5) | P1 | P2 |
|---|---|---|
| Originality | 3.3 | 3.3 |
| Technical soundness | 4.2 | 4 |
| Clarity | 4.2 | 4 |
| Significance | 3.5 | 3.5 |
| Reproducibility | 4.3 | 4 |
| **Overall** | **about 4.1 to 4.2** (was 3.8) | **about 3.8** (was 3.4) |

Only the conference reviewers give the real score.

## What would still raise the score

1. **P2:** a co-author fills in the second-annotator sheet; we then report Cohen's kappa (highest value, no API calls).
2. **P2:** one more model family (Llama or Qwen); needs approval for API calls.
3. **P1:** run the fixed-angle circuit on real hardware or a hardware noise model.
4. **P1:** run `exp_p1_r4.py dis` (three other disruption patterns) in the main repository; `post_p1_r4.py` already writes its macros and table rows. This answers the last open major comment (M2).
5. **P1:** a capacity-aware mixer (or slack encoding) test at 21 to 27 qubits, since capacity is now the main stated limit.

## Submission checklist

- Upload only the `*_SUBMIT_blind_review.pdf` files.
- Run each through IEEE PDF eXpress with the conference ID.
- Check the venue's page limit and blind-review rule.
- Do not submit P5 to the same venue as P1 or P2, because it reuses their results.
- The AI-use disclosure stays in the Acknowledgment, as the IEEE policy requires.
