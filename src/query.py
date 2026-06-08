"""
query.py — Retrieval + Grounded Generation
Used by app.py (Gradio UI) and can be run standalone for testing.

Retrieval:  ChromaDB + all-MiniLM-L6-v2  (top-k = 5)
Generation: Groq llama-3.3-70b-versatile (grounded — no outside knowledge)
"""

import os
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
CHROMA_DIR   = os.path.join("data", "chroma_db")
COLLECTION   = "gsu_professor_reviews"
EMBED_MODEL  = "all-MiniLM-L6-v2"
TOP_K        = 5
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ── Lazy-loaded singletons (avoid reloading on every query) ───────────────────
_embed_model  = None
_chroma_col   = None
_groq_client  = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL)
    return _embed_model


def _get_collection() -> chromadb.Collection:
    global _chroma_col
    if _chroma_col is None:
        client      = chromadb.PersistentClient(path=CHROMA_DIR)
        _chroma_col = client.get_collection(name=COLLECTION)
    return _chroma_col


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found. "
                "Copy .env.example to .env and add your key."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


# ── Retrieval ─────────────────────────────────────────────────────────────────
def retrieve(query: str, top_k: int = TOP_K, professor: str = None) -> list[dict]:
    """
    Embed the query and return the top_k most similar chunks with metadata.
    Each result dict has: text, source, chunk_index, distance.

    Optional metadata filtering:
      professor — restrict results to a specific professor's source file.
                  Pass the filename prefix e.g. "prof_Islam" or "prof_Bal".
                  This is a Stage 4 metadata filter applied inside ChromaDB
                  before cosine similarity ranking, so only chunks from that
                  professor are considered. Useful for targeted queries like
                  "Is Professor Islam good at explaining?" where you already
                  know which professor you're asking about.
    """
    model      = _get_embed_model()
    collection = _get_collection()

    query_vec = model.encode([query]).tolist()

    # Build optional where clause for metadata filtering
    where = None
    if professor:
        # ChromaDB metadata filter: source field must contain the professor filename
        # e.g. professor="prof_Islam" matches source="prof_Islam.txt"
        where = {"source": {"$eq": f"{professor}.txt"}}

    query_kwargs = dict(
        query_embeddings = query_vec,
        n_results        = top_k,
        include          = ["documents", "metadatas", "distances"],
    )
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":        doc,
            "source":      meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance":    dist,
        })
    return chunks


# ── Generation ────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful assistant for Georgia State University students.
You answer questions about CS professors using ONLY the student reviews provided to you.

CRITICAL rules you must follow:
1. Answer ONLY using information found in the provided review excerpts.
2. Do NOT use any outside knowledge about professors, courses, or universities.
3. Each excerpt is labeled with its source filename (e.g. prof_Alser.txt, prof_Bal.txt).
   The filename tells you EXACTLY which professor the review is about:
   - prof_Alser.txt = Mohammed Alser
   - prof_Bal.txt = Bal Abdullah
   - prof_Islam.txt = S M Towhidul Islam
   - prof_Johnson.txt = William Johnson
   - prof_Sadasivuni.txt = Tushara Sadasivuni
   - prof_Kumar.txt = Saliesh Kumar
   - prof_Ashok.txt = Ashwin Ashok
   - prof_Bingyi.txt = Xie Bingyi
   - prof_Esra.txt = Esra Akbas
   - prof_Lan.txt = Gao Lan
   - prof_Rahman.txt = Mahfuzur Rahman
   - prof_Roya.txt = Hosseini Roya
4. Always use the source filename to identify which professor a review is about,
   even if the professor's name is not mentioned in the review text itself.
5. If the provided excerpts do not contain enough information to answer the question,
   respond with exactly: "I don't have enough information in the available reviews to answer that."
6. Keep your answer concise and directly relevant to the question.
"""


def generate(query: str, chunks: list[dict]) -> str:
    """
    Build a grounded prompt from retrieved chunks and call the Groq LLM.
    Returns the model's response string.
    """
    # Build the context block from retrieved chunks
    # Professor name lookup so context is always explicit
    PROF_NAMES = {
        "prof_Alser.txt":      "Mohammed Alser",
        "prof_Ashok.txt":      "Ashwin Ashok",
        "prof_Bal.txt":        "Bal Abdullah",
        "prof_Bingyi.txt":     "Xie Bingyi",
        "prof_Esra.txt":       "Esra Akbas",
        "prof_Islam.txt":      "S M Towhidul Islam",
        "prof_Johnson.txt":    "William Johnson",
        "prof_Lan.txt":        "Gao Lan",
        "prof_Rahman.txt":     "Mahfuzur Rahman",
        "prof_Sadasivuni.txt": "Tushara Sadasivuni",
        "prof_Kumar.txt":      "Saliesh Kumar",
        "prof_Roya.txt":       "Hosseini Roya",
    }

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        prof_name = PROF_NAMES.get(chunk['source'], chunk['source'])
        context_parts.append(
            f"[Excerpt {i} — Professor: {prof_name} | source: {chunk['source']}]\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    user_message = f"""Use the following student review excerpts to answer the question.

--- REVIEW EXCERPTS ---
{context}
--- END OF EXCERPTS ---

Question: {query}

Remember: answer using only the excerpts above. Cite which professor or source the information comes from."""

    client   = _get_groq()
    response = client.chat.completions.create(
        model    = GROQ_MODEL,
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,    # low temperature → more factual, less creative
        max_tokens  = 512,
    )
    return response.choices[0].message.content.strip()


# ── End-to-end ask() function (used by app.py) ────────────────────────────────
def ask(query: str, professor: str = None) -> dict:
    """
    Full RAG pipeline: retrieve → generate.

    Args:
        query:     The user's plain-English question.
        professor: Optional metadata filter. Pass a professor filename prefix
                   (e.g. "prof_Islam", "prof_Bal") to restrict retrieval to
                   only that professor's review chunks. When set, ChromaDB
                   applies a metadata filter at Stage 4 before cosine
                   similarity ranking — only chunks from that source file
                   are considered. This directly fixes the failure case in
                   Question 1 of the evaluation plan.

    Returns: { answer: str, sources: list[str], chunks: list[dict] }
    """
    chunks  = retrieve(query, professor=professor)
    answer  = generate(query, chunks)
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # unique, ordered

    return {
        "answer":  answer,
        "sources": sources,
        "chunks":  chunks,
    }


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_questions = [
        "Which professor for CSC 2720 is most frequently described as explaining concepts clearly?",
        "Which professor requires attendance according to student reviews?",
        "Which professor is described as having a heavy workload?",
        "Which professor is lenient in grading?",
        "Which professor has the best reviews irrespective of the course?",
    ]

    for q in test_questions:
        print("\n" + "─" * 70)
        print(f"Q: {q}")
        result = ask(q)
        print(f"\nA: {result['answer']}")
        print(f"\nSources: {', '.join(result['sources'])}")
        print("\nRetrieved chunks:")
        for i, c in enumerate(result["chunks"], 1):
            print(f"  [{i}] {c['source']}  dist={c['distance']:.4f}  {c['text'][:120]!r}")