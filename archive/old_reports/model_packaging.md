# Model Packaging

## Model: sentence-transformers/all-MiniLM-L6-v2

| Property | Value |
|---|---|
| Model name | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding dimension | 384 |
| Max sequence length | 256 tokens |
| Model size | ~87 MB |
| Device | CPU |
| License | Apache-2.0 |
| Source | Hugging Face Hub |

## Bundled Location

```
models/all-MiniLM-L6-v2/
  ├── 1_Pooling/config.json
  ├── config.json
  ├── config_sentence_transformers.json
  ├── model.safetensors          (86.7 MB)
  ├── modules.json
  ├── README.md
  ├── sentence_bert_config.json
  ├── special_tokens_map.json
  ├── tokenizer.json             (0.4 MB)
  ├── tokenizer_config.json
  └── vocab.txt                  (0.2 MB)
```

## Installation Process

### Automatic (Recommended)

The model is bundled in the repository. No additional setup required:

```bash
git clone <repo-url>
cd redrob_agent_starter
pip install -r requirements.txt
python rank.py --candidates candidates.jsonl --out submission.csv
```

### Manual Setup (If Model Missing)

If the `models/all-MiniLM-L6-v2/` directory is not present:

```bash
pip install sentence-transformers
python scripts/setup_embeddings.py
```

### Docker

```bash
docker build -t redrob-ranker .
docker run -p 7860:7860 redrob-ranker
```

The Dockerfile copies the model directory into the container.

## Reproducibility Steps

1. Clone repository (includes model weights)
2. Install dependencies: `pip install -r requirements.txt`
3. Run ranking: `python rank.py --candidates candidates.jsonl --out submission.csv`
4. Output is deterministic given the same input

### Determinism Guarantees

- Model weights are fixed (bundled in repo)
- Inference uses `device="cpu"` (no GPU variability)
- Embeddings are normalized before similarity computation
- Random seeds are set before model initialization
- No data augmentation or stochastic layers

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `REDROB_EMBEDDING_MODEL_DIR` | `models/all-MiniLM-L6-v2` | Override model location |
| `REDROB_EMBEDDING_SEED` | `42` | Random seed for determinism |

## Model Selection Rationale

| Model | Size | Dim | Quality | Selected |
|---|---|---|---|---|
| all-MiniLM-L6-v2 | 87 MB | 384 | Good | **Yes** |
| all-mpnet-base-v2 | 420 MB | 768 | Better | No (too large) |
| paraphrase-MiniLM-L6-v2 | 87 MB | 384 | Good | No (overlaps) |
| all-MiniLM-L12-v2 | 130 MB | 384 | Better | No (larger) |

`all-MiniLM-L6-v2` was chosen for the best size-to-quality ratio. At 87 MB it bundles cleanly in git without bloating the repository, while providing strong semantic similarity for recruitment-domain text.
