import discord
from discord.ext import commands
from discord import app_commands
from database import get_conn
from data.countries import initial_countries, initial_provinces

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="init_game", description="Инициализировать игру (админ)")
    @app_commands.default_permissions(administrator=True)
    async def init_game(self, interaction: discord.Interaction):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM wars")
        cur.execute("DELETE FROM alliance_members")
        cur.execute("DELETE FROM alliances")
        cur.execute("DELETE FROM resources")
        cur.execute("DELETE FROM buildings")
        cur.execute("DELETE FROM provinces")
        cur.execute("DELETE FROM technologies")
        cur.execute("DELETE FROM countries")
        for country_data in initial_countries:
            cur.execute("INSERT INTO countries (name, type, owner_id) VALUES (?, ?, ?)",
                        (country_data['name'], country_data['type'], None))
            country_id = cur.lastrowid
            provinces = initial_provinces.get(country_data['name'], [country_data['name']])
            for pname in provinces:
                cur.execute("INSERT INTO provinces (name, country_id) VALUES (?, ?)", (pname, country_id))
            resources_list = ['Нефть', 'Природный газ', 'Уголь', 'Железная руда', 'Продовольствие', 'Древесина', 'Пресная вода']
            for res in resources_list:
                cur.execute("INSERT OR IGNORE INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?)",
                            (country_id, res, 1000))
            branches = ['Военная доктрина', 'Вооружение и техника', 'Авиация и космос', 'Флот', 'Информационные технологии',
                        'Медицина и биотехнологии', 'Энергетика', 'Промышленность', 'Сельское хозяйство', 'Транспорт и логистика',
                        'Гражданское строительство', 'Финансы и экономика']
            for branch in branches:
                cur.execute("INSERT OR IGNORE INTO technologies (country_id, branch, level) VALUES (?, ?, 0)",
                            (country_id, branch))
        conn.commit()
        conn.close()
        await interaction.response.send_message("Игра инициализирована! Все страны созданы.", ephemeral=True)

    @app_commands.command(name="set_host", description="Назначить ведущего")
    @app_commands.default_permissions(administrator=True)
    async def set_host(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"{member.mention} теперь ведущий.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))