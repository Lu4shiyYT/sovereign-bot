import discord
from discord.ext import commands
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute
from data.buildings import BUILDING_TYPES
import time
import math

# ========================
# ЭМОДЗИ (замените на свои ID)
# ========================
EMOJI = {
    "budget": "<:budget:123456789>",
    "population": "👥",
    "support": "👍",
    "eco_stab": "<:eco:123456789>",
    "health": "<:health:123456789>",
    "industry": "<:industry:123456789>",
    "science": "<:science:123456789>",
    "mood": "<:mood:123456789>",
    "crime": "<:crime:123456789>",
    "ecology": "<:ecology:123456789>",
    "gov_eff": "<:gov:123456789>",
    "info_sec": "<:info_sec:123456789>",
    "counter_int": "<:counter_int:123456789>",
    "growth": "<:growth:123456789>",
    "army_strength": "<:army:123456789>",
    "army_count": "<:soldiers:123456789>",
    "reservists": "<:reserv:123456789>",
    "weapon": "<:weapon:123456789>",
    "vehicle": "<:vehicle:123456789>",
    "buildings_icon": "<:buildings:123456789>",
    "territory": "<:territory:123456789>",
    "colony": "🏝️",
    "war_status": "⚔️",
    "dependency": "🔗",
    "alliance": "🤝",
    "sanction": "🚫",
    "aggression": "😈",
    "prestige": "🌟",
    "flag": "🏳️"
}

# Форматирование чисел
def format_number(n, decimals=0):
    if n is None:
        return "0"
    if decimals == 0:
        return f"{int(n):,}".replace(",", ".")
    else:
        return f"{n:,.{decimals}f}".replace(",", ".").replace(".", ",", 1)

def get_color_circle(value):
    if value <= 20:
        return "🔴"
    elif value <= 40:
        return "🟠"
    elif value <= 60:
        return "🟡"
    elif value <= 80:
        return "🟢"
    else:
        return "🔵"

def get_aggression_text(score):
    if score <= 20:
        return "Мирное", "🔵"
    elif score <= 40:
        return "Умеренное", "🟢"
    elif score <= 60:
        return "Нейтральное", "🟡"
    elif score <= 80:
        return "Агрессивное", "🟠"
    else:
        return "Сильно агрессивное", "🔴"

def get_prestige_text(score):
    if score <= 20:
        return "Незначимый", "🔴"
    elif score <= 40:
        return "Минимальное влияние", "🟠"
    elif score <= 60:
        return "Влиятельный", "🟡"
    elif score <= 80:
        return "Сильно-Влиятельный", "🟢"
    else:
        return "Сверхвлиятельный", "🔵"

# ========================
# VIEW ДЛЯ СТАТИСТИКИ
# ========================
class StatsView(discord.ui.View):
    def __init__(self, country_data, is_ally, target_user):
        super().__init__(timeout=None)
        self.country = country_data
        self.is_ally = is_ally
        self.target_user = target_user
        self.current_section = None

    async def show_section(self, interaction: discord.Interaction, section: str):
        self.current_section = section
        country = self.country
        name = country['display_name'] or country['name']
        ruler = country['ruler_name'] or "Неизвестный"
        flag_emoji = EMOJI.get('flag', '🏳️')
        header = f"Статистика игрока {self.target_user.mention}\n{flag_emoji} {name}\n\n"
        nick = self.target_user.display_name if self.target_user else ruler

        def param_line(emoji, name, value, max_val=100, is_unknown=False, suffix=""):
            if is_unknown:
                return f"{emoji} {name}: неизвестно\n"
            if max_val == 100:
                circle = get_color_circle(value)
                return f"{emoji} {name}: {circle} {value}/{max_val}\n"
            else:
                return f"{emoji} {name}: {value}{suffix}\n"

        content = ""
        if section == "main":
            content += f"**// Основные параметры**\n{nick} | {flag_emoji} {name}\n\n"
            budget_row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name='Доллары'", (country['id'],))
            budget_val = budget_row['amount'] if budget_row else 0
            content += f"{EMOJI['budget']} Бюджет: {format_number(budget_val, 2)}$\n"
            population = 0  # заглушка, позже добавим реальное население
            content += f"{EMOJI['population']} Население: {format_number(population)} человек\n"
            support = int(country['citizen_mood'])
            content += f"{EMOJI['support']} Рейтинг поддержки правительства: {support}\n"

        elif section == "development":
            content += f"**// Развитие государства**\n{nick} | {flag_emoji} {name}\n\n"
            content += param_line(EMOJI['eco_stab'], "Экономическая стабильность", country['economic_stability'])
            content += param_line(EMOJI['health'], "Здоровье населения", country['health'])
            content += param_line(EMOJI['industry'], "Промышленность", country['industry_level'])
            content += param_line(EMOJI['science'], "Научный прогресс", country['science_progress'])
            content += param_line(EMOJI['mood'], "Настрой граждан", country['citizen_mood'])
            content += param_line(EMOJI['crime'], "Преступность", country['crime_rate'])
            content += param_line(EMOJI['ecology'], "Экология", country['ecology'])
            content += f"{EMOJI['gov_eff']} Эффективность правительства: ур. {int(country['government_efficiency'])} (максимум 100)\n"
            if self.is_ally:
                content += f"{EMOJI['info_sec']} Информационная безопасность: ур. {int(country['info_security'])} (максимум 20)\n"
                content += f"{EMOJI['counter_int']} Контрразведка: ур. {int(country['counter_intelligence'])} (максимум 20)\n"
            else:
                content += f"{EMOJI['info_sec']} Информационная безопасность: неизвестно\n"
                content += f"{EMOJI['counter_int']} Контрразведка: неизвестно\n"
            content += f"{EMOJI['growth']} Демографический рост: {country['demographic_growth']:.2f}% (в год)\n"

        elif section == "international":
            content += f"**// Международная арена**\n{nick} | {flag_emoji} {name}\n\n"
            aggr_text, aggr_circle = get_aggression_text(country['aggression_score'])
            content += f"{EMOJI['aggression']} Агрессия государства: {aggr_circle} {aggr_text}\n"
            prest_text, prest_circle = get_prestige_text(country['international_prestige'])
            content += f"{EMOJI['prestige']} Международный авторитет: {prest_circle} {prest_text}\n"
            # Заглушки для войны, зависимости и т.д.
            content += f"{EMOJI['war_status']} В состоянии войны: нет\n"
            content += f"{EMOJI['dependency']} Зависимость: независимое\n"
            if self.is_ally:
                content += f"{EMOJI['alliance']} Союзы: нет\n"
                content += f"{EMOJI['alliance']} Альянсы: нет\n"
            else:
                content += f"{EMOJI['alliance']} Союзы: неизвестно\n"
                content += f"{EMOJI['alliance']} Альянсы: неизвестно\n"
            content += f"{EMOJI['sanction']} Санкции: нет\n"

        elif section == "territory":
            content += f"**// Территория**\n{nick} | {flag_emoji} {name}\n\n"
            content += f"{EMOJI['colony']} Колонии: нет\n"
            provs = await async_fetch_all("SELECT name FROM provinces WHERE country_id=?", (country['id'],))
            if provs:
                region_list = ", ".join([p['name'] for p in provs])
                content += f"{EMOJI['territory']} Регионы: {region_list}\n"
            else:
                content += f"{EMOJI['territory']} Регионы: нет\n"

        elif section == "buildings_info":
            content += f"**// Строительство**\n{nick} | {flag_emoji} {name}\n\n"
            builds = await async_fetch_all(
                "SELECT building_type, level FROM buildings WHERE country_id=? AND build_end_time=0 AND level>0",
                (country['id'],)
            )
            if builds:
                groups = {}
                for b in builds:
                    t = b['building_type']
                    lvl = b['level']
                    groups.setdefault(t, []).append(lvl)
                lines = []
                for btype, levels in groups.items():
                    lines.append(f"{EMOJI['buildings_icon']} {btype}: {len(levels)} шт. (уровни: {', '.join(map(str, levels))})")
                content += "\n".join(lines)
            else:
                content += f"{EMOJI['buildings_icon']} Постройки: нет\n"

        elif section == "resources_info":
            content += f"**// Ресурсы**\n{nick} | {flag_emoji} {name}\n\n"
            res = await async_fetch_all("SELECT resource_name, amount FROM resources WHERE country_id=?", (country['id'],))
            if res:
                for r in res:
                    content += f"{r['resource_name']}: {format_number(r['amount'], 2)}\n"
            else:
                content += "Нет ресурсов\n"

        elif section == "army":
            content += f"**// Армия**\n{nick} | {flag_emoji} {name}\n\n"
            content += param_line(EMOJI['army_strength'], "Сила армии", country['combat_capability'])
            content += f"{EMOJI['army_count']} Численность армии: {format_number(0)} человек\n"
            if self.is_ally:
                content += f"{EMOJI['reservists']} Военный резерв: {format_number(0)} человек\n"
                content += f"{EMOJI['weapon']} Вооружение: нет\n"
                content += f"{EMOJI['vehicle']} Военная техника: нет\n"
            else:
                content += f"{EMOJI['reservists']} Военный резерв: неизвестно\n"
                content += f"{EMOJI['weapon']} Вооружение: неизвестно\n"
                content += f"{EMOJI['vehicle']} Военная техника: неизвестно\n"

        await interaction.response.edit_message(content=header + content, view=self)

    @discord.ui.button(label="Основные параметры", style=discord.ButtonStyle.primary)
    async def btn_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_section(interaction, "main")

    @discord.ui.button(label="Развитие государства", style=discord.ButtonStyle.primary)
    async def btn_dev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_section(interaction, "development")

    @discord.ui.button(label="Международная арена", style=discord.ButtonStyle.primary)
    async def btn_intl(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_section(interaction, "international")

    @discord.ui.button(label="Территория", style=discord.ButtonStyle.primary)
    async def btn_territory(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_section(interaction, "territory")

    @discord.ui.button(label="Строительство", style=discord.ButtonStyle.primary)
    async def btn_buildings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_section(interaction, "buildings_info")

    @discord.ui.button(label="Ресурсы", style=discord.ButtonStyle.primary)
    async def btn_resources(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_section(interaction, "resources_info")

    @discord.ui.button(label="Армия", style=discord.ButtonStyle.primary)
    async def btn_army(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_section(interaction, "army")


# ========================
# VIEW СТРОИТЕЛЬСТВА (прежний BuildingsView, без автообновления)
# ========================
class GameMenu(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="🏭 Постройки", style=discord.ButtonStyle.primary)
    async def buildings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BuildingsView(self.country_id)
        await view.refresh_buttons(interaction)
        await interaction.response.edit_message(content="Меню построек", view=view)

    @discord.ui.button(label="💰 Ресурсы", style=discord.ButtonStyle.primary)
    async def resources_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        rows = await async_fetch_all("SELECT resource_name, amount FROM resources WHERE country_id=?", (self.country_id,))
        text = "**Ваши ресурсы:**\n" + "\n".join([f"{r['resource_name']}: {format_number(r['amount'], 2)}" for r in rows])
        await interaction.response.edit_message(content=text, view=self)

    @discord.ui.button(label="🌍 Дипломатия", style=discord.ButtonStyle.primary)
    async def diplomacy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Дипломатия (заглушка)", view=DiplomacyView(self.country_id))

    @discord.ui.button(label="⚔️ Война", style=discord.ButtonStyle.danger)
    async def war_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Военное меню (заглушка)", view=WarMenuView(self.country_id))

    @discord.ui.button(label="🏛️ Управление", style=discord.ButtonStyle.success)
    async def gov_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Управление государством", view=GovernmentView(self.country_id))

class BuildingsView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    async def refresh_buttons(self, interaction):
        self.clear_items()
        now = time.time()
        for b_type in BUILDING_TYPES:
            row = await async_fetch_one(
                "SELECT level, build_end_time FROM buildings WHERE country_id=? AND building_type=?",
                (self.country_id, b_type)
            )
            level = 0 if row is None else row['level']
            end_time = row['build_end_time'] if row else 0

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

        refresh_btn = discord.ui.Button(label="🔄 Обновить", style=discord.ButtonStyle.secondary)
        refresh_btn.callback = self.refresh_callback
        self.add_item(refresh_btn)

        back_btn = discord.ui.Button(label="◀ Назад", style=discord.ButtonStyle.danger)
        back_btn.callback = self.back_callback
        self.add_item(back_btn)

    async def refresh_callback(self, interaction: discord.Interaction):
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

            cost = {res: int(amount * BUILDING_TYPES[building_type]["upgrade_multiplier"] ** current_level)
                    for res, amount in BUILDING_TYPES[building_type]["cost"].items()}
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

            build_time = BUILDING_TYPES[building_type]["build_time"] * (BUILDING_TYPES[building_type]["upgrade_multiplier"] ** current_level)
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

class GovernmentView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Изменить название", style=discord.ButtonStyle.primary)
    async def rename_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # здесь должна открываться модалка для ввода нового названия, но в рамках View проще использовать команду
        await interaction.response.send_message("Используйте команду `/rename` (в разработке)", ephemeral=True)

    @discord.ui.button(label="Изменить религию", style=discord.ButtonStyle.primary)
    async def religion_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/set_religion`", ephemeral=True)

    @discord.ui.button(label="Изменить идеологию", style=discord.ButtonStyle.primary)
    async def ideology_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/set_ideology`", ephemeral=True)

    @discord.ui.button(label="Форма правления", style=discord.ButtonStyle.primary)
    async def govform_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/set_government`", ephemeral=True)

    @discord.ui.button(label="Мобилизация", style=discord.ButtonStyle.danger)
    async def mob_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Упрощённо: переключаем мобилизацию
        await async_execute("UPDATE countries SET mobilization = 1 - mobilization WHERE id=?", (self.country_id,))
        await interaction.response.send_message("Мобилизация переключена.", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class DiplomacyView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id
    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class WarMenuView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id
    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
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

    @app_commands.command(name="country_choose", description="Выбрать свободную страну и правителя")
    @app_commands.autocomplete(country=country_autocomplete)
    @app_commands.describe(country="Название страны", ruler_name="Ваше имя правителя")
    async def country_choose(self, interaction: discord.Interaction, country: str, ruler_name: str):
        existing = await async_fetch_one("SELECT name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if existing:
            await interaction.response.send_message(f"Вы уже управляете страной: {existing['name']}. Сначала откажитесь от неё.", ephemeral=True)
            return
        row = await async_fetch_one("SELECT id, name FROM countries WHERE name=? AND owner_id IS NULL", (country,))
        if not row:
            await interaction.response.send_message("Страна не найдена или уже занята.", ephemeral=True)
            return
        await async_execute(
            "UPDATE countries SET owner_id=?, ruler_name=?, display_name=? WHERE id=?",
            (interaction.user.id, ruler_name, country, row['id'])
        )
        await interaction.response.send_message(
            f"Вы теперь управляете страной **{country}** как **{ruler_name}**! Используйте `/game`.",
            ephemeral=True
        )

    @app_commands.command(name="country_leave", description="Отказаться от управления страной")
    async def country_leave(self, interaction: discord.Interaction):
        row = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете ни одной страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET owner_id=NULL, ruler_name='' WHERE id=?", (row['id'],))
        await interaction.response.send_message(f"Вы отказались от управления страной **{row['name']}**.", ephemeral=True)

    @app_commands.command(name="game", description="Открыть главное меню управления страной")
    async def game(self, interaction: discord.Interaction):
        row = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете страной. Используйте `/country_choose`.", ephemeral=True)
            return
        await interaction.response.send_message("Главное меню", view=GameMenu(row['id']), ephemeral=True)

    @app_commands.command(name="daily", description="Получить ежедневный бонус ресурсов")
    async def daily(self, interaction: discord.Interaction):
        row = await async_fetch_one("SELECT id, last_daily FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Сначала выберите страну.", ephemeral=True)
            return
        country_id = row['id']
        now = time.time()
        if row['last_daily'] and (now - row['last_daily']) < 86400:
            remaining = int(86400 - (now - row['last_daily']))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.response.send_message(f"Бонус можно забрать через {hours} ч {minutes} мин.", ephemeral=True)
            return
        bonus = {"Доллары": 500, "Продовольствие": 200, "Нефть": 100}
        for res, amount in bonus.items():
            await async_execute(
                "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                (country_id, res, amount, amount)
            )
        await async_execute("UPDATE countries SET last_daily = ? WHERE id = ?", (now, country_id))
        await interaction.response.send_message("Ежедневный бонус получен! +500$, +200 прод., +100 нефти.", ephemeral=True)

    @app_commands.command(name="stats", description="Статистика страны")
    @app_commands.describe(member="Игрок (оставьте пустым для своей статистики)")
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            target_user = interaction.user
        else:
            target_user = member

        country = await async_fetch_one(
            "SELECT * FROM countries WHERE owner_id=?",
            (target_user.id,)
        )
        if not country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        country = dict(country)
        # Проверка союзника (пока заглушка: если смотрим свою страну или модератор, то is_ally=True)
        is_ally = (interaction.user.id == target_user.id) or interaction.user.guild_permissions.administrator
        view = StatsView(country, is_ally, target_user)
        await view.show_section(interaction, "main")
        # Сообщение уже отправлено через edit_message, но первый раз нужно отправить новое
        await interaction.response.send_message("Загрузка...", view=view, ephemeral=True)
        # Сразу покажем основной раздел (повторно, но уже с правильным content)
        await view.show_section(interaction, "main")

    # Команды управления государством (заглушки)
    @app_commands.command(name="rename", description="Изменить название страны")
    async def rename(self, interaction: discord.Interaction, new_name: str):
        row = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET display_name=? WHERE id=?", (new_name, row['id']))
        await interaction.response.send_message(f"Название страны изменено на {new_name}.", ephemeral=True)

    @app_commands.command(name="set_religion", description="Установить государственную религию")
    async def set_religion(self, interaction: discord.Interaction, religion: str):
        row = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET religion=? WHERE id=?", (religion, row['id']))
        await interaction.response.send_message(f"Религия изменена на {religion}.", ephemeral=True)

    @app_commands.command(name="set_ideology", description="Установить государственную идеологию")
    async def set_ideology(self, interaction: discord.Interaction, ideology: str):
        row = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET ideology=? WHERE id=?", (ideology, row['id']))
        await interaction.response.send_message(f"Идеология изменена на {ideology}.", ephemeral=True)

    @app_commands.command(name="set_government", description="Установить форму правления")
    async def set_government(self, interaction: discord.Interaction, form: str):
        row = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET government_form=? WHERE id=?", (form, row['id']))
        await interaction.response.send_message(f"Форма правления изменена на {form}.", ephemeral=True)

    @app_commands.command(name="mobilize", description="Переключить мобилизацию")
    async def mobilize(self, interaction: discord.Interaction):
        row = await async_fetch_one("SELECT id, mobilization FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not row:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        new_mob = 1 - row['mobilization']
        await async_execute("UPDATE countries SET mobilization=? WHERE id=?", (new_mob, row['id']))
        state = "включена" if new_mob else "выключена"
        await interaction.response.send_message(f"Мобилизация {state}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Game(bot))
