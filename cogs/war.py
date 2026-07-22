import discord
from discord.ext import commands
from discord import app_commands

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="declare_war", description="Объявить войну")
    async def declare_war(self, interaction: discord.Interaction, target_country: str):
        # Упрощённая логика
        await interaction.response.send_message(f"Война объявлена стране {target_country}!")

async def setup(bot):
    await bot.add_cog(War(bot))