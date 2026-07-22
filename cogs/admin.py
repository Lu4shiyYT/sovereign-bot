import discord
from discord.ext import commands
from discord import app_commands
from database import get_conn
from data.countries import initial_countries, initial_provinces
import os

DB_PATH = "sovereign.db"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="init_game", description="Инициализировать игру (админ)")
    @app_commands.default_permissions(administrator=True)
    async def init_game(self, interaction: discord.Interaction):
        conn = get_conn()
        cur = conn.cursor()

        # Очищаем всё
        cur.execute("DELETE FROM wars")
        cur.execute("DELETE FROM alliance_members")
        cur.execute("DELETE FROM alliances")
        cur.execute("DELETE FROM sanctions")
        cur.execute("DELETE FROM resources")
        cur.execute("DELETE FROM buildings")
        cur.execute("DELETE FROM provinces")
        cur.execute("DELETE FROM technologies")
        cur.execute("DELETE FROM countries")

        # Пересоздаём таблицу pacts с колонкой subtype (устраняем проблему)
        cur.execute("DROP TABLE IF EXISTS pacts")
        cur.execute("""
            CREATE TABLE pacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_country INTEGER,
                to_country INTEGER,
                type TEXT,
                subtype TEXT DEFAULT '',
                accepted INTEGER DEFAULT 0,
                FOREIGN KEY (from_country) REFERENCES countries(id),
                FOREIGN KEY (to_country) REFERENCES countries(id)
            )
        """)

        # Заполняем страны
        for country_data in initial_countries:
            cur.execute(
                "INSERT INTO countries (name, type, owner_id, display_name, aggression_score) VALUES (?, ?, ?, ?, ?)",
                (country_data['name'], country_data['type'], None, country_data['name'], 50)
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
            branches = ['Военная доктрина', 'Вооружение и техника', 'Авиация и космос', 'Флот', 'Информационные технологии',
                        'Медицина и биотехнологии', 'Энергетика', 'Промышленность', 'Сельское хозяйство', 'Транспорт и логистика',
                        'Гражданское строительство', 'Финансы и экономика']
            for branch in branches:
                cur.execute(
                    "INSERT OR IGNORE INTO technologies (country_id, branch, level) VALUES (?, ?, 0)",
                    (country_id, branch)
                )
        conn.commit()
        conn.close()
        await interaction.response.send_message("Игра инициализирована! Все страны созданы.", ephemeral=True)

    @app_commands.command(name="set_host", description="Назначить ведущего")
    @app_commands.default_permissions(administrator=True)
    async def set_host(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"{member.mention} теперь ведущий.", ephemeral=True)

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

async def setup(bot):
    await bot.add_cog(Admin(bot))
