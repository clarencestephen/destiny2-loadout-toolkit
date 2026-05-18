# Welcome + Rules — channel post bodies

Bodies for the two posts that the install script drops into `#welcome` and
`#imperial-law`. Voice borrows from DARTH_BANKAI brand guide (confident,
technical, dry humor) and the Twitch "Imperial Transmission" panel copy.

Both posts are sent as **Discord embeds** with Sith Purple (`#B432FF`)
accent. `setup_server.py` reads the text below verbatim; if you edit, the
next run re-posts the updated version (idempotent via a hidden marker
comment in the embed footer).

---

## `#welcome` — Imperial Transmission

**Embed title:** `▲ IMPERIAL TRANSMISSION RECEIVED`
**Color:** `#B432FF` (Sith Purple)
**Footer:** `Order 66 · home of Destiny Voyager` *(this footer line is the
idempotency marker — do not change without bumping `WELCOME_MARKER` in
`setup_server.py`)*

**Body:**

```
Everything that has transpired has done so according to my design.

You have entered the **Order 66** clan server — the dark side of Destiny 2
build optimization. Home of **Destiny Voyager**, the workbook that turns
your DIM URLs, inventory, and exotic queue into one ruthless plan.

**Start here, Padawan:**

➊  Read 📋 **#imperial-law** — react to accept the code. This unlocks
    the rest of the server.
➋  Drop into 🌟 **#recruitment-roles** — react to the 8 messages to set
    your platform, dungeon/raid experience, time zone, and clan status.
➌  Introduce yourself in 📋 **#in-a-galaxy-far-far-away** — name, class,
    timezone, what you're chasing this season.
➍  Grab Destiny Voyager from 🚀 **#destiny-voyager** if you want the
    workbook.

We don't tag `@everyone` or `@here`. If you want pings for raid nights,
GMs, or dungeon teaches, pick the roles in #recruitment-roles. Otherwise
your phone stays quiet.

If you're not signed up with **Charlemagne** (the Destiny 2 Discord bot),
you'll need to be — `/profile link` in any channel after he's invited.
See the pinned message in #imperial-law for the link.

There is no luck. Only probability — and execution.

The negotiation loudly inhales. And now... the server begins.
```

---

## `#imperial-law` — the rules + verification

**Embed title:** `▲ IMPERIAL LAW`
**Color:** `#B432FF` (Sith Purple)
**Footer:** `react ✅ to accept · Order 66`

**Body:**

```
You underestimate the power of the dark side.

**The seven precepts. Read. React. Comply.**

➊  **Respect all troopers in chat.** No slurs, no harassment, no
    targeting anyone for who they are. The Empire is a meritocracy of
    builds, not a free-for-all.

➋  **No spam, excessive caps, or rebel alliance behaviour.** One emoji
    per thought. Reaction roles are not a slot machine.

➌  **No self-promotion or solicitation.** Don't drop your stream, your
    Discord, your commission rates, or your sketchy "I sell loadouts"
    DMs. Ask a mod first if you're not sure.

➍  **Spoilers go in spoiler tags.** New raid week, new exotic mission,
    new campaign — wrap it with `||spoiler||` for at least one week
    after release.

➎  **Stay on-topic per channel.** Build chat in build channels, LFG in
    LFG channels, the Cantina is the off-topic catch-all. The Imperial
    Senate exists for everything else.

➏  **Mod's word is final.** Death Star Command runs the moderation
    queue. Disagree quietly via DM; do not litigate it in public chat.

➐  **USE THE FORCE.** If a question can be answered by `/sanity` from
    Darth Bot, by the manifest, by light.gg, or by reading the pinned
    message — try those first. Then ask.

The Empire does not issue earnings twice.

────────────────────────────────────────────

**To enter the rest of the server: react ✅ below.**

Reacting acknowledges the code and grants you the `@Padawan` role,
which unlocks every public channel. From there, ask a mod in
🎫 **#bounty-office** to be promoted to `@Imperial Trooper` (if you're
joining the clan) or `@Rebel Ally` (if you're a verified friend of
the clan).

`@Unverified` members only see #welcome and #imperial-law. Until you
react, that's all there is.
```

---

## How verification works (operator notes — not posted)

1. **On join → Unverified.** This is the Discord default role. Sapphire
   (or any reaction-role bot) can be configured to auto-assign
   `@Unverified` to new joiners, but the simpler path is to set
   `@everyone` permissions to mirror Unverified (deny view on every
   category except `📋 In a Galaxy Far Far Away`). Then no auto-assign
   is needed — joining gives them `@everyone`, which is locked out
   already.

2. **React ✅ on the Imperial Law embed → Padawan.** Wire this in
   Sapphire/MEE6 reaction-roles dashboard: emoji `✅`, role `@Padawan`,
   message ID = whichever Discord message ID the bot ends up posting
   (visible in the script's stdout after a successful run, or
   right-click → Copy Message ID).

3. **Mod promotes Padawan → Imperial Trooper / Rebel Ally.** Manual.
   Death Star Command does this when:
   - Imperial Trooper: clan invite has been accepted in-game
   - Rebel Ally: trusted non-clan member (e.g. raid regular, mutual
     friend) — granted at mod discretion

4. **(Optional) Auto-prune Unverified.** Sapphire and MEE6 both support
   "kick after N days if user has only the @everyone / Unverified
   role." Useful for clearing dead accounts after 30 days.

The verification design intentionally keeps `@Padawan` as the gateway
role even for non-clan members. It maps cleanly to Star Wars semantics
(new arrival, learning) and avoids inventing a generic `@Verified` role
that duplicates what the hoisted ones already encode.
