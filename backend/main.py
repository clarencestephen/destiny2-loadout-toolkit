"""
backend/main.py
===============
FastAPI entry point. See backend/README.md for the endpoint inventory.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load /home/cs/.env first, then any backend/.env override
load_dotenv("/home/cs/.env")
load_dotenv(Path(__file__).parent / ".env")

# darth-bot modules are imported via importlib (hyphen-prefixed package name);
# rather than re-jiggering the existing layout, add darth-bot/ to sys.path so
# its inner modules import as top-level (config, router, meta_state, kb.*, etc.)
REPO_ROOT = Path(__file__).resolve().parent.parent
DARTH_BOT_DIR = REPO_ROOT / "darth-bot"
if str(DARTH_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(DARTH_BOT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("destiny-voyager-backend")


from .api import chat, inventory, link, manifest, meta  # noqa: E402


app = FastAPI(
    title="Destiny Voyager Backend",
    version="0.1.0",
    description="Python core for Darth Bot (Discord) and Destiny Voyager (web).",
)


ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173,https://destiny-voyager.clarencestephen.com",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": os.environ.get("BACKEND_ENV", "dev"),
    }


app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(manifest.router, prefix="/manifest", tags=["manifest"])
app.include_router(meta.router, prefix="/meta", tags=["meta"])
app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
app.include_router(link.router, prefix="/link", tags=["link"])
