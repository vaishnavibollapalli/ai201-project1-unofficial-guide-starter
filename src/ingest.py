"""
Milestone 3 — Document Ingestion and Chunking
GSU CS Professor Reviews (Rate My Professors)

Loads .txt files from data/raw/, cleans them, splits into chunks
using the strategy from planning.md:
  - chunk size : 500 characters
  - overlap    : 100 characters
Saves all chunks to data/chunks.json for use in Milestone 4.
"""

import os
import re
import json

# Configuration
RAW_DIR    = os.path.join("data", "raw")        # folder with prof_*.txt files
OUTPUT     = os.path.join("data", "chunks.json")
CHUNK_SIZE = 500   # characters  (from planning.md)
OVERLAP    = 100   # characters  (from planning.md)


# Step 1: Load
def load_documents(raw_dir: str) -> list[dict]:
    """
    Read every .txt file in raw_dir.
    Returns a list of dicts with keys: source (filename), text (raw string).
    """
    documents = []
    if not os.path.isdir(raw_dir):
        raise FileNotFoundError(
            f"Raw data directory not found: '{raw_dir}'. "
            "Make sure you're running this script from the repo root."
        )

    for filename in sorted(os.listdir(raw_dir)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(raw_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        documents.append({"source": filename, "text": text})
        print(f"  Loaded  {filename}  ({len(text):,} chars)")

    print(f"\n→ {len(documents)} documents loaded.\n")
    return documents


# Step 2: Clean
def clean_text(text: str) -> str:
    """
    Remove noise that doesn't belong in a student review corpus:
      - HTML tags and entities
      - URLs
      - Repeated whitespace / blank lines
      - Common Rate My Professors boilerplate phrases
    Keep: review text, professor names, course numbers, ratings context.
    """
    # Remove any stray HTML tags (just in case text was copy-pasted from a browser)
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common HTML entities
    html_entities = {
        "&amp;": "&", "&nbsp;": " ", "&lt;": "<",
        "&gt;": ">", "&quot;": '"', "&#39;": "'",
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)

    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remove Rate My Professors UI boilerplate (customize if your .txt files differ)
    boilerplate = [
        r"Rate My Professors",
        r"Submit a Correction",
        r"Flag this professor",
        r"Add a Rating",
        r"Is this professor.*?\?",
        r"Overall Quality",
        r"Would Take Again",
        r"Level of Difficulty",
    ]
    for pattern in boilerplate:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Collapse multiple spaces and blank lines into single whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# Step 3: Chunk 
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Split text into overlapping fixed-size character chunks.

    Why fixed-size characters (from planning.md):
      - Reviews are short and loosely structured, so sentence/paragraph
        splitting can produce very uneven chunks.
      - 500 chars is large enough to hold one complete thought (a review
        sentence + context) but small enough to stay on-topic.
      - 100-char overlap ensures a detail that falls near a boundary
        (e.g. "attendance is required") appears in at least one full chunk.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) > 0:          # skip empty strings
            chunks.append(chunk)
        start += chunk_size - overlap   # slide forward by (size - overlap)
    return chunks


# Step 4: Build chunk records 
def process_documents(documents: list[dict]) -> list[dict]:
    """
    For each document: clean → chunk → attach metadata.
    Returns a flat list of chunk dicts ready for embedding.
    """
    all_chunks = []
    for doc in documents:
        source   = doc["source"]
        raw_text = doc["text"]

        cleaned  = clean_text(raw_text)
        chunks   = chunk_text(cleaned)

        for idx, chunk in enumerate(chunks):
            all_chunks.append({
                "id":     f"{source}__chunk_{idx}",   # unique ID for ChromaDB
                "source": source,                      # filename → source attribution
                "chunk_index": idx,
                "text":   chunk,
            })

        print(f"  {source:35s}  cleaned: {len(cleaned):>5,} chars  →  {len(chunks):>3} chunks")

    return all_chunks


# Step 5: Inspect + Validate
def inspect_chunks(chunks: list[dict], sample_n: int = 5) -> None:
    """
    Print sample_n evenly-spaced chunks so you can read them and verify
    they look like complete, self-contained review fragments.
    """
    import random
    random.seed(42)
    sample = random.sample(chunks, min(sample_n, len(chunks)))

    print("\n" + "═" * 70)
    print(f"  SAMPLE CHUNKS  (showing {len(sample)} of {len(chunks)} total)")
    print("═" * 70)
    for i, c in enumerate(sample, 1):
        print(f"\n[{i}] source={c['source']}  chunk_index={c['chunk_index']}")
        print(f"    length={len(c['text'])} chars")
        print(f"    text preview: {c['text'][:300]!r}")
    print("\n" + "═" * 70)


def validate_chunks(chunks: list[dict]) -> None:
    """
    Run basic sanity checks and surface common problems.
    Prints a warning for each issue found.
    """
    issues = 0

    empty = [c for c in chunks if len(c["text"].strip()) == 0]
    if empty:
        print(f"  ⚠  {len(empty)} empty chunk(s) found — check cleaning/splitting logic.")
        issues += 1

    html_leftovers = [c for c in chunks if re.search(r"<[a-zA-Z/]", c["text"])]
    if html_leftovers:
        print(f"  ⚠  {len(html_leftovers)} chunk(s) still contain HTML tags — tighten clean_text().")
        issues += 1

    very_short = [c for c in chunks if 0 < len(c["text"]) < 50]
    if very_short:
        print(f"  ⚠  {len(very_short)} chunk(s) are shorter than 50 chars — may be too fragmented.")
        issues += 1

    if len(chunks) < 50:
        print(f"  ⚠  Only {len(chunks)} chunks total. Chunks may be too large or documents too short.")
        issues += 1

    if len(chunks) > 2000:
        print(f"  ⚠  {len(chunks)} chunks total. Chunks may be too small — semantic signal may be weak.")
        issues += 1

    if issues == 0:
        print("  ✓  All validation checks passed.")


# Step 6: Save 
def save_chunks(chunks: list[dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"\n✓  Saved {len(chunks)} chunks → {output_path}")


# Main
def main():
    print("=" * 70)
    print("  Milestone 3 — Ingestion & Chunking")
    print(f"  chunk_size={CHUNK_SIZE}  overlap={OVERLAP}")
    print("=" * 70 + "\n")

    # 1. Load
    print("[ Step 1 ] Loading documents …")
    documents = load_documents(RAW_DIR)

    # 2. Process (clean + chunk + metadata)
    print("[ Step 2 ] Cleaning and chunking …\n")
    chunks = process_documents(documents)

    # 3. Inspect 5 random chunks so you can read them
    inspect_chunks(chunks, sample_n=5)

    # 4. Validate
    print("\n[ Step 3 ] Validating chunks …")
    validate_chunks(chunks)

    # 5. Save
    print("\n[ Step 4 ] Saving …")
    save_chunks(chunks, OUTPUT)

    print(f"\n  Total chunks : {len(chunks)}")
    print(f"  Documents    : {len(documents)}")
    print(f"  Avg per doc  : {len(chunks) / max(len(documents), 1):.1f} chunks")
    print("\nDone. ✓  Move on to Milestone 4 once chunk samples look clean.\n")


if __name__ == "__main__":
    main()