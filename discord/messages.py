"""
discord/messages.py
===================
Content for the messages setup_server.py posts into channels.

Each message has a `marker` string that goes into its embed footer (or
into the message body for the reaction-role plain messages) — the script
uses that marker to detect "this is already posted, skip it." Edit a
message? Bump its marker (e.g. "v1" -> "v2") to force a re-post.

Source of truth for the prose: discord/welcome_and_rules.md and
discord/pick_roles_messages.md. Keep them in sync when editing here.
"""

from __future__ import annotations

SITH_PURPLE = 0xB432FF


# ────────────────────────────────────────────────────────────────────
# #welcome — Imperial Transmission embed
# ────────────────────────────────────────────────────────────────────

WELCOME_MARKER = "Order 66 · home of Destiny Voyager · v1"

WELCOME_TITLE = "▲ IMPERIAL TRANSMISSION RECEIVED"

WELCOME_BODY = (
    "Everything that has transpired has done so according to my design.\n\n"
    "You have entered the **Order 66** clan server — the dark side of "
    "Destiny 2 build optimization. Home of **Destiny Voyager**, the "
    "workbook that turns your DIM URLs, inventory, and exotic queue into "
    "one ruthless plan.\n\n"
    "**Start here, Padawan:**\n\n"
    "➊  Read 📋 **#imperial-law** — react to accept the code. This "
    "unlocks the rest of the server.\n"
    "➋  Drop into 🌟 **#recruitment-roles** — react to the messages to "
    "set your platform, dungeon/raid experience, time zone, and clan "
    "status.\n"
    "➌  Introduce yourself in 📋 **#in-a-galaxy-far-far-away** — name, "
    "class, timezone, what you're chasing this season.\n"
    "➍  Grab Destiny Voyager from 🚀 **#destiny-voyager** if you want "
    "the workbook.\n\n"
    "We don't tag `@everyone` or `@here`. Pick roles if you want pings "
    "for raid nights, GMs, or dungeon teaches. Otherwise your phone "
    "stays quiet.\n\n"
    "If you're not signed up with **Charlemagne** (the Destiny 2 Discord "
    "bot), you'll need to be — `/profile link` in any channel after "
    "he's invited. See the pinned message in #imperial-law for the link.\n\n"
    "There is no luck. Only probability — and execution.\n\n"
    "*The negotiation loudly inhales. And now... the server begins.*"
)


# ────────────────────────────────────────────────────────────────────
# #imperial-law — rules embed + ✅ verification reaction
# ────────────────────────────────────────────────────────────────────

RULES_MARKER = "react ✅ to accept · Order 66 · v1"

RULES_TITLE = "▲ IMPERIAL LAW"

RULES_BODY = (
    "You underestimate the power of the dark side.\n\n"
    "**The seven precepts. Read. React. Comply.**\n\n"
    "➊  **Respect all troopers in chat.** No slurs, no harassment, no "
    "targeting anyone for who they are. The Empire is a meritocracy of "
    "builds, not a free-for-all.\n\n"
    "➋  **No spam, excessive caps, or rebel alliance behaviour.** One "
    "emoji per thought. Reaction roles are not a slot machine.\n\n"
    "➌  **No self-promotion or solicitation.** Don't drop your stream, "
    "your Discord, your commission rates, or your sketchy \"I sell "
    "loadouts\" DMs. Ask a mod first if you're not sure.\n\n"
    "➍  **Spoilers go in spoiler tags.** New raid week, new exotic "
    "mission, new campaign — wrap it with `||spoiler||` for at least "
    "one week after release.\n\n"
    "➎  **Stay on-topic per channel.** Build chat in build channels, "
    "LFG in LFG channels, the Cantina is the off-topic catch-all.\n\n"
    "➏  **Mod's word is final.** Death Star Commander runs the moderation "
    "queue. Disagree quietly via DM; do not litigate it in public chat.\n\n"
    "➐  **USE THE FORCE.** If a question can be answered by `/sanity` "
    "from Darth Bot, by the manifest, by light.gg, or by reading the "
    "pinned message — try those first. Then ask.\n\n"
    "*The Empire does not issue earnings twice.*\n\n"
    "────────────────────────────────────────\n\n"
    "**To enter the rest of the server: react ✅ below.**\n\n"
    "Reacting acknowledges the code and grants you `@Padawan`, which "
    "unlocks every public channel. From there, ask a mod in 🎫 "
    "**#bounty-office** to be promoted to `@Imperial Trooper` (if "
    "you're joining the clan) or `@Rebel Ally` (if you're a verified "
    "friend of the clan).\n\n"
    "`@Unverified` members only see #welcome and #imperial-law. Until "
    "you react, that's all there is."
)

VERIFY_REACTION = "✅"


# ────────────────────────────────────────────────────────────────────
# #recruitment-roles — 8 reaction-role messages (intro + 7 categories)
#
# Each entry: (marker, body_text, [reaction_emoji, ...])
# The bot posts these as plain text messages (not embeds) because
# Sapphire/MEE6 reaction-role wiring works most reliably on plain text.
# ────────────────────────────────────────────────────────────────────

RECRUITMENT_MESSAGES = [
    (
        "Order 66 · recruitment-roles · intro · v1",
        (
            "**🌟  ROLE ASSIGNMENT  🌟**\n\n"
            "React to the messages below. Each one assigns a role you "
            "can toggle on/off at any time.\n\n"
            "We don't ping `@everyone`, so if you want notifications for "
            "raid nights, GMs, or dungeon teaches, you need to pick the "
            "roles below. Otherwise your phone stays quiet.\n\n"
            "*Marker: Order 66 · recruitment-roles · intro · v1*"
        ),
        [],  # no reactions — just an intro
    ),
    (
        "Order 66 · clan-status · v1",
        (
            "**1️⃣  Clan status**\n\n"
            "🍑  →  `@Clan`  (you're in the Order 66 clan in-game)\n"
            "🐕  →  `@Non-clan members`  (in a different clan)\n"
            "🖕  →  `@Want to join`  (looking to join Order 66)\n\n"
            "*Marker: Order 66 · clan-status · v1*"
        ),
        ["🍑", "🐕", "🖕"],
    ),
    (
        "Order 66 · pronouns · v1",
        (
            "**2️⃣  Pronouns / gender** (optional)\n\n"
            "💃  →  `@Female`\n"
            "🕺  →  `@Male`\n\n"
            "*Marker: Order 66 · pronouns · v1*"
        ),
        ["💃", "🕺"],
    ),
    (
        "Order 66 · platform · v1",
        (
            "**3️⃣  Platform** — react to each platform you play on\n\n"
            "❎  →  `@Xbox`\n"
            "🎮  →  `@PlayStation`\n"
            "💻  →  `@PC`\n"
            "📡  →  `@Steam`\n\n"
            "*Marker: Order 66 · platform · v1*"
        ),
        ["❎", "🎮", "💻", "📡"],
    ),
    (
        "Order 66 · dungeon-experience · v1",
        (
            "**4️⃣  Dungeon experience** — pick what fits\n\n"
            "🔫  →  `@Dungeon`  (general — runs dungeons sometimes)\n"
            "🙈  →  `@Run 10+ dungeons each`\n"
            "🦖  →  `@Teaching dungeons`  (you sherpa newbies)\n"
            "🍌  →  `@Learning dungeon (clan)`\n"
            "📚  →  `@Learning dungeon (non-clan)`\n\n"
            "*Marker: Order 66 · dungeon-experience · v1*"
        ),
        ["🔫", "🙈", "🦖", "🍌", "📚"],
    ),
    (
        "Order 66 · raid-experience · v1",
        (
            "**5️⃣  Raid experience** — pick what fits\n\n"
            "🚬  →  `@Raids`  (general — runs raids)\n"
            "💀  →  `@Teaching raids`  (you sherpa first-clears)\n"
            "☠️  →  `@10 raids each+`\n"
            "🍻  →  `@Learning raids (clan)`\n"
            "👍  →  `@Learning raids (non-clan)`\n\n"
            "*Marker: Order 66 · raid-experience · v1*"
        ),
        ["🚬", "💀", "☠️", "🍻", "👍"],
    ),
    (
        "Order 66 · activities · v1",
        (
            "**6️⃣  Activity interests**\n\n"
            "⚔️  →  `@PvP`\n"
            "🐔  →  `@Gambit`\n"
            "🏆  →  `@End game`  (GMs, Master raids, Conqueror)\n"
            "🧡  →  `@Making friends 🧡`\n\n"
            "*Marker: Order 66 · activities · v1*"
        ),
        ["⚔️", "🐔", "🏆", "🧡"],
    ),
    (
        "Order 66 · time-zone · v1",
        (
            "**7️⃣  Time zone / region** — helps with LFG timing\n\n"
            "🌅  →  `@US East`\n"
            "🌆  →  `@US Central`\n"
            "🏔️  →  `@US Mountain`\n"
            "🌉  →  `@US Pacific`\n"
            "🇬🇧  →  `@UK`\n"
            "🇪🇺  →  `@EU`\n"
            "🌏  →  `@Asia`\n"
            "🇦🇺  →  `@Australia`\n\n"
            "*Marker: Order 66 · time-zone · v1*"
        ),
        ["🌅", "🌆", "🏔️", "🌉", "🇬🇧", "🇪🇺", "🌏", "🇦🇺"],
    ),
]


# ────────────────────────────────────────────────────────────────────
# Gating policy
# ────────────────────────────────────────────────────────────────────

# Categories visible to @everyone (and therefore @Unverified). Anything
# not in this set OR in CATEGORY_RESTRICTIONS (defined in setup_server.py)
# gets denied for @everyone and granted to Padawan/Rebel Ally/Imperial
# Trooper.
GATEWAY_CATEGORIES = {
    "📋 In a Galaxy Far Far Away",  # welcome / law / introductions / TZ chat
    "🌟 Recruitment Roles",         # everyone needs to pick roles
    "🎫 Galactic Senate",           # tickets — anyone can open one
}

# Categories handled by apply_category_restrictions() in setup_server.py;
# don't double-apply gating to these.
ALREADY_RESTRICTED_CATEGORIES = {
    "⚔️ Imperial Troopers",
    "💀 Death Star Commander",
    "🚀 The Imperial Armory",
    "📣 Imperial Declarations",
}
