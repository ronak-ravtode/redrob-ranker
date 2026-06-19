# Final Determinism Report

## Commands used
- `python rank.py --candidates .\candidates.jsonl --out .\reports\determinism_run_1.csv`
- `python rank.py --candidates .\candidates.jsonl --out .\reports\determinism_run_2.csv`

## Environment
- OS: Windows-11-10.0.26200-SP0
- Python: 3.14.3
- CPU count: 12

## Outputs
- Output 1: `C:\Users\ronak\Downloads\redrob_agent_starter\redrob_agent_starter\reports\determinism_run_1.csv`
- Output 2: `C:\Users\ronak\Downloads\redrob_agent_starter\redrob_agent_starter\reports\determinism_run_2.csv`
- SHA-256 output 1: `115952cd4b5e1d2396707271d8db8c565abd79027781b71baac71bf59caa2277`
- SHA-256 output 2: `115952cd4b5e1d2396707271d8db8c565abd79027781b71baac71bf59caa2277`
- Match: PASS

## Nondeterminism discovered
None in the final run. Ordering is score descending with deterministic candidate-ID tie-breaking.

## Fixes applied
No determinism fix was needed in this final pass.
