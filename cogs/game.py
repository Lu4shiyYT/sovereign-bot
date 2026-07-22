import discord
from discord.ext import commands
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute
from data.buildings import BUILDING_TYPES
import time
import math

# ========================
# КОНФИГУРАЦИЯ ЭМОДЗИ (замените на свои ID)
# ========================
EMOJI = {
    "budget": "<:budget:123456789>",        # пример
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
    "flag": "🏳️"  # будет заменён на флаг страны, если есть эмодзи флага
}

# Функция форматирования чисел
def format_number(n, decimals=0):
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

class StatsView(discord.ui.View):
    def __init__(self, country_data, is_ally, target_user):
        super().__init__(timeout=None)
        self.country = country_data
        self.is_ally = is_ally
        self.target_user = target_user  # discord.User or None
        self.current_section = None

    async def show_section(self, interaction: discord.Interaction, section: str):
        self.current_section = section
        country = self.country
        name = country['display_name'] or country['name']
        ruler = country['ruler_name'] or "Неизвестный"
        flag_emoji = EMOJI.get('flag', '🏳️')
        # Базовая шапка
        header = f"Статистика игрока {self.target_user.mention if self.target_user else 'Неизвестно'}\n{flag_emoji} {name}\n\n"
        # Никнейм показываем как упоминание пользователя
        nick = self.target_user.display_name if self.target_user else ruler

        # Функция для цветного показателя
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
            budget = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name='Доллары'", (country['id'],))
            budget_val = budget['amount'] if budget else 0
            content += f"{EMOJI['budget']} Бюджет: {format_number(budget_val, 2)}$\n"
            # Население пока нет в БД, добавим позже; пока заглушка
            content += f"{EMOJI['population']} Население: 0 человек\n"
            support = int(country['citizen_mood'])
            content += f"{EMOJI['support']} Рейтинг поддержки правительства: {support}\n"

        elif section == "development":
            content += f"**// Развитие государства**\n{nick} | {flag_emoji} {name}\n\n"
            eco = country['economic_stability']
            content += param_line(EMOJI['eco_stab'], "Экономическая стабильность", eco)
            health = country['health']
            content += param_line(EMOJI['health'], "Здоровье населения", health)
            ind = country['industry_level']
            content += param_line(EMOJI['industry'], "Промышленность", ind)
            sci = country['science_progress']
            content += param_line(EMOJI['science'], "Научный прогресс", sci)
            mood = country['citizen_mood']
            content += param_line(EMOJI['mood'], "Настрой граждан", mood)
            crime = country['crime_rate']
            content += param_line(EMOJI['crime'], "Преступность", crime)
            eco_ = country['ecology']
            content += param_line(EMOJI['ecology'], "Экология", eco_)
            gov_eff = int(country['government_efficiency'])
            content += f"{EMOJI['gov_eff']} Эффективность правительства: ур. {gov_eff} (максимум 100)\n"
            if self.is_ally:
                info_sec = int(country['info_security'])
                content += f"{EMOJI['info_sec']} Информационная безопасность: ур. {info_sec} (максимум 20)\n"
                cnt_int = int(country['counter_intelligence'])
                content += f"{EMOJI['counter_int']} Контрразведка: ур. {cnt_int} (максимум 20)\n"
            else:
                content += f"{EMOJI['info_sec']} Информационная безопасность: неизвестно\n"
                content += f"{EMOJI['counter_int']} Контрразведка: неизвестно\n"
            growth = country['demographic_growth']
            content += f"{EMOJI['growth']} Демографический рост: {growth:.2f}% (в год)\n"

        elif section == "international":
            content += f"**// Международная арена**\n{nick} | {flag_emoji} {name}\n\n"
            aggr_score = country['aggression_score']
            aggr_text, aggr_circle = get_aggression_text(aggr_score)
            content += f"{EMOJI['aggression']} Агрессия государства: {aggr_circle} {aggr_text}\n"
            prestige = country['international_prestige']
            prest_text, prest_circle = get_prestige_text(prestige)
            content += f"{EMOJI['prestige']} Международный авторитет: {prest_circle} {prest_text}\n"
            # Война, зависимость, союзы, альянсы, санкции - пока заглушки
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
            # Колонии
            content += f"{EMOJI['colony']} Колонии: нет\n"
            # Регионы
            provs = await async_fetch_all("SELECT name FROM provinces WHERE country_id=?", (country['id'],))
            if provs:
                region_list = ", ".join([p['name'] for p in provs])
                content += f"{EMOJI['territory']} Регионы: {region_list}\n"
            else:
                content += f"{EMOJI['territory']} Регионы: нет\n"

        elif section == "buildings_info":
            content += f"**// Строительство**\n{nick} | {flag_emoji} {name}\n\n"
            builds = await async_fetch_all("SELECT building_type, level FROM buildings WHERE country_id=? AND build_end_time=0 AND level>0", (country['id'],))
            if builds:
                # Группируем по типу и считаем количество
                groups = {}
                for b in builds:
                    t = b['building_type']
                    lvl = b['level']
                    groups[t] = groups.get(t, []) + [lvl]
                lines = []
                for btype, levels in groups.items():
                    count = len(levels)
                    levels_str = ", ".join(str(l) for l in levels)
                    lines.append(f"{EMOJI['buildings_icon']} {btype}: {count} шт. (уровни: {levels_str})")
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
            combat = country['combat_capability']
            content += param_line(EMOJI['army_strength'], "Сила армии", combat)
            # Численность армии, резерв, вооружение - позже
            content += f"{EMOJI['army_count']} Численность армии: 0 человек\n"
            if self.is_ally:
                content += f"{EMOJI['reservists']} Военный резерв: 0 человек\n"
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

# ... (остальные View остаются без изменений, кроме добавления меню управления государством)

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ... (country_autocomplete, country_choose, country_leave, game, daily, stats и новые модалки)

    # Добавим регистрацию с правителем
    @app_commands.command(name="country_choose", description="Выбрать свободную страну для управления")
    @app_commands.autocomplete(country=country_autocomplete)
    @app_commands.describe(country="Название страны", ruler_name="Ваше имя правителя")
    async def country_choose(self, interaction: discord.Interaction, country: str, ruler_name: str):
        # существующий код, но дополнительно сохраняем ruler_name и устанавливаем display_name = country
        # ...

    # Команда stats
    @app_commands.command(name="stats", description="Статистика страны")
    @app_commands.describe(member="Игрок (оставьте пустым для своей статистики)")
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        # логика получения страны, проверка союзника, создание StatsView и показ первого раздела
