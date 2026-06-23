# Initial dataset findings

These figures were obtained by streaming the supplied full candidate pool:

- Candidate records: 100,000
- Approximate uncompressed size: 487 MB
- India-based: 75,113
- Open-to-work: 35,339
- Willing to relocate: 28,804
- Experience in stated 5–9 year band: 34,375
- Obviously AI/ML/search-related current titles: about 1,047
- High-confidence internal-consistency anomaly union: 69 candidates
  - total-experience mismatch: 48
  - individual job-duration mismatch: 35
  - 3+ expert skills with zero duration: 21

Some fields contain frequent synthetic noise and should not be treated as honeypots by themselves:
- salary minimum greater than maximum appears very frequently
- last-active before signup also appears frequently

The most useful discriminator is career-description evidence. The skill list is deliberately noisy.
