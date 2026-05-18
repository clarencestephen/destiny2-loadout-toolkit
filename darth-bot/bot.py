"""
darth-bot/bot.py
================
Discord bot entry point. Run with:

    cd darth-bot
    python3 -m darth-bot.bot

Or once you've set DARTH_BOT_DISCORD_TOKEN in /home/cs/.env, just:
    python3 bot.py

Commands:
    /ask <question>           — any Destiny question
    /build <activity>         — build recommendation (uses your inventory)
    /raid <name>              — encounter rundown
    /catalyst <weapon>        — catalyst quest steps
    /sanity                   — verify ollama + kb + inventory are reachable

The bot also responds to @mentions in any allowed channel.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord
from discord import app_commands

from .config import (ALLOWED_CHANNEL_NAMES, DISCORD_BOT_TOKEN, DISCORD_GUILD_ID,
                     MODEL)
from .llm import check_ollama
from .router import answer, classify

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("darth-bot")


# Discord setup — minimal intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True


class DarthBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.guild = discord.Object(id=DISCORD_GUILD_ID)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

    async def on_ready(self):
        log.info(f"Connected as {self.user} (id={self.user.id})")
        log.info(f"Model: {MODEL}")
        if not await check_ollama():
            log.warning("Ollama not reachable or model not pulled — answers will fail "
                        "until `ollama pull %s` is done.", MODEL)


bot = DarthBot()


# ============================================================
# Helpers
# ============================================================


def _is_allowed_channel(channel) -> bool:
    if isinstance(channel, discord.DMChannel):
        return True
    return getattr(channel, "name", "") in ALLOWED_CHANNEL_NAMES


async def _reply_long(interaction: discord.Interaction, text: str):
    """Send a possibly-long answer in 2000-char chunks."""
    chunks = []
    while text:
        if len(text) <= 1900:
            chunks.append(text)
            break
        # split on paragraph boundary if possible
        split = text.rfind("\n\n", 0, 1900)
        if split < 800:
            split = text.rfind("\n", 0, 1900)
        if split < 800:
            split = 1900
        chunks.append(text[:split])
        text = text[split:].lstrip()
    for i, chunk in enumerate(chunks):
        if i == 0:
            await interaction.followup.send(chunk)
        else:
            await interaction.channel.send(chunk)


# ============================================================
# Slash commands
# ============================================================


@bot.tree.command(name="ask", description="Ask Darth Bot a Destiny 2 question")
@app_commands.describe(question="What do you want to know?")
async def cmd_ask(interaction: discord.Interaction, question: str):
    if not _is_allowed_channel(interaction.channel):
        await interaction.response.send_message(
            "I only work in toolkit / cantina / LFG channels.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    try:
        text = await answer(question)
    except Exception as e:
        log.exception("ask failed")
        text = f"⚠️  Something broke: `{e}`"
    await _reply_long(interaction, text)


@bot.tree.command(name="build",
                  description="Recommend a build using your current inventory")
@app_commands.describe(activity="Activity context (pvp, pve, raid, gm, solo ops)")
async def cmd_build(interaction: discord.Interaction, activity: str = "pve"):
    await interaction.response.defer(thinking=True)
    question = f"What is a good {activity} build with my current weapons and armor?"
    try:
        text = await answer(question)
    except Exception as e:
        text = f"⚠️  {e}"
    await _reply_long(interaction, text)


@bot.tree.command(name="raid",
                  description="Summarize a raid's encounters")
@app_commands.describe(name="Raid name (e.g., 'salvations edge')")
async def cmd_raid(interaction: discord.Interaction, name: str):
    await interaction.response.defer(thinking=True)
    question = f"Can you summarize the main roles and encounters for the {name} raid?"
    try:
        text = await answer(question)
    except Exception as e:
        text = f"⚠️  {e}"
    await _reply_long(interaction, text)


@bot.tree.command(name="catalyst",
                  description="How to get a weapon's catalyst")
@app_commands.describe(weapon="Weapon name (e.g., 'crimson')")
async def cmd_catalyst(interaction: discord.Interaction, weapon: str):
    await interaction.response.defer(thinking=True)
    question = f"How do I get the {weapon} catalyst, step by step?"
    try:
        text = await answer(question)
    except Exception as e:
        text = f"⚠️  {e}"
    await _reply_long(interaction, text)


@bot.tree.command(name="sanity",
                  description="Verify Darth Bot's backend services")
async def cmd_sanity(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    bits = []
    bits.append(f"Model: `{MODEL}`")
    bits.append(f"Ollama: {'✅ reachable' if await check_ollama() else '❌ unreachable / model not pulled'}")
    try:
        from .kb.retrieve import _collection
        n = _collection().count()
        bits.append(f"Knowledge base: {'✅' if n > 0 else '⚠️ empty'} ({n} chunks)")
    except Exception as e:
        bits.append(f"Knowledge base: ❌ {e}")
    try:
        from .inventory import has_inventory
        bits.append(f"Inventory cache: {'✅' if has_inventory() else '⚠️ not populated'}")
    except Exception as e:
        bits.append(f"Inventory cache: ❌ {e}")
    await interaction.followup.send("\n".join(bits))


# ============================================================
# @mention listener
# ============================================================


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if bot.user not in message.mentions:
        return
    if not _is_allowed_channel(message.channel):
        return

    # Strip the mention from the message
    content = message.content
    for mention in [f"<@{bot.user.id}>", f"<@!{bot.user.id}>"]:
        content = content.replace(mention, "")
    content = content.strip()
    if not content:
        return

    async with message.channel.typing():
        try:
            text = await answer(content)
        except Exception as e:
            text = f"⚠️  {e}"

    # Reply, chunked
    while text:
        chunk, text = text[:1900], text[1900:].lstrip()
        await message.reply(chunk, mention_author=False)


# ============================================================
# Bootstrap
# ============================================================


def main():
    if not DISCORD_BOT_TOKEN:
        raise SystemExit(
            "ERROR: DARTH_BOT_DISCORD_TOKEN (or DISCORD_BOT_TOKEN) not set. "
            "Create a bot at https://discord.com/developers/applications, copy "
            "the token, and add it to /home/cs/.env."
        )
    bot.run(DISCORD_BOT_TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
