import discord
from discord.ext import commands
from discord import app_commands
from database import get_conn

class GameMenu(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="🏭 Постройки", style=discord.ButtonStyle.primary, custom_id="buildings")
    async def buildings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Обновляем сообщение, показывая подменю построек
        await interaction.response.edit_message(content="Меню построек (заглушка)", view=BuildingsView(self.country_id))

    @discord.ui.button(label="💰 Ресурсы", style=discord.ButtonStyle.primary, custom_id="resources")
    async def resources_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT resource_name, amount FROM resources WHERE country_id=?", (self.country_id,))
        rows = cur.fetchall()
        conn.close()
        text = "**Ваши ресурсы:**\n" + "\n".join([f"{r['resource_name']}: {r['amount']}" for r in rows])
        await interaction.response.edit_message(content=text, view=self)  # возврат в главное меню

    @discord.ui.button(label="🌍 Дипломатия", style=discord.ButtonStyle.primary, custom_id="diplomacy")
    async def diplomacy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Дипломатия (заглушка)", view=DiplomacyView(self.country_id))

    @discord.ui.button(label="⚔️ Война", style=discord.ButtonStyle.danger, custom_id="war")
    async def war_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Военное меню (заглушка)", view=WarMenuView(self.country_id))

class BuildingsView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

# Аналогично DiplomacyView, WarMenuView — оставлю заготовки, потом дополним

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="game", description="Открыть главное меню управления страной")
    async def game(self, interaction: discord.Interaction):
        # Находим страну игрока
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            await interaction.response.send_message("Вы не управляете ни одной страной. Попросите ведущего назначить вас.", ephemeral=True)
            return
        country_id = row['id']
        await interaction.response.send_message("Главное меню", view=GameMenu(country_id), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Game(bot))