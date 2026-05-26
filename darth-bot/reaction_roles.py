"""
darth-bot/reaction_roles.py
===========================
Native reaction-role handling for Darth Bot. Replaces the MEE6 / Sapphire
dependency: when a member reacts to one of the configured messages in
#imperial-law or #recruitment-roles, this module assigns / removes the
corresponding role.

How it works:
  1. At bot startup, scan each configured channel for the message whose
     marker substring matches. Build a cache:
       message_id → {emoji: role_id}
  2. Hook into on_raw_reaction_add / on_raw_reaction_remove. Look up
     the message_id in the cache, find the role, assign or remove.

Self-healing: when setup_server.py reposts a message (because its
marker version bumped), the next bot startup picks up the new
message_id automatically. No code change required.

Configuration: discord/messages.py § REACTION_ROLE_MAP.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Dict

import discord

# Pull the mapping from discord/messages.py
_DISCORD_DIR = Path(__file__).resolve().parents[1] / "discord"
sys.path.insert(0, str(_DISCORD_DIR))
import messages as msg_content  # noqa: E402

log = logging.getLogger("darth-bot.reaction_roles")


class ReactionRoleManager:
    """Holds the message_id → {emoji: role_id} cache and the event handlers."""

    def __init__(self, client: discord.Client, guild_id: int):
        self.client = client
        self.guild_id = guild_id
        # message_id → {emoji_str: role_id}
        self.cache: Dict[int, Dict[str, int]] = {}

    async def refresh(self):
        """Rebuild the cache by walking the configured channels and
        finding the marker-stamped messages. Safe to re-run."""
        guild = self.client.get_guild(self.guild_id)
        if not guild:
            log.warning("guild %s not found yet; reaction-roles unavailable", self.guild_id)
            return

        new_cache: Dict[int, Dict[str, int]] = {}
        for marker_substr, channel_name, emoji_role_map in msg_content.REACTION_ROLE_MAP:
            ch = discord.utils.get(guild.text_channels, name=channel_name)
            if not ch:
                log.warning("channel #%s not found", channel_name)
                continue

            msg = await self._find_message_by_marker(ch, marker_substr)
            if not msg:
                log.warning("no message with marker %r in #%s", marker_substr, channel_name)
                continue

            # Resolve emoji → role_id (by role name)
            resolved: Dict[str, int] = {}
            for emoji, role_name in emoji_role_map.items():
                role = discord.utils.get(guild.roles, name=role_name)
                if not role:
                    log.warning("role @%s not found in guild — skipping %s", role_name, emoji)
                    continue
                resolved[emoji] = role.id

            new_cache[msg.id] = resolved
            log.info("wired #%s msg %d (%r) → %d reactions",
                     channel_name, msg.id, marker_substr, len(resolved))

        self.cache = new_cache
        log.info("reaction-roles cache: %d messages wired", len(self.cache))

    async def _find_message_by_marker(self, channel: discord.TextChannel,
                                       marker_substr: str) -> discord.Message | None:
        """Scan recent messages in channel for one matching marker_substr in
        its embed footer or body."""
        async for m in channel.history(limit=100):
            # Bots only — skip user messages
            if not m.author.bot:
                continue
            # Check embed footer first
            for emb in m.embeds:
                if emb.footer and emb.footer.text and marker_substr in emb.footer.text:
                    return m
                if emb.description and marker_substr in emb.description:
                    return m
            # Then check plain body
            if marker_substr in (m.content or ""):
                return m
        return None

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self._handle(payload, add=True)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self._handle(payload, add=False)

    async def _handle(self, payload: discord.RawReactionActionEvent, *, add: bool):
        if payload.guild_id != self.guild_id:
            return
        roles = self.cache.get(payload.message_id)
        if not roles:
            return
        emoji_str = str(payload.emoji)
        role_id = roles.get(emoji_str)
        if role_id is None:
            return

        guild = self.client.get_guild(self.guild_id)
        if not guild:
            return
        # Skip bot reactions
        if payload.user_id == self.client.user.id:
            return
        member = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if not member or member.bot:
            return
        role = guild.get_role(role_id)
        if not role:
            return

        try:
            if add:
                await member.add_roles(role, reason="reaction-role: react add")
                log.info("+ @%s → %s (msg %d %s)",
                         member.display_name, role.name, payload.message_id, emoji_str)
            else:
                await member.remove_roles(role, reason="reaction-role: react remove")
                log.info("- @%s ← %s (msg %d %s)",
                         member.display_name, role.name, payload.message_id, emoji_str)
        except discord.Forbidden:
            log.warning("Forbidden assigning %s to %s — check role hierarchy",
                        role.name, member.display_name)
        except Exception as e:
            log.warning("failed to %s role: %s", "add" if add else "remove", e)


def attach(client: discord.Client, guild_id: int) -> ReactionRoleManager:
    """Attach reaction-role handlers to a discord.Client. Call this once
    at startup. Returns the manager so the caller can refresh() it."""
    mgr = ReactionRoleManager(client, guild_id)

    @client.event
    async def on_raw_reaction_add(payload):
        await mgr.on_raw_reaction_add(payload)

    @client.event
    async def on_raw_reaction_remove(payload):
        await mgr.on_raw_reaction_remove(payload)

    return mgr
