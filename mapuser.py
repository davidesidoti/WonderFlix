from discord.ext import commands
from discord import app_commands, Interaction
import json, os
from dotenv import load_dotenv

load_dotenv()

USER_MAP_PATH = os.getenv("USER_MAP_PATH", "user_mapping.json")

class MapUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mapuser", description="Mappa un utente Jellyfin/Jellyseerr a un utente Discord")
    @app_commands.checks.has_permissions(administrator=True)
    async def mapuser(self, interaction: Interaction,
                      jelly_user: str,
                      discord_user: str):
        try:
            discord_id = int(discord_user.strip('<@!>'))
        except Exception:
            await interaction.response.send_message("❌ Formato ID utente Discord non valido.", ephemeral=True)
            return

        try:
            with open(USER_MAP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"users": []}

        jelly_user_lower = jelly_user.lower()
        existing = [u for u in data["users"] if jelly_user_lower in (u.get("jellyseerr", "").lower(), u.get("jellyfin", "").lower())]

        if existing:
            await interaction.response.send_message(f"⚠️ Utente `{jelly_user}` già mappato.", ephemeral=True)
            return

        data["users"].append({
            "discord_id": discord_id,
            "jellyseerr": jelly_user,
            "jellyfin": jelly_user
        })

        try:
            with open(USER_MAP_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            await interaction.response.send_message(f"✅ Utente `{jelly_user}` mappato con successo a <@{discord_id}>.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Errore durante il salvataggio della mappatura.", ephemeral=True)

    @app_commands.command(name="unmapuser", description="Rimuove un utente Jellyfin/Jellyseerr dalla mappatura")
    @app_commands.checks.has_permissions(administrator=True)
    async def unmapuser(self, interaction: Interaction, jelly_user: str):
        jelly_user_lower = jelly_user.lower()

        try:
            with open(USER_MAP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            await interaction.response.send_message("❌ Errore nel caricamento del file di mappatura.", ephemeral=True)
            return

        old_count = len(data.get("users", []))
        data["users"] = [u for u in data.get("users", [])
                          if jelly_user_lower not in (u.get("jellyseerr", "").lower(), u.get("jellyfin", "").lower())]
        new_count = len(data["users"])

        if new_count == old_count:
            await interaction.response.send_message(f"⚠️ Nessun utente trovato con nome `{jelly_user}`.", ephemeral=True)
            return

        try:
            with open(USER_MAP_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            await interaction.response.send_message(f"✅ Utente `{jelly_user}` rimosso dalla mappatura.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Errore durante il salvataggio della mappatura.", ephemeral=True)

    @app_commands.command(name="listmapped", description="Mostra tutti gli utenti mappati")
    @app_commands.checks.has_permissions(administrator=True)
    async def listmapped(self, interaction: Interaction):
        try:
            with open(USER_MAP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            await interaction.response.send_message("❌ Errore nel caricamento della mappatura.", ephemeral=True)
            return

        users = data.get("users", [])
        if not users:
            await interaction.response.send_message("⚠️ Nessun utente mappato.", ephemeral=True)
            return

        rows = []
        for u in users:
            row = f"• `{u.get('jellyfin', u.get('jellyseerr'))}` → <@{u['discord_id']}>"
            rows.append(row)

        text = "\n".join(rows)
        await interaction.response.send_message(f"**📄 Utenti mappati:**\n{text}", ephemeral=True)

    @app_commands.command(name="getmap", description="Mostra la mappatura di un utente Jellyfin o di un tag Discord")
    @app_commands.checks.has_permissions(administrator=True)
    async def getmap(self, interaction: Interaction, user: str):
        query = user.lower().strip("<@!>")

        try:
            with open(USER_MAP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            await interaction.response.send_message("❌ Errore nel caricamento della mappatura.", ephemeral=True)
            return

        # Ricerca per nome Jellyfin/Jellyseerr
        for u in data.get("users", []):
            if query in (u.get("jellyseerr", "").lower(), u.get("jellyfin", "").lower()):
                tag = f"<@{u['discord_id']}>"
                await interaction.response.send_message(f"🔎 `{user}` → {tag}", ephemeral=True)
                return

        # Ricerca per ID Discord
        try:
            id_int = int(query)
            for u in data.get("users", []):
                if u.get("discord_id") == id_int:
                    jelly_name = u.get("jellyfin") or u.get("jellyseerr")
                    await interaction.response.send_message(f"🔎 <@{id_int}> → `{jelly_name}`", ephemeral=True)
                    return
        except ValueError:
            pass

        await interaction.response.send_message(f"⚠️ Nessuna mappatura trovata per `{user}`.", ephemeral=True)



async def setup(bot):
    await bot.add_cog(MapUser(bot))
