import discord
from discord.ext import commands
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute
import time
import asyncio

# ========================
# ДАННЫЕ О ПОСТРОЙКАХ
# ========================
BUILDING_TYPES = {
    "Ферма": {
        "cost": {"Продовольствие": 50},
        "build_time": 60,          # секунд (для теста)
        "upgrade_multiplier": 1.5,
        "produces": {"Продовольствие": 10}
    },
    "Шахта": {
        "cost": {"Уголь": 100},
        "build_time": 90,
        "upgrade_multiplier": 1.8,
        "produces": {"Уголь": 8, "Железная руда": 5}
    },
    "Бизнес-центр": {
        "cost": {"Доллары": 200},
        "build_time": 120,
        "upgrade_multiplier": 2.0,
        "produces": {"Доллары": 50}
    },
    "Казарма": {
        "cost": {"Продовольствие": 150, "Доллары": 100},
        "build_time": 150,
        "upgrade_multiplier": 1.7,
        "produces": {}
    },
    "Лаборатория": {
        "cost": {"Доллары": 300, "Электроэнергия": 100},
        "build_time": 200,
        "upgrade_multiplier": 2.2,
        "produces": {"Очки науки": 5}
    }
}

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
        await view.initialize_buttons()
        await interaction.response.edit_message(content="Меню построек", view=view)
        if view.has_active_builds():
            await interaction.channel.send("🔧 Автообновление запущено")  # диагностика
            view.start_updating(interaction.message)

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
        self.message = None
        self.update_task = None
        self.active = False

    async def initialize_buttons(self):
        self.clear_items()
        now = time.time()
        self.active = False
        for b_type in BUILDING_TYPES:
            row = await async_fetch_one(
                "SELECT level, build_end_time FROM buildings WHERE country_id=? AND building_type=?",
                (self.country_id, b_type)
            )
            level = 0 if row is None else row['level']
            end_time = row['build_end_time'] if row else 0

            # Проверяем, не завершилось ли строительство
            if end_time > 0 and end_time <= now:
                # Завершаем стройку: повышаем уровень, сбрасываем таймер
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
                self.active = True
            else:
                next_level = level + 1
                label = f"{b_type} (ур.{level} → {next_level})"
                disabled = False

            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=disabled, custom_id=b_type)
            btn.callback = self.make_callback(b_type)
            self.add_item(btn)

        refresh_btn = discord.ui.Button(label="🔄 Обновить", style=discord.ButtonStyle.secondary)
        refresh_btn.callback = self.refresh_callback
        self.add_item(refresh_btn)

        back_btn = discord.ui.Button(label="◀ Назад", style=discord.ButtonStyle.danger)
        back_btn.callback = self.back_callback
        self.add_item(back_btn)

    def has_active_builds(self):
        return self.active

    def start_updating(self, message: discord.Message):
        self.message = message
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
        self.update_task = asyncio.create_task(self.auto_update())

    async def auto_update(self):
        await self.message.channel.send("⏳ Цикл автообновления начат")  # диагностика
        try:
            while True:
                await self.refresh_data_and_buttons()
                if self.message:
                    try:
                        await self.message.edit(view=self)
                    except discord.NotFound:
                        break
                    except discord.HTTPException as e:
                        await self.message.channel.send(f"Ошибка обновления меню: {e}")
                if not self.active:
                    await self.message.channel.send("🛑 Автообновление остановлено (нет активных строек)")
                    break
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await self.message.channel.send("🛑 Автообновление отменено")
        except Exception as e:
            await self.message.channel.send(f"Критическая ошибка автообновления: {e}")
            raise

    async def refresh_data_and_buttons(self):
        now = time.time()
        self.active = False
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id in BUILDING_TYPES:
                b_type = child.custom_id
                row = await async_fetch_one(
                    "SELECT level, build_end_time FROM buildings WHERE country_id=? AND building_type=?",
                    (self.country_id, b_type)
                )
                level = 0 if row is None else row['level']
                end_time = row['build_end_time'] if row else 0

                # Завершение просроченной стройки
                if end_time > 0 and end_time <= now:
                    new_level = level + 1
                    await async_execute(
                        "UPDATE buildings SET level=?, build_end_time=0 WHERE country_id=? AND building_type=?",
                        (new_level, self.country_id, b_type)
                    )
                    level = new_level
                    end_time = 0

                if level >= 10:
                    child.label = f"{b_type} (макс.)"
                    child.disabled = True
                elif end_time > now:
                    remaining = int(end_time - now)
                    child.label = f"{b_type} (стр-во {remaining}с)"
                    child.disabled = True
                    self.active = True
                else:
                    next_level = level + 1
                    child.label = f"{b_type} (ур.{level} → {next_level})"
                    child.disabled = False

    async def refresh_callback(self, interaction: discord.Interaction):
        await self.refresh_data_and_buttons()
        await interaction.response.edit_message(view=self)
        if self.has_active_builds():
            self.start_updating(interaction.message)

    async def back_callback(self, interaction: discord.Interaction):
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
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

            await self.refresh_data_and_buttons()
            await interaction.response.edit_message(view=self)
            if self.has_active_builds():
                self.start_updating(interaction.message)

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

async def setup(bot):
    await bot.add_cog(Game(bot))
