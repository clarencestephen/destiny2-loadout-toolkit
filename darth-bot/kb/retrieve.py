"""
darth-bot/kb/retrieve.py
========================
Query chromadb for the top-K most relevant chunks given a user question.
Returns plaintext suitable for the LLM context block.
"""

from __future__ import annotations

from functools import lru_cache

from ..config import CHROMA_DIR, EMBED_MODEL, TOP_K


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
