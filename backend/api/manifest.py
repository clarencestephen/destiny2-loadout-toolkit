"""Manifest endpoints — name lookup + named-entity extraction from text."""
from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/lookup")
async def lookup(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    from kb.manifest import lookup_by_name  # type: ignore[import-not-found]

    matches = lookup_by_name(q, limit=limit)
    return {"query": q, "count": len(matches), "matches": matches}


@router.get("/extract")
async def extract(
    text: str = Query(..., min_length=1, max_length=4000),
    limit: int = Query(8, ge=1, le=20),
) -> dict:
    from kb.manifest import extract_named_items, verify_names  # type: ignore[import-not-found]

    items = extract_named_items(text, max_results=limit)
    verification = verify_names(text)
    return {"items": items, "verification": verification}
