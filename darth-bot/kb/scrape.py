"""
darth-bot/kb/scrape.py
======================
One-time scraper for Destiny 2 knowledge sources.

Targets (politely, with delays + cache):
  - light.gg          item/perk/roll pages
  - bungie.net        exotic mission + quest pages
  - reddit.com        top posts in r/destinythegame, r/destiny2 (last 90d)
  - destinypedia      raid + dungeon mechanic articles
  - d2checklist       weekly reset summary

Output: clean Markdown files under data/scrape/<source>/<slug>.md
        Each file has a YAML frontmatter with source URL + tags.

After scraping, run kb/embed.py to chunk + embed into chromadb.

Usage:
    python3 -m darth-bot.kb.scrape --source lightgg --pages 100
    python3 -m darth-bot.kb.scrape --source reddit --subreddit destinythegame --top 200
    python3 -m darth-bot.kb.scrape --all

NOTE: This file is a starter scraper — Light.gg & Reddit have rate limits.
Add User-Agent identifying yourself, respect robots.txt, throttle to ~1 req/s.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import time
from pathlib import Path
from typing import Iterable

import httpx
from bs4 import BeautifulSoup

from ..config import SCRAPE_DIR

USER_AGENT = "darth-bot/0.1 (https://github.com/clarencestephen/order-66 — personal Destiny 2 chatbot)"
HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
DELAY_SECONDS = 1.2  # be a polite scraper


def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:80] or "untitled"


def write_doc(source: str, title: str, url: str, body: str, tags: Iterable[str] = ()):
    out_dir = SCRAPE_DIR / source
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / f"{slugify(title)}.md"
    fm = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"source: {source}",
        f"url: {url}",
        f"scraped: {int(time.time())}",
    ]
    if tags:
        fm.append("tags: [" + ", ".join(f'"{t}"' for t in tags) + "]")
    fm.append("---")
    fname.write_text("\n".join(fm) + "\n\n" + body, encoding="utf-8")
    return fname


async def fetch(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        r = await client.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        if r.status_code != 200:
            print(f"  ! {r.status_code} {url}")
            return None
        return r.text
    except Exception as e:
        print(f"  ! err {url}: {e}")
        return None


async def scrape_lightgg(pages: int = 50):
    """
    Light.gg has thousands of weapon/armor/perk pages. The cleanest starting
    point is their roll-and-perk database. Start with the top exotics page
    then crawl linked items.
    """
    import trafilatura
    seeds = [
        "https://www.light.gg/db/items/?Category=exotic",
        "https://www.light.gg/db/items/?Category=primary",
        "https://www.light.gg/god-rolls/",
    ]
    visited = set()
    queue = list(seeds)
    count = 0
    async with httpx.AsyncClient(http2=True) as client:
        while queue and count < pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            html = await fetch(client, url)
            if not html:
                await asyncio.sleep(DELAY_SECONDS)
                continue
            extracted = trafilatura.extract(html, include_comments=False,
                                            include_tables=True, output_format="markdown")
            soup = BeautifulSoup(html, "lxml")
            title = (soup.title.string if soup.title else "untitled").strip()
            if extracted and len(extracted) > 300:
                write_doc("lightgg", title, url, extracted, tags=["lightgg"])
                count += 1
                print(f"  [{count}/{pages}] {title[:60]}")
            # discover more item links
            for a in soup.select("a[href]"):
                href = a.get("href")
                if not href or not href.startswith("/db/items/"):
                    continue
                full = "https://www.light.gg" + href
                if full not in visited and len(queue) < 500:
                    queue.append(full)
            await asyncio.sleep(DELAY_SECONDS)


async def scrape_reddit(subreddit: str = "destinythegame", top: int = 100):
    """
    Reddit JSON endpoints — no auth needed for read-only listings.
    Pull top posts of past 90 days from a subreddit.
    """
    base = f"https://www.reddit.com/r/{subreddit}/top/.json?t=year&limit=100"
    count = 0
    after = None
    async with httpx.AsyncClient() as client:
        while count < top:
            url = base + (f"&after={after}" if after else "")
            html = await fetch(client, url)
            if not html:
                break
            import json
            data = json.loads(html)
            children = data.get("data", {}).get("children", [])
            if not children:
                break
            for child in children:
                if count >= top:
                    break
                d = child["data"]
                if d.get("is_video") or d.get("over_18"):
                    continue
                title = d.get("title", "")
                body = d.get("selftext", "")
                if not body or len(body) < 200:
                    continue
                permalink = "https://reddit.com" + d.get("permalink", "")
                write_doc("reddit", title, permalink, body,
                          tags=[subreddit, f"score:{d.get('score',0)}"])
                count += 1
                print(f"  [{count}/{top}] r/{subreddit} :: {title[:60]}")
            after = data.get("data", {}).get("after")
            if not after:
                break
            await asyncio.sleep(DELAY_SECONDS)


async def scrape_destinypedia(seeds: Iterable[str] = ()):
    """Bungie + raid + dungeon mechanic pages from destinypedia."""
    import trafilatura
    default_seeds = [
        "https://www.destinypedia.com/Salvation%27s_Edge",
        "https://www.destinypedia.com/Root_of_Nightmares",
        "https://www.destinypedia.com/Vow_of_the_Disciple",
        "https://www.destinypedia.com/Deep_Stone_Crypt",
        "https://www.destinypedia.com/King%27s_Fall",
        "https://www.destinypedia.com/Last_Wish",
        "https://www.destinypedia.com/Vault_of_Glass",
        "https://www.destinypedia.com/Crota%27s_End",
        "https://www.destinypedia.com/Garden_of_Salvation",
    ]
    seeds = list(seeds) or default_seeds
    async with httpx.AsyncClient() as client:
        for url in seeds:
            html = await fetch(client, url)
            if not html:
                continue
            extracted = trafilatura.extract(html, include_tables=True, output_format="markdown")
            soup = BeautifulSoup(html, "lxml")
            title = (soup.title.string if soup.title else url).strip()
            if extracted and len(extracted) > 300:
                write_doc("destinypedia", title, url, extracted, tags=["raid"])
                print(f"  [destinypedia] {title[:60]}")
            await asyncio.sleep(DELAY_SECONDS)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["lightgg", "reddit", "destinypedia", "all"], default="all")
    ap.add_argument("--pages", type=int, default=100, help="for lightgg")
    ap.add_argument("--subreddit", default="destinythegame", help="for reddit")
    ap.add_argument("--top", type=int, default=100, help="for reddit")
    args = ap.parse_args()

    if args.source in ("lightgg", "all"):
        print("=== light.gg ===")
        await scrape_lightgg(pages=args.pages)
    if args.source in ("reddit", "all"):
        print("=== reddit ===")
        await scrape_reddit(args.subreddit, top=args.top)
    if args.source in ("destinypedia", "all"):
        print("=== destinypedia ===")
        await scrape_destinypedia()


if __name__ == "__main__":
    asyncio.run(main())
