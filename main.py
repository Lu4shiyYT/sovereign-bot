import discord
from discord.ext import commands, tasks
import os
from data.buildings import BUILDING_TYPES
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

# ---------- Загрузка когов ----------
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

@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!", flush=True)
    init_db()
    await load_cogs()
    await bot.tree.sync()
    print("Синхронизация команд выполнена.", flush=True)
    if not monthly_income.is_running():
        monthly_income.start()
    if not weather_update_loop.is_running():
        weather_update_loop.start()

# ---------- Месячный доход ----------
@tasks.loop(hours=2)
async def monthly_income():
    from database import async_fetch_all, async_execute, async_get_game_date
    import datetime
    print("Начисление месячного дохода...")
    countries = await async_fetch_all("SELECT * FROM countries WHERE owner_id IS NOT NULL")
    for c in countries:
        income_money = 0
        income_resources = {}
        buildings = await async_fetch_all(
            "SELECT building_type, level FROM buildings WHERE country_id=? AND build_end_time=0 AND level>0",
            (c['id'],)
        )
        for b in buildings:
            lvl = b['level']
            if b['building_type'] == "Ферма":
                income_resources["Продовольствие"] = income_resources.get("Продовольствие", 0) + 100 * lvl
            elif b['building_type'] == "Шахта":
                income_resources["Нефть"] = income_resources.get("Нефть", 0) + 50 * lvl
            elif b['building_type'] == "Бизнес-центр":
                income_money += 200 * lvl

        # Доход от всех завершённых построек страны
        all_buildings = await async_fetch_all(
            "SELECT * FROM buildings WHERE country_id=? AND status='completed'",
            (c['id'],)
        )
        for b in all_buildings:
            btype = BUILDING_TYPES.get(b['building_type'])
            if not btype:
                continue
            level = b['level']
            mult = btype['upgrade_multiplier'] ** level
            # Ресурсы
            for res, base in btype.get('resource_production', {}).items():
                produced = int(base * mult)
                # Проверяем, есть ли ещё ресурс в провинции
                prov_res = await async_fetch_one(
                    "SELECT amount FROM province_resources WHERE province_id=? AND resource_name=?",
                    (b['province_id'], res)
                )
                if prov_res and prov_res['amount'] > 0:
                    mined = min(produced, prov_res['amount'])
                    await async_execute(
                        "UPDATE province_resources SET amount = amount - ? WHERE province_id=? AND resource_name=?",
                        (mined, b['province_id'], res)
                    )
                    await async_execute(
                        "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                        (c['id'], res, mined, mined)
                    )
            # Деньги
            if btype.get('money_production'):
                income_money += int(btype['money_production'] * mult)
        
        if c['mobilization']:
            income_money = int(income_money * 0.5)
            for res in income_resources:
                income_resources[res] = int(income_resources[res] * 0.5)

        # Начисление денег в бюджет
        if income_money > 0:
            await async_execute("UPDATE countries SET budget = budget + ? WHERE id = ?", (income_money, c['id']))
        # Начисление ресурсов
        for res_name, amount in income_resources.items():
            if amount > 0:
                await async_execute(
                    "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                    (c['id'], res_name, amount, amount)
                )

        # Содержание армии
        army_count = c['army_count']
        upkeep_money = int(army_count * 0.1)
        upkeep_food = int(army_count * 0.05)
        if upkeep_money > 0:
            await async_execute("UPDATE countries SET budget = budget - ? WHERE id = ?", (upkeep_money, c['id']))
        if upkeep_food > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'", (upkeep_food, c['id']))

        # Потребление продовольствия населением
        population = c['population']
        food_consumption = int(population * 0.001)
        if food_consumption > 0:
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'", (food_consumption, c['id']))

        # Прирост населения
        growth_rate_year = c['demographic_growth'] / 100.0
        growth_per_month = int(population * growth_rate_year / 12)
        if growth_per_month > 0:
            new_population = population + growth_per_month
            await async_execute("UPDATE countries SET population = ? WHERE id=?", (new_population, c['id']))

        # Личное сообщение владельцу
        user = bot.get_user(c['owner_id'])
        if user:
            try:
                await user.send(
                    f"**Месячный отчёт для {c['display_name'] or c['name']}**\n"
                    f"Доход: Доллары +{income_money}\n"
                    f"Ресурсы: " + ", ".join(f"{r} +{v}" for r, v in income_resources.items()) + "\n"
                    f"Содержание армии: -{upkeep_money}$ и -{upkeep_food} прод.\n"
                    f"Потребление продовольствия населением: -{food_consumption}\n"
                    f"Прирост населения: +{growth_per_month} чел.\n"
                )
            except:
                pass

    # --- ОБНОВЛЕНИЕ ИГРОВОЙ ДАТЫ И НАЗВАНИЯ КАНАЛА ---
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
            print(f"Не удалось изменить название канала: {e}")

# ---------- Цикл обновления погоды (каждые 8 часов) ----------
@tasks.loop(hours=8)
async def weather_update_loop():
    war_cog = bot.get_cog("War")
    if war_cog:
        await war_cog._update_weather()
@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    await bot.tree.sync()
    await ctx.send("Команды синхронизированы.")

keep_alive()
bot.run(TOKEN)
