# Failure Case Analysis — Redrob Candidate Ranking System

**Role:** Senior AI Engineer (Ranking, Retrieval, Recommendation, Semantic Search, Evaluation Metrics, Production Ownership)

**Data Source:** `top50_review_data.json` (Top 50 Candidates)

**Generated:** 2026-06-23

---

## 1. False Positives (Over-Ranked Candidates)

These candidates are ranked higher than their actual fit warrants. The system's evidence scoring or semantic alignment compensates for weaknesses that would be red flags in a manual review.

### 1.1 CAND_0086022 — Rank #8, Score 1.067

| Metric | Value |
|---|---|
| evidence_only | 1.145 |
| semantic_score | 0.832 |
| skill_corroboration | 0.40 |
| anomaly_flags | `skill_duration_exceeds_profile_experience:penalize` |
| relevant_months / total_months | 63 / 63 |

**Why ranked high:** Strong evidence-only score (1.145) from claimed roles at Sarvam AI and Uber. The semantic layer (0.832) maintains alignment with production-scale concepts.

**Why problematic:** The `skill_duration_exceeds_profile_experience` anomaly flag indicates claimed skill durations exceed the candidate's total profile experience — a signal of possible credential inflation. With `skill_corroboration` at only 0.40, the system is not cross-validating skill claims against career trajectory. The anomaly penalty was applied but was insufficient to suppress the ranking.

**Root cause:** Evidence scoring relies on role descriptions without adequately penalizing inconsistent skill-to-experience ratios.

---

### 1.2 CAND_0005649 — Rank #9, Score 1.047

| Metric | Value |
|---|---|
| evidence_only | 1.118 |
| semantic_score | 0.834 |
| relevant_months / total_months | 34 / 88 (39%) |
| behavior_fit | 0.816 |
| notice_fit | 0.50 |

**Why ranked high:** High evidence-only score (1.118) from claimed search-relevance work at Sarvam AI and Glance.

**Why problematic:** Only 34 out of 88 total months (39%) involve relevant roles. The majority of this candidate's career is in unrelated domains. The `experience_fit: 1.0` flag suggests the system treats any relevant role as full experience fit, regardless of what proportion of total career it represents. A 90-day notice period further complicates hiring.

**Root cause:** The `experience_fit` metric does not discount for what fraction of total career is actually relevant. A candidate with 2 years of relevant work in an 8-year career should not score the same as one with 6 years of relevant work in a 6-year career.

---

### 1.3 CAND_0086151 — Rank #15, Score 0.973

| Metric | Value |
|---|---|
| evidence_only | 1.018 |
| semantic_score | 0.841 |
| skill_corroboration | 0.40 |
| notice_fit | 0.25 (120-day notice) |

**Why ranked high:** Strong evidence from Glance and Meta roles. High semantic alignment (0.841) with the target role.

**Why problematic:** A 120-day notice period (`notice_fit: 0.25`) is a practical dealbreaker in most hiring contexts. Low skill corroboration (0.40) means skill claims are not well-validated by career evidence. The system's scoring formula (`0.75 × evidence + 0.25 × semantic`) allows the evidence score to override the severe notice constraint.

**Root cause:** Notice period is a binary constraint in many hiring pipelines. A 120-day wait is equivalent to a rejection for time-sensitive roles, but the system treats it as a continuous penalty rather than a hard gate.

---

### 1.4 CAND_0092278 — Rank #13, Score 0.996

| Metric | Value |
|---|---|
| evidence_only | 1.050 |
| semantic_score | 0.832 |
| behavior_fit | 0.216 |
| skill_corroboration | 0.40 |

**Why ranked high:** Evidence-only score of 1.050 from Saarthi.ai and Microsoft roles. Strong alignment with ranking/retrieval concepts.

**Why problematic:** `behavior_fit` at 0.216 is extremely low — the lowest in the top 15. This metric typically reflects platform engagement patterns, application consistency, or profile activity signals. A score this low suggests the candidate may have inconsistent or concerning engagement patterns that could predict poor hiring outcomes. The system does not apply a minimum threshold or exponential penalty for critically low behavior scores.

**Root cause:** Linear weighting of `behavior_fit` allows other high-scoring dimensions to compensate. Behavior scores below 0.30 should trigger a hard review gate.

---

### 1.5 CAND_0046525 — Rank #3, Score 1.098

| Metric | Value |
|---|---|
| evidence_only | 1.190 |
| semantic_score | 0.821 |
| skill_corroboration | 0.40 |
| notice_fit | 0.75 (60-day notice) |

**Why ranked high:** Third-highest evidence-only score (1.190) from LinkedIn and Genpact AI roles.

**Why problematic:** `skill_corroboration` at 0.40 is below the median for top-10 candidates. A 60-day notice period introduces delay. Being ranked #3 based primarily on role descriptions without stronger corroboration of skill claims risks interviewing candidates whose actual capabilities may not match their stated experience.

**Root cause:** The evidence scoring weight is too dominant relative to corroboration and practical constraints.

---

## 2. False Negatives (Under-Ranked Candidates)

These candidates have strong evidence that the system undervalues due to coarse filtering, penalty over-weighting, or scoring blind spots.

### 2.1 CAND_0088025 — Rank #36, Score 0.870

| Metric | Value |
|---|---|
| evidence_only | 0.896 |
| semantic_score | 0.790 |
| years | 8.6 |
| relevant_months / total_months | 102 / 102 (100%) |
| behavior_fit | 0.940 |
| skill_corroboration | 0.80 |
| career_core | 8 |

**What evidence the system missed:** This candidate has 102 relevant months — the highest of any candidate in the top 50 — with 100% career relevance. `behavior_fit` at 0.94 and `skill_corroboration` at 0.80 are both in the top tier. The 8.6-year career spans 3 directly relevant roles at Yellow.ai and Genpact AI.

**Why ranked low:** The `career_core` score of 8 is unusually low and appears to penalize the candidate disproportionately. The 90-day notice period (`notice_fit: 0.50`) further reduces the score. The system appears to use `career_core` as a multiplicative factor that suppresses otherwise strong candidates.

**Missed signal:** A candidate with 102 months of perfectly relevant experience and top-tier behavior/corroboration scores should not rank below candidates with 34 relevant months (e.g., CAND_0005649 at rank #9).

---

### 2.2 CAND_0039383 — Rank #37, Score 0.864

| Metric | Value |
|---|---|
| evidence_only | 0.882 |
| semantic_score | 0.811 |
| years | 7.1 |
| relevant_months / total_months | 84 / 84 (100%) |
| location_fit | 1.0 |
| skill_corroboration | 0.60 |
| career_core | 10 |

**What evidence the system missed:** 84 out of 84 months are relevant (100% ratio). 3 relevant roles spanning 7.1 years. Perfect location fit. Skill corroboration is solid at 0.60. Career evidence includes ranking model training (XGBoost/LightGBM) and semantic search feature development.

**Why ranked low:** `career_core` at 10 and 90-day notice period (`notice_fit: 0.50`) suppress the score. The system treats `career_core` as a structural dimension that cannot be compensated by strong evidence.

**Missed signal:** The 100% relevance ratio is the strongest signal of focused career development, yet the system ranks this candidate below candidates with <50% relevance ratios.

---

### 2.3 CAND_0064326 — Rank #41, Score 0.852

| Metric | Value |
|---|---|
| evidence_only | 0.869 |
| semantic_score | 0.799 |
| years | 7.6 |
| behavior_fit | 0.935 |
| location_fit | 1.0 |
| skill_corroboration | 0.40 |
| career_core | 11 |

**What evidence the system missed:** 7.6 years of experience with `behavior_fit` at 0.935 (top 5% of all candidates). 3 relevant roles. Perfect location fit. Career evidence includes offline-online correlation analysis and ranking layer evolution work at Aganitha and Sarvam AI.

**Why ranked low:** `skill_corroboration` at 0.40 limits the score. The system appears to penalize candidates whose skill lists don't closely match the job description keywords, even when career evidence demonstrates equivalent competence.

**Missed signal:** High `behavior_fit` is one of the strongest predictors of hiring success. The system should weight behavior signals more heavily when skill corroboration is moderate.

---

### 2.4 CAND_0071974 — Rank #27, Score 0.910

| Metric | Value |
|---|---|
| evidence_only | 0.933 |
| semantic_score | 0.840 |
| years | 7.8 |
| relevant_months / total_months | 92 / 92 (100%) |
| skill_corroboration | 0.60 |
| title_trajectory | 0.375 |

**What evidence the system missed:** 92 out of 92 months are relevant (100% ratio). Skills include Learning to Rank, BM25, Pinecone, Qdrant, Information Retrieval — directly matching the role. Career evidence includes end-to-end ranking pipeline ownership and evaluation harness construction.

**Why ranked low:** `title_trajectory` at 0.375 suggests the system penalizes the candidate's career progression trajectory. The candidate's titles may not show clear upward progression in the way the trajectory model expects, even though the work is directly relevant.

**Missed signal:** When `title_trajectory` is low but `relevant_months` is 100%, the trajectory metric may be measuring title semantics rather than actual career growth.

---

### 2.5 CAND_0030827 — Rank #46, Score 0.824

| Metric | Value |
|---|---|
| evidence_only | 0.820 |
| semantic_score | 0.836 |
| years | 5.4 |
| relevant_months / total_months | 64 / 64 (100%) |
| skill_corroboration | 0.80 |
| anomaly_flags | `skill_duration_exceeds_profile_experience:penalize` |

**What evidence the system missed:** 100% relevance ratio. `skill_corroboration` at 0.80 (top tier). Skills include Hugging Face Transformers, NLP, Recommendation Systems, FAISS, LlamaIndex, BM25 — a strong match. Career evidence includes ranking layer evolution and semantic search feature development.

**Why ranked low:** The anomaly penalty for `skill_duration_exceeds_profile_experience` is suppressing an otherwise strong candidate. Additionally, location (Singapore, `location_fit: 0.05`) and 120-day notice (`notice_fit: 0.25`) compound the penalty.

**Missed signal:** The anomaly penalty may be a false positive itself — a 5.4-year career with 64 relevant months and strong skill corroboration suggests the skill duration claims are plausible, not inflated.

---

## 3. Borderline Candidates (Mixed Signals)

These candidates have strong evidence in some areas but significant gaps in others, making them difficult to classify.

### 3.1 CAND_0028793 — Rank #23, Score 0.951

| Strength | Concern |
|---|---|
| 7.2 years experience | 120-day notice period (`notice_fit: 0.25`) |
| Google (current employer) | Only 2 relevant roles (45 / 85 months = 53%) |
| skill_corroboration: 0.60 | career_core: 11 |

**Assessment:** The Google affiliation and solid skill corroboration are offset by a 120-day notice period and below-average relevance ratio. The system ranks this candidate at #23, which seems appropriate given the practical constraints. However, if the notice period is negotiable, this candidate's Google experience and semantic alignment (0.823) make them a strong potential hire.

---

### 3.2 CAND_0018499 — Rank #12, Score 1.014

| Strength | Concern |
|---|---|
| 7.2 years, 86/86 relevant months (100%) | career_core: 11 (below median of ~12-14) |
| 3 relevant roles | skill_corroboration: 0.60 |
| location_fit: 1.0 | |

**Assessment:** This candidate has perfect relevance ratio and strong evidence, but the below-average `career_core` score creates uncertainty. The system ranks them at #12, which may slightly under-rank them given the 100% relevance ratio. The main risk is that `career_core` may be a proxy for company prestige or role seniority that doesn't directly predict performance.

---

### 3.3 CAND_0026532 — Rank #45, Score 0.826

| Strength | Concern |
|---|---|
| semantic_score: 0.852 (highest in top 50) | evidence_only: 0.818 (below average) |
| 2 relevant roles, 56/56 months (100%) | years: 4.8 (below threshold) |
| location_fit: 0.82 | experience_fit: 0.62 |

**Assessment:** This candidate has the highest semantic score in the entire dataset (0.852), suggesting excellent conceptual alignment with the role. However, the evidence-only score (0.818) is below average, and the 4.8-year experience is below the typical senior threshold. The semantic layer is doing most of the work to maintain this candidate's rank. If semantic scoring is removed, this candidate would rank significantly lower.

---

### 3.4 CAND_0005538 — Rank #40, Score 0.855

| Strength | Concern |
|---|---|
| 4 relevant roles (most in top 50) | career_core: 9 (low) |
| 69/69 relevant months (100%) | skill_corroboration: 0.20 (very low) |
| behavior_fit: 0.90 | anomaly_flags: research_only |

**Assessment:** This candidate has the most diverse relevant role experience (4 roles) with 100% relevance ratio. However, `skill_corroboration` at 0.20 is the lowest in the top 50, and the `research_only` flag suggests the system detects research-oriented rather than production-oriented work. The breadth of experience vs. depth of corroboration creates a genuine ambiguity.

---

### 3.5 CAND_0060054 — Rank #14, Score 0.988

| Strength | Concern |
|---|---|
| 3 relevant roles, 76/76 months (100%) | career_core: 12 |
| location_fit: 0.82 | behavior_fit: 0.585 (below average) |
| evidence_only: 1.040 | |

**Assessment:** Strong evidence-only score with 100% relevance ratio. The below-average `behavior_fit` (0.585) introduces uncertainty about platform engagement patterns. This candidate is correctly ranked at #14 — strong enough to interview but with enough behavioral signals to warrant additional screening.

---

## 4. Semantic Layer Impact

The scoring formula is `final_score = 0.75 × evidence_only + 0.25 × semantic_score`. Since all candidates have `semantic_score < evidence_only`, the semantic layer consistently moderates scores downward. The impact is most significant for candidates at decision boundaries.

### 4.1 CAND_0026532 — Semantic as Primary Differentiator

| Metric | Value |
|---|---|
| evidence_only | 0.818 |
| semantic_score | 0.852 |
| final_score | 0.826 |

This is the only candidate in the top 50 where `semantic_score` (0.852) exceeds the proportional contribution needed to maintain rank. The semantic layer adds +0.8% to the final score relative to evidence-only. Without it, this candidate would likely fall out of the top 50. The semantic model identifies strong conceptual alignment with "ranking evaluation and experimentation" and "semantic retrieval and information retrieval" despite limited career evidence.

### 4.2 CAND_0086151 — Semantic Compensating for Practical Constraints

| Metric | Value |
|---|---|
| evidence_only | 1.018 |
| semantic_score | 0.841 |
| final_score | 0.973 |

The semantic score (0.841) is among the highest in the dataset. While it doesn't fully compensate for the 120-day notice period, it prevents the candidate from being ranked lower. Without the semantic layer, this candidate's ranking would drop further, likely below rank #20.

### 4.3 CAND_0046064 — Semantic Alignment with Amazon Evidence

| Metric | Value |
|---|---|
| evidence_only | 1.170 |
| semantic_score | 0.843 |
| final_score | 1.088 |

The semantic score (0.843) is the second-highest in the top 10. The candidate's Amazon Search & Ranking role provides strong evidence that the semantic model correctly identifies as relevant. The semantic layer contributes +0.4% to the final score, helping maintain the #5 rank.

### 4.4 CAND_0005649 — Semantic Masking Weak Evidence Ratio

| Metric | Value |
|---|---|
| evidence_only | 1.118 |
| semantic_score | 0.834 |
| final_score | 1.047 |
| relevant_months / total_months | 34 / 88 (39%) |

The high semantic score (0.834) helps maintain this candidate's #9 rank despite only 39% career relevance. The semantic model identifies alignment with "ranking evaluation and experimentation" and "semantic retrieval and information retrieval" from the limited relevant roles, but does not account for the fact that 61% of the candidate's career is in unrelated domains.

### 4.5 CAND_0041669 — Semantic Holding Rank #50

| Metric | Value |
|---|---|
| evidence_only | 0.812 |
| semantic_score | 0.823 |
| final_score | 0.815 |

This candidate at rank #50 has the smallest evidence-semantic gap (0.011) in the dataset. The semantic score (0.823) is nearly equal to the evidence score (0.812), meaning the semantic layer adds minimal value. The candidate barely makes the top 50 cutoff, and removing the semantic layer would likely push them out.

---

## 5. Mitigation Strategies

### 5.1 Reducing False Positives

| Priority | Strategy | Impact | Implementation |
|---|---|---|---|
| **P0** | Add hard gate for `behavior_fit < 0.30` | Prevents candidates like CAND_0092278 from ranking in top 20 | Add `if behavior_fit < 0.30: score *= 0.5` or route to manual review |
| **P0** | Add hard gate for `notice_fit < 0.30` (120+ days) | Prevents impractical candidates from占据 top ranks | Add `if notice_fit < 0.30: flag_for_review = true` |
| **P1** | Penalize low `relevant_months / total_months` ratio | Prevents candidates like CAND_0005649 (39% relevance) from ranking high | Multiply `experience_fit` by relevance ratio |
| **P1** | Increase weight of `skill_corroboration` for anomaly-flagged candidates | Prevents inflated profiles from ranking high | For anomaly-flagged: `score *= (0.5 + 0.5 * skill_corroboration)` |
| **P2** | Implement exponential penalty for `career_core < 8` | Prevents structurally weak profiles from ranking in top 15 | `if career_core < 8: score *= 0.7` |

### 5.2 Reducing False Negatives

| Priority | Strategy | Impact | Implementation |
|---|---|---|---|
| **P0** | Decouple `career_core` from evidence scoring | Prevents strong candidates like CAND_0088025 from being suppressed by structural factors | Use `career_core` as a tiebreaker, not a multiplicative factor |
| **P0** | Reward 100% relevance ratio explicitly | Surfaces candidates like CAND_0039383 (84/84 months) who are fully focused | Add `relevance_ratio_bonus = 1.0 + 0.1 * (relevant_months / total_months)` |
| **P1** | Add minimum `behavior_fit` bonus for scores > 0.90 | Rewards high-engagement candidates like CAND_0064326 (0.935) | `if behavior_fit > 0.90: score *= 1.05` |
| **P1** | Relax `title_trajectory` weight when relevance ratio is 100% | Prevents title-naming conventions from penalizing strong candidates | `if relevance_ratio == 1.0: title_trajectory_weight *= 0.5` |
| **P2** | Implement "experience density" metric | Rewards candidates with concentrated relevant experience over spread-out careers | `density = relevant_months / years` |

### 5.3 Improving Borderline Classification

| Priority | Strategy | Impact | Implementation |
|---|---|---|---|
| **P1** | Create decision boundary confidence intervals | Flags candidates within ±5% of cutoff scores for manual review | Add `confidence` field to ranking output |
| **P1** | Implement ensemble scoring with multiple models | Reduces single-model blind spots | Average evidence-based, semantic, and behavioral models |
| **P2** | Add "hiring manager override" capability | Allows domain experts to adjust weights for specific roles | Expose weight configuration per job posting |

### 5.4 Improving Semantic Layer Accuracy

| Priority | Strategy | Impact | Implementation |
|---|---|---|---|
| **P1** | Fine-tune semantic model on domain-specific career data | Reduces false alignment from generic embedding similarity | Train on historical hire/no-hire decisions |
| **P1** | Add semantic penalty for low relevance ratio | Prevents semantic model from boosting partially-relevant candidates | Weight semantic contribution by relevance ratio |
| **P2** | Implement concept-level scoring instead of profile-level | Better captures specific skill alignment | Score against individual job requirements, not overall profile |

---

## Summary

| Failure Type | Count | Primary Root Cause | Highest-Impact Fix |
|---|---|---|---|
| False Positives | 5 | No hard gates for practical constraints | Hard gate for `behavior_fit < 0.30` and `notice_fit < 0.30` |
| False Negatives | 5 | `career_core` over-penalization | Decouple `career_core` from evidence scoring |
| Borderline | 5 | Single-score decision boundary | Add confidence intervals and manual review routing |
| Semantic Impact | 5 | Uniform semantic scores reduce differentiation | Fine-tune semantic model on domain-specific data |

The highest-priority fix is implementing hard review gates for critically low `behavior_fit` and `notice_fit` scores, which would immediately prevent the most problematic false positives from reaching the top of the ranking.
