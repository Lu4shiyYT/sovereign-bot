import discord
from discord.ext import commands
from discord import app_commands

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("War cog initialized", flush=True)

    @app_commands.command(name="declare_war", description="Объявить войну")
    async def declare_war(self, interaction: discord.Interaction, target: discord.Member):
        await interaction.response.send_message(f"Война объявлена стране {target.display_name}!", ephemeral=True)

    # Заглушки для вызовов из game.py
    async def _declare_war(self, interaction, attacker_id, defender_id, is_bot=False):
        await interaction.followup.send("Функция в разработке.", ephemeral=True)

    async def _make_peace(self, interaction, war_id):
        await interaction.followup.send("Функция в разработке.", ephemeral=True)

async def setup(bot):
    print("Adding War cog...", flush=True)
    await bot.add_cog(War(bot))
    print("War cog added successfully.", flush=True)
