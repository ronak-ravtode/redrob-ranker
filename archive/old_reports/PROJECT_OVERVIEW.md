# Redrob Ranker — Complete Project Overview

## 1. What This Project Does

**Problem:** A company (Redrob) has a pool of **100,000 candidate profiles** in JSONL format. They need to hire a **Senior AI/ML Engineer** focused on ranking, recommendation systems, search, and information retrieval. The task is to rank all 100K candidates and output the **top 100** as a CSV submission.

**Solution:** A deterministic, evidence-first ranking pipeline that scores each candidate using a hybrid formula: **75% evidence-based scoring + 25% semantic embedding similarity**. Every ranked candidate gets a grounded explanation citing actual profile facts.

**Key Numbers:**
- 100,000 candidates processed in ~55 seconds (warm)
- 46 tests passing (22 original + 24 adversarial)
- 10/10 deterministic runs (identical output every time)
- 100/100 reasoning explanations grounded in profile data
- ~236 MB peak memory, CPU-only, no GPU required
- Zero external API calls, fully offline

---

## 2. Architecture Overview

```
candidates.jsonl (100K profiles)
         │
         ▼
┌─────────────────────┐
│  Coarse Filter       │  ← Rejects ~99% of obviously irrelevant candidates
│  (is_coarse_candidate)│     Uses regex on career text + title matching
└─────────┬───────────┘
          │ ~900 candidates pass
          ▼
┌─────────────────────┐
│  Anomaly Detection   │  ← Excludes honeypots/impossible profiles
│  (detect_anomaly_confidence)│  High confidence = exclude, Medium = penalize
└─────────┬───────────┘
          │ ~850 candidates pass
          ▼
┌─────────────────────┐
│  Feature Extraction  │  ← Extracts 30+ features per candidate
│  (extract_features)  │     Career evidence, skills, behavior, fit signals
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Semantic Scoring    │  ← Transformer (70%) + Domain keywords (30%)
│  (semantic_features) │     local all-MiniLM-L6-v2, cached JD embedding
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Hybrid Scoring      │  ← score = 0.75 * evidence + 0.25 * semantic
│  (score_features)    │     Additive formula with penalties
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Top-K Selection     │  ← Min-heap keeps top 300, sort by score
│  (rank_candidates)   │     Tie-breaking: candidate_id ascending
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Reasoning Generation│  ← Plain-English explanation for each candidate
│  (build_reason)      │     Cites specific career facts, no hallucination
└─────────┬───────────┘
          │
          ▼
    submission.csv (top 100 with reasoning)
```

---

## 3. File Structure

```
redrob-ranker/
├── rank.py                    # Main CLI: iter_candidates, rank_candidates, write_submission
├── Dockerfile                 # Judge evaluation container (downloads model during build)
├── requirements.txt           # numpy, sentence-transformers, torch
├── candidates.jsonl           # 100K candidate profiles (464 MB)
├── submission.csv             # Output: top 100 with reasoning
├── validate_submission.py     # Validates output format
│
├── src/
│   ├── config.py              # Ontology: PATTERN_GROUPS, NEGATIVE_PATTERNS, RELEVANT_TITLE_TERMS
│   ├── jd_understanding.py    # JDProfile dataclass, DEFAULT_JD_TEXT
│   ├── features.py            # Feature extraction: is_coarse_candidate, extract_features
│   ├── scoring.py             # Additive scoring formula: score_features
│   ├── semantic.py            # Hybrid semantic: transformer + domain fallback
│   ├── embedding_model.py     # Model loading, encode_texts, cosine_similarity
│   ├── anomaly.py             # Anomaly detection with confidence levels
│   ├── reasoning.py           # Grounded explanation generation
│   └── text_utils.py          # normalize, clipped, contains_any, candidate_id_suffix
│
├── models/
│   └── all-MiniLM-L6-v2/     # Bundled transformer weights (87 MB, not in git)
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── config.json
│
├── tests/
│   ├── test_adversarial.py    # 24 adversarial tests
│   ├── test_anomaly.py        # Anomaly detection tests
│   ├── test_hybrid_layers.py  # Hybrid scoring tests
│   ├── test_ontology.py       # Pattern coverage tests
│   ├── test_rank.py           # Pipeline integration tests
│   ├── test_reasoning.py      # Reasoning generation tests
│   └── test_scoring.py        # Scoring formula tests
│
├── scripts/
│   ├── generate_top50.py      # Human review data generation
│   ├── reasoning_audit.py     # Audit 100 random explanations
│   ├── determinism_test.py    # 10-run determinism verification
│   └── setup_embeddings.py    # Model download helper
│
├── reports/                   # Evaluation reports
│   ├── judge_gap_analysis.md
│   ├── top50_human_review.md
│   ├── failure_case_review.md
│   ├── semantic_ablation.md
│   ├── post_embedding_benchmark.md
│   ├── reasoning_grounding_audit.md
│   ├── determinism_stress_test.md
│   ├── recruiter_trust_report.md
│   └── reproducibility_review.md
│
├── docs/
│   ├── embedding_upgrade_plan.md
│   ├── model_packaging.md
│   ├── final_judge_presentation.md  # 10-slide presentation content
│   └── mock_judge_interview.md      # 50 Q&A for judge prep
│
├── FINAL_JUDGE_REVIEW.md           # Scored at 90.7%
├── FINAL_EMBEDDING_UPGRADE_REVIEW.md
└── .gitignore                      # models/ excluded from git
```

---

## 4. Scoring Formula (The Core)

### 4.1 Final Score

```python
score = 0.75 * evidence_only_score + 0.25 * semantic_fit_score
```

Evidence dominates. Semantic is supporting.

### 4.2 Evidence Score Components

```python
evidence_score = ranking_retrieval + evaluation + production_ownership

ranking_retrieval =
    0.36 * saturated(career.ranking + career.retrieval, 8)      # Career evidence of ranking/retrieval work
    + 0.12 * saturated(career.vector_infra, 4)                   # Vector DB experience
    + 0.08 * saturated(current.ranking + current.retrieval, 4)   # Current job relevance
    + 0.06 * saturated(career.ranking + career.retrieval + career.production, 10)

evaluation = 0.18 * saturated(career.evaluation, 5)             # NDCG, A/B testing, etc.

production_ownership =
    0.08 * saturated(career.production, 5)                       # Shipped to production
    + 0.08 * saturated(career.ownership, 6)                      # Led/designed/built
    + 0.03 * saturated(career.scale_systems, 4)                   # Kubernetes, monitoring, etc.
```

### 4.3 Supporting Score

```python
supporting =
    0.030 * saturated(career.python, 4)                          # Python/ML stack
    + 0.015 * saturated(career.fine_tuning, 3)                    # LoRA, PEFT
    + 0.018 * saturated(profile_evidence.ranking + ... , 5)       # Profile/headline claims
    + 0.012 * saturated(skill_evidence.ranking + ..., 5)          # Skill list mentions
    + 0.018 * skill_corroboration                                 # Skills match career evidence
```

### 4.4 Fit Score

```python
fit =
    0.042 * experience_fit(years)          # Sweet spot: 6-8.5 years = 1.0
    + 0.028 * title_relevant               # Binary: is current title relevant?
    + 0.030 * role_depth                    # How many relevant roles + months
    + 0.022 * location_fit                  # India preferred cities = 1.0
    + 0.016 * notice_fit                    # <30 days notice = 1.0
    + 0.020 * title_trajectory             # Career progression
    + 0.018 * job_stability                 # Low churn = high stability
    + 0.020 * product_company_history       # Non-consulting experience
```

### 4.5 Behavior Score

```python
behavior = 0.035 * behavior_fit
# behavior_fit = recency (26%) + open_to_work (18%) + response_rate (18%)
#              + response_speed (8%) + interview_completion (13%)
#              + saved_by_recruiters (7%) + github_activity (6%) + verified (4%)
```

### 4.6 Penalties

```python
penalty = 0.0
if keyword_stuffer:   penalty += 0.34    # Skills listed but no career evidence
if consulting_only:   penalty += 0.16    # Only worked at consulting firms
if cv_only:           penalty += 0.22    # CV/speech background, no ranking
if research_only:     penalty += 0.18    # Academic only, no production
if recent_llm_only:   penalty += 0.18    # Just started learning LLMs
if career_core == 0:  penalty += 0.20    # No ranking/retrieval/evaluation evidence
penalty += anomaly_penalty               # From anomaly detection (0.06 per medium flag, max 0.16)
```

### 4.7 Semantic Score

```python
# If transformer available:
semantic_score = 0.70 * transformer_cosine + 0.30 * domain_keyword_similarity

# If transformer unavailable (fallback):
semantic_score = domain_keyword_similarity
```

---

## 5. Feature Extraction Details

### 5.1 Career Text Processing

```python
career_text = normalize所有job titles + descriptions concatenated)
current_career_text = normalize(current job title + description only)
profile_text = normalize(headline + summary + current_title)
```

### 5.2 Pattern Matching (Ontology)

Each pattern group counts unique regex matches in career text:

| Group | Examples | Weight in Scoring |
|-------|----------|-------------------|
| ranking | "learning-to-rank", "relevance", "scoring function" | 0.36 |
| retrieval | "semantic search", "dense retrieval", "bm25" | 0.36 |
| vector_infra | "faiss", "pinecone", "hnsw", "vector database" | 0.12 |
| evaluation | "ndcg", "a/b test", "human relevance" | 0.18 |
| production | "shipped", "deployed", "at scale", "p95" | 0.08 |
| ownership | "owned", "led", "built", "end-to-end" | 0.08 |
| python | "python", "pytorch", "scikit-learn" | 0.03 |
| fine_tuning | "lora", "qlora", "peft" | 0.015 |
| scale_systems | "kubernetes", "mlflow", "monitoring" | 0.03 |

### 5.3 Fast Path Optimization

For 100K candidates, most are obviously irrelevant. The fast path skips detailed extraction:

```python
if not title_relevant and not COARSE_CAREER_REGEX.search(career_text):
    return zero_features  # Skip expensive regex scans
```

This processes ~99K candidates in microseconds each.

### 5.4 Skill Corroboration

Checks if skills listed in profile are backed by career evidence:

```python
corroborated = count(groups where career[group] > 0 AND skills[group] > 0)
skill_corroboration = corroborated / 5.0
```

---

## 6. Semantic Embedding System

### 6.1 Model

- **Model:** `all-MiniLM-L6-v2` (22M parameters, 384 dimensions)
- **Size:** 87 MB (bundled locally, not in git)
- **Device:** CPU-only
- **Caching:** JD embedding cached via `lru_cache(maxsize=1)` — computed once, reused for all 900+ candidates

### 6.2 Hybrid Scoring

```python
# Transformer path (if model available):
transformer_score = cosine_similarity(jd_embedding, candidate_embedding)
# Maps from [-1, 1] to [0, 1]: (cosine + 1) / 2

# Domain fallback (always available):
domain_score = cosine_similarity(
    _candidate_embedding(candidate),   # Weighted: career=1.0, profile=0.55, skills=0.30
    _jd_embedding(jd_text)             # Cached, weight=1.0
)
# Uses CONCEPT_SYNONYMS (9 categories) + token hashing

# Final:
if transformer available:
    semantic_score = 0.70 * transformer_score + 0.30 * domain_score
else:
    semantic_score = domain_score
```

### 6.3 Domain Fallback (No Transformer)

When transformer is unavailable, uses deterministic domain embedding:

1. **Concept matching:** Counts matches against 9 concept synonym groups (ranking, retrieval, matching, etc.)
2. **Token hashing:** Hashes tokens to 192-dim sparse vector
3. **Bigram hashing:** Hashes token pairs for phrase detection
4. **Cosine similarity:** Dot product of candidate and JD domain vectors

### 6.4 Candidate Text Representation

For transformer encoding, candidates are represented as:

```
headline summary current_title Skills: skill1, skill2, skill3 Experience: Title at Company | Description | ...
```

---

## 7. Anomaly Detection

### 7.1 High Confidence (Exclude)

| Flag | Detection | Action |
|------|-----------|--------|
| job_negative_duration | end_date < start_date | Exclude |
| future_employment_date | start_date > reference_date | Exclude |
| job_duration_mismatch | |calculated - declared| > 3 months | Exclude |
| company_before_founding_year | Job start before company founding | Exclude |
| experience_sum_mismatch | |summed_years - declared_years| > 2.0 | Exclude |
| contradictory_current_job_state | Multiple current jobs or title mismatch | Exclude |
| multiple_expert_skills_with_zero_duration | 3+ expert skills with 0 months | Exclude |

### 7.2 Medium Confidence (Penalize)

| Flag | Detection | Penalty |
|------|-----------|---------|
| skill_duration_exceeds_profile_experience | Skill months > total experience + 24 | 0.06 |
| many_expert_skills_with_low_tenure | 4+ expert skills with ≤6 months | 0.06 |
| current_job_missing_from_history | Current company not in career history | 0.06 |

### 7.3 Low Confidence (Warn)

| Flag | Detection |
|------|-----------|
| missing_experience_or_history | No years or no career history |
| thin_skill_duration_metadata | 5+ skills missing duration |

---

## 8. Negative Pattern Detection

Catches profiles that have keywords but no substance:

| Pattern | Examples | Penalty |
|---------|----------|---------|
| recent_llm_only | "recently started learning langchain", "calling openai" | 0.18 |
| cv_speech_only | "computer vision models", "speech recognition" | 0.22 |
| research_only | "academic lab", "pure research", "phd" | 0.18 |

**Keyword stuffer detection:** 3+ AI skill mentions in skill list but 0 career evidence = penalty 0.34

---

## 9. Reasoning Generation

Every ranked candidate gets a plain-English explanation:

```
"Rank 1: Built ranking and recommendation systems at Acme Corp over 48 months with
production ownership. Strong evaluation background (NDCG, A/B testing). 7 years
experience aligns with role requirements. Active on platform with fast response time."
```

**Grounding:** Each explanation cites specific companies, titles, and durations from the actual profile. No hallucinated facts.

---

## 10. Coarse Filter

Before expensive feature extraction, quickly rejects obviously irrelevant candidates:

```python
def is_coarse_candidate(candidate):
    # Check 1: Current title contains relevant terms?
    if contains_any(title, RELEVANT_TITLE_TERMS):
        return True
    # Check 2: Career text contains ranking/retrieval terms?
    if COARSE_CAREER_REGEX.search(all_career_text):
        return True
    return False
```

**Effect:** Processes ~900 candidates in detail out of 100K. The other ~99K are rejected in microseconds.

---

## 11. Determinism

The system is fully deterministic:

1. **No randomness:** All scores are computed from deterministic functions
2. **Tie-breaking:** When scores are equal, candidates are ordered by `candidate_id` ascending
3. **Heap selection:** Uses `(score, -suffix, candidate_id, record)` as heap key
4. **Final sort:** `(-score, suffix, candidate_id)` for descending order
5. **Verified:** 10/10 runs produce identical SHA-256 hash of ranking output

---

## 12. Test Coverage

### 12.1 Original Tests (22)

| Test File | Tests | What It Tests |
|-----------|-------|---------------|
| test_scoring.py | 3 | Score formula correctness, missing data handling |
| test_reasoning.py | 3 | Explanation generation, malformed input |
| test_anomaly.py | 3 | Anomaly detection for impossible profiles |
| test_rank.py | 5 | Pipeline integration, CSV output, error handling |
| test_ontology.py | 5 | Pattern coverage, paraphrase detection |
| test_hybrid_layers.py | 3 | Semantic scoring, JD profile, anomaly integration |

### 12.2 Adversarial Tests (24)

| Category | Tests | What It Tests |
|----------|-------|---------------|
| KeywordStuffingTests | 2 | Detects skill-list-only candidates |
| FakeExperienceTests | 2 | Detects fabricated ranking/retrieval experience |
| SkillOnlyProfileTests | 2 | Skill-only profiles not treated as relevant |
| AIBuzzwordProfileTests | 2 | LLM-only and prompt engineer profiles penalized |
| MalformedDateTests | 2 | Future dates, invalid formats handled |
| DuplicateCompanyTests | 1 | Duplicate companies allowed (not anomalous) |
| ContradictoryTitleTests | 1 | Current job contradictions detected |
| EmptySummaryTests | 2 | Empty/None summaries don't crash |
| AnomalyExclusionTests | 2 | High/medium anomalies handled correctly |
| ScoringEdgeCaseTests | 2 | Score bounds for extreme inputs |
| ReasoningEdgeCaseTests | 2 | Empty/single job histories produce valid reasoning |
| SemanticEdgeCaseTests | 2 | Empty candidates, JD alignment |
| IntegrationTests | 2 | Full pipeline, submission validation |

---

## 13. Deployment

### 13.1 Docker (for Judges)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Downloads model during build (not copied from git)
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2').save('models/all-MiniLM-L6-v2')"
COPY rank.py sandbox_app.py ./
COPY src ./src
COPY data ./data
EXPOSE 7860
CMD ["python", "sandbox_app.py", "--host", "0.0.0.0", "--port", "7860"]
```

### 13.2 Model Auto-Download

If model isn't found locally, `src/embedding_model.py` auto-downloads it:

```python
def _resolve_model_dir():
    # Check env var, then local paths
    # If not found, download from HuggingFace Hub
    SentenceTransformer("all-MiniLM-L6-v2").save("models/all-MiniLM-L6-v2")
```

### 13.3 Running

```bash
# Direct
python rank.py --candidates candidates.jsonl --out submission.csv --keep 300 --top-k 100

# Docker
docker build -t redrob-ranker .
docker run -p 7860:7860 redrob-ranker
```

---

## 14. Evaluation Results

### 14.1 Human Review (Top 50)

| Category | Count | Percentage |
|----------|-------|------------|
| Strong Fit | 19 | 38% |
| Moderate Fit | 30 | 60% |
| Weak Fit | 1 | 2% |

### 14.2 Semantic Ablation

| Configuration | Top-100 Overlap with Evidence-Only | Spearman Correlation |
|---------------|-------------------------------------|---------------------|
| Evidence Only | 100/100 (baseline) | 1.00 |
| Hybrid (Current) | 87/100 | 0.94 |
| Semantic Only | 62/100 | 0.71 |

### 14.3 Performance

| Metric | Value |
|--------|-------|
| Cold start | ~115s |
| Warm runtime | ~55s |
| Memory peak | ~236 MB |
| Model size | 87 MB |
| Candidates processed | 100,000 |
| Candidates after coarse filter | ~900 |
| Top-K output | 100 |

### 14.4 Judge Review Score

**90.7%** (304/335 points) across 5 categories:
- Ranking Quality: 80/90
- Evaluation & Auditability: 92/100
- Engineering Quality: 74/80
- Innovation: 39/45
- Presentation & Polish: 19/20

---

## 15. Key Design Decisions

1. **Evidence-dominant (75%):** Recruiters need explainable, evidence-backed rankings. Pure ML models are black boxes.

2. **Local transformer:** No API calls, no cloud, no data exfiltration. Privacy-compliant, reproducible.

3. **Deterministic output:** Prerequisite for production deployment and auditability. 10/10 identical runs.

4. **Coarse filter first:** Processes 900 out of 100K candidates in detail. Others rejected in microseconds.

5. **Anomaly-aware:** High-confidence honeypots excluded before scoring. Medium anomalies penalized, not excluded.

6. **Graceful degradation:** If transformer unavailable, falls back to domain keywords. System never crashes.

7. **Bundled model:** 87MB model weights in `models/` dir. Downloaded during Docker build, not pushed to git.

---

## 16. How to Extend

### Add New Role
1. Update `RELEVANT_TITLE_TERMS` in `src/config.py`
2. Update `PATTERN_GROUPS` with role-specific terms
3. Update `DEFAULT_JD_TEXT` in `src/jd_understanding.py`
4. Re-run scoring

### Add New Feature
1. Add extraction function in `src/features.py`
2. Add to `extract_features()` return dict
3. Add weight in `src/scoring.py` `score_features()`
4. Add test in `tests/`

### Add New Anomaly
1. Add detection logic in `src/anomaly.py` `detect_anomalies()`
2. Add confidence level in appropriate set (HIGH/MEDIUM/LOW)
3. Add test in `tests/test_anomaly.py`

---

## 17. Dependencies

```
numpy
sentence-transformers
torch (CPU-only)
```

No cloud services, no APIs, no GPU required.

---

## 18. Repository URLs

- **GitHub:** https://github.com/ronak-ravtode/redrob-ranker
- **HuggingFace:** https://huggingface.co/spaces/ronak-ravtode/redrob-ranker
- **Team:** "Code With Errors" — Nek Patel, Ronak Ravtode
