import os, logging, discord, asyncio, logging
from discord.ext import commands
from discord import app_commands, Embed
from dotenv import load_dotenv

load_dotenv()  # carica .env

TOKEN  = os.getenv("DISCORD_TOKEN")
APP_ID = int(os.getenv("DISCORD_APP_ID", 0))

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents, application_id=APP_ID)

@bot.event
async def on_ready():
    logging.info(f"✅ Logged in as {bot.user} (id={bot.user.id})")
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logging.exception("Slash-sync failed")

@bot.tree.command(name="ping", description="Latency test")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

@bot.tree.command(name="info", description="WonderFlix service status")
async def info(interaction: discord.Interaction):
    embed = Embed(title="WonderFlix", description="Bot operational 🚀", color=0xcfa146)
    await interaction.response.send_message(embed=embed)

async def main():
    # carica l’extension notifications.py
    await bot.load_extension("notifications")        # stesso path del file
    await bot.load_extension("mapuser")
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(main())