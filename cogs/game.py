import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import get_conn
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
        await interaction.response.edit_message(content="Меню построек", view=view)
        # Запускаем фоновое обновление таймера
        view.start_updating(interaction.message)

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
        self.message = None
        self.update_task = None
        self.add_buttons()

    def add_buttons(self):
        """Формирует кнопки на основе текущего состояния построек"""
        self.clear_items()
        conn = get_conn()
        cur = conn.cursor()
        now = time.time()

        for b_type, data in BUILDING_TYPES.items():
            cur.execute("SELECT level, build_end_time FROM buildings WHERE country_id=? AND building_type=?",
                        (self.country_id, b_type))
            row = cur.fetchone()
            level = 0 if row is None else row['level']
            end_time = row['build_end_time'] if row else 0

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

        # Кнопка обновления (на всякий случай)
        refresh_btn = discord.ui.Button(label="🔄 Обновить", style=discord.ButtonStyle.secondary)
        refresh_btn.callback = self.refresh_callback
        self.add_item(refresh_btn)

        # Кнопка назад (останавливает обновление)
        back_btn = discord.ui.Button(label="◀ Назад", style=discord.ButtonStyle.danger)
        back_btn.callback = self.back_callback
        self.add_item(back_btn)
        conn.close()

    def start_updating(self, message: discord.Message):
        """Запускает задачу, обновляющую сообщение каждую секунду"""
        self.message = message
        # Останавливаем предыдущую задачу, если была
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
        # Запускаем новую
        self.update_task = asyncio.create_task(self.auto_update())

    async def auto_update(self):
        """Фоновая задача: обновляет кнопки каждую секунду, пока сообщение не будет удалено или таймеры не обнулятся"""
        try:
            while True:
                await asyncio.sleep(1)
                if self.message is None:
                    break
                # Проверяем, не истекли ли все таймеры
                now = time.time()
                any_active = False
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT building_type, build_end_time FROM buildings WHERE country_id=? AND build_end_time > ?",
                            (self.country_id, now))
                active_rows = cur.fetchall()
                conn.close()
                if active_rows:
                    any_active = True
                if not any_active:
                    # Если все строительства завершены, можно остановить автообновление
                    self.stop_updating()
                # Пересоздаём кнопки
                self.add_buttons()
                try:
                    await self.message.edit(view=self)
                except discord.NotFound:
                    break
                except discord.HTTPException:
                    pass  # игнорируем случайные ошибки
        except asyncio.CancelledError:
            pass

    def stop_updating(self):
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()

    async def refresh_callback(self, interaction: discord.Interaction):
        """Ручное обновление (на всякий случай)"""
        self.add_buttons()
        await interaction.response.edit_message(view=self)
        # Если пользователь обновил вручную, можно перезапустить автообновление
        self.start_updating(interaction.message)

    async def back_callback(self, interaction: discord.Interaction):
        self.stop_updating()
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

    def make_callback(self, building_type):
        async def callback(interaction: discord.Interaction):
            conn = get_conn()
            cur = conn.cursor()
            now = time.time()

            # Проверка на идущее строительство
            cur.execute("SELECT level, build_end_time FROM buildings WHERE country_id=? AND building_type=?",
                        (self.country_id, building_type))
            row = cur.fetchone()
            if row and row['build_end_time'] > now:
                await interaction.response.send_message("Строительство уже идёт!", ephemeral=True)
                conn.close()
                return

            current_level = row['level'] if row else 0
            next_level = current_level + 1
            if next_level > 10:
                await interaction.response.send_message("Максимальный уровень!", ephemeral=True)
                conn.close()
                return

            cost = get_build_cost(building_type, current_level)
            for res, amount in cost.items():
                cur.execute("SELECT amount FROM resources WHERE country_id=? AND resource_name=?",
                            (self.country_id, res))
                res_row = cur.fetchone()
                if not res_row or res_row['amount'] < amount:
                    await interaction.response.send_message(f"Недостаточно {res}!", ephemeral=True)
                    conn.close()
                    return

            # Списываем ресурсы
            for res, amount in cost.items():
                cur.execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?",
                            (amount, self.country_id, res))

            build_time = get_build_time(building_type, current_level)
            end_time = now + build_time

            if row:
                cur.execute("UPDATE buildings SET build_end_time=? WHERE country_id=? AND building_type=?",
                            (end_time, self.country_id, building_type))
            else:
                cur.execute("INSERT INTO buildings (country_id, building_type, level, build_end_time) VALUES (?, ?, ?, ?)",
                            (self.country_id, building_type, current_level, end_time))

            conn.commit()
            conn.close()

            # Обновляем сообщение и перезапускаем таймер
            self.add_buttons()
            await interaction.response.edit_message(view=self)
            self.start_updating(interaction.message)  # обновим задачу на новое сообщение

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
        cur.execute("SELECT name FROM countries WHERE owner_id=?", (interaction.user.id,))
        existing = cur.fetchone()
        if existing:
            await interaction.response.send_message(f"Вы уже управляете страной: {existing['name']}. Сначала откажитесь от неё.", ephemeral=True)
            conn.close()
            return
        cur.execute("SELECT id, name FROM countries WHERE name=? AND owner_id IS NULL", (country,))
        row = cur.fetchone()
        if not row:
            await interaction.response.send_message("Страна не найдена или уже занята.", ephemeral=True)
            conn.close()
            return
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
