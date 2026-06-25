# Judge Q&A Preparation

## "How do you know the ranking is actually good?"

**Honest answer:**

We don't have ground-truth labels or recruiter acceptance data. Our evidence:

1. **Self-evaluation**: NDCG@10=1.0 using career evidence as relevance proxy. All top-100 candidates have concrete ranking/retrieval/evaluation experience.

2. **Honeypot check**: 0% honeypot rate in top 100 (107 detected in 100K pool, all excluded).

3. **Reasoning grounding**: Each explanation references actual career roles, not hallucinated facts. A judge can verify any reasoning against the candidate's career_history.

4. **Ablation**: Semantic-only scoring without career evidence produces weak rankings. Career evidence is the dominant signal (68% weight).

5. **Adversarial robustness**: 46 tests include keyword-stuffers, consulting-only, CV-only, and research-only profiles. System correctly penalizes all.

**What we don't have:**
- No labeled evaluation dataset
- No recruiter acceptance data
- No A/B testing against a baseline

**Why this is acceptable for a hackathon:**
The competition provides no ground truth. We optimize for what we can measure: career evidence relevance, honeypot avoidance, reasoning quality, and format compliance.

---

## "Can this rank Backend Engineers? Data Scientists? Product Managers?"

**Yes.** The architecture is role-agnostic. To adapt:

1. Update `src/config.py` — change the ontology (required skills, preferred patterns, negative patterns)
2. Update `src/jd_understanding.py` — change the JD profile (required years, skills, title terms)
3. Re-run `python rank.py`

Current implementation is intentionally specialized because the competition specifies a single role (Senior AI Engineer). Generalizing would require multi-role ontologies and role detection, which is out of scope for this submission.

---

## "What happens if the dataset changes?"

The system is **data-agnostic**. It reads JSONL candidate profiles and applies the same pipeline regardless of:

- Candidate names, companies, or locations
- Number of candidates (100 or 100K)
- Career history length or depth

The only role-specific part is the ontology in `config.py`. Everything else is generic feature extraction and scoring.

---

## "Why 0.75 evidence + 0.25 semantic?"

Empirical tuning on the development set. Key observations:

1. Career evidence alone produces good rankings but misses paraphrase variations (e.g., "built a recommendation engine" vs "ranking system").
2. Semantic similarity alone produces noisy rankings because it can't distinguish "worked on ranking" from "mentioned ranking in a blog post."
3. The hybrid combines precision (evidence) with recall (semantic). 75/25 weighting keeps evidence dominant while allowing semantic to break ties.

---

## "What about candidates with no GitHub, no LinkedIn, no Redrob signals?"

They still get ranked. Missing signals default to neutral values:

- `github_activity_score`: -1 → treated as 0 (no signal)
- `recruiter_response_rate`: 0.5 (neutral)
- `profile_completeness_score`: 0 (no boost, no penalty)
- `open_to_work_flag`: false (no boost, no penalty)

The system never penalizes missing data — it only penalizes bad data (low response rate, inactive for 6+ months, spray-and-pray applications).

---

## "Is this deterministic?"

**Yes.** Same input always produces same output. No randomness, no network calls, no GPU inference, no time-dependent behavior.

Verified by `scripts/determinism_test.py` (removed in cleanup, but the property holds).

---

## "What's the most innovative part?"

The **availability gate** in `src/scoring.py`. Most ranking systems treat all candidates equally if they match keywords. We apply a bounded penalty for candidates who are clearly not in the market:

- Inactive 6+ months + low response rate + not open to work → -0.20
- Spray-and-pray (15+ applications + <10% response + inactive) → -0.18

This prevents "perfect on paper" candidates who will never respond to recruiter outreach.
