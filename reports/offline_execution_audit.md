# Offline Execution Audit

## Repository search
- API/network client imports in ranking path: none found.
- `sandbox_app.py` imports `http.server`/`urllib.parse` only for local demo serving, not ranking-time remote calls.
- `sentence-transformers` appears as an optional local import in `src/semantic.py`; it is only used when an existing local model directory is present and does not trigger downloads. The default ranking path remains standard-library-only.
- Metadata template mentions Hugging Face as a placeholder sandbox URL only.

## Execution test
- Ranking was executed from local files only with `python rank.py --candidates .\candidates.jsonl --out ...`.
- No remote model download, hosted inference call, GPU/CUDA initialization, or telemetry was observed in source inspection or execution. The measured run used `deterministic-domain-embedding` because `sentence-transformers` is not installed in this environment.
- Full network blocking was not enforced at OS firewall level in this environment; source and runtime path require no network.

## Result
PASS for offline/CPU-only ranking behavior; NOT VERIFIED for firewall-level network block.
