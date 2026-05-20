"""Discord ↔ Bungie account link flow.

Flow:
  1. Discord user runs `/link-bungie` → bot calls POST /link/start { discord_id }
     Backend generates a one-time code, stores discord_id → code in DB with 10min TTL.
     Returns: link URL on the web (https://destiny-voyager.../link?code=XYZ).
  2. User opens link, logs into Bungie OAuth via the web app.
  3. Web frontend (after successful OAuth) calls POST /link/complete { code, session_id }.
     Backend looks up session in KV (via Worker proxy) → bungie_id, stores
     discord_id ↔ bungie_id pair, deletes code.
  4. Future Discord commands resolve discord_id → bungie_id via GET /link/discord/{discord_id}.
"""
from __future__ import annotations

import os
import secrets
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db import LinkStore

router = APIRouter()

PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5173")
CODE_TTL_SECONDS = 600  # 10 minutes
_store = LinkStore(Path(__file__).resolve().parents[1] / "data" / "links.db")


class StartRequest(BaseModel):
    discord_id: str = Field(..., min_length=10, max_length=32)


class StartResponse(BaseModel):
    url: str
    code: str
    expires_in: int


@router.post("/start", response_model=StartResponse)
async def start(req: StartRequest) -> StartResponse:
    code = secrets.token_urlsafe(16)
    expires_at = int(time.time()) + CODE_TTL_SECONDS
    _store.save_pending(code, req.discord_id, expires_at)
    return StartResponse(
        url=f"{PUBLIC_BASE_URL}/link?code={code}",
        code=code,
        expires_in=CODE_TTL_SECONDS,
    )


class CompleteRequest(BaseModel):
    code: str
    bungie_id: str
    display_name: str | None = None


class CompleteResponse(BaseModel):
    discord_id: str
    bungie_id: str
    linked_at: int


@router.post("/complete", response_model=CompleteResponse)
async def complete(req: CompleteRequest) -> CompleteResponse:
    pending = _store.consume_pending(req.code)
    if not pending:
        raise HTTPException(status_code=404, detail="Link code expired or unknown")
    discord_id = pending["discord_id"]
    linked_at = int(time.time())
    _store.save_link(discord_id, req.bungie_id, req.display_name or "", linked_at)
    return CompleteResponse(discord_id=discord_id, bungie_id=req.bungie_id, linked_at=linked_at)


@router.get("/discord/{discord_id}")
async def resolve(discord_id: str) -> dict:
    link = _store.lookup_by_discord(discord_id)
    if not link:
        raise HTTPException(status_code=404, detail="Discord account not linked")
    return link
