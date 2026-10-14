# Final PDFs for CMT upload (14 Oct 2026)

Upload the **blind review** PDFs. They have no author names, and the PDF author field is empty. Each one is 6 pages in IEEE conference format, with no Type 3 fonts and the IEEE AI-use disclosure in the Acknowledgment.

| File | Paper |
|---|---|
| `P1_QAOA_blind_review.pdf` | One-Hot-Preserving QAOA for Flood Shelter Assignment: Pairwise Capacity Encoding and Angle Transfer |
| `P2_LLM_Grounding_blind_review.pdf` | Rules Decide, Language Models Narrate: Fail-Closed Numeric Grounding of LLM Narration in a Flood-Response Pipeline |
| `P3_Runtime_Assurance_blind_review.pdf` | Runtime Assurance for Sampling-Based Optimizers in Flood Re-Planning: Exact Verification and Certified Escalation |
| `P4_Forecasting_blind_review.pdf` | Forecasting Three-Day High-Flow Exceedance at Gauges Unseen in Space and Time: A Leakage-Controlled Benchmark on CAMELS-IND |
| `P5_Merged_System_blind_review.pdf` | Checking Every Proposal: A Fail-Closed Flood Decision-Support Chain from Forecast to Dispatch |

`camera_ready_with_authors/` holds the copies with author names. Use them only after acceptance.

## Rules before you submit

1. **P5 reuses the results of P1 to P4.** Submit either P5 or the separate papers, never both. Never send two overlapping papers to the same venue.
2. **P1 and P3 share the shelter problem and the twin.** Send them to different venues, or say in each one that the other exists.
3. Run every PDF through IEEE PDF eXpress with the conference ID if the venue asks for it.
4. Check the venue's page limit (these are 6 pages) and its blind-review rules.
5. **P2:** a co-author still has to fill in the second-annotator sheet (`P2_Agentic_AI/pdf_and_tex/second_annotator/`). Do not report Cohen's kappa before that.

## Where things are

The sources are in `<paper>/code/paper.tex`. The numbers come from `post_<key>.py`. The review history is in `latest_14_oct/IEEE_reviewer_response.md`.
