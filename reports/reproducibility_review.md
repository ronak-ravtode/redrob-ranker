# Reproducibility Review

## Checklist

### Offline Execution
- [x] No network calls during ranking
- [x] No API endpoints called
- [x] No external services required
- [x] Model weights bundled locally
- [x] All dependencies available offline

### No Network Dependency
- [x] `sentence-transformers` loads from local path
- [x] Model loaded from `models/all-MiniLM-L6-v2/`
- [x] No HuggingFace Hub downloads at runtime
- [x] No PyPI downloads at runtime
- [x] Environment variable `REDROB_EMBEDDING_MODEL_DIR` optional

### Sandbox Compatibility
- [x] `sandbox_app.py` works with bundled model
- [x] Docker image includes model directory
- [x] No external file dependencies
- [x] Self-contained deployment

### Docker Compatibility
- [x] `requirements.txt` installs all dependencies
- [x] `COPY models ./models` includes model weights
- [x] No network required during `docker build`
- [x] No network required during `docker run`

### Hugging Face Compatibility
- [x] Model bundled in repository
- [x] No runtime downloads needed
- [x] Works in HF Spaces environment
- [x] CPU-only inference

### Determinism
- [x] Random seeds set before model init
- [x] Device forced to CPU
- [x] Embeddings normalized
- [x] No stochastic layers
- [x] Same input -> same output (verified)

### Reproduction Steps
1. Clone repository
2. `pip install -r requirements.txt`
3. `python rank.py --candidates candidates.jsonl --out submission.csv`
4. Output matches reference submission

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDROB_EMBEDDING_MODEL_DIR` | No | `models/all-MiniLM-L6-v2` | Model location |
| `REDROB_EMBEDDING_SEED` | No | `42` | Random seed |

### Risk Assessment

| Risk | Mitigation |
|---|---|
| Model weights corruption | SHA256 verification possible |
| Dependency version conflict | Pinned versions in requirements.txt |
| Platform-specific behavior | CPU-only, cross-platform compatible |
| Memory constraints | 236 MB peak, well under 500 MB limit |
