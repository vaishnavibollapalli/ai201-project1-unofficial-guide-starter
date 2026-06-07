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

# Configuration
CHROMA_DIR   = os.path.join("data", "chroma_db")
COLLECTION   = "gsu_professor_reviews"
EMBED_MODEL  = "all-MiniLM-L6-v2"
TOP_K        = 5
GROQ_MODEL   = "llama-3.3-70b-versatile"

# Lazy-loaded singletons (avoid reloading on every query) 
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


# Retrieval
def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return the top_k most similar chunks with metadata.
    Each result dict has: text, source, chunk_index, distance.
    """
    model      = _get_embed_model()
    collection = _get_collection()

    query_vec = model.encode([query]).tolist()
    results   = collection.query(
        query_embeddings = query_vec,
        n_results        = top_k,
        include          = ["documents", "metadatas", "distances"],
    )

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


# Generation 
SYSTEM_PROMPT = """You are a helpful assistant for Georgia State University students.
You answer questions about CS professors using ONLY the student reviews provided to you.

Rules you must follow:
1. Answer ONLY using information found in the provided review excerpts.
2. Do NOT use any outside knowledge about professors, courses, or universities.
3. If the provided excerpts do not contain enough information to answer the question,
   respond with exactly: "I don't have enough information in the available reviews to answer that."
4. Always mention which professor(s) the information came from.
5. Keep your answer concise and directly relevant to the question.
"""


def generate(query: str, chunks: list[dict]) -> str:
    """
    Build a grounded prompt from retrieved chunks and call the Groq LLM.
    Returns the model's response string.
    """
    # Build the context block from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Excerpt {i} — source: {chunk['source']}]\n{chunk['text']}"
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


# End-to-end ask() function (used by app.py)
def ask(query: str) -> dict:
    """
    Full RAG pipeline: retrieve → generate.
    Returns: { answer: str, sources: list[str], chunks: list[dict] }
    """
    chunks  = retrieve(query)
    answer  = generate(query, chunks)
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # unique, ordered

    return {
        "answer":  answer,
        "sources": sources,
        "chunks":  chunks,
    }


# Standalone testing of retrieval and generation (run `python src/query.py`)
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