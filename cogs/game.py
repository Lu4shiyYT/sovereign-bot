import discord
from discord.ext import commands
from discord import app_commands
from database import get_conn

class GameMenu(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="🏭 Постройки", style=discord.ButtonStyle.primary)
    async def buildings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Меню построек (заглушка)", view=BuildingsView(self.country_id))

    @discord.ui.button(label="💰 Ресурсы", style=discord.ButtonStyle.primary)
    async def resources_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT resource_name, amount FROM resources WHERE country_id=?", (self.country_id,))
        rows = cur.fetchall()
        conn.close()
        text = "**Ваши ресурсы:**\n" + "\n".join([f"{r['resource_name']}: {r['amount']}" for r in rows])
        await interaction.response.edit_message(content=text, view=self)

    @discord.ui.button(label="🌍 Дипломатия", style=discord.ButtonStyle.primary)
    async def diplomacy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Дипломатия (заглушка)", view=DiplomacyView(self.country_id))

    @discord.ui.button(label="⚔️ Война", style=discord.ButtonStyle.danger)
    async def war_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Военное меню (заглушка)", view=WarMenuView(self.country_id))

class BuildingsView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class DiplomacyView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id
    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class WarMenuView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id
    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def country_autocomplete(self, interaction: discord.Interaction, current: str):
        """Возвращает список свободных стран, начинающихся с current"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM countries WHERE owner_id IS NULL AND name LIKE ?", (f"{current}%",))
        results = [row['name'] for row in cur.fetchall()]
        conn.close()
        return [app_commands.Choice(name=name, value=name) for name in results]

    @app_commands.command(name="country_choose", description="Выбрать свободную страну для управления")
    @app_commands.autocomplete(country=country_autocomplete)
    @app_commands.describe(country="Название страны")
    async def country_choose(self, interaction: discord.Interaction, country: str):
        conn = get_conn()
        cur = conn.cursor()
        # Проверим, не управляет ли уже игрок какой-то страной
        cur.execute("SELECT name FROM countries WHERE owner_id=?", (interaction.user.id,))
        existing = cur.fetchone()
        if existing:
            await interaction.response.send_message(f"Вы уже управляете страной: {existing['name']}. Сначала откажитесь от неё.", ephemeral=True)
            conn.close()
            return

        # Ищем выбранную страну
        cur.execute("SELECT id, name FROM countries WHERE name=? AND owner_id IS NULL", (country,))
        row = cur.fetchone()
        if not row:
            await interaction.response.send_message("Страна не найдена или уже занята.", ephemeral=True)
            conn.close()
            return

        # Назначаем игрока владельцем
        cur.execute("UPDATE countries SET owner_id=? WHERE id=?", (interaction.user.id, row['id']))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Вы теперь управляете страной **{row['name']}**! Используйте `/game` для управления.", ephemeral=True)

    @app_commands.command(name="country_leave", description="Отказаться от управления страной")
    async def country_leave(self, interaction: discord.Interaction):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        row = cur.fetchone()
        if not row:
            await interaction.response.send_message("Вы не управляете ни одной страной.", ephemeral=True)
            conn.close()
            return
        cur.execute("UPDATE countries SET owner_id=NULL WHERE id=?", (row['id'],))
        conn.commit()
        conn.close()
        await interaction.response.send_message(f"Вы отказались от управления страной **{row['name']}**.", ephemeral=True)

    @app_commands.command(name="game", description="Открыть главное меню управления страной")
    async def game(self, interaction: discord.Interaction):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            await interaction.response.send_message("Вы не управляете ни одной страной. Используйте `/country_choose`.", ephemeral=True)
            return
        country_id = row['id']
        await interaction.response.send_message("Главное меню", view=GameMenu(country_id), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Game(bot))
