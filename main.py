import os, logging, discord
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
    embed = Embed(title="WonderFlix", description="Bot operational 🚀", color=0x00ff00)
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot.run(TOKEN)
