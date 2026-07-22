import discord
from discord.ext import commands
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute
from data.buildings import BUILDING_TYPES
import time

def get_build_time(building_type, level):
    base = BUILDING_TYPES[building_type]["build_time"]
    return base * (BUILDING_TYPES[building_type]["upgrade_multiplier"] ** level)

def get_build_cost(building_type, level):
    base_cost = BUILDING_TYPES[building_type]["cost"]
    mult = BUILDING_TYPES[building_type]["upgrade_multiplier"] ** level
    return {res: int(amount * mult) for res, amount in base_cost.items()}

# ========================
# VIEW КЛАССЫ
# ========================
class GameMenu(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="🏭 Постройки", style=discord.ButtonStyle.primary)
    async def buildings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BuildingsView(self.country_id)
        await view.refresh_buttons(interaction)
        await interaction.response.edit_message(content="Меню построек", view=view)

    @discord.ui.button(label="💰 Ресурсы", style=discord.ButtonStyle.primary)
    async def resources_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        rows = await async_fetch_all("SELECT resource_name, amount FROM resources WHERE country_id=?", (self.country_id,))
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

    async def refresh_buttons(self, interaction):
        """Загружает актуальные данные, завершает просроченные стройки и пересоздаёт кнопки."""
        self.clear_items()
        now = time.time()
        for b_type in BUILDING_TYPES:
            row = await async_fetch_one(
                "SELECT level, build_end_time FROM buildings WHERE country_id=? AND building_type=?",
                (self.country_id, b_type)
            )
            level = 0 if row is None else row['level']
            end_time = row['build_end_time'] if row else 0

            # Автоматически завершаем строительство, если время вышло
            if end_time > 0 and end_time <= now:
                new_level = level + 1
                await async_execute(
                    "UPDATE buildings SET level=?, build_end_time=0 WHERE country_id=? AND building_type=?",
                    (new_level, self.country_id, b_type)
                )
                level = new_level
                end_time = 0

            if level >= 10:
                label = f"{b_type} (макс.)"
                disabled = True
            elif end_time > now:
                remaining = int(end_time - now)
                label = f"{b_type} (стр-во {remaining}с)"
                disabled = True
            else:
                next_level = level + 1
                label = f"{b_type} (ур.{level} → {next_level})"
                disabled = False

            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=disabled, custom_id=b_type)
            btn.callback = self.make_callback(b_type)
            self.add_item(btn)

        # Кнопка «Обновить»
        refresh_btn = discord.ui.Button(label="🔄 Обновить", style=discord.ButtonStyle.secondary)
        refresh_btn.callback = self.refresh_callback
        self.add_item(refresh_btn)

        # Кнопка «Назад»
        back_btn = discord.ui.Button(label="◀ Назад", style=discord.ButtonStyle.danger)
        back_btn.callback = self.back_callback
        self.add_item(back_btn)

    async def refresh_callback(self, interaction: discord.Interaction):
        """Ручное обновление — перезагружает кнопки с актуальными таймерами."""
        await self.refresh_buttons(interaction)
        await interaction.response.edit_message(view=self)

    async def back_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

    def make_callback(self, building_type):
        async def callback(interaction: discord.Interaction):
            now = time.time()
            row = await async_fetch_one(
                "SELECT level, build_end_time FROM buildings WHERE country_id=? AND building_type=?",
                (self.country_id, building_type)
            )
            if row and row['build_end_time'] > now:
                await interaction.response.send_message("Строительство уже идёт!", ephemeral=True)
                return

            current_level = row['level'] if row else 0
            next_level = current_level + 1
            if next_level > 10:
                await interaction.response.send_message("Максимальный уровень!", ephemeral=True)
                return

            cost = get_build_cost(building_type, current_level)
            for res, amount in cost.items():
                res_row = await async_fetch_one(
                    "SELECT amount FROM resources WHERE country_id=? AND resource_name=?",
                    (self.country_id, res)
                )
                if not res_row or res_row['amount'] < amount:
                    await interaction.response.send_message(f"Недостаточно {res}!", ephemeral=True)
                    return

            for res, amount in cost.items():
                await async_execute(
                    "UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?",
                    (amount, self.country_id, res)
                )

            build_time = get_build_time(building_type, current_level)
            end_time = now + build_time

            if row:
                await async_execute(
                    "UPDATE buildings SET build_end_time=? WHERE country_id=? AND building_type=?",
                    (end_time, self.country_id, building_type)
                )
            else:
                await async_execute(
                    "INSERT INTO buildings (country_id, building_type, level, build_end_time) VALUES (?, ?, ?, ?)",
                    (self.country_id, building_type, current_level, end_time)
                )

            await self.refresh_buttons(interaction)
            await interaction.response.edit_message(view=self)

        return callback

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

# ========================
# КОГ
# ========================
class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def country_autocomplete(self, interaction: discord.Interaction, current: str):
        rows = await async_fetch_all(
            "SELECT name FROM countries WHERE owner_id IS NULL AND name LIKE ?",
            (f"{current}%",)
        )
        return [app_commands.Choice(name=row['name'], value=row['name']) for row in rows]

    @app_commands.command(name="country_choose", description="Выбрать свободную страну для управления")
    @app_commands.autocomplete(country=country_autocomplete)
    @app_commands.describe(country="Название страны")
    async def country_choose(self, interaction: discord.Interaction, country: str):
        existing = await async_fetch_one("SELECT name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if existing:
            await interaction.response.send_message(f"Вы уже управляете страной: {existing['name']}. Сначала откажитесь от неё.", ephemeral=True)
            return
        row = await async_fetch_one("SELECT id, name FROM countries WHERE name=? AND owner_id IS NULL", (country,))
        if not row:
            await interaction.response.send_message("Страна не найдена или уже занята.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET owner_id=? WHERE id=?", (interaction.user.id, row['id']))
        await interaction.response.send_message(f"Вы теперь управляете страной **{row['name']}**! Используйте `/game`.", ephemeral=True)

    @app_commands.command(name="country_leave", description="Отказаться от управления страной")
    async def country_leave(self, interaction: discord.Interaction):
        row = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете ни одной страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET owner_id=NULL WHERE id=?", (row['id'],))
        await interaction.response.send_message(f"Вы отказались от управления страной **{row['name']}**.", ephemeral=True)

    @app_commands.command(name="game", description="Открыть главное меню управления страной")
    async def game(self, interaction: discord.Interaction):
        row = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете ни одной страной. Используйте `/country_choose`.", ephemeral=True)
            return
        country_id = row['id']
        await interaction.response.send_message("Главное меню", view=GameMenu(country_id), ephemeral=True)

    # ---- ЕЖЕДНЕВНЫЙ БОНУС ----
    @app_commands.command(name="daily", description="Получить ежедневный бонус ресурсов")
    async def daily(self, interaction: discord.Interaction):
        row = await async_fetch_one("SELECT id, last_daily FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Сначала выберите страну через `/country_choose`.", ephemeral=True)
            return
        country_id = row['id']
        last_daily = row['last_daily']
        now = time.time()
        if last_daily and (now - last_daily) < 86400:
            remaining = int(86400 - (now - last_daily))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.response.send_message(
                f"Вы уже забирали бонус. Следующий доступен через {hours} ч {minutes} мин.",
                ephemeral=True
            )
            return
        # Выдача бонуса
        bonus = {"Доллары": 500, "Продовольствие": 200, "Нефть": 100}
        for res, amount in bonus.items():
            await async_execute(
                "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) "
                "ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                (country_id, res, amount, amount)
            )
        # Обновляем время последнего бонуса
        await async_execute("UPDATE countries SET last_daily = ? WHERE id = ?", (now, country_id))
        await interaction.response.send_message(
            "Ежедневный бонус получен! +500 Долларов, +200 Продовольствия, +100 Нефти.",
            ephemeral=True
        )

    # ---- СТАТИСТИКА СТРАНЫ ----
    @app_commands.command(name="stats", description="Просмотреть статистику вашей страны")
    async def stats(self, interaction: discord.Interaction):
        country = await async_fetch_one(
            "SELECT * FROM countries WHERE owner_id=?",
            (interaction.user.id,)
        )
        if not country:
            await interaction.response.send_message("Сначала выберите страну.", ephemeral=True)
            return
        country = dict(country)
        # Постройки
        builds = await async_fetch_all(
            "SELECT building_type, level FROM buildings WHERE country_id=? AND build_end_time=0",
            (country['id'],)
        )
        build_text = "\n".join([f"{b['building_type']}: ур.{b['level']}" for b in builds]) or "Нет построек"

        text = f"**{country['name']}** ({country['type']})\n"
        text += f"💰 Экономическая стабильность: {country['economic_stability']:.1f}%\n"
        text += f"❤️ Здоровье населения: {country['health']:.1f}%\n"
        text += f"⚔️ Боеспособность: {country['combat_capability']:.1f}%\n"
        text += f"🏭 Промышленность: {country['industry_level']:.1f}%\n"
        text += f"🔬 Научный прогресс: {country['science_progress']:.1f}%\n"
        text += f"😊 Настрой граждан: {country['citizen_mood']:.1f}%\n"
        text += f"🚨 Преступность: {country['crime_rate']:.1f}%\n"
        text += f"🌿 Экология: {country['ecology']:.1f}%\n"
        text += f"🌐 Международный авторитет: {country['international_prestige']:.1f}\n"
        text += f"🏛️ Эффективность правительства: {country['government_efficiency']:.1f}%\n"
        text += f"🔐 Инфо-безопасность: {country['info_security']:.1f}%\n"
        text += f"🕵️ Контрразведка: {country['counter_intelligence']:.1f}%\n"
        text += f"👥 Демографический рост: {country['demographic_growth']:.2f}%\n\n"
        text += f"**Постройки:**\n{build_text}"

        await interaction.response.send_message(text, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Game(bot))
