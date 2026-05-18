"""Inventory analysis — compares the user's vault to the current meta."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class AnalyzeRequest(BaseModel):
    focus: str = Field("all", description="all | weapons | armor | hunter | titan | warlock | pvp | pve")
    session_id: str | None = None  # for multi-user setups (future)


class AnalyzeResponse(BaseModel):
    inventory_context: str
    meta_block: str
    has_inventory: bool
    suggestions: list[str]


def _suggest_upgrades(inventory_text: str, meta_state: dict) -> list[str]:
    """Compare what's in inventory to the curated meta lists.
    Returns short "consider chasing X" lines for top meta items the user
    doesn't seem to own."""
    out = []
    inv_lower = inventory_text.lower()
    for slot_key, label in [
        ("top_primaries", "primary"),
        ("top_specials", "special"),
        ("top_heavies", "heavy"),
    ]:
        for pool in ("pvp_meta", "pve_meta"):
            block = (meta_state.get(pool) or {}).get(slot_key) or []
            for item in block:
                name = item.get("name") if isinstance(item, dict) else str(item)
                if not name:
                    continue
                if name.lower() not in inv_lower:
                    mode = pool.split("_")[0].upper()
                    out.append(f"Chase **{name}** — top {mode} {label}, missing from inventory")
    return out[:8]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    from inventory import build_context, has_inventory  # type: ignore[import-not-found]
    from meta_state import current_state, format_for_prompt  # type: ignore[import-not-found]

    inv_text = build_context(focus=req.focus)
    return AnalyzeResponse(
        inventory_context=inv_text,
        meta_block=format_for_prompt(),
        has_inventory=has_inventory(),
        suggestions=_suggest_upgrades(inv_text, current_state),
    )
