import discord
from discord.ext import commands, tasks
import asyncio
from keep_alive import keep_alive
from database import init_db, async_fetch_all, async_execute
from config import CHANNEL_NAME  # Убедитесь, что config.py содержит нужные константы, или замените на свои
import datetime

# --- Настройки ---
TOKEN = "YOUR_TOKEN"  # Замените на ваш токен
PREFIX = "/"          # Для slash-команд не обязательно

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
    # Запуск фоновой задачи (если не запущена)
    if not monthly_income.is_running():
        monthly_income.start()

# --- Фоновая задача: месячный доход (каждые 2 часа = 1 игровой месяц) ---
@tasks.loop(hours=2)
async def monthly_income():
    print("Начисление месячного дохода...")
    # Получаем все страны, у которых есть владелец
    countries = await async_fetch_all("SELECT * FROM countries WHERE owner_id IS NOT NULL")
    for c in countries:
        # 1. Доход от построек
        buildings = await async_fetch_all(
            "SELECT building_type, level FROM buildings WHERE country_id=? AND build_end_time=0 AND level>0",
            (c['id'],)
        )
        income = {"Доллары": 0, "Продовольствие": 0, "Нефть": 0}
        for b in buildings:
            btype = b['building_type']
            level = b['level']
            # Данные о производстве берутся из BUILDING_TYPES, например:
            # Ферма: продовольствие, Шахта: ресурсы, Бизнес-центр: доллары и т.д.
            # В этом примере просто заглушка, нужно синхронизировать с data/buildings.py
            # Предположим, что Ферма дает продовольствие, Шахта — нефть, Бизнес-центр — доллары.
            # Подставьте реальные данные из вашего BUILDING_TYPES.
            if btype == "Ферма":
                income["Продовольствие"] += 100 * level
            elif btype == "Шахта":
                income["Нефть"] += 50 * level
            elif btype == "Бизнес-центр":
                income["Доллары"] += 200 * level
            # ... другие типы построек

        # Применяем модификатор мобилизации: доход снижается вдвое
        if c['mobilization']:
            for res in income:
                income[res] = int(income[res] * 0.5)

        # Начисляем ресурсы
        for res_name, amount in income.items():
            if amount > 0:
                await async_execute(
                    "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                    (c['id'], res_name, amount, amount)
                )

        # 2. Расход на содержание армии
        army_count = c['army_count']
        if army_count > 0:
            upkeep_money = int(army_count * 0.1)   # 0.1 доллара в месяц за солдата
            upkeep_food = int(army_count * 0.05)  # 0.05 продовольствия
            # Списание денег
            await async_execute(
                "UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Доллары'",
                (upkeep_money, c['id'])
            )
            # Списание продовольствия
            await async_execute(
                "UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'",
                (upkeep_food, c['id'])
            )

        # 3. Потребление продовольствия населением
        population = c['population']
        food_consumption = int(population * 0.001)  # 1 единица на 1000 жителей
        await async_execute(
            "UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'",
            (food_consumption, c['id'])
        )

        # 4. Прирост населения
        growth_rate_year = c['demographic_growth'] / 100.0
        growth_per_month = int(population * growth_rate_year / 12)
        if growth_per_month > 0:
            new_population = population + growth_per_month
            await async_execute("UPDATE countries SET population = ? WHERE id=?", (new_population, c['id']))

        # Уведомление игроку о доходах/расходах (можно отправить краткий отчёт в ЛС)
        user = bot.get_user(c['owner_id'])
        if user:
            try:
                report = (
                    f"**Месячный отчёт для {c['display_name'] or c['name']}**\n"
                    f"Доход: {income}\n"
                    f"Содержание армии: -{upkeep_money}$ и -{upkeep_food} прод.\n"
                    f"Потребление продовольствия населением: -{food_consumption}\n"
                    f"Прирост населения: +{growth_per_month} чел.\n"
                )
                await user.send(report)
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
