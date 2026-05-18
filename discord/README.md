# Discord server setup — Order 66 (the Destiny Voyager clan)

Files in this folder:

| File | Purpose |
|---|---|
| `server_layout.json` | Full structure (roles, categories, channels). Star Wars themed names. Target server ID: `1471072707524296767`. |
| `setup_server.py` | One-shot Discord bot script. Reads the JSON, builds the structure, gates Unverified, and posts the welcome/rules/reaction-role messages. Idempotent — safe to re-run. |
| `messages.py` | Content module imported by `setup_server.py` — welcome embed, imperial-law embed, and the 8 reaction-role message bodies + their emoji lists. Edit text here. |
| `welcome_and_rules.md` | Human-readable source for the `#welcome` and `#imperial-law` posts. Mirrored in `messages.py`. |
| `pick_roles_messages.md` | Human-readable source for the 8 `#recruitment-roles` messages + emoji → role mapping tables. Mirrored in `messages.py`. |

---

## End-to-end setup (~15 minutes)

### Step 1 — Build the structure with `setup_server.py`

1. **Create a Discord bot** at https://discord.com/developers/applications → **New Application**
   - Name: "Order 66 Setup Bot" (or anything)
   - Go to **Bot** tab → **Reset Token** → copy the token
   - Under **Privileged Gateway Intents**: enable **Message Content** (needed for idempotency — the script reads its own past messages to avoid double-posting)
2. **Generate an invite URL**: OAuth2 → URL Generator
   - Scopes: `bot` + `applications.commands`
   - Bot Permissions: **Administrator** (simplest) — or specifically: Manage Roles, Manage Channels, Manage Messages, Add Reactions, Send Messages, Read Message History, View Channels
3. **Invite the bot** to your server using the generated URL
4. **Run the script**:
   ```bash
   pip install discord.py
   export DISCORD_BOT_TOKEN="<your_token_here>"
   python3 discord/setup_server.py
   ```
   (Add `--skip-posts` if you only want structure changes and don't want the script to post or update messages.)

The script does, in order:

1. **Roles** — creates everything in `roles[]` in priority order (Emperor at top, Unverified at bottom).
2. **Categories + channels** — every category and its channels.
3. **Sensitive-category restrictions** — `⚔️ Imperial Troopers` (clan only), `💀 Death Star Command` (mods only), `🚀 The Imperial Armory` (verified only), `📣 Imperial Declarations` (read-only for members).
4. **Unverified gating** — every other category is locked to `@Padawan` / `@Rebel Ally` / `@Imperial Trooper`. The gateway (`📋 In a Galaxy Far Far Away`, `🌟 Recruitment Roles`, `🎫 Galactic Senate`) stays open to `@everyone` so Unverified members can still see #welcome, #imperial-law, and react to roles.
5. **Welcome + Imperial Law embeds** — posts both, pins them, and adds the ✅ reaction to imperial-law so reaction-role bots can wire it.
6. **8 recruitment-role messages** — posts each one with its emoji pre-applied so users can react immediately. Sapphire/MEE6 still need to be told *which role* each emoji maps to (next step).

The script prints **message IDs** at the end. You'll need these to wire up the reaction-role bot.

---

### Step 2 — Invite TicketTool.xyz

For `🎫 Galactic Senate / #bounty-office`:

1. Go to https://tickettool.xyz/
2. Click **Invite TicketTool** → pick your server → authorize
3. In `#bounty-office` run `/setup`
4. Configure the panel to drop into `#bounty-office`

---

### Step 3 — Wire reaction roles in Sapphire (or MEE6)

You already have **MEE6**, **FlaviBot**, and **Sapphire** options:

| Bot | Reaction roles? | Notes |
|---|---|---|
| **Sapphire** | ✅ Yes | Free, good dashboard. https://sapphirebot.dev |
| **MEE6** | ✅ Yes (Premium for advanced) | https://mee6.xyz |
| **FlaviBot** | ✅ Yes | https://flavibot.xyz |

Invite your chosen bot, then map emoji → role for each of the 9 messages the script posted. The script printed message IDs in its stdout — copy each one.

**Mappings (from `messages.py` / `pick_roles_messages.md`):**

| Message | Emoji → Role |
|---|---|
| `#imperial-law` (verification) | ✅ → `@Padawan` |
| Clan status (1️⃣) | 🍑 → `@Clan` · 🐕 → `@Non-clan members` · 🖕 → `@Want to join` |
| Pronouns (2️⃣) | 💃 → `@Female` · 🕺 → `@Male` |
| Platform (3️⃣) | ❎ → `@Xbox` · 🎮 → `@PlayStation` · 💻 → `@PC` · 📡 → `@Steam` |
| Dungeon experience (4️⃣) | 🔫 → `@Dungeon` · 🙈 → `@Run 10+ dungeons each` · 🦖 → `@Teaching dungeons` · 🍌 → `@Learning dungeon (clan)` · 📚 → `@Learning dungeon (non-clan)` |
| Raid experience (5️⃣) | 🚬 → `@Raids` · 💀 → `@Teaching raids` · ☠️ → `@10 raids each+` · 🍻 → `@Learning raids (clan)` · 👍 → `@Learning raids (non-clan)` |
| Activities (6️⃣) | ⚔️ → `@PvP` · 🐔 → `@Gambit` · 🏆 → `@End game` · 🧡 → `@Making friends 🧡` |
| Time zone (7️⃣) | 🌅 → `@US East` · 🌆 → `@US Central` · 🏔️ → `@US Mountain` · 🌉 → `@US Pacific` · 🇬🇧 → `@UK` · 🇪🇺 → `@EU` · 🌏 → `@Asia` · 🇦🇺 → `@Australia` |

Test by reacting on yourself — the role should toggle on/off.

---

### Step 4 — Invite Charlemagne (Destiny 2 stats bot)

For commands like `/profile`, `/triumphs`, `/season-pass`, `/clears`, `/loadout`:

1. Go to https://warmind.io
2. Click **Add to Discord** → pick your server → authorize
3. In any channel, members run `/profile link` to connect their Bungie account
4. After linking, `/profile` shows their full Destiny 2 dossier (light, raids, exotics, trials rating)

Members **must** be linked to use raid attendance / event signups via Charlemagne. Mention this in your welcome embed (already done — see `messages.py` `WELCOME_BODY`).

The welcome message references Charlemagne by name and tells people to run `/profile link`. Just confirm after install that the command is available.

---

### Step 5 — Use Xenon to back up the result

After everything looks right:

1. Invite Xenon: https://xenon.bot
2. In your server: `/backup create`
3. Save the backup ID — `/backup load <id>` restores everything if it ever gets nuked

---

### Step 6 — Set Carbonite Chamber as AFK

**Server Settings → Overview → Inactive Channel** → pick `💤 Carbonite Chamber` → set timeout (5/15/30 min).

---

### Step 7 — (Optional) Set the brand assets

From `/mnt/c/Users/clare/OneDrive/Gaming/Darth_bankai - branding/`:

- **Server icon** — `discord_avatar.png` (512×512). Server Settings → Overview → upload.
- **Server banner** — any Destiny AI image at 960×540, e.g. one from `/mnt/c/Users/clare/OneDrive/Gaming/Destiny AI images/`. Server Settings → Overview (requires Boost Level 2).
- **Bot avatar** — same `discord_avatar.png` works for the Order 66 Setup Bot in https://discord.com/developers/applications → your app → General Information → App Icon.

---

## Verification flow

How members move from `@Unverified` → `@Padawan` → `@Imperial Trooper` / `@Rebel Ally`:

```
JOIN SERVER
   │
   ▼
@everyone (which is effectively @Unverified — only sees the gateway)
   │   sees: #welcome, #imperial-law, #recruitment-roles, #bounty-office
   │   blocked from: everything else
   ▼
React ✅ to #imperial-law
   │  (wired in Sapphire/MEE6 reaction-role config)
   ▼
@Padawan — full read access to every public channel
   │
   ├── (clan invite accepted in-game) ──────► mod promotes to @Imperial Trooper
   │                                          (unlocks ⚔️ Imperial Troopers category)
   │
   └── (trusted non-clan member)     ──────► mod promotes to @Rebel Ally
                                              (no change in access, just a visible badge)
```

**Why `@Padawan` as the default verified role?** It's a Star Wars-themed "new arrival" label that works whether the person eventually joins the clan or not. Padawan also already exists in the role list, so we avoid inventing a separate `@Verified` role that just duplicates what the hoisted set encodes.

**Optional: auto-prune Unverified.** Both Sapphire and MEE6 support "kick after N days if user only has @everyone." Useful for clearing dead accounts after 30 days.

---

## Re-running the script

`setup_server.py` is idempotent across all five phases:

- **Roles / categories / channels** — detected by name, skipped if they exist
- **Permission overwrites** — re-applied (no harm, same result)
- **Welcome / rules / recruitment posts** — detected via a hidden marker string in the embed footer (or message body for plain text). Skipped if found.

**To force a re-post of a message:** bump its `_MARKER` constant in `messages.py` (e.g. `· v1` → `· v2`). The old version stays in the channel; the new version is posted fresh. Delete the stale message manually in Discord if you want it gone.

**To skip posting entirely on a structural re-run:** `python3 discord/setup_server.py --skip-posts`.

---

## Customizing the layout

`server_layout.json` is just JSON — edit freely:

- Add a category: append a new object to `categories[]`
- Add a channel: append to a category's `channels[]`
- Add a role: append to `roles[]`
- Change a name: edit the `name` field; on re-run the bot can't auto-rename (it'll skip because the old name still exists). To rename: do it in Discord manually, then update the JSON to match for future re-runs.

To rename the clan brand "Order 66" to something else: search-and-replace across this folder and the project root. (The app is **Destiny Voyager** — separate brand, owned by the same clan.)

---

## Troubleshooting

**"Bot is not in guild X"**
Bot wasn't invited. Use the OAuth URL Generator (Step 1) and re-invite.

**"Missing Permissions" / "Forbidden 50013"**
Bot's role is lower than the role you're trying to manage, OR it lacks Manage Roles / Manage Channels. After running, drag the bot's auto-generated role above all custom roles you want it to manage.

**"Message Content Intent" error on startup**
You didn't enable the Message Content privileged intent in the developer portal (Step 1, point 1). Without it the script can't read its own past messages to detect duplicates and will refuse to post.

**Reactions don't assign roles**
The script posts messages and pre-applies the reactions, but you still have to **map emoji → role in Sapphire/MEE6 dashboard** (Step 3). Each message needs to be registered individually using its message ID.

**Welcome / rules posted twice**
Marker drift — either you edited an old post manually (which removed the footer) or the marker string in `messages.py` changed. Delete the duplicate(s) manually; future runs will use the current marker.
