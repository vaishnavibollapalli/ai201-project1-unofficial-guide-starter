"""
Milestone 4 — Embedding + Vector Store
Loads chunks from data/chunks.json, embeds them with all-MiniLM-L6-v2,
and stores them in ChromaDB with source metadata.
"""

import os
import json
from sentence_transformers import SentenceTransformer
import chromadb

# Configuration 
CHUNKS_FILE  = os.path.join("data", "chunks.json")
CHROMA_DIR   = os.path.join("data", "chroma_db")
COLLECTION   = "gsu_professor_reviews"
EMBED_MODEL  = "all-MiniLM-L6-v2"
BATCH_SIZE   = 64   # embed this many chunks at a time


# Load chunks 
def load_chunks(path: str) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"'{path}' not found. Run src/ingest.py first."
        )
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks)} chunks from {path}")
    return chunks


# Embed & store 
def embed_and_store(chunks: list[dict]) -> chromadb.Collection:
    print(f"\n  Loading embedding model: {EMBED_MODEL} …")
    model = SentenceTransformer(EMBED_MODEL)

    print(f"  Connecting to ChromaDB at {CHROMA_DIR} …")
    client     = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection so re-runs start fresh
    try:
        client.delete_collection(COLLECTION)
        print(f"  Deleted existing collection '{COLLECTION}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )

    texts     = [c["text"]         for c in chunks]
    ids       = [c["id"]           for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]

    # Embed in batches
    total = len(chunks)
    print(f"\n  Embedding {total} chunks in batches of {BATCH_SIZE} …")
    for start in range(0, total, BATCH_SIZE):
        end        = min(start + BATCH_SIZE, total)
        batch_text = texts[start:end]
        embeddings = model.encode(batch_text, show_progress_bar=False).tolist()

        collection.add(
            ids        = ids[start:end],
            documents  = batch_text,
            embeddings = embeddings,
            metadatas  = metadatas[start:end],
        )
        print(f"    Stored chunks {start+1}–{end} / {total}")

    print(f"\n  ✓  Collection '{COLLECTION}' now has {collection.count()} entries.")
    return collection


# Test retrieval 
def test_retrieval(collection: chromadb.Collection) -> None:
    model = SentenceTransformer(EMBED_MODEL)

    test_queries = [
        "Which professor explains concepts clearly?",
        "Which professor requires attendance?",
        "Which professor has a heavy workload?",
    ]

    print("\n" + "═" * 70)
    print("  RETRIEVAL TEST  (top-3 results per query)")
    print("═" * 70)

    for query in test_queries:
        print(f"\nQuery: {query!r}")
        query_embedding = model.encode([query]).tolist()
        results = collection.query(
            query_embeddings = query_embedding,
            n_results        = 3,
            include          = ["documents", "metadatas", "distances"],
        )
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ), 1):
            print(f"  [{i}] source={meta['source']}  distance={dist:.4f}")
            print(f"      {doc[:200]!r}")

    print("\n" + "═" * 70)
    print("  Check: are the results relevant? Distance < 0.5 is a good sign.")
    print("  If results look off-topic, go back and review your chunks.")
    print("═" * 70 + "\n")


# Main
def main():
    print("=" * 70)
    print("  Milestone 4 — Embedding + Vector Store")
    print("=" * 70 + "\n")

    chunks     = load_chunks(CHUNKS_FILE)
    collection = embed_and_store(chunks)
    test_retrieval(collection)

    print("Done. ✓  Move on to Milestone 5 once retrieval results look relevant.\n")


if __name__ == "__main__":
    main()