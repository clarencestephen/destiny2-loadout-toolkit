"""
darth-bot/kb/embed.py
=====================
Chunks the scraped Markdown docs in data/scrape/ and embeds each chunk
into chromadb at data/chroma/.

Run after scraping:
    python3 -m darth-bot.kb.embed

Re-running is idempotent — chunks already in the DB are skipped (matched
by their stable hash).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable

from ..config import CHROMA_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBED_MODEL, SCRAPE_DIR


def chunk_text(text: str, *, size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Word-based chunker. Keeps paragraph breaks where possible."""
    paras = re.split(r"\n\s*\n", text)
    chunks, cur = [], []
    cur_len = 0
    for p in paras:
        words = p.split()
        if cur_len + len(words) > size and cur:
            chunks.append(" ".join(cur))
            # overlap by keeping last `overlap` words
            if overlap > 0:
                cur = cur[-overlap:]
                cur_len = len(cur)
            else:
                cur, cur_len = [], 0
        cur.extend(words)
        cur_len += len(words)
    if cur:
        chunks.append(" ".join(cur))
    return [c for c in chunks if len(c.split()) >= 30]


def stable_id(source: str, title: str, idx: int) -> str:
    h = hashlib.sha1(f"{source}|{title}|{idx}".encode()).hexdigest()[:16]
    return f"{source}-{h}-{idx:03d}"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Strip the YAML-ish frontmatter our scraper writes."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    fm_lines = text[4:end].splitlines()
    body = text[end + 4 :].lstrip("\n")
    meta = {}
    for line in fm_lines:
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, body


def main():
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL,
    )
    coll = client.get_or_create_collection(
        name="destiny",
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    existing_ids = set()
    try:
        for batch in coll.get(include=[])["ids"]:
            existing_ids.add(batch) if isinstance(batch, str) else existing_ids.update(batch)
    except Exception:
        pass

    new_ids, new_docs, new_meta = [], [], []
    md_files = list(SCRAPE_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files under {SCRAPE_DIR}")
    for f in md_files:
        text = f.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        source = meta.get("source", f.parent.name)
        title = meta.get("title", f.stem)
        url = meta.get("url", "")
        for i, chunk in enumerate(chunk_text(body)):
            cid = stable_id(source, title, i)
            if cid in existing_ids:
                continue
            new_ids.append(cid)
            new_docs.append(chunk)
            new_meta.append({"source": source, "title": title, "url": url})
        # batch insert every N
        if len(new_ids) >= 200:
            coll.add(ids=new_ids, documents=new_docs, metadatas=new_meta)
            print(f"  ↳ inserted {len(new_ids)} chunks")
            new_ids, new_docs, new_meta = [], [], []

    if new_ids:
        coll.add(ids=new_ids, documents=new_docs, metadatas=new_meta)
        print(f"  ↳ inserted {len(new_ids)} chunks (final batch)")

    print(f"Done. Collection size: {coll.count()}")


if __name__ == "__main__":
    main()
