# CLAUDE.md: AquaSentinel IEEE paper series

Instructions for Claude Code (or any AI assistant) working in this repository. Read `README.md` first for the layout and the status of each paper.

## What this repository is

A snapshot of five 6-page IEEE conference papers (P1 to P5) with their LaTeX, experiment scripts, stored results and built PDFs. The source of truth during development is the main AquaSentinel repository (`.claude/skills/ieee-paper/series/`); this repository is the shareable copy.

| Key | Code folder here | Folder name in the main repo |
|---|---|---|
| p1 | `P1_Quantum_QAOA/code` | `p1_quantum` |
| p2 | `P2_Agentic_AI/code` | `p2_agentic` |
| p3 | `P3_Runtime_Assurance/code` | `p3_qagentic` |
| p4 | `P4_Forecasting_CAMELS_IND/code` | `p4_forecast` |
| p5 | `P5_Merged_FailClosed_Chain/code` | `p5_merged` |

## Rules that must never be broken

- **Never type a number into `paper.tex`.** Numbers come only from `post_<key>.py`, which reads the experiment JSON, writes `nums.tex` and asserts every comparison the text makes.
- **Never fabricate, guess or round up results.** If a new analysis weakens a claim, change the claim (title and abstract included).
- **No fabricated human labels or agreement scores.** P2's second-annotator sheet (`P2_Agentic_AI/pdf_and_tex/second_annotator/`) waits for a real co-author; do not report Cohen's kappa until it is filled in.
- **No remote LLM API calls** for the papers (the authors stopped them). Re-analyse the stored replies only.
- **No humanizer or AI-detector-evasion tools.** Edit prose by hand: plain academic English, no em dashes in prose, no AI tell words (delve, leverage, robust, seamless, crucial, notably, pivotal, showcase, underscore), varied sentence length. Never claim an AI-detector or plagiarism percentage.
- **Keep the IEEE AI-use disclosure** in the Acknowledgment.
- **Blind copies have no author names.** Check every `*_SUBMIT_blind_review.pdf` after a build.
- **P5 reuses P1 to P4.** Submit P5 or the separate papers, never both, and never overlapping papers to one venue.
- City experiments read `shared_code/city_snapshot_2026-10-13/` only, never live city files.

## Describing the methods correctly

- P1's QAOA is a classical statevector simulation. Claim no quantum advantage and no hardware run.
- P1 angle selection by mean optimal-plan probability uses the exact optima of the development set (an oracle). Oracle-free rules (energy, CVaR) fell below per-instance training in leave-one-out tests. Every summary of P1, including P5's, must say this.
- P2 covers numeric grounding only. The claim check's accuracy is not measured; say "flagged x% of replies", not "catches".
- The benchmark "QAOA" in `hqrl_demo.py` (main repo) is a softmax heuristic, not QAOA.

## Building

```powershell
$env:PAPER_MAX_PAGES=6; $env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python.exe .claude\skills\ieee-paper\series\build_series.py p1
```

- Always set the page limit to 6 (the default is 8).
- A good build ends with `REFERENCES OK` and `ALL CHECKS PASSED`, 6 pages, no Type 3 fonts (matplotlib needs `pdf.fonttype 42`).
- The work directory is `%TEMP%\aquasentinel-series` unless `PAPER_SERIES_WORK` is set; the stored results are in `shared_code/results_snapshot_2026-10-14/`.
- After changing any `\cite` in P5, run `p5_merged/fill_bib.py`. P5's post script re-runs post_p1..p4 and uses the macro prefixes `Qa` (P1), `Ag` (P2), `Ra` (P3), `Fc` (P4).

## Pitfalls

- Bash heredocs collapse `\\` in LaTeX; write LaTeX-touching Python with an editor tool or `chr(92)`.
- `audit_refs.py` only sees `\ref` written in `paper.tex`, not inside generated macros.
- A macro followed by text needs `{}` (for example `\StrWarm{}`), or the space after it is lost.
- HiGHS status 1 means time limit, not infeasible.
- The authors' laptop is a slow Core i3: run long experiments in the background, one at a time, and prefer re-using stored JSON over re-running experiments.

## Work style

- Change one paper at a time and rebuild only that paper.
- Back up delivered PDFs to a dated `_before_revisionN/` folder before replacing them.
- Record each reviewer comment, its status and the change in `latest_14_oct/IEEE_reviewer_response.md`.
- Commit or push only when the authors ask.
