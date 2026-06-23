# Reasoning Quality Review

## Improvements Made

- Explanations still cite concrete titles, companies, and project sentences from `career_history`.
- Reasoning now adds semantic alignment concepts from the retrieval layer, such as production scale, ranking evaluation, and semantic retrieval.
- The reason generator prefers role descriptions containing BM25, dense retrieval, vector indexing, learning-to-rank, metrics, A/B tests, latency, engagement, and ownership terms.
- Concerns remain grounded in actual fields such as notice period, stale activity, location fit, missing evaluation evidence, or missing vector-infrastructure evidence.

## Example Output

`CAND_0081846` ranks first because the profile includes Lead AI Engineer work at Razorpay with BM25 plus dense retrieval, BGE embeddings, FAISS HNSW, LLM re-ranking, and fallback learning-to-rank, plus additional Paytm migration from BM25-only retrieval to hybrid sparse/dense vectors.

The explanation now also states that semantic retrieval aligns the profile with production scale and operations, ranking evaluation and experimentation, and semantic retrieval/information retrieval.

## Quality Controls

- No LLM generation is used during ranking or explanation.
- Explanations are deterministic and derived from candidate evidence plus computed feature fields.
- Reasoning remains faithful to the same fields used for scoring: career history, skills, behavior/logistics, anomaly metadata, and semantic concepts.

## Remaining Limitation

- Many generated candidate descriptions share project templates, so top-candidate explanations can still sound similar even when they are factually grounded.
