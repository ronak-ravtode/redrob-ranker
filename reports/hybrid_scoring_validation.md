# Hybrid Scoring Validation

## Scoring Formula

Final score is now:

```text
0.75 * evidence_only_score + 0.25 * semantic_fit_score
```

The evidence score is the existing deterministic career/profile/skill/logistics score. The semantic score is bounded to `[0, 1]` and supports retrieval-style recall without replacing evidence.

## Evidence-Only Top 10

| rank | candidate_id | evidence_only |
| ---: | --- | ---: |
| 1 | CAND_0081846 | 1.21510470 |
| 2 | CAND_0041611 | 1.21246417 |
| 3 | CAND_0046525 | 1.19021020 |
| 5 | CAND_0094759 | 1.18177799 |
| 8 | CAND_0077337 | 1.17409617 |
| 4 | CAND_0046064 | 1.16992330 |
| 7 | CAND_0010685 | 1.16322400 |
| 6 | CAND_0086022 | 1.14475953 |
| 9 | CAND_0005649 | 1.11761220 |
| 12 | CAND_0080766 | 1.09822273 |

## Semantic-Only Top 10 From Review Pool

| semantic_rank | candidate_id | semantic_fit | evidence_only |
| ---: | --- | ---: | ---: |
| 1 | CAND_0007411 | 0.85924497 | 0.70958600 |
| 2 | CAND_0011687 | 0.85619699 | 0.72133530 |
| 3 | CAND_0054123 | 0.85288842 | 0.72131612 |
| 4 | CAND_0046064 | 0.85279171 | 1.16992330 |
| 5 | CAND_0081846 | 0.85275022 | 1.21510470 |
| 6 | CAND_0005260 | 0.84180494 | 0.94542262 |
| 7 | CAND_0026532 | 0.83765873 | 0.81752717 |
| 8 | CAND_0075249 | 0.83763074 | 0.79258431 |
| 9 | CAND_0008425 | 0.83752119 | 1.08282680 |
| 10 | CAND_0066376 | 0.83295382 | 0.73939500 |

## Hybrid Top 10

| hybrid_rank | candidate_id | hybrid_score | evidence_only | semantic_fit |
| ---: | --- | ---: | ---: | ---: |
| 1 | CAND_0081846 | 1.12451608 | 1.21510470 | 0.85275022 |
| 2 | CAND_0041611 | 1.10452420 | 1.21246417 | 0.78070431 |
| 3 | CAND_0046525 | 1.09448906 | 1.19021020 | 0.80732563 |
| 4 | CAND_0046064 | 1.09064040 | 1.16992330 | 0.85279171 |
| 5 | CAND_0094759 | 1.08224577 | 1.18177799 | 0.78364910 |
| 6 | CAND_0086022 | 1.06563558 | 1.14475953 | 0.82826371 |
| 7 | CAND_0010685 | 1.06103687 | 1.16322400 | 0.75447547 |
| 8 | CAND_0077337 | 1.05987077 | 1.17409617 | 0.71719458 |
| 9 | CAND_0005649 | 1.03594490 | 1.11761220 | 0.79094301 |
| 10 | CAND_0008425 | 1.02150040 | 1.08282680 | 0.83752119 |

## Why Hybrid Is Superior

- Evidence-only is precise but can under-reward paraphrased semantic fit.
- Semantic-only finds conceptually aligned profiles, but some have much weaker career evidence and should not outrank proven production owners.
- Hybrid keeps the strongest evidence candidates at the top while allowing semantic alignment to resolve close cases.
- `CAND_0046064` moves above some evidence-near peers because it has both high evidence and very high semantic fit.
- Semantic-only leaders with evidence scores around `0.71` remain below candidates with production ranking/retrieval evidence above `1.1`, which protects ranking quality.
