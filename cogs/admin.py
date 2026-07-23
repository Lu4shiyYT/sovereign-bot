import discord
from discord.ext import commands
from discord import app_commands
from database import get_conn, init_db, async_fetch_one, async_execute
from data.countries import initial_countries, initial_provinces
import os
import asyncio

DB_PATH = "sovereign.db"

# Доступные ресурсы (тот же список)
RESOURCE_NAMES = [
    "Доллары", "Нефть", "Природный газ", "Уголь", "Железная руда",
    "Продовольствие", "Древесина", "Пресная вода"
]

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def resource_autocomplete(self, interaction: discord.Interaction, current: str):
        choices = [res for res in RESOURCE_NAMES if current.lower() in res.lower()]
        return [app_commands.Choice(name=res, value=res) for res in choices]

    def _init_game_sync(self):
        conn = get_conn()
        cur = conn.cursor()
        tables = ["wars", "alliance_members", "alliances", "sanctions", "pacts",
                  "resources", "buildings", "provinces", "technologies", "countries",
                  "mobilize_cooldowns", "market"]
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        conn.close()

        init_db()

        conn = get_conn()
        cur = conn.cursor()
        for country_data in initial_countries:
            cur.execute(
                "INSERT INTO countries (name, type, owner_id, display_name, aggression_score, population) VALUES (?, ?, ?, ?, ?, ?)",
                (country_data['name'], country_data['type'], None, country_data['name'], 50, country_data['population'])
            )
            country_id = cur.lastrowid
            provinces = initial_provinces.get(country_data['name'], [country_data['name']])
            for pname in provinces:
                cur.execute("INSERT INTO provinces (name, country_id) VALUES (?, ?)", (pname, country_id))
            resources_list = ['Нефть', 'Природный газ', 'Уголь', 'Железная руда', 'Продовольствие', 'Древесина', 'Пресная вода']
            for res in resources_list:
                cur.execute(
                    "INSERT OR IGNORE INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?)",
                    (country_id, res, 1000)
                )
            branches = ['Военная доктрина', 'Вооружение и техника', 'Авиация и космос', 'Флот',
                        'Информационные технологии', 'Медицина и биотехнологии', 'Энергетика',
                        'Промышленность', 'Сельское хозяйство', 'Транспорт и логистика',
                        'Гражданское строительство', 'Финансы и экономика']
            for branch in branches:
                cur.execute(
                    "INSERT OR IGNORE INTO technologies (country_id, branch, level) VALUES (?, ?, 0)",
                    (country_id, branch)
                )
        conn.commit()
        conn.close()
        return True

    @app_commands.command(name="init_game", description="Инициализировать игру (админ) – полностью пересоздаёт базу")
    @app_commands.default_permissions(administrator=True)
    async def init_game(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            result = await asyncio.to_thread(self._init_game_sync)
            if result:
                await interaction.followup.send("✅ Игра инициализирована! Все страны созданы, база пересоздана.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при инициализации: {e}", ephemeral=True)

    @app_commands.command(name="backup", description="Сохранить базу данных (файл)")
    @app_commands.default_permissions(administrator=True)
    async def backup(self, interaction: discord.Interaction):
        if not os.path.exists(DB_PATH):
            await interaction.response.send_message("База данных не найдена.", ephemeral=True)
            return
        user = interaction.user
        try:
            await user.send("Ваш бэкап:", file=discord.File(DB_PATH))
            await interaction.response.send_message("Бэкап отправлен вам в личные сообщения.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Не могу отправить вам личное сообщение. Убедитесь, что у вас открыты ЛС.", ephemeral=True)

    @app_commands.command(name="restore", description="Восстановить базу данных (прикрепите файл sovereign.db)")
    @app_commands.default_permissions(administrator=True)
    async def restore(self, interaction: discord.Interaction, file: discord.Attachment):
        if not file.filename.endswith(".db"):
            await interaction.response.send_message("Пожалуйста, прикрепите файл с расширением .db (sovereign.db).", ephemeral=True)
            return
        try:
            await file.save(DB_PATH)
            await interaction.response.send_message("База данных восстановлена! Прогресс загружен.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при восстановлении: {e}", ephemeral=True)

    @app_commands.command(name="give_money", description="Выдать деньги стране (только админ)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(target="Игрок, которому выдать деньги", amount="Сумма в долларах")
    async def give_money(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Сумма должна быть положительной.", ephemeral=True)
            return
        country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id = ?", (target.id,))
        if not country:
            await interaction.response.send_message(f"Игрок {target.mention} не управляет страной.", ephemeral=True)
            return
        await async_execute(
            "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, 'Доллары', ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
            (country['id'], amount, amount)
        )
        await interaction.response.send_message(f"✅ Выдано {amount:,} долларов стране **{country['name']}** (игрок {target.mention}).", ephemeral=True)

    @app_commands.command(name="give_resource", description="Выдать ресурс стране (только админ)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(target="Игрок", resource="Название ресурса", amount="Количество")
    @app_commands.autocomplete(resource=resource_autocomplete)
    async def give_resource(self, interaction: discord.Interaction, target: discord.Member, resource: str, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Количество должно быть положительным.", ephemeral=True)
            return
        if resource not in RESOURCE_NAMES:
            await interaction.response.send_message("Неизвестный ресурс.", ephemeral=True)
            return
        country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id = ?", (target.id,))
        if not country:
            await interaction.response.send_message(f"Игрок {target.mention} не управляет страной.", ephemeral=True)
            return
        await async_execute(
            "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
            (country['id'], resource, amount, amount)
        )
        await interaction.response.send_message(f"✅ Выдано {amount} единиц ресурса '{resource}' стране **{country['name']}** ({target.mention}).", ephemeral=True)

    @app_commands.command(name="take_money", description="Забрать деньги у страны (только админ)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(target="Игрок", amount="Сумма")
    async def take_money(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Сумма должна быть положительной.", ephemeral=True)
            return
        country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id = ?", (target.id,))
        if not country:
            await interaction.response.send_message(f"Игрок {target.mention} не управляет страной.", ephemeral=True)
            return
        money_row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name='Доллары'", (country['id'],))
        if not money_row or money_row['amount'] < amount:
            await interaction.response.send_message(f"У страны {country['name']} недостаточно денег (имеется {money_row['amount'] if money_row else 0}).", ephemeral=True)
            return
        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Доллары'", (amount, country['id']))
        await interaction.response.send_message(f"✅ Забрано {amount} долларов у страны **{country['name']}** ({target.mention}).", ephemeral=True)

    @app_commands.command(name="take_resource", description="Забрать ресурс у страны (только админ)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(target="Игрок", resource="Название ресурса", amount="Количество")
    @app_commands.autocomplete(resource=resource_autocomplete)
    async def take_resource(self, interaction: discord.Interaction, target: discord.Member, resource: str, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Количество должно быть положительным.", ephemeral=True)
            return
        if resource not in RESOURCE_NAMES:
            await interaction.response.send_message("Неизвестный ресурс.", ephemeral=True)
            return
        country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id = ?", (target.id,))
        if not country:
            await interaction.response.send_message(f"Игрок {target.mention} не управляет страной.", ephemeral=True)
            return
        res_row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name=?", (country['id'], resource))
        if not res_row or res_row['amount'] < amount:
            await interaction.response.send_message(f"У страны {country['name']} недостаточно ресурса '{resource}' (имеется {res_row['amount'] if res_row else 0}).", ephemeral=True)
            return
        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?", (amount, country['id'], resource))
        await interaction.response.send_message(f"✅ Забрано {amount} единиц ресурса '{resource}' у страны **{country['name']}** ({target.mention}).", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
