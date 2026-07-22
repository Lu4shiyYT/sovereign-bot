import discord
from discord.ext import commands
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute
from data.buildings import BUILDING_TYPES
import time
import random

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

# Типы союзов
ALLIANCE_SUBTYPES = [
    "military", "economic", "trade", "defensive", "research",
    "cultural", "political", "full", "military_economic",
    "economic_trade", "military_defensive", "technological",
    "educational", "environmental", "health"
]

# Типы санкций (влияют на разные параметры)
SANCTION_TYPES = {
    "trade_embargo": {"param": "economic_stability", "amount": 5, "desc": "Торговое эмбарго"},
    "arms_embargo": {"param": "combat_capability", "amount": 3, "desc": "Оружейное эмбарго"},
    "travel_ban": {"param": "international_prestige", "amount": 2, "desc": "Запрет на поездки"},
    "visa_ban": {"param": "citizen_mood", "amount": 2, "desc": "Визовый бан"},
    "financial_sanctions": {"param": "economic_stability", "amount": 4, "desc": "Финансовые санкции"},
    "asset_freeze": {"param": "economic_stability", "amount": 3, "desc": "Заморозка активов"},
    "diplomatic_isolation": {"param": "international_prestige", "amount": 3, "desc": "Дипломатическая изоляция"},
    "sport_isolation": {"param": "international_prestige", "amount": 1, "desc": "Спортивная изоляция"},
    "cultural_ban": {"param": "citizen_mood", "amount": 1, "desc": "Культурный бан"},
    "technology_ban": {"param": "science_progress", "amount": 3, "desc": "Технологическое эмбарго"},
    "food_embargo": {"param": "health", "amount": 3, "desc": "Продовольственное эмбарго"},
    "medicine_embargo": {"param": "health", "amount": 4, "desc": "Эмбарго на медикаменты"},
    "energy_embargo": {"param": "industry_level", "amount": 3, "desc": "Энергетическое эмбарго"},
    "arms_trade_ban": {"param": "combat_capability", "amount": 2, "desc": "Запрет на торговлю оружием"},
    "oil_embargo": {"param": "economic_stability", "amount": 5, "desc": "Нефтяное эмбарго"},
    "gas_embargo": {"param": "economic_stability", "amount": 4, "desc": "Газовое эмбарго"},
    "coal_embargo": {"param": "industry_level", "amount": 3, "desc": "Угольное эмбарго"},
    "diamond_embargo": {"param": "economic_stability", "amount": 2, "desc": "Алмазное эмбарго"},
    "gold_embargo": {"param": "economic_stability", "amount": 2, "desc": "Золотое эмбарго"},
    "uranium_embargo": {"param": "combat_capability", "amount": 3, "desc": "Урановое эмбарго"},
    "timber_embargo": {"param": "industry_level", "amount": 2, "desc": "Эмбарго на древесину"},
    "textile_embargo": {"param": "economic_stability", "amount": 2, "desc": "Текстильное эмбарго"},
    "machinery_embargo": {"param": "industry_level", "amount": 3, "desc": "Эмбарго на оборудование"},
}

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

    async def build_section(self, section: str) -> str:
        country = self.country
        name = country['display_name'] or country['name']
        ruler = country['ruler_name'] or "Неизвестный"
        flag_emoji = EMOJI.get('flag', '🏳️')
        nick = self.target_user.display_name if self.target_user else ruler

        def param_line(emoji, title, value, max_val=100, unknown=False, suffix=""):
            if unknown:
                return f"{emoji} {title}: неизвестно\n"
            if max_val == 100:
                circle = get_color_circle(value)
                return f"{emoji} {title}: {circle} {value}/{max_val}\n"
            else:
                return f"{emoji} {title}: {value}{suffix}\n"

        header = f"{nick} | {flag_emoji} {name}\n\n"

        content = ""
        if section == "main":
            content += header
            budget_row = await async_fetch_one(
                "SELECT amount FROM resources WHERE country_id=? AND resource_name='Доллары'",
                (country['id'],)
            )
            budget_val = budget_row['amount'] if budget_row else 0
            content += f"{EMOJI['budget']} Бюджет: {format_number(budget_val, 2)}$\n"
            content += f"{EMOJI['population']} Население: {format_number(0)} человек\n"
            content += f"{EMOJI['support']} Рейтинг поддержки правительства: {int(country['citizen_mood'])}\n"

        elif section == "development":
            content += header
            eco = country['economic_stability']
            health = country['health']
            ind = country['industry_level']
            sci = country['science_progress']
            mood = country['citizen_mood']
            crime = country['crime_rate']
            eco_val = country['ecology']
            gov_eff = int(country['government_efficiency'])
            info_sec = int(country['info_security'])
            cnt_int = int(country['counter_intelligence'])
            growth = country['demographic_growth']

            content += param_line(EMOJI['eco_stab'], "Экономическая стабильность", eco)
            content += param_line(EMOJI['health'], "Здоровье населения", health)
            content += param_line(EMOJI['industry'], "Промышленность", ind)
            content += param_line(EMOJI['science'], "Научный прогресс", sci)
            content += param_line(EMOJI['mood'], "Настрой граждан", mood)
            content += param_line(EMOJI['crime'], "Преступность", crime)
            content += param_line(EMOJI['ecology'], "Экология", eco_val)
            content += f"{EMOJI['gov_eff']} Эффективность правительства: ур. {gov_eff}\n"
            if self.is_ally:
                content += f"{EMOJI['info_sec']} Информационная безопасность: ур. {info_sec}\n"
                content += f"{EMOJI['counter_int']} Контрразведка: ур. {cnt_int}\n"
            else:
                content += f"{EMOJI['info_sec']} Информационная безопасность: неизвестно\n"
                content += f"{EMOJI['counter_int']} Контрразведка: неизвестно\n"
            content += f"{EMOJI['growth']} Демографический рост: {growth:.2f}% (в год)\n"

        elif section == "international":
            content += header
            aggr_text, aggr_circle = get_aggression_text(country['aggression_score'])
            content += f"{EMOJI['aggression']} Агрессия государства: {aggr_circle} {aggr_text}\n"
            prest_text, prest_circle = get_prestige_text(country['international_prestige'])
            content += f"{EMOJI['prestige']} Международный авторитет: {prest_circle} {prest_text}\n"

            # Войны
            wars = await async_fetch_all(
                "SELECT id, attacker_id, defender_id FROM wars WHERE (attacker_id=? OR defender_id=?) AND status='active'",
                (country['id'], country['id'])
            )
            if wars:
                enemies = []
                for w in wars:
                    enemy_id = w['attacker_id'] if w['defender_id'] == country['id'] else w['defender_id']
                    enemy = await async_fetch_one("SELECT name FROM countries WHERE id=?", (enemy_id,))
                    enemies.append(enemy['name'] if enemy else "Неизвестно")
                content += f"{EMOJI['war_status']} В состоянии войны: да (против: {', '.join(enemies)})\n"
            else:
                content += f"{EMOJI['war_status']} В состоянии войны: нет\n"

            content += f"{EMOJI['dependency']} Зависимость: независимое\n"

            # Союзы и пакты
            if self.is_ally:
                pacts = await async_fetch_all(
                    "SELECT type, subtype, from_country, to_country, accepted FROM pacts WHERE (from_country=? OR to_country=?) AND accepted=1",
                    (country['id'], country['id'])
                )
                allies = []
                trade = []
                for p in pacts:
                    partner_id = p['from_country'] if p['to_country'] == country['id'] else p['to_country']
                    partner = await async_fetch_one("SELECT name FROM countries WHERE id=?", (partner_id,))
                    if partner:
                        if p['type'] == 'alliance':
                            subtype = p['subtype'] or ''
                            allies.append(f"{partner['name']} ({subtype})")
                        elif p['type'] == 'trade':
                            trade.append(partner['name'])
                content += f"{EMOJI['alliance']} Союзы: {', '.join(allies) if allies else 'нет'}\n"
                content += f"{EMOJI['alliance']} Торговые партнёры: {', '.join(trade) if trade else 'нет'}\n"
            else:
                content += f"{EMOJI['alliance']} Союзы: неизвестно\n"
                content += f"{EMOJI['alliance']} Торговые партнёры: неизвестно\n"

            # Альянсы
            if self.is_ally:
                member_of = await async_fetch_all(
                    "SELECT a.name FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id WHERE am.country_id=?",
                    (country['id'],)
                )
                if member_of:
                    content += f"{EMOJI['alliance']} Альянсы: "
                    content += ", ".join([a['name'] for a in member_of]) + "\n"
                else:
                    content += f"{EMOJI['alliance']} Альянсы: нет\n"
            else:
                content += f"{EMOJI['alliance']} Альянсы: неизвестно\n"

            # Санкции (с заголовком)
            sanctions = await async_fetch_all(
                "SELECT id, description, sanction_type, from_country FROM sanctions WHERE to_country=?",
                (country['id'],)
            )
            if sanctions:
                content += "**Санкции:**\n"
                for s in sanctions:
                    from_c = await async_fetch_one("SELECT name FROM countries WHERE id=?", (s['from_country'],))
                    stype = s['sanction_type'] or ""
                    desc = s['description']
                    line = f"{EMOJI['sanction']} {stype}: {desc}"
                    if from_c:
                        line += f" – от {from_c['name']}"
                    content += line + "\n"
            else:
                content += "**Санкции:** нет\n"

        elif section == "territory":
            content += header
            content += f"{EMOJI['colony']} Колонии: нет\n"
            provs = await async_fetch_all("SELECT name FROM provinces WHERE country_id=?", (country['id'],))
            if provs:
                region_list = ", ".join([p['name'] for p in provs])
                content += f"{EMOJI['territory']} Регионы: {region_list}\n"
            else:
                content += f"{EMOJI['territory']} Регионы: нет\n"

        elif section == "buildings_info":
            content += header
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
                    lines.append(
                        f"{EMOJI['buildings_icon']} {btype}: {len(levels)} шт. (уровни: {', '.join(map(str, levels))})"
                    )
                content += "\n".join(lines)
            else:
                content += f"{EMOJI['buildings_icon']} Постройки: нет\n"

        elif section == "resources_info":
            content += header
            res = await async_fetch_all("SELECT resource_name, amount FROM resources WHERE country_id=?", (country['id'],))
            if res:
                for r in res:
                    content += f"{r['resource_name']}: {format_number(r['amount'], 0)}\n"
            else:
                content += "Нет ресурсов\n"

        elif section == "army":
            content += header
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

        return content

    async def show_section(self, interaction: discord.Interaction, section: str):
        text = await self.build_section(section)
        await interaction.response.edit_message(content=text, view=self)

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
# VIEW ДЛЯ ДИПЛОМАТИИ
# ========================
class DiplomacyView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Предложить союз", style=discord.ButtonStyle.primary)
    async def propose_alliance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/propose_pact alliance @игрок` (выберите подтип)", ephemeral=True)

    @discord.ui.button(label="Предложить торговый пакт", style=discord.ButtonStyle.primary)
    async def propose_trade_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/propose_pact trade @игрок`", ephemeral=True)

    @discord.ui.button(label="Предложить пакт о ненападении", style=discord.ButtonStyle.primary)
    async def propose_nap_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/propose_pact non_aggression @игрок`", ephemeral=True)

    @discord.ui.button(label="Мои пакты", style=discord.ButtonStyle.secondary)
    async def my_pacts_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pacts = await async_fetch_all(
            "SELECT id, type, subtype, from_country, to_country FROM pacts WHERE (from_country=? OR to_country=?) AND accepted=1",
            (self.country_id, self.country_id)
        )
        text = "**Ваши действующие соглашения:**\n"
        for p in pacts:
            partner_id = p['from_country'] if p['to_country'] == self.country_id else p['to_country']
            partner = await async_fetch_one("SELECT name FROM countries WHERE id=?", (partner_id,))
            partner_name = partner['name'] if partner else "Неизвестно"
            stype = f" ({p['subtype']})" if p['type'] == 'alliance' and p['subtype'] else ""
            text += f"ID {p['id']}: {p['type']}{stype} с {partner_name}\n"
        if not pacts:
            text += "Нет действующих пактов."
        await interaction.response.edit_message(content=text, view=self)

    @discord.ui.button(label="Мои санкции (исходящие)", style=discord.ButtonStyle.danger)
    async def my_sanctions_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        sanctions = await async_fetch_all(
            "SELECT id, to_country, sanction_type, description FROM sanctions WHERE from_country=?",
            (self.country_id,)
        )
        text = "**Ваши наложенные санкции:**\n"
        if sanctions:
            for s in sanctions:
                target = await async_fetch_one("SELECT name FROM countries WHERE id=?", (s['to_country'],))
                target_name = target['name'] if target else "Неизвестно"
                text += f"ID {s['id']}: {s['sanction_type']} – {s['description']} (против {target_name})\n"
            text += "Для снятия используйте `/lift_sanction ID`"
        else:
            text += "Нет активных санкций."
        await interaction.response.edit_message(content=text, view=self)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))


# ========================
# VIEW ДЛЯ АЛЬЯНСОВ
# ========================
class AlliancesView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Создать альянс", style=discord.ButtonStyle.success)
    async def create_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/create_alliance имя`", ephemeral=True)

    @discord.ui.button(label="Пригласить в альянс", style=discord.ButtonStyle.primary)
    async def invite_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/invite_alliance @игрок`", ephemeral=True)

    @discord.ui.button(label="Покинуть альянс", style=discord.ButtonStyle.danger)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/leave_alliance`", ephemeral=True)

    @discord.ui.button(label="Удалить участника", style=discord.ButtonStyle.danger)
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/kick_alliance @участник` (только для лидера)", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))


# ========================
# VIEW СТРОИТЕЛЬСТВА И ПРОЧИЕ
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
        text = "**Ваши ресурсы:**\n" + "\n".join(
            [f"{r['resource_name']}: {format_number(r['amount'], 0)}" for r in rows]
        )
        await interaction.response.edit_message(content=text, view=self)

    @discord.ui.button(label="🌍 Дипломатия", style=discord.ButtonStyle.primary)
    async def diplomacy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Дипломатические действия", view=DiplomacyView(self.country_id))

    @discord.ui.button(label="🤝 Альянсы", style=discord.ButtonStyle.success)
    async def alliances_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Управление альянсами", view=AlliancesView(self.country_id))

    @discord.ui.button(label="⚔️ Война", style=discord.ButtonStyle.danger)
    async def war_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Военные действия", view=WarMenuView(self.country_id))

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
        await interaction.response.send_message("Используйте команду `/rename`", ephemeral=True)

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
        await async_execute("UPDATE countries SET mobilization = 1 - mobilization WHERE id=?", (self.country_id,))
        await interaction.response.send_message("Мобилизация переключена.", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class WarMenuView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Объявить войну", style=discord.ButtonStyle.danger)
    async def declare_war_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/declare_war @игрок`", ephemeral=True)

    @discord.ui.button(label="Предложить мир", style=discord.ButtonStyle.primary)
    async def peace_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/peace_treaty @игрок`", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))


# ========================
# КОГ С КОМАНДАМИ
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
            await interaction.response.send_message(
                f"Вы уже управляете страной: {existing['name']}. Сначала откажитесь от неё.", ephemeral=True
            )
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
            await interaction.response.send_message(
                "Вы не управляете страной. Используйте `/country_choose`.", ephemeral=True
            )
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
            await interaction.response.send_message(
                f"Бонус можно забрать через {hours} ч {minutes} мин.", ephemeral=True
            )
            return
        bonus = {"Доллары": 500, "Продовольствие": 200, "Нефть": 100}
        for res, amount in bonus.items():
            await async_execute(
                "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) "
                "ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                (country_id, res, amount, amount)
            )
        await async_execute("UPDATE countries SET last_daily = ? WHERE id = ?", (now, country_id))
        await interaction.response.send_message(
            "Ежедневный бонус получен! +500$, +200 прод., +100 нефти.", ephemeral=True
        )

    @app_commands.command(name="stats", description="Статистика страны")
    @app_commands.describe(member="Игрок (оставьте пустым для своей статистики)")
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        target_user = member or interaction.user
        country = await async_fetch_one("SELECT * FROM countries WHERE owner_id=?", (target_user.id,))
        if not country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        country = dict(country)
        is_ally = (interaction.user.id == target_user.id) or interaction.user.guild_permissions.administrator
        view = StatsView(country, is_ally, target_user)
        name = country['display_name'] or country['name']
        flag_emoji = EMOJI.get('flag', '🏳️')
        header = f"Статистика игрока {target_user.mention}\n{flag_emoji} {name}"
        await interaction.response.send_message(header, view=view, ephemeral=True)

    # ---- ДИПЛОМАТИЯ ----
    @app_commands.command(name="propose_pact", description="Предложить дипломатический пакт")
    @app_commands.describe(target="Страна (игрок)", pact_type="Тип: alliance, trade, non_aggression", subtype="Подтип союза (для alliance)")
    async def propose_pact(self, interaction: discord.Interaction, target: discord.Member, pact_type: str, subtype: str = None):
        if pact_type not in ['alliance', 'trade', 'non_aggression']:
            await interaction.response.send_message("Неверный тип пакта.", ephemeral=True)
            return
        if pact_type == 'alliance':
            if subtype is None or subtype not in ALLIANCE_SUBTYPES:
                await interaction.response.send_message(f"Неверный подтип союза. Доступные: {', '.join(ALLIANCE_SUBTYPES)}", ephemeral=True)
                return
        my_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (target.id,))
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        if my_country['id'] == target_country['id']:
            await interaction.response.send_message("Нельзя заключить пакт с самим собой.", ephemeral=True)
            return

        if pact_type == 'alliance':
            # проверка лимитов (5 созданных, 10 участий)
            created = await async_fetch_one(
                "SELECT COUNT(*) as cnt FROM pacts WHERE from_country=? AND type='alliance' AND accepted=1",
                (my_country['id'],)
            )
            if created['cnt'] >= 5:
                await interaction.response.send_message("Вы уже создали максимальное количество союзов (5).", ephemeral=True)
                return
            total = await async_fetch_one(
                "SELECT COUNT(*) as cnt FROM pacts WHERE (from_country=? OR to_country=?) AND type='alliance' AND accepted=1",
                (my_country['id'], my_country['id'])
            )
            if total['cnt'] >= 10:
                await interaction.response.send_message("Вы уже участвуете в максимальном количестве союзов (10).", ephemeral=True)
                return

        existing = await async_fetch_one(
            "SELECT id FROM pacts WHERE ((from_country=? AND to_country=?) OR (from_country=? AND to_country=?)) AND type=? AND accepted=1",
            (my_country['id'], target_country['id'], target_country['id'], my_country['id'], pact_type)
        )
        if existing:
            await interaction.response.send_message("Такой пакт уже существует.", ephemeral=True)
            return

        await async_execute(
            "INSERT INTO pacts (from_country, to_country, type, subtype, accepted) VALUES (?, ?, ?, ?, 0)",
            (my_country['id'], target_country['id'], pact_type, subtype or "")
        )
        try:
            await target.send(f"{interaction.user.mention} предлагает вам {pact_type}{' (' + subtype + ')' if subtype else ''} пакт от страны {my_country['name']}. Используйте `/accept_pact` для принятия.")
        except:
            pass
        await interaction.response.send_message(f"Предложение пакта '{pact_type}' отправлено стране {target_country['name']}.", ephemeral=True)

    @app_commands.command(name="accept_pact", description="Принять предложенный пакт (приходит в ЛС)")
    async def accept_pact(self, interaction: discord.Interaction, pact_id: int = None):
        if pact_id is None:
            my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
            if not my_country:
                await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
                return
            proposals = await async_fetch_all(
                "SELECT id, from_country, type, subtype FROM pacts WHERE to_country=? AND accepted=0",
                (my_country['id'],)
            )
            if not proposals:
                await interaction.response.send_message("Нет входящих предложений.", ephemeral=True)
                return
            text = "**Входящие предложения:**\n"
            for p in proposals:
                from_country = await async_fetch_one("SELECT name FROM countries WHERE id=?", (p['from_country'],))
                subtype_str = f" ({p['subtype']})" if p['type'] == 'alliance' and p['subtype'] else ""
                text += f"ID: {p['id']} – {p['type']}{subtype_str} от {from_country['name']}\n"
            text += "Используйте `/accept_pact ID` чтобы принять."
            await interaction.response.send_message(text, ephemeral=True)
            return

        proposal = await async_fetch_one("SELECT * FROM pacts WHERE id=? AND accepted=0", (pact_id,))
        if not proposal:
            await interaction.response.send_message("Предложение не найдено или уже принято.", ephemeral=True)
            return
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country or proposal['to_country'] != my_country['id']:
            await interaction.response.send_message("Это предложение не вам.", ephemeral=True)
            return

        if proposal['type'] == 'alliance':
            total = await async_fetch_one(
                "SELECT COUNT(*) as cnt FROM pacts WHERE (from_country=? OR to_country=?) AND type='alliance' AND accepted=1",
                (my_country['id'], my_country['id'])
            )
            if total['cnt'] >= 10:
                await interaction.response.send_message("Вы уже участвуете в максимальном количестве союзов (10).", ephemeral=True)
                return

        await async_execute("UPDATE pacts SET accepted=1 WHERE id=?", (pact_id,))
        await interaction.response.send_message("Пакт принят!", ephemeral=True)

    @app_commands.command(name="break_pact", description="Расторгнуть пакт с указанной страной")
    @app_commands.describe(target="Страна, с которой разорвать пакт")
    async def break_pact(self, interaction: discord.Interaction, target: discord.Member):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (target.id,))
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        # Удаляем все активные пакты между странами
        await async_execute(
            "DELETE FROM pacts WHERE ((from_country=? AND to_country=?) OR (from_country=? AND to_country=?)) AND accepted=1",
            (my_country['id'], target_country['id'], target_country['id'], my_country['id'])
        )
        await interaction.response.send_message(f"Все пакты с {target_country['name']} расторгнуты.", ephemeral=True)

    @app_commands.command(name="impose_sanction", description="Наложить санкции с выбором типа")
    @app_commands.describe(target="Страна (игрок)", sanction_type="Тип санкции", description="Описание (необязательно)")
    @app_commands.command(name="impose_sanction", description="Наложить санкции с выбором типа")
    @app_commands.describe(target="Страна (игрок)", sanction_type="Тип санкции", description="Описание (необязательно)")
    async def impose_sanction(self, interaction: discord.Interaction, target: discord.Member, sanction_type: str, description: str = ""):
        if sanction_type not in SANCTION_TYPES:
            await interaction.response.send_message(f"Неизвестный тип санкции. Доступные: {', '.join(SANCTION_TYPES.keys())}", ephemeral=True)
            return
        my_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (target.id,))
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return

        stype = SANCTION_TYPES[sanction_type]
        param = stype['param']
        amount = stype['amount']
        desc = stype['desc'] if not description else description

        # Безопасная вставка имени столбца (проверено, что param есть в словаре)
        await async_execute(
            f'UPDATE countries SET "{param}" = "{param}" - ? WHERE id=?',
            (amount, target_country['id'])
        )

        await async_execute(
            "INSERT INTO sanctions (from_country, to_country, description, sanction_type, affected_param, effect_amount) VALUES (?, ?, ?, ?, ?, ?)",
            (my_country['id'], target_country['id'], desc, sanction_type, param, amount)
        )
        await interaction.response.send_message(f"Санкция '{desc}' наложена на {target_country['name']}.", ephemeral=True)

    @app_commands.command(name="lift_sanction", description="Снять санкцию по ID (посмотреть ID через кнопку 'Мои санкции')")
    @app_commands.describe(sanction_id="ID санкции для снятия")
    async def lift_sanction(self, interaction: discord.Interaction, sanction_id: int):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        sanction = await async_fetch_one(
            "SELECT * FROM sanctions WHERE id=? AND from_country=?",
            (sanction_id, my_country['id'])
        )
        if not sanction:
            await interaction.response.send_message("Санкция с таким ID не найдена или вы не её инициатор.", ephemeral=True)
            return

        # Восстановление параметра
        await async_execute(
            f'UPDATE countries SET "{sanction["affected_param"]}" = "{sanction["affected_param"]}" + ? WHERE id=?',
            (sanction['effect_amount'], sanction['to_country'])
        )
        await async_execute("DELETE FROM sanctions WHERE id=?", (sanction_id,))
        await interaction.response.send_message(f"Санкция ID {sanction_id} снята.", ephemeral=True)

    @app_commands.command(name="list_sanctions", description="Показать все ваши исходящие санкции")
    async def list_sanctions(self, interaction: discord.Interaction):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        sanctions = await async_fetch_all(
            "SELECT id, to_country, sanction_type, description FROM sanctions WHERE from_country=?",
            (my_country['id'],)
        )
        if not sanctions:
            await interaction.response.send_message("У вас нет активных санкций.", ephemeral=True)
            return
        text = "**Ваши наложенные санкции:**\n"
        for s in sanctions:
            target = await async_fetch_one("SELECT name FROM countries WHERE id=?", (s['to_country'],))
            target_name = target['name'] if target else "Неизвестно"
            text += f"ID {s['id']}: {s['sanction_type']} – {s['description']} (против {target_name})\n"
        await interaction.response.send_message(text, ephemeral=True)

    # ---- АЛЬЯНСЫ ----
    @app_commands.command(name="create_alliance", description="Создать новый альянс")
    async def create_alliance(self, interaction: discord.Interaction, alliance_name: str):
        my_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return

        leader_count = await async_fetch_one("SELECT COUNT(*) as cnt FROM alliances WHERE leader_id=?", (my_country['id'],))
        if leader_count['cnt'] >= 2:
            await interaction.response.send_message("Вы уже создали максимальное количество альянсов (2).", ephemeral=True)
            return

        member_count = await async_fetch_one("SELECT COUNT(*) as cnt FROM alliance_members WHERE country_id=?", (my_country['id'],))
        if member_count['cnt'] >= 5:
            await interaction.response.send_message("Вы уже состоите в максимальном количестве альянсов (5).", ephemeral=True)
            return

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        category = discord.utils.get(guild.categories, name="Альянсы")
        if category is None:
            category = await guild.create_category("Альянсы")
        channel = await guild.create_text_channel(alliance_name, category=category, overwrites=overwrites)
        await async_execute(
            "INSERT INTO alliances (name, leader_id, channel_id) VALUES (?, ?, ?)",
            (alliance_name, my_country['id'], channel.id)
        )
        alliance_id = (await async_fetch_one("SELECT id FROM alliances WHERE name=? AND leader_id=?", (alliance_name, my_country['id'])))['id']
        await async_execute("INSERT INTO alliance_members (alliance_id, country_id) VALUES (?, ?)", (alliance_id, my_country['id']))
        await interaction.response.send_message(f"Альянс '{alliance_name}' создан, канал {channel.mention}.", ephemeral=True)

    @app_commands.command(name="invite_alliance", description="Пригласить страну в ваш альянс (только лидер)")
    async def invite_alliance(self, interaction: discord.Interaction, target: discord.Member):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        alliance = await async_fetch_one(
            "SELECT a.id, a.name FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id WHERE am.country_id=? AND a.leader_id=?",
            (my_country['id'], my_country['id'])
        )
        if not alliance:
            await interaction.response.send_message("Вы не лидер альянса или не состоите в нём.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (target.id,))
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return

        target_member_count = await async_fetch_one("SELECT COUNT(*) as cnt FROM alliance_members WHERE country_id=?", (target_country['id'],))
        if target_member_count['cnt'] >= 5:
            await interaction.response.send_message(f"Игрок {target.mention} уже состоит в максимальном количестве альянсов (5).", ephemeral=True)
            return

        await async_execute("INSERT INTO alliance_members (alliance_id, country_id) VALUES (?, ?)", (alliance['id'], target_country['id']))
        channel = self.bot.get_channel((await async_fetch_one("SELECT channel_id FROM alliances WHERE id=?", (alliance['id'],)))['channel_id'])
        if channel:
            await channel.set_permissions(target, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"{target.mention} приглашён в альянс '{alliance['name']}'.", ephemeral=True)

    @app_commands.command(name="kick_alliance", description="Исключить участника из вашего альянса (только лидер)")
    async def kick_alliance(self, interaction: discord.Interaction, target: discord.Member):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        alliance = await async_fetch_one(
            "SELECT a.id, a.name, a.channel_id FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id WHERE am.country_id=? AND a.leader_id=?",
            (my_country['id'], my_country['id'])
        )
        if not alliance:
            await interaction.response.send_message("Вы не лидер альянса или не состоите в нём.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (target.id,))
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        # Проверяем, что цель состоит в альянсе
        member = await async_fetch_one("SELECT * FROM alliance_members WHERE alliance_id=? AND country_id=?", (alliance['id'], target_country['id']))
        if not member:
            await interaction.response.send_message("Этот игрок не состоит в вашем альянсе.", ephemeral=True)
            return
        if target_country['id'] == my_country['id']:
            await interaction.response.send_message("Вы не можете исключить самого себя.", ephemeral=True)
            return

        await async_execute("DELETE FROM alliance_members WHERE alliance_id=? AND country_id=?", (alliance['id'], target_country['id']))
        channel = self.bot.get_channel(alliance['channel_id'])
        if channel:
            await channel.set_permissions(target, overwrite=None)
        await interaction.response.send_message(f"{target.mention} исключён из альянса '{alliance['name']}'.", ephemeral=True)

    @app_commands.command(name="leave_alliance", description="Покинуть текущий альянс")
    async def leave_alliance(self, interaction: discord.Interaction):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        member = await async_fetch_one("SELECT alliance_id FROM alliance_members WHERE country_id=?", (my_country['id'],))
        if not member:
            await interaction.response.send_message("Вы не состоите в альянсе.", ephemeral=True)
            return
        alliance = await async_fetch_one("SELECT id, name, leader_id, channel_id FROM alliances WHERE id=?", (member['alliance_id'],))
        if alliance['leader_id'] == my_country['id']:
            await interaction.response.send_message("Лидер не может покинуть альянс. Распустите его командой `/disband_alliance`.", ephemeral=True)
            return
        await async_execute("DELETE FROM alliance_members WHERE alliance_id=? AND country_id=?", (alliance['id'], my_country['id']))
        channel = self.bot.get_channel(alliance['channel_id'])
        if channel:
            await channel.set_permissions(interaction.user, overwrite=None)
        await interaction.response.send_message(f"Вы покинули альянс '{alliance['name']}'.", ephemeral=True)

    @app_commands.command(name="disband_alliance", description="Распустить альянс (только лидер)")
    async def disband_alliance(self, interaction: discord.Interaction):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        alliance = await async_fetch_one(
            "SELECT a.id, a.name, a.channel_id FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id WHERE am.country_id=? AND a.leader_id=?",
            (my_country['id'], my_country['id'])
        )
        if not alliance:
            await interaction.response.send_message("Вы не лидер альянса.", ephemeral=True)
            return
        channel = self.bot.get_channel(alliance['channel_id'])
        if channel:
            await channel.delete()
        await async_execute("DELETE FROM alliance_members WHERE alliance_id=?", (alliance['id'],))
        await async_execute("DELETE FROM alliances WHERE id=?", (alliance['id'],))
        await interaction.response.send_message(f"Альянс '{alliance['name']}' распущен.", ephemeral=True)

    # ---- ВОЙНА ----
    @app_commands.command(name="declare_war", description="Объявить войну стране")
    async def declare_war(self, interaction: discord.Interaction, target: discord.Member):
        my_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (target.id,))
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        existing = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (my_country['id'], target_country['id'], target_country['id'], my_country['id'])
        )
        if existing:
            await interaction.response.send_message("Вы уже воюете с этой страной.", ephemeral=True)
            return
        await async_execute(
            "INSERT INTO wars (attacker_id, defender_id, status, start_time) VALUES (?, ?, 'active', ?)",
            (my_country['id'], target_country['id'], time.time())
        )
        war_channel_name = "военные-сводки"
        war_channel = discord.utils.get(interaction.guild.text_channels, name=war_channel_name)
        if war_channel:
            await war_channel.send(f"⚔️ {my_country['name']} объявил войну {target_country['name']}!")
        await interaction.response.send_message(f"Война объявлена стране {target_country['name']}.", ephemeral=True)

    @app_commands.command(name="peace_treaty", description="Предложить мир противнику")
    async def peace_treaty(self, interaction: discord.Interaction, target: discord.Member):
        my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (target.id,))
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        war = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (my_country['id'], target_country['id'], target_country['id'], my_country['id'])
        )
        if not war:
            await interaction.response.send_message("Вы не находитесь в состоянии войны с этой страной.", ephemeral=True)
            return
        await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
        await interaction.response.send_message(f"Мир заключён с {target_country['name']}.", ephemeral=True)

    # ---- УПРАВЛЕНИЕ ГОСУДАРСТВОМ ----
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
