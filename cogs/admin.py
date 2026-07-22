import discord
from discord.ext import commands
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute
from data.countries import initial_countries, initial_provinces
import os

DB_PATH = "sovereign.db"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="init_game", description="Инициализировать игру (админ)")
    @app_commands.default_permissions(administrator=True)
    async def init_game(self, interaction: discord.Interaction):
        # Очистка старых данных
        await async_execute("DELETE FROM wars")
        await async_execute("DELETE FROM alliance_members")
        await async_execute("DELETE FROM alliances")
        await async_execute("DELETE FROM pacts")
        await async_execute("DELETE FROM sanctions")
        await async_execute("DELETE FROM resources")
        await async_execute("DELETE FROM buildings")
        await async_execute("DELETE FROM provinces")
        await async_execute("DELETE FROM technologies")
        await async_execute("DELETE FROM countries")

        for country_data in initial_countries:
            row = await async_fetch_one(
                "INSERT INTO countries (name, type, owner_id, display_name, aggression_score) VALUES ($1, $2, $3, $4, $5) RETURNING id",
                (country_data['name'], country_data['type'], None, country_data['name'], 50)
            )
            country_id = row['id']
            provinces = initial_provinces.get(country_data['name'], [country_data['name']])
            for pname in provinces:
                await async_execute(
                    "INSERT INTO provinces (name, country_id) VALUES ($1, $2)",
                    (pname, country_id)
                )
            resources_list = ['Нефть', 'Природный газ', 'Уголь', 'Железная руда', 'Продовольствие', 'Древесина', 'Пресная вода']
            for res in resources_list:
                await async_execute(
                    "INSERT INTO resources (country_id, resource_name, amount) VALUES ($1, $2, $3) ON CONFLICT (country_id, resource_name) DO UPDATE SET amount = $3",
                    (country_id, res, 1000)
                )
            branches = ['Военная доктрина', 'Вооружение и техника', 'Авиация и космос', 'Флот', 'Информационные технологии',
                        'Медицина и биотехнологии', 'Энергетика', 'Промышленность', 'Сельское хозяйство', 'Транспорт и логистика',
                        'Гражданское строительство', 'Финансы и экономика']
            for branch in branches:
                await async_execute(
                    "INSERT INTO technologies (country_id, branch, level) VALUES ($1, $2, 0) ON CONFLICT (country_id, branch) DO UPDATE SET level = 0",
                    (country_id, branch)
                )
        await interaction.response.send_message("Игра инициализирована! Все страны созданы.", ephemeral=True)

    @app_commands.command(name="set_host", description="Назначить ведущего")
    @app_commands.default_permissions(administrator=True)
    async def set_host(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"{member.mention} теперь ведущий.", ephemeral=True)

    # ---------- БЭКАП ----------
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

    # ---------- ВОССТАНОВЛЕНИЕ ----------
    @app_commands.command(name="restore", description="Восстановить базу данных (прикрепите файл sovereign.db)")
    @app_commands.default_permissions(administrator=True)
    async def restore(self, interaction: discord.Interaction, file: discord.Attachment):
        if not file.filename.endswith(".db"):
            await interaction.response.send_message("Пожалуйста, прикрепите файл с расширением .db (sovereign.db).", ephemeral=True)
            return

        # Сохраняем загруженный файл поверх текущей базы
        try:
            await file.save(DB_PATH)
            await interaction.response.send_message("База данных восстановлена! Прогресс загружен.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при восстановлении: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
