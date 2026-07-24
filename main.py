import discord
from discord.ext import commands, tasks
import os
from config import BATTLE_ROUND_INTERVAL_MINUTES
from keep_alive import keep_alive
from database import init_db, async_fetch_all, async_execute, async_get_game_date
import datetime
import time

# Токен читается из переменной окружения (безопасно)
TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("ОШИБКА: не установлена переменная окружения DISCORD_TOKEN!")
    exit(1)

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
    if not battle_loop.is_running():
        battle_loop.start()

# --- Фоновая задача: месячный доход (каждые 2 часа = 1 игровой месяц) ---
@tasks.loop(hours=2)
async def monthly_income():
    print("Начисление месячного дохода...")
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

    # --- ОБНОВЛЕНИЕ ИГРОВОЙ ДАТЫ И НАЗВАНИЯ КАНАЛА (ПОСЛЕ ЦИКЛА) ---
    game_date = await async_get_game_date()
    next_date = game_date + datetime.timedelta(days=1)
    await async_execute("UPDATE game_date SET day=?, month=?, year=? WHERE id=1",
                        (next_date.day, next_date.month, next_date.year))

    voice_channel_id = 1529236474896322583   # твой ID голосового канала
    channel = bot.get_channel(voice_channel_id)
    if channel and isinstance(channel, discord.VoiceChannel):
        try:
            await channel.edit(name=f"📅 {next_date.strftime('%d.%m.%Y')}")
        except Exception as e:
            print(f"Не удалось изменить название канала: {e}")

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    await bot.tree.sync()
    await ctx.send("Команды синхронизированы.")

# Боевой цикл
@tasks.loop(minutes=BATTLE_ROUND_INTERVAL_MINUTES)
async def battle_loop():
    active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
    for war in active_wars:
        battle = await async_fetch_one("SELECT last_battle_time FROM war_battles WHERE war_id=?", (war['id'],))
        now = time.time()
        if battle and (now - battle['last_battle_time']) < BATTLE_ROUND_INTERVAL_MINUTES * 60:
            continue
        attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['attacker_id'],))
        defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['defender_id'],))
        if not attacker or not defender:
            continue
        atk_power = attacker['army_count'] * (attacker['combat_capability'] / 100)
        def_power = defender['army_count'] * (defender['combat_capability'] / 100)
        def_loss = min(defender['army_count'], int(atk_power * 0.1))
        atk_loss = min(attacker['army_count'], int(def_power * 0.08))
        await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (atk_loss, attacker['id']))
        await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (def_loss, defender['id']))
        if battle:
            await async_execute("UPDATE war_battles SET last_battle_time=? WHERE war_id=?", (now, war['id']))
        else:
            await async_execute("INSERT INTO war_battles (war_id, last_battle_time) VALUES (?, ?)", (war['id'], now))
        if attacker['army_count'] <= 0 or defender['army_count'] <= 0:
            await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
            # опционально: сообщение в канал war_reports о завершении войны

# --- Запуск ---
keep_alive()
bot.run(TOKEN)
