# Final Architecture

## Layered System

```text
candidates.jsonl
  -> 1. JD Understanding Layer
  -> 2. Candidate Intelligence Layer
  -> 3. Semantic Retrieval Layer
  -> 4. Evidence Extraction Layer
  -> 5. Integrity Validation Layer
  -> 6. Hybrid Ranking Engine
  -> 7. Explainability Layer
  -> 8. Top-100 Output Layer
```

## Architecture Diagram

```text
                      +-------------------------+
                      | JD Understanding Layer  |
                      | JDProfile requirements  |
                      +-----------+-------------+
                                  |
                                  v
+----------------+     +----------+-----------+     +---------------------+
| candidates     | --> | Candidate Intelligence | --> | Evidence Extraction |
| JSONL stream   |     | profile/career/skills |     | ontology features   |
+----------------+     +----------+-----------+     +----------+----------+
                                  |                           |
                                  v                           v
                      +-----------+------------+    +---------+----------+
                      | Semantic Retrieval     |    | Integrity          |
                      | deterministic embedding|    | Validation         |
                      | optional local MiniLM  |    | confidence/action  |
                      +-----------+------------+    +---------+----------+
                                  |                           |
                                  +------------+--------------+
                                               v
                                  +------------+--------------+
                                  | Hybrid Ranking Engine     |
                                  | .75 evidence + .25 sem    |
                                  +------------+--------------+
                                               v
                                  +------------+--------------+
                                  | Explainability Layer      |
                                  | evidence + semantic why   |
                                  +------------+--------------+
                                               v
                                  +------------+--------------+
                                  | Top-100 CSV Output        |
                                  +---------------------------+
```

## Layer Details

1. JD Understanding Layer: `src/jd_understanding.py` converts the Senior AI Engineer role into a structured `JDProfile` with required skills, preferred skills, domain signals, production signals, evaluation signals, ownership signals, negative signals, ontology groups, and title terms.
2. Candidate Intelligence Layer: `rank.py` streams candidates and keeps memory bounded; `src/features.py` extracts profile, career, skill, logistics, behavior, and title trajectory features.
3. Semantic Retrieval Layer: `src/semantic.py` computes deterministic semantic embeddings over JD and candidate text, with optional CPU local `sentence-transformers` model loading from `REDROB_SEMANTIC_MODEL_PATH` or `models/all-MiniLM-L6-v2` when local weights exist.
4. Evidence Extraction Layer: ontology-based evidence remains the precision layer and continues to favor career-history proof over summaries or skill lists.
5. Integrity Validation Layer: `src/anomaly.py` separates high-confidence exclusions, medium-confidence penalties, and low-confidence warnings.
6. Hybrid Ranking Engine: `src/scoring.py` blends `0.75 * evidence_only_score + 0.25 * semantic_fit_score`.
7. Explainability Layer: `src/reasoning.py` cites titles, companies, projects, evaluation/production evidence, concerns, and semantic concepts.
8. Top-100 Output Layer: `rank.py` writes the official CSV schema: `candidate_id,rank,score,reasoning`.

## Reproducibility Controls

- Default path uses only the Python standard library and local files.
- Optional transformer mode never downloads weights; it only loads an existing local directory.
- Ranking is deterministic: two full runs produced byte-identical output.
- Validator passes on the generated `Code_With_Errors.csv`.
