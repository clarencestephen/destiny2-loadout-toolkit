"""
discord/setup_server.py
=======================
One-shot Discord server builder. Reads server_layout.json and creates every
role, category, and channel in your Discord server. Sets up the basic
clan-only / mod-only permission overwrites.

Usage:
    pip install discord.py
    python3 discord/setup_server.py

Environment variables (or pass on CLI):
    DISCORD_BOT_TOKEN   — your bot token from https://discord.com/developers/applications
    DISCORD_GUILD_ID    — target server ID (default: from server_layout.json)

Setup:
1. Go to https://discord.com/developers/applications → New Application
2. Bot tab → Reset Token → copy token → set DISCORD_BOT_TOKEN
3. OAuth2 → URL Generator → check `bot` + `applications.commands` scopes
4. Bot Permissions: Administrator (simplest) — or specifically:
   Manage Roles, Manage Channels, Manage Messages, Add Reactions, Send Messages, Read Message History
5. Open the generated URL → invite the bot to your server
6. Run this script

The script is IDEMPOTENT for the role + category + channel structure:
  - Roles that already exist (by name) are skipped
  - Categories that already exist are reused
  - Channels that already exist inside a category are skipped
So you can re-run it safely after editing the JSON to add new things.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

try:
    import discord
except ImportError:
    sys.exit("ERROR: discord.py not installed. Run: pip install discord.py")

LAYOUT_PATH = Path(__file__).parent / "server_layout.json"

# Discord built-in color names → discord.Color
COLOR_MAP = {
    "red":    discord.Color.red(),
    "blue":   discord.Color.blue(),
    "green":  discord.Color.green(),
    "yellow": discord.Color.gold(),
    "orange": discord.Color.orange(),
    "purple": discord.Color.purple(),
    "pink":   discord.Color.magenta(),
    "teal":   discord.Color.teal(),
    "gold":   discord.Color.gold(),
    "navy":   discord.Color.dark_blue(),
    "grey":   discord.Color.light_grey(),
    "gray":   discord.Color.light_grey(),
}


def color_from(name):
    return COLOR_MAP.get(name, discord.Color.default())


def find_role(guild, name):
    return discord.utils.get(guild.roles, name=name)


def find_category(guild, name):
    return discord.utils.get(guild.categories, name=name)


def find_channel_in_cat(category, name):
    for ch in category.channels:
        if ch.name == name.lower().replace(" ", "-"):
            return ch
        if ch.name == name:
            return ch
    return None


async def ensure_roles(guild, role_defs):
    print(f"\n[Roles] Ensuring {len(role_defs)} roles exist...")
    # Discord creates roles at the bottom of the hierarchy by default.
    # Iterate reversed so the "top" role in JSON ends up highest in the list.
    for rd in reversed(role_defs):
        name = rd["name"]
        existing = find_role(guild, name)
        if existing:
            print(f"  ✓ exists: {name}")
            continue
        try:
            await guild.create_role(
                name=name,
                color=color_from(rd.get("color", "default")),
                hoist=rd.get("hoist", False),
                mentionable=rd.get("mentionable", False),
                reason="setup_server.py — initial server build",
            )
            print(f"  + created: {name}")
        except Exception as e:
            print(f"  ✗ failed: {name} — {e}")


async def ensure_category(guild, cat_def):
    name = cat_def["name"]
    existing = find_category(guild, name)
    if existing:
        print(f"\n[Category] ✓ exists: {name}")
        return existing
    cat = await guild.create_category(name=name, reason="setup_server.py")
    print(f"\n[Category] + created: {name}")
    return cat


async def ensure_channels(guild, category, channel_defs):
    """Create text/voice channels within a category if they don't exist."""
    for cd in channel_defs:
        ch_name = cd["name"]
        ch_type = cd["type"]
        existing = find_channel_in_cat(category, ch_name)
        if existing:
            print(f"    ✓ exists: {ch_type:6} #{existing.name}")
            continue
        try:
            if ch_type == "text":
                ch = await guild.create_text_channel(
                    name=ch_name, category=category,
                    topic=cd.get("topic"),
                    reason="setup_server.py",
                )
            elif ch_type == "voice":
                ch = await guild.create_voice_channel(
                    name=ch_name, category=category,
                    reason="setup_server.py",
                )
            else:
                print(f"    ? unknown type {ch_type!r} for {ch_name}")
                continue
            print(f"    + created: {ch_type:6} #{ch.name}")
        except Exception as e:
            print(f"    ✗ failed: {ch_name} — {e}")


async def apply_category_restrictions(guild, layout):
    """
    Apply basic permission overwrites for sensitive categories:
      - Imperial Troopers → @Imperial Trooper only
      - Death Star Command → @Death Star Command + @Emperor only
      - The Imperial Armory → verified roles only
      - Imperial Declarations → everyone reads, mods write
    """
    print("\n[Permissions] Applying category overwrites...")
    everyone = guild.default_role
    trooper = find_role(guild, "Imperial Trooper")
    rebel = find_role(guild, "Rebel Ally")
    padawan = find_role(guild, "Padawan")
    death_star = find_role(guild, "Death Star Command")
    emperor = find_role(guild, "Emperor")

    restrictions = {
        "⚔️ Imperial Troopers": {
            everyone: discord.PermissionOverwrite(view_channel=False),
            trooper:  discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True),
        },
        "💀 Death Star Command": {
            everyone:    discord.PermissionOverwrite(view_channel=False),
            death_star:  discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True),
            emperor:     discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True),
        },
        "🚀 The Imperial Armory": {
            everyone: discord.PermissionOverwrite(view_channel=False),
            trooper:  discord.PermissionOverwrite(view_channel=True, send_messages=True),
            rebel:    discord.PermissionOverwrite(view_channel=True, send_messages=True),
            padawan:  discord.PermissionOverwrite(view_channel=True, send_messages=True),
        },
        "📣 Imperial Declarations": {
            everyone:   discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True),
            death_star: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            emperor:    discord.PermissionOverwrite(view_channel=True, send_messages=True),
        },
    }

    for cat_name, overwrites in restrictions.items():
        cat = find_category(guild, cat_name)
        if not cat:
            print(f"  ? skipped {cat_name} (not found)")
            continue
        # Strip None role keys (e.g. if a role didn't exist yet)
        clean = {k: v for k, v in overwrites.items() if k is not None}
        try:
            await cat.edit(overwrites=clean, reason="setup_server.py — restrict access")
            # Propagate to child channels
            for ch in cat.channels:
                await ch.edit(sync_permissions=True)
            print(f"  ✓ restricted: {cat_name}")
        except Exception as e:
            print(f"  ✗ failed: {cat_name} — {e}")


class SetupClient(discord.Client):
    def __init__(self, layout, guild_id, **kw):
        intents = discord.Intents.default()
        super().__init__(intents=intents, **kw)
        self.layout = layout
        self.guild_id = int(guild_id)

    async def on_ready(self):
        print(f"\n[ready] Logged in as {self.user} (id={self.user.id})")
        guild = self.get_guild(self.guild_id)
        if not guild:
            print(f"ERROR: bot is not in guild {self.guild_id}. "
                  "Invite the bot first (OAuth2 → URL Generator with 'bot' scope).")
            await self.close()
            return

        print(f"[guild] {guild.name} ({guild.id}) — {len(guild.members)} members")

        await ensure_roles(guild, self.layout["roles"])

        for cat_def in self.layout["categories"]:
            cat = await ensure_category(guild, cat_def)
            await ensure_channels(guild, cat, cat_def.get("channels", []))

        await apply_category_restrictions(guild, self.layout)

        print("\n[done] Server structure built. Next steps:")
        print("  1. Invite TicketTool.xyz and run /setup in #bounty-office")
        print("  2. Invite Sapphire/MEE6 reaction-role bot, then post reaction-role messages from")
        print("     discord/pick_roles_messages.md into #recruitment-roles and add reactions")
        print("  3. Server Settings → Overview → set 'Inactive Channel' to '💤 Carbonite Chamber'")
        print("  4. Server Settings → Roles → drag 'Emperor' to the top above any bot roles")
        print()
        await self.close()


def main():
    layout = json.loads(LAYOUT_PATH.read_text())
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        sys.exit("ERROR: DISCORD_BOT_TOKEN env var not set. "
                 "Create a bot at https://discord.com/developers/applications "
                 "and export DISCORD_BOT_TOKEN=<token>")
    guild_id = os.environ.get("DISCORD_GUILD_ID") or layout.get("_target_server_id")
    if not guild_id:
        sys.exit("ERROR: DISCORD_GUILD_ID env var not set and no _target_server_id in JSON.")

    client = SetupClient(layout, guild_id)
    client.run(token)


if __name__ == "__main__":
    main()
