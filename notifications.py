import os
import json
import logging
import aiohttp
import textwrap
from typing import Tuple, Optional, Dict
from aiohttp import web
from discord.ext import commands
from discord import Embed
from dotenv import load_dotenv

"""
WonderFlix – Notifications Cog (extension)
=========================================

* Toggle `LOG_LEVEL=DEBUG` to enable deep diagnostics (look for **Tag debug:** lines).
* Mentions mapped Discord users or shows requester username.
* Works with default Jellyfin payloads **and** custom Handlebars template.
* Uses Jellyseerr `/request` list endpoint to resolve requester (no direct tmdbId query).
* English‑only embeds. Brand colour `#cfa146`.
"""

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration variables
# ---------------------------------------------------------------------------

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
NOTIFY_CHANNEL_ID: int = int(os.getenv("NOTIFY_CHANNEL_ID", 0))
TMDB_API_KEY: Optional[str] = os.getenv("TMDB_API_KEY")
JELLYSEERR_URL: str = os.getenv("JELLYSEERR_URL", "").rstrip("/")
JELLYSEERR_API_KEY: Optional[str] = os.getenv("JELLYSEERR_API_KEY")
USER_MAP_PATH: str = os.getenv("USER_MAP_PATH", "user_mapping.json")
WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "127.0.0.1")
WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", 8921))
TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p/w500"
BRAND_COLOR: int = 0xCFA146

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------------------------------------------------------
# Mapping loader
# ---------------------------------------------------------------------------

def load_user_mapping(path: str = USER_MAP_PATH) -> Dict[str, int]:
    """Return dict {lower_username: discord_id}."""
    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        mapping: Dict[str, int] = {}
        for u in data.get("users", []):
            for key in (u.get("jellyseerr"), u.get("jellyfin")):
                if key:
                    mapping[str(key).lower()] = int(u["discord_id"])
        logging.info("Loaded %d user mappings: %s", len(mapping), list(mapping.keys()))
        return mapping
    except FileNotFoundError:
        logging.warning("Mapping file %s not found – mentions disabled", path)
        return {}
    except Exception:
        logging.exception("Failed to parse mapping file")
        return {}

# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class Notifications(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_map = load_user_mapping()
        self.aiohttp_session: Optional[aiohttp.ClientSession] = None
        self.web_runner: Optional[web.AppRunner] = None

    # ---------------- Discord events ----------------
    @commands.Cog.listener()
    async def on_ready(self):
        if self.aiohttp_session is None:
            self.aiohttp_session = aiohttp.ClientSession()
            await self._start_webhook_server()
            logging.info("✅ Notifications ready – listening on %s:%d", WEBHOOK_HOST, WEBHOOK_PORT)

    # ---------------- Webhook server ----------------
    async def _start_webhook_server(self):
        app = web.Application()
        app.router.add_post("/jellyfin-webhook", self.jellyfin_webhook)
        self.web_runner = web.AppRunner(app)
        await self.web_runner.setup()
        await web.TCPSite(self.web_runner, WEBHOOK_HOST, WEBHOOK_PORT).start()

    async def jellyfin_webhook(self, request: web.Request):
        try:
            payload = await request.json()
        except Exception:
            logging.warning("Invalid JSON payload from Jellyfin")
            return web.Response(status=400)

        if payload.get("Event") not in {"ItemAdded", "Library.New"}:
            return web.Response(text="Ignored")

        item = payload.get("Item", {})
        user_field = payload.get("User", {})
        jelly_user = user_field.lower() if isinstance(user_field, str) else str(user_field.get("Name", "")).lower()

        title = item.get("Name")
        media_type = item.get("Type")
        tmdb_id = (
            item.get("ProviderIds", {}).get("Tmdb")
            or item.get("Tmdb")
            or item.get("Provider_tmdb")
        )

        await self._process_new_item(title, media_type, tmdb_id, jelly_user)
        return web.Response(text="OK")

    # ---------------- Core logic ----------------
    async def _process_new_item(self, title: str, media_type: str, tmdb_id: Optional[str], jelly_user: str):
        tag_user_id = self.user_map.get(jelly_user)
        js_username = ""

        logging.info("Tag debug: initial jelly_user='%s' tag_user_id=%s", jelly_user, tag_user_id)

        if tmdb_id:
            js_uid, js_username = await self._lookup_jellyseerr_requester(tmdb_id)
            logging.info("Tag debug: Jellyseerr username='%s' js_uid=%s", js_username, js_uid)
            tag_user_id = js_uid or tag_user_id
            if not jelly_user:
                jelly_user = js_username

        logging.info("Tag debug: resolved tag_user_id=%s jelly_user='%s'", tag_user_id, jelly_user)

        overview = poster_url = None
        if tmdb_id and TMDB_API_KEY:
            overview, poster_url = await self._fetch_tmdb(tmdb_id, media_type)

        embed = Embed(
            title="🎬 New media available!",
            description=f"**{title}** was added to the library.",
            colour=BRAND_COLOR,
        )
        embed.add_field(name="Type", value=media_type or "N/A", inline=True)
        embed.add_field(name="Requested by", value=f"<@{tag_user_id}>" if tag_user_id else (jelly_user or js_username or "Unknown"), inline=True)
        if overview:
            embed.add_field(name="Overview", value=textwrap.shorten(overview, width=300, placeholder="…"), inline=False)
        if poster_url:
            embed.set_thumbnail(url=poster_url)

        channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
        if channel:
            try:
                await channel.send(embed=embed)
                logging.info("Embed sent to channel %s for '%s'", NOTIFY_CHANNEL_ID, title)
            except Exception:
                logging.exception("Discord API error while sending embed")
        else:
            logging.error("Channel ID %s not found", NOTIFY_CHANNEL_ID)

    # ---------------- Helper methods ----------------
    async def _fetch_tmdb(self, tmdb_id: str, media_type: str) -> Tuple[Optional[str], Optional[str]]:
        endpoint = "movie" if (media_type or "").lower() == "movie" else "tv"
        url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}?language=en-US&api_key={TMDB_API_KEY}"
        try:
            async with self.aiohttp_session.get(url) as r:
                if r.status != 200:
                    logging.info("TMDb %s lookup failed: %s", r.status, url)
                    return None, None
                data = await r.json()
        except Exception:
            logging.info("TMDb request exception")
            return None, None
        return data.get("overview"), (f"{TMDB_IMAGE_BASE}{data.get('poster_path')}" if data.get("poster_path") else None)

    async def _lookup_jellyseerr_requester(self, tmdb_id: str) -> Tuple[Optional[int], str]:
        """Fetch latest requests and find the one matching given tmdbId."""
        if not (JELLYSEERR_URL and JELLYSEERR_API_KEY):
            return None, ""

        url = (
            f"{JELLYSEERR_URL}/api/v1/request?take=20&skip=0&sort=added&sortDirection=desc&mediaType=all"
        )
        headers = {"X-Api-Key": JELLYSEERR_API_KEY}

        try:
            async with self.aiohttp_session.get(url, headers=headers) as r:
                if r.status != 200:
                    logging.info("Jellyseerr list %s", r.status)
                    return None, ""
                data = await r.json()
        except Exception:
            logging.info("Jellyseerr request list exception")
            return None, ""

        for req in data.get("results", []):
            media = req.get("media", {}) or {}
            if int(media.get("tmdbId", 0)) == int(tmdb_id):
                requester = req.get("requestedBy", {}) or {}
                raw_username = str(
                    requester.get("username")
                    or requester.get("plexUsername")
                    or requester.get("displayName")
                    or ""
                ).lower()
                discord_id = self.user_map.get(raw_username)
                logging.info(
                    "Tag debug: matched tmdbId %s with raw_username='%s' → discord_id=%s",
                    tmdb_id,
                    raw_username,
                    discord_id,
                )
                return discord_id, raw_username

        logging.info("Tag debug: no request found for tmdbId=%s in latest 20", tmdb_id)
        return None, ""

# ---------------------------------------------------------------------------
# Entry‑point
# ---------------------------------------------------------------------------

async def setup(bot: commands.Bot):
    await bot.add_cog(Notifications(bot))
