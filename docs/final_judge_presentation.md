# Redrob Ranker: Evidence-First Candidate Ranking

## Intelligent Candidate Discovery Challenge

---

## Slide 1: Title

### Redrob Ranker: Evidence-First Candidate Ranking

**Intelligent Candidate Discovery Challenge**

> Every ranking decision is grounded in verifiable evidence.

**Speaker Notes:**
Welcome judges. Today we present redrob-ranker, a candidate ranking system built on a core philosophy: evidence first. We process 100K candidates for an ML/Information Retrieval role and deliver a transparent, reproducible top-100 list with full reasoning. No black boxes.

---

## Slide 2: The Problem

### Why is candidate ranking hard?

- **Scale**: 100K candidates to evaluate for a single ML/IR role
- **Noise**: Keyword matching misses paraphrases and domain adjacency
  - "search relevance optimization" ≠ exact keyword "information retrieval"
- **Opacity**: Pure LLM approaches are non-deterministic and provide no audit trail
- **Speed**: Manual screening is impossible at this volume

**The gap**: We need a system that is fast, explainable, and robust — not just accurate.

**Speaker Notes:**
The core challenge is not just finding candidates, but doing so reliably. Traditional keyword search fails on paraphrases. LLMs hallucinate and give different results each run. We needed something deterministic, auditable, and fast enough for 100K records.

---

## Slide 3: Our Approach

### Evidence-First Philosophy

| Component | Weight | Purpose |
|-----------|--------|---------|
| Evidence-based scoring | **75%** | Skills, career trajectory, experience, behavior signals |
| Semantic embedding | **25%** | Transformer-based similarity for paraphrase capture |

**Design principles:**
1. Every score is additive and traceable to specific features
2. Semantic layer enhances but never overrides evidence
3. Anomaly detection flags suspicious profiles with confidence levels
4. Grounded reasoning generated for every ranked candidate

**Speaker Notes:**
We deliberately kept evidence at 75% weight. This means the system remains deterministic and auditable. The 25% semantic component catches what keywords miss — like paraphrased skills — but cannot override the evidence signal. This is a feature, not a limitation.

---

## Slide 4: Architecture

### Pipeline Overview

```
candidates.jsonl (100K)
        │
        ▼
┌──────────────────┐
│  Coarse Filter   │  ← Rule-based pre-screening
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ Feature Extract  │  ← Skills, trajectory, experience, behavior
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  Scoring Engine  │  ← 75% evidence + 25% semantic
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  Reasoning Gen   │  ← Grounded explanations per candidate
└──────────────────┘
        │
        ▼
   top_100.jsonl
```

**Key specs:**
- Local transformer: `all-MiniLM-L6-v2` (87MB, bundled)
- No external API calls — fully offline execution
- Single command: `python rank.py`

**Speaker Notes:**
The pipeline is four stages. First, a coarse filter removes obvious non-matches. Then we extract structured features. The scoring engine combines evidence and semantic signals. Finally, we generate a grounded reason for every candidate. The entire system runs locally — no cloud dependency.

---

## Slide 5: Semantic Upgrade

### From Keywords to Embeddings

| Metric | Before (Keywords) | After (Transformer) |
|--------|-------------------|---------------------|
| Paraphrase capture | None | High |
| Top-100 overlap | Baseline | **87% overlap** with baseline |
| External dependency | None | None (local model) |
| Bundle size | 0 MB | 87 MB |

**Example:**
- Candidate profile: "search relevance optimization and ranking systems"
- Keyword match: FAILS (no exact "information retrieval" match)
- Semantic match: **MATCHES** — transformer captures domain adjacency

**Why 87% overlap matters:**
The semantic layer enhances without replacing evidence. 87% of top-100 candidates are shared between evidence-only and hybrid scoring — proving evidence dominance is preserved.

**Speaker Notes:**
The semantic upgrade was the most impactful change. We went from pure keyword matching to a local transformer. The key result: 87% overlap between the evidence-only top-100 and the hybrid top-100. This proves the semantic layer is additive, not disruptive. We caught paraphrases like "search relevance optimization" that keywords missed entirely.

---

## Slide 6: Robustness

### Adversarial Testing

**46 tests passing** (22 original + 24 adversarial)

| Adversarial Pattern | Detection | Action |
|---------------------|-----------|--------|
| Keyword stuffers | Anomaly flag | Confidence: HIGH |
| Fake experience claims | Anomaly flag | Confidence: MEDIUM |
| AI buzzword profiles | Anomaly flag | Confidence: HIGH |
| Malformed JSON | Graceful skip | Logged, not ranked |
| Empty profiles | Filtered | Pre-screening stage |

**Anomaly detection output:**
```json
{
  "candidate_id": "edge_001",
  "anomaly_flags": ["keyword_stuffing"],
  "confidence": "high",
  "action": "flagged_for_review"
}
```

**Speaker Notes:**
We tested against real-world adversarial patterns. Keyword stuffers load up on terms without substance. Fake experience claims don't hold up under feature extraction. AI buzzword profiles are detected by their pattern. All 46 tests pass, including 24 adversarial cases we specifically designed.

---

## Slide 7: Determinism & Reproducibility

### Same Input → Same Output, Every Time

**Verification:**
- 10/10 identical runs confirmed
- Deterministic hash verification on output files
- No random seeds, no stochastic elements in scoring

**Reproducibility guarantees:**
- Bundled model weights (no download required at runtime)
- Pinned dependencies in `requirements.txt`
- Docker-ready for judge evaluation
- Single command execution: `python rank.py`

**Speaker Notes:**
This is critical for hackathon evaluation. We ran the system 10 times on the same input and got identical output files, verified by hash comparison. The model weights are bundled — no internet access needed. Judges can reproduce our results exactly with a single command.

---

## Slide 8: Results

### Performance Summary

| Metric | Value |
|--------|-------|
| Input size | 100,000 candidates |
| Output size | Top 100 ranked |
| Processing time | ~55 seconds |
| Peak memory | ~236 MB |
| Reasoning grounding rate | **100%** |

**Human evaluation (50 candidates reviewed):**
- Strong Fit: **19/50** (38%)
- Moderate Fit: **30/50** (60%)
- Weak Fit: **1/50** (2%)

**Key insight:** 98% of ranked candidates are at least moderate fits for the role.

**Speaker Notes:**
The numbers speak for themselves. 100K candidates processed in under a minute. Every single ranked candidate has a grounded reason. Human review of 50 candidates showed 98% are moderate or strong fits. The one weak fit was an edge case we've since addressed in the adversarial tests.

---

## Slide 9: Key Differentiators

### Why Redrob Ranker Wins

1. **Evidence-dominant scoring (75% weight)**
   - Auditable, deterministic, explainable
   - Semantic layer enhances but never overrides

2. **Local transformer (no cloud dependency)**
   - `all-MiniLM-L6-v2` bundled at 87MB
   - Works offline, no API costs, no rate limits

3. **Transparent reasoning for every candidate**
   - 100% grounding rate
   - Every score traces to specific features

4. **Comprehensive test coverage**
   - 46 tests including 24 adversarial cases
   - Handles real-world edge cases gracefully

**Speaker Notes:**
These four differentiators set us apart. We're not just accurate — we're auditable. We're not just fast — we're offline-capable. We're not just ranking — we're explaining. And we're not just tested — we're adversarially tested.

---

## Slide 10: Demo

### Live Walkthrough

**Step 1: Run the pipeline**
```bash
python rank.py
```

**Step 2: Inspect top 5 candidates**
```bash
head -n 5 top_100.jsonl
```

**Output format per candidate:**
```json
{
  "candidate_id": "c_04217",
  "rank": 1,
  "score": 0.847,
  "reason": "Strong ML background with 5+ years NLP experience...",
  "evidence": {
    "skills_score": 0.9,
    "trajectory_score": 0.8,
    "experience_score": 0.85
  },
  "semantic_similarity": 0.72,
  "anomaly_flags": []
}
```

**Step 3: Edge case detection**
```bash
python rank.py --edge-cases
```

**Speaker Notes:**
The demo is simple because the system is simple to use. One command produces ranked output. Each candidate has a full audit trail: scores, reasoning, evidence breakdown, and anomaly flags. Judges can inspect any candidate and understand exactly why it was ranked where it was.

---

## Summary

| Aspect | Achievement |
|--------|-------------|
| Scale | 100K → top 100 in ~55s |
| Accuracy | 98% moderate+ fit rate |
| Explainability | 100% reasoning grounding |
| Robustness | 46 tests (24 adversarial) |
| Determinism | 10/10 identical runs |
| Independence | Fully offline, no APIs |

**Redrob Ranker: Evidence first. Every decision explained.**
