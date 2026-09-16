"""Build actual E5-small-v2 embeddings for the 580 corpus chunks and construct real candidate pools.

Integrates real E5 forward pass, exact cosine indexing, BM25, and RRF fusion
to produce real candidate pools for the 56 core incidents.
"""
import hashlib
import json
from pathlib import Path
import sys

# Ensure local source tree and user-site are accessible
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import site
for p in site.getsitepackages():
    if p not in sys.path:
        sys.path.append(p)

import numpy as np
import yaml

from src.retrieval.dense import E5Encoder, DenseIndex, verify_model_assets
from src.retrieval.bm25 import BM25
from src.retrieval.fusion import rrf


def load_corpus_chunks(corpus_chunks_path: Path):
    """Loads chunks from JSONL file."""
    chunks = []
    with open(corpus_chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def build_and_cache_embeddings(corpus_chunks_path: Path, model_dir: Path, config: dict, cache_path: Path):
    """Encodes all 580 chunks with real E5-small-v2 and saves to disk."""
    print(f"Loading chunks from {corpus_chunks_path}...")
    chunks = load_corpus_chunks(corpus_chunks_path)
    print(f"Loaded {len(chunks)} chunks.")
    
    dense_cfg = config["dense"]
    print("Verifying model assets...")
    verify_model_assets(model_dir, dense_cfg["assets"])
    print("Model assets verified.")
    
    print("Initializing E5Encoder...")
    encoder = E5Encoder(
        model_dir=model_dir,
        expected_assets=dense_cfg["assets"],
        revision=dense_cfg["revision"],
        max_tokens=dense_cfg.get("max_tokens", 512),
        batch_size=32,
        device="cpu",
    )
    
    print(f"Encoding {len(chunks)} chunks...")
    texts = [c.get("content") or f"{c['section_heading']}\n{c['text']}" for c in chunks]
    vectors, audits = encoder.encode(texts, kind="passage")
    print(f"Encoding complete. Matrix shape: {vectors.shape}")
    
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache_path, vectors)
    print(f"Saved normalized embeddings to {cache_path}")
    
    h = hashlib.sha256(cache_path.read_bytes()).hexdigest()
    print(f"Embeddings cache SHA256: {h}")
    return chunks, vectors, encoder


def generate_real_candidate_pools(chunks, embeddings, encoder, queries_path: Path, output_pools_dir: Path, depth=10):
    """Runs BM25, Dense, and RRF to generate real candidate pools."""
    print("Building BM25 and Dense indexes...")
    bm25 = BM25(chunks)
    dense_index = DenseIndex(chunks, embeddings)
    
    print(f"Reading queries from {queries_path}...")
    queries = []
    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
                
    # Filter to R2 variant
    r2_queries = [q for q in queries if q.get("representation_id") == "R2" or q.get("representation") == "R2"]
    print(f"Found {len(r2_queries)} R2 queries.")
    
    candidate_records = []
    for q in r2_queries:
        inc_id = q["incident_id"]
        q_text = q.get("query_text") or q.get("text", "")
        
        bm25_hits = bm25.search(q_text, depth=50)
        q_vectors, _ = encoder.encode([q_text], kind="query")
        dense_hits = dense_index.search(q_vectors[0], depth=50)
        fused = rrf([bm25_hits, dense_hits], depth=depth, constant=60)
        
        for rank, hit in enumerate(fused[:depth], 1):
            chunk_id = hit["chunk_id"]
            doc_id = hit.get("document_id", "")
            candidate_records.append({
                "incident_id": inc_id,
                "rank": rank,
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "score": hit["score"],
            })
            
    output_pools_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_pools_dir / "real-fused-candidates.tsv"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("incident_id\trank\tchunk_id\tdocument_id\tscore\n")
        for rec in candidate_records:
            f.write(f"{rec['incident_id']}\t{rec['rank']}\t{rec['chunk_id']}\t{rec['document_id']}\t{rec['score']}\n")
            
    print(f"Saved {len(candidate_records)} real candidate pairs to {out_file}")
    return candidate_records, out_file


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    with open(base / "configs" / "retrieval.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
        
    chunks_file = base / "data" / "knowledge" / "chunks.jsonl"
    model_dir = base / "vendor" / "e5-small-v2"
    cache_file = base / "cache" / "retrieval" / "e5_embeddings.npy"
    queries_file = base / "queries" / "variants.train-dev.jsonl"
    pools_dir = base / "annotations" / "pools"
    
    chunks, vectors, encoder = build_and_cache_embeddings(chunks_file, model_dir, cfg, cache_file)
    generate_real_candidate_pools(chunks, vectors, encoder, queries_file, pools_dir)

