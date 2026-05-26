# Order 66 — Bungie clan reference (as-built)

**STATUS: LIVE — created 2026-05-24.**
Profile: https://www.bungie.net/7/en/Clan/Profile/5421866
groupId: `5421866` (also in `/home/cs/.env` as `BUNGIE_CLAN_GROUP_ID`)

## Form field values (as submitted)

| Field | Value |
|---|---|
| Clan Name | `Order 66` |
| Callsign | `SITH` |
| Motto | `Together we will rule the galaxy.` |
| Homepage | `https://discord.gg/prqqQ8n2U` |
| Membership | Approval Required |
| About | *Final version below — Bungie-filter-cleaned* |

## About text (final, Bungie-accepted)

```
ORDER 66 — Imperial Destiny 2 clan. The dark side, but with snacks.

WHO WE ARE
18+ Destiny 2 community. We're here to play the game, run cool stuff
together, and have a good time. Drama-free, sherpa-friendly, and we'll
explain mechanics in voice instead of rushing to the finish. Mic preferred
for raids — chat is fine for everything else.

SCHEDULE
Mostly Eastern Time (US) — raid nights cluster weeknights + Sunday
evenings ET. Members from every time zone welcome; we'll grow into
broader coverage over time.

WHAT WE RUN
Raids · Dungeons · GMs · Trials · Iron Banner. We teach Salvation's
Edge, Desert Perpetual, Vow, and the full rotation back to Vault of
Glass. New to endgame? Hop in, we got you.

JOIN US
Discord: https://discord.gg/prqqQ8n2U
Approval required (just so we can say hi first). House rules in
#imperial-law. After joining Discord, ping a mod in #bounty-office
for the in-game clan invite.

It's a game. We're here to have fun.

— Together we will rule the galaxy.
```

## Lessons learned

### Bungie's About-field content filter

Bungie's automated filter blocks About text that promotes external tools,
services, or apps (even if they're community-owned and free). The original
draft included a `BUILDING SOMETHING TOGETHER` section advertising Destiny
Voyager and Darth Bot. **The filter rejected it on first submission.**

The section was stripped from the About and the content moved to
[`community_builds_pin.md`](community_builds_pin.md) — a Discord pinned
message in `#destiny-voyager`.

**Rule of thumb for future edits:** anything that looks like advertising
external URLs, products, or projects belongs in Discord, not Bungie. The
clan About should describe the clan itself, schedule, what we run, and
how to join — nothing else.

## What unlocks now that the clan exists

| Task | Status | Path |
|---|---|---|
| Auto-assign `@Imperial Trooper` on Bungie clan verification | Unblocked | Build Darth Bot `/verify-clan` slash command — calls Bungie `GetGroupsForMember` with the linked membershipId, assigns the role if `groupId == 5421866` |
| Charlemagne clan-event integration | Unblocked | Charlemagne will detect Order 66 by Bungie groupId once members link via `/profile link` |
| Recruiting flow | Live | Bungie.net clan page → Discord invite (in Homepage field) → `#imperial-law` verification → mod-promote to `@Imperial Trooper` |

## Editing the About later

Bungie.net → Clans → Order 66 → Admin → Edit Clan. Same content filter
applies. If the edit gets silently rejected, look for promotional language
or external URLs.
