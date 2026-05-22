"""
darth-bot/kb/retrieve.py
========================
Query chromadb for the top-K most relevant chunks given a user question.
Returns plaintext suitable for the LLM context block.
"""

from __future__ import annotations

from functools import lru_cache

from ..config import CHROMA_DIR, EMBED_MODEL, TOP_K


def _chroma_has_data() -> bool:
    """Cheap probe: does the chroma DB have any documents?
    Inspecting the DB without loading the embedding model first avoids the
    ~133MB BGE download blocking Discord interactions when KB is empty.
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        # Use a no-op embedding fn — we're only counting rows, not querying
        from chromadb.utils import embedding_functions as ef
        coll = client.get_or_create_collection(
            name="destiny",
            embedding_function=ef.DefaultEmbeddingFunction(),
        )
        return coll.count() > 0
    except Exception:
        return False


@lru_cache(maxsize=1)
def _collection():
    import chromadb
    from chromadb.utils import embedding_functions
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL,
    )
    return client.get_or_create_collection(
        name="destiny", embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )


def retrieve(query: str, *, top_k: int = TOP_K) -> list[dict]:
    """Returns list of {text, source, title, url, distance}."""
    # Short-circuit if the KB is empty — avoids loading the heavy embed model
    # for nothing (was hanging Discord interactions on first /ask).
    if not _chroma_has_data():
        return []
    try:
        coll = _collection()
    except Exception as e:
        print(f"[retrieve] chromadb not ready: {e}")
        return []
    if coll.count() == 0:
        return []
    res = coll.query(query_texts=[query], n_results=top_k)
    out = []
    for i, doc in enumerate(res["documents"][0]):
        meta = res["metadatas"][0][i] or {}
        out.append({
            "text": doc,
            "source": meta.get("source", ""),
            "title": meta.get("title", ""),
            "url": meta.get("url", ""),
            "distance": res["distances"][0][i] if "distances" in res else 0.0,
        })
    return out


def format_for_context(query: str, *, top_k: int = TOP_K) -> str:
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return ""
    parts = []
    for c in chunks:
        head = f"[{c['source']} :: {c['title'][:60]}]"
        body = c["text"].strip()[:1200]
        url = f"  ({c['url']})" if c["url"] else ""
        parts.append(f"{head}{url}\n{body}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "how do I get Conditional Finality"
    print(format_for_context(q))
