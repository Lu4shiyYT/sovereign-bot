import discord
from discord.ext import commands, tasks
import os
import asyncio
from keep_alive import keep_alive
from database import init_db, async_fetch_all, async_execute
from data.buildings import BUILDING_TYPES

TOKEN = os.environ['DISCORD_TOKEN']

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Фоновая задача для месячного дохода (каждые 2 часа)
@tasks.loop(hours=2)
async def monthly_income_loop():
    print("Начисление месячного дохода...")
    rows = await async_fetch_all(
        "SELECT country_id, building_type, level FROM buildings WHERE build_end_time = 0 AND level > 0"
    )
    if not rows:
        print("Нет активных построек.")
        return
    income = {}
    for row in rows:
        cid = row['country_id']
        btype = row['building_type']
        level = row['level']
        produces = BUILDING_TYPES.get(btype, {}).get('produces', {})
        for res, base in produces.items():
            total = base * level
            income[(cid, res)] = income.get((cid, res), 0) + total
    for (cid, res), amount in income.items():
        await async_execute(
            "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) "
            "ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
            (cid, res, amount, amount)
        )
    print(f"Доход начислен: {len(income)} записей.")

@bot.event
async def on_ready():
    print(f'{bot.user} запущен!')
    init_db()
    # Загружаем только нужные расширения (war не загружаем!)
    await bot.load_extension('cogs.admin')
    await bot.load_extension('cogs.game')
    print('Cogs загружены.')

    # Синхронизация слеш-команд
    try:
        synced = await bot.tree.sync()
        print(f'Синхронизировано {len(synced)} команд.')
    except Exception as e:
        print(f'Ошибка синхронизации: {e}')

    # Запускаем месячный доход, если ещё не запущен
    if not monthly_income_loop.is_running():
        monthly_income_loop.start()

keep_alive()
bot.run(TOKEN)
