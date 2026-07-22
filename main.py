import discord
from discord.ext import commands, tasks
import asyncio
from keep_alive import keep_alive
from database import init_db, async_fetch_all, async_execute
import datetime

# --- Настройки ---
TOKEN = "MTUyOTIzNTQ0MDgxNTgzNzIxNQ.GuA9-m.yGTCujy8y5cuu8S4lx2AvMGQrMSMFtg43aGOXg"  # Замените на ваш реальный токен
PREFIX = "/"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- Загрузка модулей ---
async def load_cogs():
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.game")

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    init_db()
    await load_cogs()
    await bot.tree.sync()
    print("Синхронизация команд выполнена.")
    if not monthly_income.is_running():
        monthly_income.start()

# --- Фоновая задача: месячный доход (каждые 2 часа = 1 игровой месяц) ---
@tasks.loop(hours=2)
async def monthly_income():
    print("Начисление месячного дохода...")
    countries = await async_fetch_all("SELECT * FROM countries WHERE owner_id IS NOT NULL")
    for c in countries:
        # 1. Доход от построек (упрощённо, синхронизируй с BUILDING_TYPES при необходимости)
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
            # ... другие типы построек, если есть

        # Модификатор мобилизации: доход снижается вдвое
        if c['mobilization']:
            for res in income:
                income[res] = int(income[res] * 0.5)

        for res_name, amount in income.items():
            if amount > 0:
                await async_execute(
                    "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                    (c['id'], res_name, amount, amount)
                )

        # 2. Расход на содержание армии
        army_count = c['army_count']
        upkeep_money = int(army_count * 0.1)
        upkeep_food = int(army_count * 0.05)
        if upkeep_money > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Доллары'", (upkeep_money, c['id']))
        if upkeep_food > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'", (upkeep_food, c['id']))

        # 3. Потребление продовольствия населением
        population = c['population']
        food_consumption = int(population * 0.001)
        if food_consumption > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'", (food_consumption, c['id']))

        # 4. Прирост населения
        growth_rate_year = c['demographic_growth'] / 100.0
        growth_per_month = int(population * growth_rate_year / 12)
        if growth_per_month > 0:
            new_population = population + growth_per_month
            await async_execute("UPDATE countries SET population = ? WHERE id=?", (new_population, c['id']))

        # Уведомление игроку
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

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    await bot.tree.sync()
    await ctx.send("Команды синхронизированы.")

# --- Запуск ---
keep_alive()
bot.run(TOKEN)
