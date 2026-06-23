# AI-Agent Execution Plan — Redrob Intelligent Candidate Ranking

## Mission

Build a deterministic, explainable ranker that selects and orders the top 100 candidates for the
Senior AI Engineer — Founding Team role from 100,000 JSONL profiles.

The final ranking command must run in at most 5 minutes on CPU, within 16 GB RAM, without network
access or hosted LLM calls. The final CSV must pass the supplied validator and every row must contain
grounded, candidate-specific reasoning.

## Non-negotiable principles

1. Career-history evidence is the primary truth source.
2. Skill lists and summaries are supporting evidence only.
3. Behavioral signals modify technical fit; they never create technical fit.
4. Negative JD requirements must be explicitly modeled.
5. Honeypot/anomaly checks run before final ranking.
6. No candidate-ID allowlists, denylists, hand-edited CSV rows, or hidden manual steps.
7. Development-time AI assistance is allowed; ranking-time API calls are forbidden.
8. All improvements require tests, benchmark results, and real Git commits.

## Observed dataset structure

- 100,000 candidates.
- 75,113 are located in India.
- Only about 1,047 have obviously AI/ML/search-related current titles.
- A much smaller pool—roughly a few hundred—contains substantive ranking, search, retrieval,
  recommendation, evaluation, or production evidence in career history.
- Skill lists are intentionally noisy and cannot be trusted without career corroboration.
- At least 69 profiles show high-confidence impossible patterns using only internal consistency checks:
  duration mismatch, total-experience mismatch, or 3+ expert skills with zero duration.
- The top-heavy metric means top-10 ordering matters more than broad recall.

These observations are development clues, not labels. Agents must verify all claims from the data.

---

# Agent team

## Agent 0 — Orchestrator and integrator

Owns sequencing, contracts, merge quality, and final sign-off. Does not accept vague output.

Deliverables:
- `docs/decision_log.md`
- `docs/scorecard.md`
- integrated main branch
- final release checklist

Rules:
- Give each agent one bounded task and explicit acceptance criteria.
- Do not allow two agents to independently rewrite the same module.
- Reject patches that hardcode candidate IDs.
- Require each agent to show before/after top-30 changes and runtime impact.

## Agent 1 — Dataset auditor

Tasks:
- Stream all 100K records and verify count/schema shape.
- Profile titles, countries, cities, companies, industries, skill frequencies, experience and signals.
- Cluster career descriptions and summaries by exact/normalized text to expose synthetic archetypes.
- Report missing fields, impossible dates, duration mismatches and suspicious distributions.
- Produce a shortlist-audit tool that exports the top 300 with complete evidence.

Deliverables:
- `scripts/profile_dataset.py`
- `scripts/audit_anomalies.py`
- `reports/dataset_profile.md`
- `reports/anomaly_summary.csv`

Acceptance:
- Streaming implementation; no 487 MB dataframe load.
- Completes under 60 seconds locally.
- Separates common synthetic noise from rare honeypot-like anomalies.

## Agent 2 — JD ontology and evidence engineer

Tasks:
- Convert the JD into explicit positive, optional and negative evidence groups.
- Define evidence strength levels:
  - Level 0: skill-list mention only
  - Level 1: summary/headline claim
  - Level 2: career-description usage
  - Level 3: production ownership with scale/metric
  - Level 4: end-to-end ownership plus evaluation/experimentation
- Add plain-language concepts so strong profiles are found even without words such as RAG or Pinecone.
- Keep every phrase/category traceable to the JD.

Required groups:
- ranking/recommendation
- retrieval/search/matching
- vector/hybrid infrastructure
- evaluation: NDCG/MRR/MAP/offline-online/A-B/human judgment
- production and scale
- ownership and mentoring
- Python/code evidence
- optional LLM fine-tuning
- product/startup orientation
- culture signals: writing, speed, product judgment
- negative archetypes from the JD

Deliverables:
- `src/config.py`
- `docs/jd_evidence_matrix.md`
- unit tests for at least 25 phrases and paraphrases

Acceptance:
- Plain-language Tier-5-style descriptions receive strong scores.
- Marketing/HR profiles with AI-heavy skill lists receive weak scores.

## Agent 3 — Honeypot and integrity engineer

Tasks:
- Implement high-confidence anomaly checks only.
- Distinguish common noise from disqualifying impossibilities.
- Checks should include:
  - declared duration vs dates
  - total experience vs career durations
  - multiple expert skills with zero usage
  - impossible employment before known company founding year, using a documented local map
  - impossible chronology or contradictory current-job state
- Use graded penalties, but hard-exclude only high-confidence impossible profiles.

Deliverables:
- `src/anomaly.py`
- `data/company_founding_years.json`
- `docs/honeypot_methodology.md`
- `tests/test_anomaly.py`

Acceptance:
- Top 100 contains zero candidates flagged by high-confidence rules.
- Each rule has a test and a rationale.
- No rule uses candidate IDs.

## Agent 4 — Ranking engineer

Implement a multi-stage ranker:

### Stage A: coarse retrieval
Retain candidates when either:
- current/past title is relevant, or
- career history contains ranking/retrieval/recommendation/matching evidence.

Do not retrieve candidates solely because their skill list contains AI keywords.

### Stage B: evidence features
Calculate:
- career evidence by requirement group
- current-role evidence
- number and months of relevant roles
- production/scale/ownership depth
- product-company vs consulting-only history
- title trajectory and job-tenure stability
- experience fit
- location/relocation/notice fit
- behavioral availability
- skill-to-career corroboration
- negative-archetype and anomaly penalties

### Stage C: score
Suggested initial structure:
- 35% ranking/retrieval career evidence
- 15% vector/hybrid operational evidence
- 15% evaluation and experimentation
- 10% production ownership and scale
- 8% relevant role depth and experience
- 5% Python/engineering evidence
- 5% product/startup fit
- 4% behavior
- 3% location/notice
- explicit penalties outside these weights

These are starting weights. Tune through evidence review, not arbitrary preference.

### Stage D: deterministic ordering
- descending score
- deterministic secondary feature
- candidate ID ascending only for exact remaining ties

Deliverables:
- `src/features.py`
- `src/scoring.py`
- `rank.py`
- `tests/test_scoring.py`
- `reports/top_300_review.csv`

Acceptance:
- Full run under 60 seconds target; hard maximum 5 minutes.
- Top 10 candidates each show at least three strong JD evidence groups.
- No all-equal or clipped score plateau.
- Skill-only keyword stuffers do not enter the top 100.

## Agent 5 — Red-team ranking reviewer

Tasks:
- Review top 200, not just top 10.
- Tag every candidate as `strong`, `borderline`, `reject`, or `honeypot-risk`.
- Record the specific scoring failure for rejects.
- Find:
  - false positives from keyword stuffing
  - false negatives from plain-language evidence
  - research-only candidates
  - CV/speech-only candidates
  - consulting-only candidates
  - stale/unavailable candidates
  - candidates with strong technical fit but weak logistics
- Propose general rules, never candidate-ID patches.

Deliverables:
- `reports/top_200_red_team.csv`
- `reports/red_team_findings.md`
- targeted regression tests

Acceptance:
- Every proposed change explains which general failure class it fixes.
- Orchestrator rejects changes that only improve one named profile.

## Agent 6 — Reasoning and explainability engineer

Tasks:
- Generate 1–2 sentence reasoning from the exact features used to rank.
- Reference at least two specific candidate facts when available:
  years, current title/company, system type, scale, metric, evaluation method, location, notice or activity.
- Mention one honest concern for borderline/lower-ranked profiles.
- Vary sentence structure and evidence selection.
- Never mention a skill, employer, metric or system absent from the profile.

Deliverables:
- `src/reasoning.py`
- `tests/test_reasoning.py`
- `reports/reasoning_audit.csv`

Acceptance:
- 100 non-empty reasons.
- No identical reasons.
- Ten random reasons manually trace back to source profile facts.
- Tone matches rank.

## Agent 7 — Reproduction, QA and submission engineer

Tasks:
- Add exact single-command reproduction.
- Run supplied validator.
- Test CPU-only/no-network behavior.
- Record wall-clock time and peak memory.
- Create Dockerfile or hosted small-sample demo.
- Complete metadata and AI-tool declaration honestly.
- Verify clean-clone execution.

Deliverables:
- `README.md`
- `Dockerfile`
- `submission_metadata.yaml`
- `scripts/benchmark.py`
- CI workflow
- final CSV

Acceptance:
- Exactly 100 rows.
- Ranks 1–100 exactly once.
- Unique IDs.
- Non-increasing scores.
- Tie rule satisfied.
- Supplied validator passes.
- Full command completes under limits.
- Sandbox handles a ≤100-candidate upload end-to-end.

---

# Iteration sequence

## Iteration 1 — Baseline

Run the provided starter and save:
- runtime
- top 100
- top-30 score components
- known false positives/negatives

Commit: `baseline: deterministic career-evidence ranker`

## Iteration 2 — Data and anomaly audit

Do not change weights yet. First understand profile templates, anomalous records and relevant candidate pool.

Commit: `analysis: dataset archetypes and honeypot rules`

## Iteration 3 — JD ontology expansion

Add semantic/plain-language evidence and stronger negative archetypes.

Commit: `feat: JD evidence ontology and corroboration`

## Iteration 4 — Ranking calibration

Review top 200 and adjust general weights. Add component-level score export.

Commit: `feat: calibrated multi-component ranking`

## Iteration 5 — Reasoning quality

Generate grounded, varied explanations and audit random rows.

Commit: `feat: evidence-grounded candidate reasoning`

## Iteration 6 — Reproduction hardening

Benchmark, Dockerize, validate, complete metadata and demo.

Commit: `release: reproducible hackathon submission`

---

# Evaluation without ground-truth labels

There is no public leaderboard, so do not pretend to optimize a measured NDCG. Use a structured proxy rubric.

For each top-100 candidate, score manually/with an auditing agent:
- 0–4: ranking/retrieval system evidence
- 0–4: production ownership
- 0–4: evaluation rigor
- 0–3: vector/hybrid infrastructure
- 0–2: Python/hands-on coding
- 0–2: product-company/startup fit
- 0–2: seniority/mentoring
- 0–2: availability/logistics
- negative flags: keyword stuffing, pure research, consulting-only, CV-only, stale, anomaly

The automated rank and audit rubric should broadly agree. Large disagreement requires investigation.

# Final release gates

Do not submit until all are true:

- [ ] Top 10 manually defended candidate by candidate.
- [ ] Top 50 contains no obvious irrelevant title/career mismatch.
- [ ] Top 100 contains zero high-confidence honeypots.
- [ ] No score plateau from clipping.
- [ ] Ten random reasons pass factual verification.
- [ ] Full runtime and memory logged.
- [ ] Validator passes.
- [ ] Clean Docker/clone reproduction works.
- [ ] Metadata and AI declaration completed.
- [ ] Git history shows genuine iteration.
