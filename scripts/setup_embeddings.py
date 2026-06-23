#!/usr/bin/env python3
from __future__ import annotations

"""
Setup script for the local all-MiniLM-L6-v2 embedding model.

Usage:
    python scripts/setup_embeddings.py

This downloads the sentence-transformers/all-MiniLM-L6-v2 model to
models/all-MiniLM-L6-v2/ for offline, deterministic semantic ranking.

Model details:
    - Name: sentence-transformers/all-MiniLM-L6-v2
    - Dimension: 384
    - Size: ~87 MB
    - Device: CPU
    - License: Apache-2.0
"""

import shutil
import sys
from pathlib import Path


MODEL_DIR_NAME = "all-MiniLM-L6-v2"
TARGET_DIR = Path(__file__).resolve().parents[1] / "models" / MODEL_DIR_NAME


def main() -> None:
    print("Setting up local embedding model: sentence-transformers/all-MiniLM-L6-v2")
    print(f"Target directory: {TARGET_DIR}")

    if TARGET_DIR.exists() and (TARGET_DIR / "model.safetensors").exists():
        print("Model already present. Skipping download.")
        print(f"  Location: {TARGET_DIR}")
        return

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers is not installed.")
        print("Install it with: pip install sentence-transformers")
        sys.exit(1)

    print("Downloading model (this may take a few minutes on first run)...")
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    except Exception as exc:
        print(f"ERROR: Failed to download model: {exc}")
        sys.exit(1)

    print("Download complete. Verifying model...")
    test_embedding = model.encode(["test"], normalize_embeddings=True)
    assert test_embedding.shape == (1, 384), f"Unexpected embedding shape: {test_embedding.shape}"
    print(f"Model verified. Embedding dimension: {test_embedding.shape[1]}")

    print(f"Copying model files to {TARGET_DIR}...")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    import sentence_transformers
    st_path = Path(sentence_transformers.__file__).parent
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--sentence-transformers--all-MiniLM-L6-v2"

    snapshot_dirs = list((cache_dir / "snapshots").glob("*")) if cache_dir.exists() else []
    if not snapshot_dirs:
        print("WARNING: Could not find cached model snapshot.")
        print("Model is available via HuggingFace cache but not copied locally.")
        return

    snapshot = snapshot_dirs[0]
    for item in snapshot.rglob("*"):
        if item.is_file():
            rel = item.relative_to(snapshot)
            dest = TARGET_DIR / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)

    print(f"Model files copied to: {TARGET_DIR}")
    total_size = sum(f.stat().st_size for f in TARGET_DIR.rglob("*") if f.is_file())
    print(f"Total model size: {total_size / (1024 * 1024):.1f} MB")
    print("Setup complete. The embedding model is now available for offline use.")


if __name__ == "__main__":
    main()
