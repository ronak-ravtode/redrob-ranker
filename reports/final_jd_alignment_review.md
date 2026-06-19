# Final JD Alignment Review

## Source references
- Ontology terms: `src/config.py` `PATTERN_GROUPS` and `NEGATIVE_PATTERNS`.
- Career/profile/skill feature extraction: `src/features.py` `_career_text`, `_group_evidence`, `extract_features`.
- Weighting: `src/scoring.py` `score_features`.
- Coarse retrieval: `src/features.py` `is_coarse_candidate`.

## Principles
| Principle | Status | Evidence |
| --- | --- | --- |
| Career-history evidence dominates raw skill keywords | PASS | `score_features` weights career/current evidence heavily; skill evidence max contribution is small and skill corroboration depends on career evidence. |
| Skills list alone cannot create a top candidate | PASS | `is_coarse_candidate` ignores skill-only relevance; keyword stuffing penalty applies when AI skills lack career core. |
| Summary claims receive less trust than career evidence | PASS | profile evidence contributes only 0.018 saturation support. |
| Behavioural signals only modify technically relevant candidates | PASS | coarse filter runs before scoring; behavior contributes only 0.035. |
| Location/notice bounded modifiers | PASS | location and notice together contribute at most 0.038. |
| Missing/-1 signal sentinels handled | PASS | safe parsing and GitHub -1 sentinel normalization in `features.py`. |
| Plain-language strong candidates identified | PASS | tests cover `match people to roles`, `surface relevant`, `candidate ranking system`. |
| Keyword stuffing penalized | PASS | `keyword_stuffer` plus test coverage. |
| Candidate-ID independence | PASS | candidate ID used only for deterministic tie-breaking and tests; no source-code allowlist/denylist. |

## Gaps
- Open-source contributions are not explicitly scored because the observed schema has no direct open-source field beyond GitHub activity.
- HR-tech/recruiting marketplace exposure is captured indirectly through matching/candidate-JD terms, not a dedicated company-domain classifier.
