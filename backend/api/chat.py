"""POST /chat — run the darth-bot router on a question."""
from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None  # optional — enables inventory-aware answers


class ChatResponse(BaseModel):
    answer: str
    category: str
    used_inventory: bool
    used_kb: bool
    used_search: bool
    used_manifest: bool


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Lazy import — these modules pull in ollama, chromadb, the manifest cache,
    # etc. We don't want them loaded at app startup if /chat is never called.
    from router import answer, classify  # type: ignore[import-not-found]

    plan = classify(req.question)
    text = await answer(req.question)
    return ChatResponse(
        answer=text,
        category=plan.category,
        used_inventory=plan.use_inventory,
        used_kb=plan.use_kb,
        used_search=plan.use_search,
        used_manifest=plan.use_manifest,
    )
