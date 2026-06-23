# Competitive Analysis: redrob-ranker

## 1. Pure Keyword Matching (BM25/TF-IDF)

**How it works:** Tokenizes text and ranks by term frequency inverse document frequency. No semantic understanding—relies on exact or fuzzy string matches.

**Strengths:**
- Fast and lightweight
- Interpretable scoring
- No external dependencies

**Weaknesses:**
- Misses paraphrases (e.g., "search relevance" ≠ "ranking optimization")
- No semantic understanding of context
- High false positive rate from keyword overlap

**Why our hybrid is better:** Our semantic branch (25% weight) captures paraphrases like "search relevance" ≈ "ranking optimization" that BM25 misses entirely. The 75% evidence backbone maintains explainability while closing the semantic gap.

---

## 2. Pure Semantic Search (Embedding-Only)

**How it works:** Encodes all text into dense vectors using a transformer model, then ranks by cosine similarity.

**Strengths:**
- Captures paraphrases and domain adjacency
- Handles synonyms naturally

**Weaknesses:**
- No evidence grounding—can't explain *why* a candidate was ranked highly
- Non-deterministic (different runs may produce slightly different results)
- Susceptible to embedding drift

**Why our hybrid is better:** 75% evidence-based scoring ensures every decision is explainable and grounded in verifiable facts. Semantic is a complement, not a replacement.

---

## 3. Pure Embedding Ranking (Learned Model)

**How it works:** Fine-tunes a transformer on labeled ranking data to learn complex patterns.

**Strengths:**
- Can learn subtle ranking patterns
- High accuracy with sufficient training data

**Weaknesses:**
- Requires labeled training data (expensive, often unavailable)
- Black-box—can't explain decisions
- Non-deterministic outputs
- Requires GPU for inference

**Why our hybrid is better:** Zero training data needed. Fully explainable. Deterministic output. Runs on CPU in ~55s for 100K candidates.

---

## 4. LLM-Only Ranking (GPT/Claude)

**How it works:** Sends candidate profiles to a large language model with a ranking prompt. Model reasons and produces a ranked list.

**Strengths:**
- Natural language understanding
- Can reason about complex qualifications
- Flexible prompt engineering

**Weaknesses:**
- Non-deterministic (different outputs per call)
- Expensive ($0.10–$1.00+ per 100K candidates)
- Slow (seconds per candidate, minutes/hours for 100K)
- Requires internet connectivity
- Output not guaranteed consistent

**Why our hybrid is better:** Deterministic. Offline. 100% reproducible. Zero API costs. No data privacy concerns.

---

## Comparison Table

| Approach          | Explainability | Deterministic | Offline | Evidence-Based | Cost    | Speed   |
| ----------------- | -------------- | ------------- | ------- | -------------- | ------- | ------- |
| Pure Keyword      | High           | Yes           | Yes     | Partial        | Low     | Fast    |
| Pure Semantic     | Low            | No            | Yes     | No             | Medium  | Medium  |
| Pure Embedding    | Low            | Depends       | Depends | No             | High    | Medium  |
| LLM-Only          | Medium         | No            | No      | No             | V. High | Slow    |
| **Our Hybrid**    | **High**       | **Yes**       | **Yes** | **Yes (75%)**  | **Low** | **Fast**|

---

## Key Differentiator

The **75/25 evidence/semantic split** is the core innovation of redrob-ranker. It ensures:

1. **Every ranking decision is explainable** — 75% of the score comes from evidence-grounded signals (skills, career trajectory, experience, behavior)
2. **Semantic captures paraphrases without overriding evidence** — the 25% semantic branch uses local all-MiniLM-L6-v2 with domain keywords to bridge lexical gaps
3. **Deterministic output** — compliant with audit and fairness requirements
4. **Zero external dependencies** — fully offline, no API costs, no data leaves the machine
5. **Testable** — 46 tests covering anomaly detection, grounded reasoning, and scoring consistency

This hybrid approach gives you the best of both worlds: the explainability of rule-based systems with the flexibility of semantic search, at a fraction of the cost and complexity of learned models or LLM-based solutions.
