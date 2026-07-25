import discord
from discord.ext import commands, tasks
import os
import sys
from keep_alive import keep_alive
from database import init_db

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("ОШИБКА: не установлена переменная окружения DISCORD_TOKEN!")
    exit(1)

PREFIX = "/"
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- Загрузка когов (выполняется сразу, до запуска бота) ---
async def load_cogs():
    modules = [
        ("cogs.war", "War"),
        ("cogs.admin", "Admin"),
        ("cogs.game", "Game")
    ]
    for path, name in modules:
        try:
            await bot.load_extension(path)
            print(f"✅ {name} loaded", flush=True)
        except Exception as e:
            print(f"❌ Failed to load {name} ({path}): {e}", flush=True)

    # Сохраняем ссылку на War
    bot.war_cog = bot.get_cog("War")
    if bot.war_cog:
        print("✅ bot.war_cog установлен", flush=True)
    else:
        print("⚠️ bot.war_cog = None после загрузки", flush=True)

# Вызываем загрузку прямо здесь, до bot.run
import asyncio
asyncio.get_event_loop().run_until_complete(load_cogs())

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!", flush=True)
    init_db()
    await bot.tree.sync()
    print("Синхронизация команд выполнена.", flush=True)
    if not monthly_income.is_running():
        monthly_income.start()

# --- Месячный доход ---
@tasks.loop(hours=2)
async def monthly_income():
    from database import async_fetch_all, async_execute, async_get_game_date
    import datetime
    print("Начисление месячного дохода...", flush=True)
    countries = await async_fetch_all("SELECT * FROM countries WHERE owner_id IS NOT NULL")
    for c in countries:
        income = {"Доллары": 0, "Продовольствие": 0, "Нефть": 0}
        buildings = await async_fetch_all(
            "SELECT building_type, level FROM buildings WHERE country_id=? AND build_end_time=0 AND level>0",
            (c['id'],)
        )
        for b in buildings:
            lvl = b['level']
            if b['building_type'] == "Ферма":
                income["Продовольствие"] += 100 * lvl
            elif b['building_type'] == "Шахта":
                income["Нефть"] += 50 * lvl
            elif b['building_type'] == "Бизнес-центр":
                income["Доллары"] += 200 * lvl
        if c['mobilization']:
            for res in income:
                income[res] = int(income[res] * 0.5)
        for res_name, amount in income.items():
            if amount > 0:
                await async_execute(
                    "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                    (c['id'], res_name, amount, amount)
                )
        army_count = c['army_count']
        upkeep_money = int(army_count * 0.1)
        upkeep_food = int(army_count * 0.05)
        if upkeep_money > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Доллары'", (upkeep_money, c['id']))
        if upkeep_food > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'", (upkeep_food, c['id']))
        population = c['population']
        food_consumption = int(population * 0.001)
        if food_consumption > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'", (food_consumption, c['id']))
        growth_rate_year = c['demographic_growth'] / 100.0
        growth_per_month = int(population * growth_rate_year / 12)
        if growth_per_month > 0:
            new_population = population + growth_per_month
            await async_execute("UPDATE countries SET population = ? WHERE id=?", (new_population, c['id']))
        user = bot.get_user(c['owner_id'])
        if user:
            try:
                await user.send(
                    f"**Месячный отчёт для {c['display_name'] or c['name']}**\n"
                    f"Доход: Доллары +{income['Доллары']}, Продовольствие +{income['Продовольствие']}, Нефть +{income['Нефть']}\n"
                    f"Содержание армии: -{upkeep_money}$ и -{upkeep_food} прод.\n"
                    f"Потребление продовольствия населением: -{food_consumption}\n"
                    f"Прирост населения: +{growth_per_month} чел.\n"
                )
            except:
                pass

    game_date = await async_get_game_date()
    next_date = game_date + datetime.timedelta(days=1)
    await async_execute("UPDATE game_date SET day=?, month=?, year=? WHERE id=1",
                        (next_date.day, next_date.month, next_date.year))
    voice_channel_id = 1529236474896322583
    channel = bot.get_channel(voice_channel_id)
    if channel and isinstance(channel, discord.VoiceChannel):
        try:
            await channel.edit(name=f"📅 {next_date.strftime('%d.%m.%Y')}")
        except Exception as e:
            print(f"Не удалось изменить название канала: {e}", flush=True)

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    await bot.tree.sync()
    await ctx.send("Команды синхронизированы.")

keep_alive()
bot.run(TOKEN)
