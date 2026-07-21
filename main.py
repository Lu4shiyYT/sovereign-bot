import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
from database import init_db

TOKEN = os.environ['DISCORD_TOKEN']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} запущен!')
    init_db()
    await bot.load_extension('cogs.admin')
    await bot.load_extension('cogs.game')
    await bot.load_extension('cogs.war')
    print('Cogs загружены.')

keep_alive()
bot.run(TOKEN)