"""
darth-bot/kb/scrape_youtube.py
==============================
Pass-3 raid+dungeon enrichment — fetches YouTube transcripts for the
per-encounter walkthrough videos curated in `raids/*.yaml` (and
`raids/dungeons/*.yaml`).

Each raid YAML may contain a `walkthrough_videos:` block (added by
`raids/kings-fall.yaml` first, others follow the same shape):

    walkthrough_videos:
      source: "Community sherpa video series"
      collected: "2026-05-26"
      playlist: ""
      per_encounter:
        - order: 1
          slug: hall-of-souls
          url: "https://youtu.be/iyXgTvLHtak"
          label: "Hall of Souls"
        - order: 2
          ...

Output: `data/scrape/youtube/<activity-slug>/<encounter-slug>.md`
with YAML front matter (source: youtube, video_id, activity_slug,
encounter_slug, scraped) and the transcript text below.

Why text and not video metadata: the bot's KB embeds these as
retrieval-augmented context for the /ask + /raid commands. Plain
transcripts (no timestamps in the chunks) lets the RAG layer pull
relevant sentences without YouTube IDs cluttering the prompt.

Run:
    # Scrape every raid + dungeon walkthrough_videos block
    python3 -m darth_bot.kb.scrape_youtube

    # Scope to one raid
    python3 -m darth_bot.kb.scrape_youtube --activity kings-fall

    # Refresh even when output already exists
    python3 -m darth_bot.kb.scrape_youtube --activity kings-fall --force
"""
from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

# trafilatura's optional yaml dep handles both safe-load and the
# Bungie-text apostrophes in raid YAML names without escaping.
import yaml

try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
except ImportError as e:
    raise SystemExit(
        "youtube-transcript-api not installed. Add it to environment.yml "
        "(or `pip install youtube-transcript-api>=0.6`) and re-run."
    ) from e


# Library exposes a single instance-based interface in ≥1.0:
#     api = YouTubeTranscriptApi()
#     api.fetch(video_id, languages=("en",))
# Older versions used classmethods (get_transcript / list_transcripts).
# We use the new instance API since that's what conda-forge ships now.
_TX_API = YouTubeTranscriptApi()

from config import SCRAPE_DIR


RAIDS_DIR = Path(__file__).parent.parent.parent / "raids"
DELAY_SECONDS = 1.0   # be polite to YouTube's transcript endpoint


def video_id_from_url(url: str) -> str | None:
    """Extract the 11-char video ID from any common YouTube URL shape."""
    if not url:
        return None
    patterns = [
        r"youtu\.be/([A-Za-z0-9_-]{11})",                # youtu.be/<id>
        r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",    # ?v=<id>
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",       # /embed/<id>
        r"youtube\.com/v/([A-Za-z0-9_-]{11})",           # /v/<id>
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",      # /shorts/<id>
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    # Bare 11-char id passthrough (the user might paste just the ID)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    return None


def fetch_transcript(video_id: str) -> str | None:
    """Return the transcript as a single block of plain text, or None
    if the video has no captions / is unavailable.

    Tries English variants in priority order. The library auto-prefers
    manually-uploaded transcripts over auto-generated when both exist.
    """
    try:
        fetched = _TX_API.fetch(video_id, languages=("en", "en-US", "en-GB"))
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return None
    except Exception:
        return None
    # FetchedTranscript is iterable; each snippet is a
    # FetchedTranscriptSnippet with .text (newer API) OR a plain dict
    # (older API). Handle both.
    lines: list[str] = []
    for snip in fetched:
        if isinstance(snip, dict):
            text = snip.get("text") or ""
        else:
            text = getattr(snip, "text", "") or ""
        text = text.strip()
        if not text:
            continue
        if re.fullmatch(r"\[[^\]]+\]", text):
            continue  # drop "[Music]", "[Applause]"
        lines.append(text)
    return " ".join(lines).strip() or None


def write_transcript_doc(
    activity_slug: str,
    encounter_slug: str,
    video_id: str,
    label: str,
    url: str,
    transcript: str,
) -> Path:
    out_dir = SCRAPE_DIR / "youtube" / activity_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / f"{encounter_slug}.md"
    label_safe = label.replace('"', "'")
    front = [
        "---",
        f'title: "{activity_slug} — {label_safe}"',
        "source: youtube",
        f"activity_slug: {activity_slug}",
        f"encounter_slug: {encounter_slug}",
        f"video_id: {video_id}",
        f"url: {url}",
        f"scraped: {int(time.time())}",
        "---",
        "",
    ]
    fname.write_text("\n".join(front) + transcript + "\n", encoding="utf-8")
    return fname


def iter_raid_yamls(only_activity: str | None) -> list[Path]:
    files: list[Path] = []
    files.extend(sorted(RAIDS_DIR.glob("*.yaml")))
    files.extend(sorted((RAIDS_DIR / "dungeons").glob("*.yaml")))
    if only_activity:
        files = [p for p in files if p.stem == only_activity]
    return files


def main(only_activity: str | None, force: bool = False) -> None:
    files = iter_raid_yamls(only_activity)
    if not files:
        target = f" for '{only_activity}'" if only_activity else ""
        print(f"No raid YAMLs found{target}.")
        return
    print(f"Scanning {len(files)} raid/dungeon YAML(s) for walkthrough_videos blocks...")

    total_videos = 0
    total_transcripts = 0
    skipped = 0
    for yaml_path in files:
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ! {yaml_path.name}: YAML parse error ({e})")
            continue
        if not isinstance(data, dict):
            continue

        activity_slug = data.get("slug") or yaml_path.stem
        ww = data.get("walkthrough_videos") or {}
        per_enc = (ww.get("per_encounter") or []) if isinstance(ww, dict) else []
        if not per_enc:
            continue

        print(f"\n[{activity_slug}] {len(per_enc)} videos")
        for entry in per_enc:
            if not isinstance(entry, dict):
                continue
            url = entry.get("url") or ""
            label = entry.get("label") or entry.get("sub_section") or entry.get("slug") or "untitled"
            encounter_slug = (
                entry.get("slug") or entry.get("sub_section") or "encounter"
            )
            vid = video_id_from_url(url)
            if not vid:
                print(f"  ! {label}: no video id parsable from {url!r}")
                continue
            total_videos += 1

            out_path = SCRAPE_DIR / "youtube" / activity_slug / f"{encounter_slug}.md"
            if out_path.exists() and not force:
                skipped += 1
                print(f"  · {encounter_slug}: cached → {out_path.name}")
                continue

            transcript = fetch_transcript(vid)
            time.sleep(DELAY_SECONDS)
            if not transcript:
                print(f"  ✗ {encounter_slug} ({vid}): no transcript available")
                continue
            path = write_transcript_doc(
                activity_slug, encounter_slug, vid, label, url, transcript,
            )
            total_transcripts += 1
            print(f"  ✓ {encounter_slug}: {len(transcript):,} chars → {path.name}")

    print(
        f"\nDone. {total_videos} videos found · {total_transcripts} transcripts written · "
        f"{skipped} cached / skipped."
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--activity",
        help="Only scrape this slug (e.g. kings-fall). Default: every raid + dungeon.",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch transcripts even when output files already exist.",
    )
    args = ap.parse_args()
    main(only_activity=args.activity, force=args.force)
