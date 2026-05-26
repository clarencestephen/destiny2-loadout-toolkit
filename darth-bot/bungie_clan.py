"""
darth-bot/bungie_clan.py
========================
Helper for checking whether a linked Bungie account is in the Order 66 clan.

Flow used by /verify-clan:
  1. Bot has a Discord user — look up their linked bungie_id via the
     backend's GET /link/discord/{discord_id} endpoint.
  2. Call Bungie's /User/GetMembershipsById/{bungie_id}/254/ to get the
     user's destinyMemberships list (one per platform).
  3. For each destinyMembership, call /GroupV2/User/{type}/{id}/0/1/
     (GetGroupsForMember, filter=0=all, groupType=1=clan). Check if
     groupId 5421866 appears.

Bungie API docs:
  https://bungie-net.github.io/multi/operation_get_User-GetMembershipsById.html
  https://bungie-net.github.io/multi/operation_get_GroupV2-GetGroupsForMember.html
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

import httpx

log = logging.getLogger("darth-bot.bungie_clan")

BUNGIE_API_BASE = "https://www.bungie.net/Platform"
ORDER_66_GROUP_ID = int(os.environ.get("BUNGIE_CLAN_GROUP_ID", "5421866"))
BUNGIE_API_KEY = os.environ.get("BUNGIE_API_KEY", "")
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:8080")

# Membership type 254 = Bungie.net account (the universal one).
BUNGIE_NET_MEMBERSHIP_TYPE = 254


class ClanCheckError(Exception):
    """Raised when the clan check can't be completed (API error, not linked, etc.)."""


class NotLinkedError(ClanCheckError):
    """Raised when the user has not run /link-bungie yet."""


async def lookup_bungie_id(discord_id: str) -> dict:
    """Resolve a Discord user ID to their stored Bungie account info via
    the backend. Returns the link dict {discord_id, bungie_id, display_name, linked_at}."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BACKEND_BASE_URL}/link/discord/{discord_id}")
        if r.status_code == 404:
            raise NotLinkedError(
                "You haven't linked your Bungie account yet. Run `/link-bungie` first."
            )
        r.raise_for_status()
        return r.json()


async def get_destiny_memberships(bungie_id: str) -> List[dict]:
    """Bungie API: /User/GetMembershipsById/{id}/254/ → returns the user's
    destinyMemberships array (one entry per platform they play on)."""
    if not BUNGIE_API_KEY:
        raise ClanCheckError("BUNGIE_API_KEY not set in env")

    url = f"{BUNGIE_API_BASE}/User/GetMembershipsById/{bungie_id}/{BUNGIE_NET_MEMBERSHIP_TYPE}/"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers={"X-API-Key": BUNGIE_API_KEY})
    if r.status_code != 200:
        raise ClanCheckError(f"Bungie API GetMembershipsById HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if data.get("ErrorCode") != 1:
        raise ClanCheckError(f"Bungie API error: {data.get('Message', 'unknown')}")
    return data["Response"].get("destinyMemberships", [])


async def get_groups_for_member(membership_type: int, membership_id: str) -> List[dict]:
    """Bungie API: /GroupV2/User/{type}/{id}/0/1/ → returns the groups
    (clans) that this Destiny membership belongs to. Filter=0 means all
    states; groupType=1 means clans (not generic groups)."""
    if not BUNGIE_API_KEY:
        raise ClanCheckError("BUNGIE_API_KEY not set in env")

    url = f"{BUNGIE_API_BASE}/GroupV2/User/{membership_type}/{membership_id}/0/1/"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers={"X-API-Key": BUNGIE_API_KEY})
    if r.status_code != 200:
        raise ClanCheckError(f"Bungie API GetGroupsForMember HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    if data.get("ErrorCode") != 1:
        raise ClanCheckError(f"Bungie API error: {data.get('Message', 'unknown')}")
    return data["Response"].get("results", [])


async def is_in_order_66(bungie_id: str) -> tuple[bool, Optional[str]]:
    """Top-level check: is this Bungie.net account in the Order 66 clan
    on any of their Destiny platforms? Returns (in_clan, display_name)."""
    memberships = await get_destiny_memberships(bungie_id)
    if not memberships:
        return False, None

    display_name = None
    for m in memberships:
        if not display_name:
            display_name = m.get("bungieGlobalDisplayName") or m.get("displayName")
        groups = await get_groups_for_member(m["membershipType"], m["membershipId"])
        for g in groups:
            gid = int(g.get("group", {}).get("groupId", 0))
            if gid == ORDER_66_GROUP_ID:
                return True, display_name
    return False, display_name


async def check_clan_membership(discord_id: str) -> dict:
    """Full /verify-clan logic: lookup link → check clan membership →
    return a dict the slash command renders.

    Returns: {
        "in_clan": bool,
        "bungie_id": str,
        "display_name": str | None,
        "error": str | None,
    }
    """
    try:
        link = await lookup_bungie_id(discord_id)
    except NotLinkedError as e:
        return {"in_clan": False, "bungie_id": None, "display_name": None, "error": str(e)}
    except httpx.HTTPError as e:
        return {"in_clan": False, "bungie_id": None, "display_name": None,
                "error": f"backend unreachable: {e}"}

    bungie_id = link["bungie_id"]
    try:
        in_clan, display_name = await is_in_order_66(bungie_id)
    except ClanCheckError as e:
        return {"in_clan": False, "bungie_id": bungie_id,
                "display_name": link.get("display_name"), "error": str(e)}

    return {
        "in_clan": in_clan,
        "bungie_id": bungie_id,
        "display_name": display_name or link.get("display_name"),
        "error": None,
    }
