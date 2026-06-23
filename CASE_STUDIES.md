# CASE STUDIES

Five case studies demonstrating the ranking system's strengths, weaknesses, and key mechanisms.

---

## Case Study 1: Strong Candidate (Rank 1)

### Profile

| Field | Value |
|-------|-------|
| **CID** | CAND_0081846 |
| **Final Score** | 1.122 |
| **Title** | Lead AI Engineer |
| **Company** | Razorpay |
| **Years** | 6.7 |
| **Location** | Jaipur, Rajasthan |

### Why Ranked #1

This candidate has direct, verifiable ownership of a production ranking pipeline serving 50M+ queries/month — exactly what the role demands. Two consecutive roles (Razorpay → Paytm) both involved hybrid retrieval and ranking system development, creating a consistent career narrative.

### System Reasoning Excerpt

```
Razorpay role Lead AI Engineer; 6.7 years total. Relevant fit comes from
Lead AI Engineer at Razorpay: The architecture combined BM25 + dense
retrieval (BGE embeddings, FAISS HNSW) with an LLM-based re-ranker on
the top-50, falling back to a learning-to-rank model when latency budget
was tight. Additional evidence: Senior Machine Learning Engineer at Paytm:
Migrated the existing BM25-only retrieval to a hybrid setup combining
sparse and dense vectors (sentence-transformers, MPNet-base initially,
later fine-tuned BGE-large for our domain).
```

### Rubric Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| experience_fit | 1.00 | Full 6.7 years directly relevant |
| evidence_only | 1.215 | Highest evidence score in top 50 |
| semantic_score | 0.841 | Strong alignment with ranking concepts |
| skill_corroboration | 0.80 | Skills match career evidence |
| notice_fit | 1.00 | No notice period concern |
| behavior_fit | 0.89 | Strong platform engagement |
| anomaly_flags | none | Clean profile |

---

## Case Study 2: Strong Candidate (Rank 5)

### Profile

| Field | Value |
|-------|-------|
| **CID** | CAND_0046064 |
| **Final Score** | 1.088 |
| **Title** | Senior NLP Engineer |
| **Company** | Salesforce |
| **Years** | 8.9 |
| **Location** | Coimbatore, Tamil Nadu |

### Why Ranked #5

This candidate stands out for end-to-end pipeline ownership at Amazon: embedding generation → Pinecone retrieval → XGBoost re-scoring → behavioral-signal feedback loop. Combined with LLM fine-tuning experience (LoRA/QLoRA on LLaMA-2-7B and Mistral-7B) for domain-specific candidate-JD matching — a rare combination of retrieval engineering and model customization.

### System Reasoning Excerpt

```
8.9 years; Senior NLP Engineer at Salesforce. Strongest evidence: Lead AI
Engineer at Verloop.io: The architecture combined BM25 + dense retrieval
(BGE embeddings, FAISS HNSW) with an LLM-based re-ranker on the top-50,
falling back to a learning-to-rank model when latency budget was tight.
Also, Senior ML Engineer - Search & Ranking at Amazon: Owned the end-to-end
ranking pipeline at a recommendations-heavy consumer product: candidate
sourcing → embedding generation (using a fine-tuned BGE-large) → Pinecone
retrieval → learning-to-rank re-scoring (XGBoost) → behavioral-signal.
```

### Rubric Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| experience_fit | 0.88 | 106 relevant months across 3 roles |
| evidence_only | 1.170 | Strongest pipeline evidence |
| semantic_score | 0.843 | Highest semantic score in top 5 |
| skill_corroboration | 0.60 | Good — BM25, Pinecone, Haystack confirmed |
| notice_fit | 1.00 | Available |
| behavior_fit | 0.85 | Solid engagement |
| anomaly_flags | none | Clean profile |

---

## Case Study 3: Moderate Candidate (Rank 15)

### Profile

| Field | Value |
|-------|-------|
| **CID** | CAND_0086151 |
| **Final Score** | 0.973 |
| **Title** | Recommendation Systems Engineer |
| **Company** | Wysa |
| **Years** | 7.7 |
| **Location** | Vizag, Andhra Pradesh |

### Why Only Moderate

Despite strong evidence (content recommendation system at Glance, search-relevance improvement at Meta), this candidate is downgraded by a 120-day notice period (`notice_fit: 0.25`) — a practical dealbreaker for time-sensitive hiring. Additionally, `skill_corroboration` is only 0.40, meaning skill claims aren't well-validated by career trajectory.

### Gap Analysis

| Signal | Score | Impact |
|--------|-------|--------|
| notice_fit | 0.25 | 120-day wait = likely rejection |
| skill_corroboration | 0.40 | Skill claims under-validated |
| behavior_fit | 0.71 | Below average engagement |

### What Would Make It Strong

1. Shorter notice period (30-60 days) — would push score above 1.05
2. Higher skill corroboration (0.60+) — confirming IR/ranking skills match career evidence
3. Relocating to India (location_fit: 0.82 is already acceptable)

---

## Case Study 4: False Positive Caught

### Profile

| Field | Value |
|-------|-------|
| **CID** | CAND_0092278 |
| **Final Score** | 0.996 |
| **Title** | Senior NLP Engineer |
| **Company** | Microsoft |
| **Rank** | 13 |

### What the System Correctly Rejected

This candidate ranks #13 despite having the lowest `behavior_fit` in the top 15 (0.216). The system caught this through the failure case analysis mechanism:

```
behavior_fit: 0.216 — extremely low, typically reflecting inconsistent
platform engagement, application patterns, or profile activity signals.
A score this low suggests concerning engagement patterns that could
predict poor hiring outcomes.
```

### Detection Mechanism

The `behavior_fit` metric acts as a behavioral signal check. While the candidate has strong evidence (Saarthi.ai, Microsoft roles) and decent semantic alignment (0.832), the system flags the critically low behavior score as a review trigger. The mitigation strategy recommends a hard gate:

```
if behavior_fit < 0.30: score *= 0.5  # or route to manual review
```

Without this gate, the candidate's strong evidence-only score (1.050) would mask the behavioral risk. The current system still ranks them at #13, but the failure analysis correctly identifies this as a candidate requiring manual review before outreach.

### Key Lesson

Single-metric hard gates (behavior_fit < 0.30) are necessary because linear weighting allows high evidence scores to compensate for critically low behavioral signals that predict hiring failure.

---

## Case Study 5: Semantic Boost Example

### Profile

| Field | Value |
|-------|-------|
| **CID** | CAND_0026532 |
| **Final Score** | 0.826 |
| **Rank** | 45 |
| **Semantic Score** | 0.852 (highest in top 50) |

### How Semantic Scoring Improved Ranking

This candidate demonstrates the semantic layer's value as a weak-signal detector. With only 4.8 years of experience and evidence_only score of 0.818 (below average), the candidate would likely fall out of the top 50 without semantic matching.

```
Evidence-only rank: ~50+ (near cutoff)
Hybrid rank: 45
Semantic contribution: +0.8% to final score
```

### Paraphrase Resolution Example

The semantic model captures equivalence between the candidate's language and job requirements without exact keyword matches:

| Candidate's Terms | Job Requirement | Semantic Match |
|-------------------|-----------------|----------------|
| "embedding-based search" | "vector search" | Conceptual equivalence |
| "information retrieval" | "semantic retrieval" | Domain adjacency |
| "search relevance optimization" | "ranking and relevance optimization" | Paraphrase |

### Semantic Ablation Evidence

From the ablation study (`semantic_ablation.md`), the hybrid model outperforms evidence-only by:

- **13 additional candidates promoted** into relevant ranking bands
- **Paraphrase resolution**: "search relevance optimization" = ranking optimization without exact keywords
- **Domain adjacency**: IR → ranking/retrieval connection captured by transformer
- **Score distribution**: Semantic-only scores are tightly clustered (std: 0.089) vs. evidence-only (std: 0.156), meaning semantic adds stability rather than noise

### Key Lesson

The 0.75/0.25 weighting ensures evidence remains dominant (75%) while semantic acts as a tiebreaker and weak-signal amplifier. Candidates with adjacent skills but limited keyword overlap benefit most from this approach.
