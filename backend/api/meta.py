"""Meta state + TWAB endpoints."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/state")
async def state() -> dict:
    """Current meta_state.json + a pre-formatted prompt block."""
    from meta_state import current_state, format_for_prompt  # type: ignore[import-not-found]

    return {
        "state": current_state,
        "prompt_block": format_for_prompt(),
    }


@router.get("/twab")
async def twab(limit: int = 10) -> dict:
    """Most-recent Bungie RSS items, fetched live."""
    from twab_scraper import fetch_recent  # type: ignore[import-not-found]

    return {"items": fetch_recent(limit=limit)}
