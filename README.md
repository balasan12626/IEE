# AquaSentinel IEEE Paper Series (P1 to P5)

Five 6-page IEEE conference papers from the AquaSentinel flood digital-twin project, with their LaTeX sources, the Python experiment scripts that produce every number, the stored experiment results and the built PDFs.

Snapshot of 14 October 2026.

## The papers

| Key | Folder | Title |
|---|---|---|
| P1 | `P1_Quantum_QAOA/` | One-Hot-Preserving QAOA for Flood Shelter Assignment: Pairwise Capacity Encoding and Angle Transfer |
| P2 | `P2_Agentic_AI/` | Rules Decide, Language Models Narrate: Fail-Closed Numeric Grounding of LLM Narration in a Flood-Response Pipeline |
| P3 | Round 5 done (14 Oct): raw-vector re-scoring, real MILP time limits, infeasibility re-check, reference and wording fixes; 6 pages, all checks pass. |
| P4 | `P4_Forecasting_CAMELS_IND/` | Forecasting Three-Day High-Flow Exceedance at Gauges Unseen in Space and Time: A Leakage-Controlled Benchmark on CAMELS-IND |
| P5 | `P5_Merged_FailClosed_Chain/` | Checking Every Proposal: A Fail-Closed Flood Decision-Support Chain from Forecast to Dispatch |

P5 is a merged system paper that reuses the results of P1 to P4. Submit either P5 or the separate papers, never both, and never two overlapping papers to the same venue.

## Folder layout

```
IEE FOLDERGITUP/
  P1_Quantum_QAOA/ ... P5_Merged_FailClosed_Chain/
    code/          paper.tex, exp_*.py (experiments), post_*.py (numbers -> nums.tex), older revisions
    pdf_and_tex/   built PDFs and their .tex, nums.tex, figures
  shared_code/
    build_series.py              builds one or more papers (PDF, page and reference checks)
    qaoa_sim.py                  statevector and one-hot-subspace QAOA simulator (P1, P3, P5)
    audit_refs.py, reorder_refs.py   reference checks and ordering
    city_snapshot_2026-10-13/    frozen city road networks used by the city experiments (SHA256SUMS.txt inside)
    results_snapshot_2026-10-14/ stored experiment results (JSON) that the post scripts read
  latest_14_oct/   newest P1, P2, P3 PDFs, IEEE_reviewer_response.md, backups of earlier rounds
```

Inside each `pdf_and_tex/`:

- `P#_SUBMIT_blind_review.pdf` is the file to upload for double-blind review (no author names).
- `P#_camera_ready_with_authors.pdf` is for after acceptance only.

## Status (14 Oct 2026)

| Paper | Status |
|---|---|
| P1 | Round 8 done (14 Oct): confirmatory test on 195 fresh city instances, CVaR and linear-ramp baselines, review fixes; 6 pages, all checks pass. Capacity remains the main open limit. |
| P2 | Second round done; PDFs are final for that round. The third round was stopped part way, so `P2_Agentic_AI/code/paper.tex` is half edited. `paper_before_r3.tex.bak` is the version that matches the PDFs. |
| P3 | Round 5 done (14 Oct): raw-vector re-scoring, real MILP time limits, infeasibility re-check, reference and wording fixes; 6 pages, all checks pass. |
| P4 | Second round done (14 Oct): built from stored results, 6 pages. |
| P5 | Must be rebuilt after P3 and P4; the build currently fails on a missing P3 macro (`RaTimeoutFeasible`), and its P1 summary needs the new caveat on oracle angle selection. |

The reviewer comments and what was changed for each are in `latest_14_oct/IEEE_reviewer_response.md`.

## How the numbers are made

No number is typed into a `paper.tex`. Each experiment script writes a JSON file; the paper's `post_*.py` reads that JSON, writes the numbers as LaTeX macros into `nums.tex` and asserts every comparison the text makes. If an experiment changes and a claim no longer holds, the build stops.

## Rebuilding

The scripts were written to run inside the main AquaSentinel repository, where they live in `.claude/skills/ieee-paper/series/` and import `backend/` modules. To rebuild from this folder:

1. Put the main repository next to this folder, or copy `shared_code/*.py` and the five `code/` folders back into `.claude/skills/ieee-paper/series/` (`p1_quantum`, `p2_agentic`, `p3_qagentic`, `p4_forecast`, `p5_merged`).
2. Point the work directory at the stored results: set `PAPER_SERIES_WORK` to a folder holding the files of `shared_code/results_snapshot_2026-10-14/`.
3. Build with a 6-page limit (the default limit is 8):

```powershell
$env:PAPER_MAX_PAGES=6; $env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python.exe .claude\skills\ieee-paper\series\build_series.py p1 p2 p3 p4 p5
```

A good build ends with `REFERENCES OK` and `ALL CHECKS PASSED`. Needs Python 3 with numpy, scipy, networkx and matplotlib, and a LaTeX install with `pdflatex` and `pdftotext`.

Re-running the experiments themselves (`exp_*.py`) is slow on a laptop; the post scripts and the build only need the stored JSON.

## Before submitting

- Upload only the `*_SUBMIT_blind_review.pdf` files and check them with IEEE PDF eXpress.
- Check the venue's page limit and blind-review rules.
- The AI-use disclosure stays in the Acknowledgment, as IEEE policy requires.
- If this repository is public, the papers can be found online while under double-blind review. Keep it private until the decisions are out.
