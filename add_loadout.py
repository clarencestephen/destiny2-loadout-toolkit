"""
add_loadout.py
==============
Append a single DIM share URL to user_config.json without re-running setup.py.

Usage:
    python3 add_loadout.py

Or non-interactive:
    python3 add_loadout.py --class Hunter --name "Still Hunt Raid" \\
                           --activity Raid --url https://dim.gg/example1/Raid

After adding, run `python3 decode_dim.py` to re-resolve and update the workbook.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path("user_config.json")
CLASSES = ["Warlock", "Hunter", "Titan"]


def prompt(label, default=None, validator=None):
    while True:
        suffix = f" [{default}]" if default else ""
        raw = input(f"  {label}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if not raw:
            print("    (required)")
            continue
        if validator:
            ok, msg = validator(raw)
            if not ok:
                print(f"    {msg}")
                continue
        return raw


def valid_class(s):
    if s.strip().capitalize() not in CLASSES:
        return False, f"pick one of: {', '.join(CLASSES)}"
    return True, ""


def valid_dim_url(s):
    if not s.strip().startswith("https://dim.gg/"):
        return False, "expected https://dim.gg/..."
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", help="Hunter / Titan / Warlock")
    ap.add_argument("--name", help='Loadout name (e.g. "Still Hunt Raid")')
    ap.add_argument("--activity", help="Raid / PvP / GM / etc.", default="General")
    ap.add_argument("--url", help="DIM share URL (https://dim.gg/...)")
    ap.add_argument("--no-decode", action="store_true",
                    help="Don't run decode_dim.py after adding")
    args = ap.parse_args()

    if not CONFIG_PATH.exists():
        sys.exit(f"ERROR: {CONFIG_PATH} not found. Run `python3 setup.py` first.")

    cfg = json.loads(CONFIG_PATH.read_text())
    cfg.setdefault("dim_loadouts", [])

    # Fill from args, prompt for anything missing
    cls = args.cls or prompt(f"Class ({'/'.join(CLASSES)})", validator=valid_class)
    cls = cls.capitalize()
    name = args.name or prompt('Name (e.g. "Still Hunt Raid")')
    activity = args.activity or prompt("Activity", default="General")
    url = args.url or prompt("DIM share URL", validator=valid_dim_url)

    cfg["dim_loadouts"].append({
        "class": cls, "name": name, "activity": activity, "url": url,
    })
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"  ✓ Added {cls} — {name}")
    print(f"  ✓ Total loadouts in config: {len(cfg['dim_loadouts'])}")

    if not args.no_decode:
        print()
        print("  Running decode_dim.py to refresh the workbook...")
        subprocess.run([sys.executable, "decode_dim.py"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Aborted.")
        sys.exit(130)
