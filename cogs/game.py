import discord
from discord.ext import commands
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute, async_get_game_date
from data.buildings import BUILDING_TYPES
from data.military import MILITARY_EQUIPMENT, WEAPONS
try:
    from config import CHANNEL_IDS
except ImportError:
    CHANNEL_IDS = {}
import time
import datetime
import random
from zoneinfo import ZoneInfo

# Континенты и страны с флагами (эмодзи Discord)
CONTINENTS = {
    "Европа": {
        "Российская Федерация": "🇷🇺",
        "Германия": "🇩🇪",
        "Франция": "🇫🇷",
        "Великобритания": "🇬🇧",
        "Италия": "🇮🇹",
        "Испания": "🇪🇸",
        "Польша": "🇵🇱",
        "Украина": "🇺🇦",
        "Швеция": "🇸🇪",
        "Норвегия": "🇳🇴",
        "Финляндия": "🇫🇮",
        "Греция": "🇬🇷",
        "Португалия": "🇵🇹",
        "Нидерланды": "🇳🇱",
        "Бельгия": "🇧🇪",
        "Австрия": "🇦🇹",
        "Швейцария": "🇨🇭",
        "Дания": "🇩🇰",
        "Ирландия": "🇮🇪",
        "Чехия": "🇨🇿",
        "Румыния": "🇷🇴",
        "Венгрия": "🇭🇺",
        "Словакия": "🇸🇰",
        "Болгария": "🇧🇬",
        "Сербия": "🇷🇸",
        "Хорватия": "🇭🇷",
        "Словения": "🇸🇮",
        "Эстония": "🇪🇪",
        "Латвия": "🇱🇻",
        "Литва": "🇱🇹",
        "Исландия": "🇮🇸",
        "Беларусь": "🇧🇾",
        "Молдова": "🇲🇩",
        "Люксембург": "🇱🇺",
        "Монако": "🇲🇨",
        "Андорра": "🇦🇩",
        "Мальта": "🇲🇹",
        "Сан-Марино": "🇸🇲",
        "Ватикан": "🇻🇦"
    },
    "Азия": {
        "Китай": "🇨🇳",
        "Индия": "🇮🇳",
        "Япония": "🇯🇵",
        "Южная Корея": "🇰🇷",
        "Турция": "🇹🇷",
        "Индонезия": "🇮🇩",
        "Саудовская Аравия": "🇸🇦",
        "Иран": "🇮🇷",
        "Ирак": "🇮🇶",
        "Афганистан": "🇦🇫",
        "Пакистан": "🇵🇰",
        "Бангладеш": "🇧🇩",
        "Вьетнам": "🇻🇳",
        "Таиланд": "🇹🇭",
        "Малайзия": "🇲🇾",
        "Филиппины": "🇵🇭",
        "Мьянма": "🇲🇲",
        "Казахстан": "🇰🇿",
        "Узбекистан": "🇺🇿",
        "Туркменистан": "🇹🇲",
        "Киргизия": "🇰🇬",
        "Таджикистан": "🇹🇯",
        "Монголия": "🇲🇳",
        "Непал": "🇳🇵",
        "Шри-Ланка": "🇱🇰",
        "Камбоджа": "🇰🇭",
        "Лаос": "🇱🇦",
        "Бруней": "🇧🇳",
        "Мальдивы": "🇲🇻",
        "Бутан": "🇧🇹",
        "Сингапур": "🇸🇬",
        "Восточный Тимор": "🇹🇱"
    },
    "Африка": {
        "Нигерия": "🇳🇬",
        "Эфиопия": "🇪🇹",
        "Египет": "🇪🇬",
        "ДР Конго": "🇨🇩",
        "ЮАР": "🇿🇦",
        "Танзания": "🇹🇿",
        "Кения": "🇰🇪",
        "Уганда": "🇺🇬",
        "Алжир": "🇩🇿",
        "Судан": "🇸🇩",
        "Марокко": "🇲🇦",
        "Ангола": "🇦🇴",
        "Гана": "🇬🇭",
        "Мозамбик": "🇲🇿",
        "Мадагаскар": "🇲🇬",
        "Камерун": "🇨🇲",
        "Кот-д'Ивуар": "🇨🇮",
        "Буркина-Фасо": "🇧🇫",
        "Мали": "🇲🇱",
        "Малави": "🇲🇼",
        "Замбия": "🇿🇲",
        "Сенегал": "🇸🇳",
        "Чад": "🇹🇩",
        "Сомали": "🇸🇴",
        "Зимбабве": "🇿🇼",
        "Руанда": "🇷🇼",
        "Тунис": "🇹🇳",
        "Гвинея": "🇬🇳",
        "Бенин": "🇧🇯",
        "Бурунди": "🇧🇮",
        "Южный Судан": "🇸🇸",
        "Нигер": "🇳🇪",
        "ЦАР": "🇨🇫"
    },
    "Северная Америка": {
        "США": "🇺🇸",
        "Канада": "🇨🇦",
        "Мексика": "🇲🇽",
        "Гватемала": "🇬🇹",
        "Куба": "🇨🇺",
        "Гаити": "🇭🇹",
        "Доминиканская Республика": "🇩🇴",
        "Гондурас": "🇭🇳",
        "Сальвадор": "🇸🇻",
        "Никарагуа": "🇳🇮",
        "Коста-Рика": "🇨🇷",
        "Панама": "🇵🇦",
        "Ямайка": "🇯🇲",
        "Тринидад и Тобаго": "🇹🇹",
        "Багамы": "🇧🇸",
        "Белиз": "🇧🇿",
        "Барбадос": "🇧🇧",
        "Сент-Люсия": "🇱🇨",
        "Сент-Винсент и Гренадины": "🇻🇨",
        "Гренада": "🇬🇩"
    },
    "Южная Америка": {
        "Бразилия": "🇧🇷",
        "Аргентина": "🇦🇷",
        "Колумбия": "🇨🇴",
        "Перу": "🇵🇪",
        "Венесуэла": "🇻🇪",
        "Чили": "🇨🇱",
        "Эквадор": "🇪🇨",
        "Боливия": "🇧🇴",
        "Парагвай": "🇵🇾",
        "Уругвай": "🇺🇾",
        "Гайана": "🇬🇾",
        "Суринам": "🇸🇷",
        "Французская Гвиана": "🇬🇫"
    },
    "Океания": {
        "Австралия": "🇦🇺",
        "Новая Зеландия": "🇳🇿",
        "Папуа - Новая Гвинея": "🇵🇬",
        "Фиджи": "🇫🇯",
        "Соломоновы Острова": "🇸🇧",
        "Вануату": "🇻🇺",
        "Самоа": "🇼🇸",
        "Тонга": "🇹🇴",
        "Федеративные Штаты Микронезии": "🇫🇲",
        "Маршалловы Острова": "🇲🇭",
        "Палау": "🇵🇼",
        "Науру": "🇳🇷",
        "Кирибати": "🇰🇮",
        "Тувалу": "🇹🇻"
    }
}

# Импорт ID из конфига (если нет — пустые словари)
try:
    from config import CATEGORY_IDS, IDEOLOGY_ROLES, GOVERNMENT_ROLES, RELIGION_ROLES, DEFAULT_PLAYER_ROLE_ID, COUNTRY_ROLES
except ImportError:
    CATEGORY_IDS = {}
    IDEOLOGY_ROLES = {}
    GOVERNMENT_ROLES = {}
    RELIGION_ROLES = {}
    DEFAULT_PLAYER_ROLE_ID = 0
    COUNTRY_ROLES = {}

# Доступные ресурсы
RESOURCE_NAMES = [
    "Нефть", "Природный газ", "Уголь", "Железная руда", "Медь", "Алюминий",
    "Уран", "Золото", "Серебро", "Алмазы", "Древесина", "Пресная вода",
    "Продовольствие", "Редкоземельные металлы", "Кремний", "Литий", "Каучук"
]

# ========================
# КОНСТАНТЫ
# ========================
EMOJI = {
    "budget": "<:budget:123456789>", "population": "👥", "support": "👍",
    "eco_stab": "<:eco:123456789>", "health": "<:health:123456789>",
    "industry": "<:industry:123456789>", "science": "<:science:123456789>",
    "mood": "<:mood:123456789>", "crime": "<:crime:123456789>",
    "ecology": "<:ecology:123456789>", "gov_eff": "<:gov:123456789>",
    "info_sec": "<:info_sec:123456789>", "counter_int": "<:counter_int:123456789>",
    "growth": "<:growth:123456789>", "army_strength": "<:army:123456789>",
    "army_count": "<:soldiers:123456789>", "reservists": "<:reserv:123456789>",
    "weapon": "<:weapon:123456789>", "vehicle": "<:vehicle:123456789>",
    "buildings_icon": "<:buildings:123456789>", "territory": "<:territory:123456789>",
    "colony": "🏝️", "war_status": "⚔️", "dependency": "🔗",
    "alliance": "🤝", "sanction": "🚫", "aggression": "😈",
    "prestige": "🌟", "flag": "🏳️"
}

ALLIANCE_SUBTYPES = [
    "military", "economic", "trade", "defensive", "research",
    "cultural", "political", "full", "military_economic",
    "economic_trade", "military_defensive", "technological",
    "educational", "environmental", "health"
]

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

SANCTION_CHOICES = [
    app_commands.Choice(name="Торговое эмбарго", value="trade_embargo"),
    app_commands.Choice(name="Оружейное эмбарго", value="arms_embargo"),
    app_commands.Choice(name="Запрет на поездки", value="travel_ban"),
    app_commands.Choice(name="Визовый бан", value="visa_ban"),
    app_commands.Choice(name="Финансовые санкции", value="financial_sanctions"),
    app_commands.Choice(name="Заморозка активов", value="asset_freeze"),
    app_commands.Choice(name="Дипломатическая изоляция", value="diplomatic_isolation"),
    app_commands.Choice(name="Спортивная изоляция", value="sport_isolation"),
    app_commands.Choice(name="Культурный бан", value="cultural_ban"),
    app_commands.Choice(name="Технологическое эмбарго", value="technology_ban"),
    app_commands.Choice(name="Продовольственное эмбарго", value="food_embargo"),
    app_commands.Choice(name="Эмбарго на медикаменты", value="medicine_embargo"),
    app_commands.Choice(name="Энергетическое эмбарго", value="energy_embargo"),
    app_commands.Choice(name="Запрет на торговлю оружием", value="arms_trade_ban"),
    app_commands.Choice(name="Нефтяное эмбарго", value="oil_embargo"),
    app_commands.Choice(name="Газовое эмбарго", value="gas_embargo"),
    app_commands.Choice(name="Угольное эмбарго", value="coal_embargo"),
    app_commands.Choice(name="Алмазное эмбарго", value="diamond_embargo"),
    app_commands.Choice(name="Золотое эмбарго", value="gold_embargo"),
    app_commands.Choice(name="Урановое эмбарго", value="uranium_embargo"),
    app_commands.Choice(name="Эмбарго на древесину", value="timber_embargo"),
    app_commands.Choice(name="Текстильное эмбарго", value="textile_embargo"),
    app_commands.Choice(name="Эмбарго на оборудование", value="machinery_embargo")
]

# Для выбора религии/правительства/идеологии
RELIGION_CHOICES = [
    app_commands.Choice(name="Христианство", value="Христианство"),
    app_commands.Choice(name="Ислам", value="Ислам"),
    app_commands.Choice(name="Иудаизм", value="Иудаизм"),
    app_commands.Choice(name="Буддизм", value="Буддизм"),
    app_commands.Choice(name="Индуизм", value="Индуизм"),
    app_commands.Choice(name="Светское государство", value="Светское государство"),
    app_commands.Choice(name="Запрет на религию", value="Запрет на религию")
]

GOVERNMENT_CHOICES = [
    app_commands.Choice(name="Президентская республика", value="Президентская республика"),
    app_commands.Choice(name="Парламентская республика", value="Парламентская республика"),
    app_commands.Choice(name="Смешанная республика", value="Смешанная республика"),
    app_commands.Choice(name="Конституционная монархия", value="Конституционная монархия"),
    app_commands.Choice(name="Абсолютная монархия", value="Абсолютная монархия"),
    app_commands.Choice(name="Дуалистическая монархия", value="Дуалистическая монархия"),
    app_commands.Choice(name="Теократия", value="Теократия"),
    app_commands.Choice(name="Однопартийная республика", value="Однопартийная республика")
]

IDEOLOGY_CHOICES = [
    app_commands.Choice(name="Либерализм", value="Либерализм"),
    app_commands.Choice(name="Национализм", value="Национализм"),
    app_commands.Choice(name="Социал-демократия", value="Социал-демократия"),
    app_commands.Choice(name="Коммунизм", value="Коммунизм"),
    app_commands.Choice(name="Демократия", value="Демократия"),
    app_commands.Choice(name="Консерватизм", value="Консерватизм"),
    app_commands.Choice(name="Национал-демократия", value="Национал-демократия"),
    app_commands.Choice(name="Монархизм", value="Монархизм"),
    app_commands.Choice(name="Анархизм", value="Анархизм")
]

pending_alliance_invites = {}

# Новостные шаблоны
MOBILIZE_ON_NEWS = [
    "⚡️ СРОЧНАЯ НОВОСТЬ: В стране {country} объявлена всеобщая мобилизация! Правитель {ruler} призвал граждан к оружию.",
    "📢 Экстренное сообщение: {country} переходит на военное положение. {ruler} подписал указ о мобилизации.",
    "🚨 Внимание! {country} вводит мобилизацию. Военные комиссариаты открыты, граждане призываются на службу.",
    "🔔 Новости: в {country} началась мобилизация населения. Армия готовится к возможным конфликтам.",
    "⚔️ {ruler} объявил о всеобщей мобилизации в {country}. Войска приводятся в полную боевую готовность."
]
MOBILIZE_OFF_NEWS = [
    "🕊️ Новости: {country} отменяет мобилизацию. {ruler} заявил о возвращении к мирной жизни.",
    "📰 Сообщение из {country}: мобилизация прекращена. Военнослужащие возвращаются домой.",
    "🔔 {ruler} подписал указ о демобилизации в {country}. Военное положение снято.",
    "✅ В {country} завершена мобилизация. {ruler} поблагодарил граждан за службу.",
    "🏳️ {country} возвращается к мирной жизни. Мобилизационные мероприятия прекращены."
]

LENDLEASE_MONEY_NEWS = [
    "💰 {sender} оказал финансовую помощь {receiver} в размере {amount} долларов.",
    "🤝 {sender} перевел {amount}$ стране {receiver}.",
    "💵 Ленд-лиз: {sender} выделил {amount} долларов для {receiver}.",
    "💲 Финансовый транш: {sender} → {receiver} на сумму {amount}$.",
    "📊 Экономическая поддержка: {sender} направил {amount} долларов в {receiver}."
]
LENDLEASE_RESOURCE_NEWS = [
    "📦 {sender} отправил {amount} {resource} стране {receiver}.",
    "🚚 Ленд-лиз: {sender} поставил {amount} {resource} в {receiver}.",
    "📤 {sender} передал {amount} единиц {resource} для {receiver}.",
    "🤲 Гуманитарная помощь: {sender} → {receiver}: {amount} {resource}.",
    "🔁 Ресурсный обмен: {sender} поделился {amount} {resource} с {receiver}."
]

# ========================
# УТИЛИТЫ
# ========================
def format_number(n, decimals=0):
    if n is None:
        return "0"
    if decimals == 0:
        return f"{int(n):,}".replace(",", ".")
    else:
        return f"{n:,.{decimals}f}".replace(",", ".").replace(".", ",", 1)

def get_color_circle(value):
    if value <= 20: return "🔴"
    elif value <= 40: return "🟠"
    elif value <= 60: return "🟡"
    elif value <= 80: return "🟢"
    else: return "🔵"

def get_aggression_text(score):
    if score <= 20: return "Мирное", "🔵"
    elif score <= 40: return "Умеренное", "🟢"
    elif score <= 60: return "Нейтральное", "🟡"
    elif score <= 80: return "Агрессивное", "🟠"
    else: return "Сильно агрессивное", "🔴"

def get_prestige_text(score):
    if score <= 20: return "Незначимый", "🔴"
    elif score <= 40: return "Минимальное влияние", "🟠"
    elif score <= 60: return "Влиятельный", "🟡"
    elif score <= 80: return "Сильно-Влиятельный", "🟢"
    else: return "Сверхвлиятельный", "🔵"

# Выпадающий список ресурсов
RESOURCE_CHOICES = [app_commands.Choice(name=r, value=r) for r in RESOURCE_NAMES]

# ========================
# VIEW: СТАТИСТИКА
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
        flag_emoji = EMOJI.get('flag', '🏳️')
        nick = self.target_user.display_name

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
            budget_val = country['budget']
            content += f"{EMOJI['budget']} Бюджет: {format_number(budget_val, 2)}$\n"
            pop = country.get('population', 0)
            content += f"{EMOJI['population']} Население: {format_number(pop)} человек\n"
            content += f"{EMOJI['support']} Рейтинг поддержки правительства: {int(country['citizen_mood'])}\n"

        elif section == "development":
            content += header
            content += param_line(EMOJI['eco_stab'], "Экономическая стабильность", country['economic_stability'])
            content += param_line(EMOJI['health'], "Здоровье населения", country['health'])
            content += param_line(EMOJI['industry'], "Промышленность", country['industry_level'])
            content += param_line(EMOJI['science'], "Научный прогресс", country['science_progress'])
            content += param_line(EMOJI['mood'], "Настрой граждан", country['citizen_mood'])
            content += param_line(EMOJI['crime'], "Преступность", country['crime_rate'])
            content += param_line(EMOJI['ecology'], "Экология", country['ecology'])
            content += f"{EMOJI['gov_eff']} Эффективность правительства: ур. {int(country['government_efficiency'])}\n"
            if self.is_ally:
                content += f"{EMOJI['info_sec']} Информационная безопасность: ур. {int(country['info_security'])}\n"
                content += f"{EMOJI['counter_int']} Контрразведка: ур. {int(country['counter_intelligence'])}\n"
            else:
                content += f"{EMOJI['info_sec']} Информационная безопасность: неизвестно\n"
                content += f"{EMOJI['counter_int']} Контрразведка: неизвестно\n"
            content += f"{EMOJI['growth']} Демографический рост: {country['demographic_growth']:.2f}% (в год)\n"

        elif section == "international":
            content += header
            aggr_text, aggr_circle = get_aggression_text(country['aggression_score'])
            content += f"{EMOJI['aggression']} Агрессия государства: {aggr_circle} {aggr_text}\n"
            prest_text, prest_circle = get_prestige_text(country['international_prestige'])
            content += f"{EMOJI['prestige']} Международный авторитет: {prest_circle} {prest_text}\n"

            wars = await async_fetch_all(
                "SELECT c2.name AS enemy FROM wars w "
                "JOIN countries c2 ON (c2.id = CASE WHEN w.attacker_id = ? THEN w.defender_id ELSE w.attacker_id END) "
                "WHERE (w.attacker_id = ? OR w.defender_id = ?) AND w.status = 'active'",
                (country['id'], country['id'], country['id']))
            if wars:
                enemies = [w['enemy'] for w in wars]
                content += f"{EMOJI['war_status']} В состоянии войны: да (против: {', '.join(enemies)})\n"
            else:
                content += f"{EMOJI['war_status']} В состоянии войны: нет\n"

            content += f"{EMOJI['dependency']} Зависимость: независимое\n"

            if self.is_ally:
                pacts = await async_fetch_all(
                    "SELECT p.type, p.subtype, c2.name AS partner FROM pacts p "
                    "JOIN countries c2 ON (c2.id = CASE WHEN p.from_country = ? THEN p.to_country ELSE p.from_country END) "
                    "WHERE (p.from_country = ? OR p.to_country = ?) AND p.accepted = 1",
                    (country['id'], country['id'], country['id']))
                allies = []
                trade = []
                for p in pacts:
                    if p['type'] == 'alliance':
                        allies.append(f"{p['partner']} ({p['subtype']})")
                    elif p['type'] == 'trade':
                        trade.append(p['partner'])
                content += f"{EMOJI['alliance']} Союзы: {', '.join(allies) if allies else 'нет'}\n"
                content += f"{EMOJI['alliance']} Торговые партнёры: {', '.join(trade) if trade else 'нет'}\n"

                alliances = await async_fetch_all(
                    "SELECT a.name FROM alliances a "
                    "JOIN alliance_members am ON a.id = am.alliance_id "
                    "WHERE am.country_id = ?",
                    (country['id'],))
                if alliances:
                    content += f"{EMOJI['alliance']} Альянсы: {', '.join([a['name'] for a in alliances])}\n"
                else:
                    content += f"{EMOJI['alliance']} Альянсы: нет\n"
            else:
                content += f"{EMOJI['alliance']} Союзы: неизвестно\n"
                content += f"{EMOJI['alliance']} Торговые партнёры: неизвестно\n"
                content += f"{EMOJI['alliance']} Альянсы: неизвестно\n"

            sanctions = await async_fetch_all(
                "SELECT s.sanction_type, s.description, c2.name AS from_name FROM sanctions s "
                "JOIN countries c2 ON s.from_country = c2.id "
                "WHERE s.to_country = ?",
                (country['id'],))
            if sanctions:
                content += "**Санкции:**\n"
                for s in sanctions:
                    line = f"{EMOJI['sanction']} {s['sanction_type']}: {s['description']}"
                    if s['from_name']:
                        line += f" – от {s['from_name']}"
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
                (country['id'],))
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
            army_count = country.get('army_count', 0)
            content += f"{EMOJI['army_count']} Численность армии: {format_number(army_count)} человек\n"
            if self.is_ally:
                population = country.get('population', 0)
                reservists = max(0, population - army_count)
                content += f"{EMOJI['reservists']} Военный резерв: {format_number(reservists)} человек\n"
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
# VIEW: ПРИГЛАШЕНИЯ И ПАКТЫ
# ========================
class AllianceInviteView(discord.ui.View):
    def __init__(self, alliance_id, alliance_name, leader_country_id, target_user_id):
        super().__init__(timeout=None)
        self.alliance_id = alliance_id
        self.alliance_name = alliance_name
        self.leader_country_id = leader_country_id
        self.target_user_id = target_user_id

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("Это приглашение не для вас.", ephemeral=True)
            return
        invite = pending_alliance_invites.pop(self.target_user_id, None)
        if not invite or invite[0] != self.alliance_id:
            await interaction.response.send_message("Приглашение больше не действительно.", ephemeral=True)
            return
        target_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not target_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        member_count = await async_fetch_one("SELECT COUNT(*) as cnt FROM alliance_members WHERE country_id=?", (target_country['id'],))
        if member_count['cnt'] >= 5:
            await interaction.response.send_message("Вы уже состоите в максимальном количестве альянсов (5).", ephemeral=True)
            return
        await async_execute("INSERT INTO alliance_members (alliance_id, country_id) VALUES (?, ?)", (self.alliance_id, target_country['id']))
        channel_id_row = await async_fetch_one("SELECT channel_id FROM alliances WHERE id=?", (self.alliance_id,))
        if channel_id_row:
            channel = interaction.client.get_channel(channel_id_row['channel_id'])
            if channel:
                await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        leader_country = await async_fetch_one("SELECT owner_id, name FROM countries WHERE id=?", (self.leader_country_id,))
        if leader_country:
            leader_user = interaction.client.get_user(leader_country['owner_id'])
            if leader_user:
                try:
                    await leader_user.send(f"Игрок {interaction.user.mention} принял приглашение в альянс **{self.alliance_name}** (страна **{target_country['name']}**).")
                except:
                    pass
        await interaction.response.edit_message(content=f"Вы вступили в альянс **{self.alliance_name}**.", view=None)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger)
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("Это приглашение не для вас.", ephemeral=True)
            return
        invite = pending_alliance_invites.pop(self.target_user_id, None)
        if invite:
            leader_country = await async_fetch_one("SELECT owner_id, name FROM countries WHERE id=?", (invite[1],))
            if leader_country:
                leader_user = interaction.client.get_user(leader_country['owner_id'])
                if leader_user:
                    try:
                        await leader_user.send(f"Игрок {interaction.user.mention} отклонил приглашение в альянс **{self.alliance_name}**.")
                    except:
                        pass
        await interaction.response.edit_message(content="Вы отклонили приглашение в альянс.", view=None)

class PactProposalView(discord.ui.View):
    def __init__(self, pact_id, target_user_id, from_country_id, pact_type, subtype):
        super().__init__(timeout=None)
        self.pact_id = pact_id
        self.target_user_id = target_user_id
        self.from_country_id = from_country_id
        self.pact_type = pact_type
        self.subtype = subtype

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("Это предложение не для вас.", ephemeral=True)
            return
        proposal = await async_fetch_one("SELECT * FROM pacts WHERE id=? AND accepted=0", (self.pact_id,))
        if not proposal:
            await interaction.response.edit_message(content="Это предложение уже не действительно.", view=None)
            return
        my_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not my_country:
            await interaction.response.edit_message(content="Вы не управляете страной.", view=None)
            return
        if proposal['to_country'] != my_country['id']:
            await interaction.response.edit_message(content="Вы не являетесь получателем этого предложения.", view=None)
            return
        if proposal['type'] == 'alliance':
            total = await async_fetch_one("SELECT COUNT(*) as cnt FROM pacts WHERE (from_country=? OR to_country=?) AND type='alliance' AND accepted=1", (my_country['id'], my_country['id']))
            if total['cnt'] >= 10:
                await interaction.response.edit_message(content="Вы уже участвуете в максимальном количестве союзов (10).", view=None)
                return
        await async_execute("UPDATE pacts SET accepted=1 WHERE id=?", (self.pact_id,))
        from_country = await async_fetch_one("SELECT owner_id, name FROM countries WHERE id=?", (self.from_country_id,))
        if from_country:
            initiator = interaction.client.get_user(from_country['owner_id'])
            if initiator:
                subtype_str = f" ({self.subtype})" if self.pact_type == 'alliance' and self.subtype else ""
                try:
                    await initiator.send(f"Ваше предложение пакта **{self.pact_type}{subtype_str}** было **принято** страной **{my_country['name']}**.")
                except:
                    pass
        await interaction.response.edit_message(content=f"Вы приняли предложение пакта **{self.pact_type}**{(' (' + self.subtype + ')') if self.subtype else ''}.", view=None)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger)
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("Это предложение не для вас.", ephemeral=True)
            return
        proposal = await async_fetch_one("SELECT * FROM pacts WHERE id=? AND accepted=0", (self.pact_id,))
        if not proposal:
            await interaction.response.edit_message(content="Это предложение уже не действительно.", view=None)
            return
        await async_execute("DELETE FROM pacts WHERE id=?", (self.pact_id,))
        from_country = await async_fetch_one("SELECT owner_id, name FROM countries WHERE id=?", (self.from_country_id,))
        if from_country:
            initiator = interaction.client.get_user(from_country['owner_id'])
            if initiator:
                try:
                    await initiator.send(f"Ваше предложение пакта **{self.pact_type}** было **отклонено** страной {interaction.user.mention}.")
                except:
                    pass
        await interaction.response.edit_message(content="Вы отклонили предложение пакта.", view=None)

# ========================
# VIEW: МЕНЮ
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
        pacts = await async_fetch_all("SELECT id, type, subtype, from_country, to_country FROM pacts WHERE (from_country=? OR to_country=?) AND accepted=1", (self.country_id, self.country_id))
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

    @discord.ui.button(label="Мои санкции", style=discord.ButtonStyle.danger)
    async def my_sanctions_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        sanctions = await async_fetch_all("SELECT id, to_country, sanction_type, description FROM sanctions WHERE from_country=?", (self.country_id,))
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

    @discord.ui.button(label="Принять приглашение", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/accept_alliance`", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class GameMenu(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="🏭 Постройки", style=discord.ButtonStyle.primary)
    async def buildings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        provinces = await async_fetch_all("SELECT id, name FROM provinces WHERE country_id=?", (self.country_id,))
        if not provinces:
            await interaction.response.send_message("У вашей страны нет регионов.", ephemeral=True)
            return
        view = ProvinceSelectView(self.country_id, provinces)
        await interaction.response.edit_message(content="Выберите регион:", view=view)

    @discord.ui.button(label="💰 Ресурсы", style=discord.ButtonStyle.primary)
    async def resources_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        rows = await async_fetch_all("SELECT resource_name, amount FROM resources WHERE country_id=?", (self.country_id,))
        text = "**Ваши ресурсы:**\n" + "\n".join([f"{r['resource_name']}: {format_number(r['amount'], 0)}" for r in rows])
        await interaction.response.edit_message(content=text, view=self)

    @discord.ui.button(label="🌍 Дипломатия", style=discord.ButtonStyle.primary)
    async def diplomacy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Дипломатические действия", view=DiplomacyView(self.country_id))

    @discord.ui.button(label="🤝 Альянсы", style=discord.ButtonStyle.success)
    async def alliances_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Управление альянсами", view=AlliancesView(self.country_id))

    @discord.ui.button(label="⚔️ Война", style=discord.ButtonStyle.danger)
    async def war_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Военное меню", view=WarMainMenu(self.country_id))

    @discord.ui.button(label="🛡️ Армия", style=discord.ButtonStyle.primary)
    async def army_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Управление армией", view=ArmyView(self.country_id))

    @discord.ui.button(label="🏛️ Управление", style=discord.ButtonStyle.success)
    async def gov_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Управление государством", view=GovernmentView(self.country_id))

    @discord.ui.button(label="🛒 Рынок", style=discord.ButtonStyle.primary)
    async def market_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lots = await async_fetch_all("SELECT id, resource_name, amount, price, seller_id FROM market WHERE sold=0")
        if not lots:
            content = "На рынке нет активных предложений."
        else:
            content = "**Рынок**\n"
            for lot in lots:
                seller_country = await async_fetch_one("SELECT name, owner_id FROM countries WHERE id=?", (lot['seller_id'],))
                seller_name = seller_country['name'] if seller_country else "Неизвестно"
                content += f"Лот #{lot['id']}: {lot['resource_name']} x{lot['amount']} за {lot['price']}$ (продавец: {seller_name})\n"
            content += "\nИспользуйте `/market buy <id>` для покупки."
        await interaction.response.edit_message(content=content, view=MarketMenuView(self.country_id))

class ProvinceSelectView(discord.ui.View):
    def __init__(self, country_id, provinces):
        super().__init__(timeout=None)
        self.country_id = country_id
        options = [discord.SelectOption(label=p['name'], value=str(p['id'])) for p in provinces]
        select = discord.ui.Select(placeholder="Регион...", options=options)
        select.callback = self.select_province
        self.add_item(select)

    async def select_province(self, interaction: discord.Interaction):
        await interaction.response.defer()  # чтобы успеть загрузить данные
        province_id = int(interaction.data['values'][0])
        await self.show_province_info(interaction, province_id)

    async def show_province_info(self, interaction, province_id):
        # Обновляем статусы построек
        game_cog = interaction.client.get_cog("Game")
        if game_cog:
            await game_cog._update_buildings_status(self.country_id)

        province = await async_fetch_one("SELECT * FROM provinces WHERE id=?", (province_id,))
        info = f"**Регион: {province['name']}**\n"
        info += f"Тип местности: {province['terrain_type']}\n"
        info += f"Экономическая ценность: {province['economic_value']}\n"

        res_rows = await async_fetch_all("SELECT resource_name, amount FROM province_resources WHERE province_id=?", (province_id,))
        if res_rows:
            info += "Потенциальные ресурсы: " + ", ".join(r['resource_name'] for r in res_rows) + "\n"

        view = ProvinceMenuView(self.country_id, province_id)
        await interaction.edit_original_response(content=info, view=view)

class ProvinceMenuView(discord.ui.View):
    def __init__(self, country_id, province_id):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.province_id = province_id

    async def show_info(self, interaction):
        game_cog = interaction.client.get_cog("Game")
        if game_cog:
            await game_cog._update_buildings_status(self.country_id)
        province = await async_fetch_one("SELECT * FROM provinces WHERE id=?", (self.province_id,))
        info = f"**Регион: {province['name']}**\n"
        info += f"Тип местности: {province['terrain_type']}\n"
        info += f"Экономическая ценность: {province['economic_value']}\n"
        res_rows = await async_fetch_all("SELECT resource_name, amount FROM province_resources WHERE province_id=?", (self.province_id,))
        if res_rows:
            info += "Потенциальные ресурсы: " + ", ".join(r['resource_name'] for r in res_rows) + "\n"
        view = self
        await interaction.edit_original_response(content=info, view=view)

    @discord.ui.button(label="Постройки", style=discord.ButtonStyle.primary)
    async def buildings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Выберите раздел:", view=BuildingCategoryView(self.country_id, self.province_id))

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        provinces = await async_fetch_all("SELECT id, name FROM provinces WHERE country_id=?", (self.country_id,))
        view = ProvinceSelectView(self.country_id, provinces)
        await interaction.edit_original_response(content="Выберите регион:", view=view)

class BuildingCategoryView(discord.ui.View):
    def __init__(self, country_id, province_id):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.province_id = province_id

    @discord.ui.button(label="Завершённые постройки", style=discord.ButtonStyle.success)
    async def completed_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        buildings = await async_fetch_all(
            "SELECT * FROM buildings WHERE country_id=? AND province_id=? AND status='completed'",
            (self.country_id, self.province_id))
        if not buildings:
            await interaction.response.send_message("Нет завершённых построек.", ephemeral=True)
            return
        view = BuildingListView(self.country_id, self.province_id, buildings, mode='completed')
        await interaction.response.edit_message(content="Ваши постройки:", view=view)

    @discord.ui.button(label="В процессе стройки", style=discord.ButtonStyle.primary)
    async def constructing_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        buildings = await async_fetch_all(
            "SELECT * FROM buildings WHERE country_id=? AND province_id=? AND status IN ('constructing','upgrading')",
            (self.country_id, self.province_id))
        if not buildings:
            await interaction.response.send_message("Нет строящихся объектов.", ephemeral=True)
            return
        view = BuildingListView(self.country_id, self.province_id, buildings, mode='in_progress')
        await interaction.response.edit_message(content="Строящиеся объекты:", view=view)

    @discord.ui.button(label="Новая постройка", style=discord.ButtonStyle.primary)
    async def new_building_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Получаем открытые типы построек для страны
        opened = await async_fetch_all("SELECT building_type FROM opened_buildings WHERE country_id=?", (self.country_id,))
        available_types = [row['building_type'] for row in opened]
        if not available_types:
            await interaction.response.send_message("Нет доступных типов построек.", ephemeral=True)
            return
        view = NewBuildingTypeView(self.country_id, self.province_id, available_types)
        await interaction.response.edit_message(content="Выберите тип постройки:", view=view)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        view = ProvinceMenuView(self.country_id, self.province_id)
        await view.show_info(interaction)

class BuildingListView(discord.ui.View):
    def __init__(self, country_id, province_id, buildings, mode='completed'):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.province_id = province_id
        self.buildings = buildings
        self.mode = mode
        # Создаём Select для выбора конкретной постройки
        options = []
        for b in buildings:
            label = f"{b['building_name']} (ур.{b['level']})"
            if mode == 'in_progress':
                if b['status'] == 'constructing':
                    label += " - строится"
                else:
                    label += f" - улучшение до {b['level']+1}"
            options.append(discord.SelectOption(label=label[:100], value=str(b['id'])))
        select = discord.ui.Select(placeholder="Выберите постройку...", options=options)
        select.callback = self.show_building_detail
        self.add_item(select)
        # Кнопка Назад
        self.add_item(BackButton(self.country_id))

    async def show_building_detail(self, interaction: discord.Interaction):
        await interaction.response.defer()
        building_id = int(interaction.data['values'][0])
        building = await async_fetch_one("SELECT * FROM buildings WHERE id=?", (building_id,))
        if not building:
            await interaction.followup.send("Постройка не найдена.", ephemeral=True)
            return
        view = BuildingDetailView(self.country_id, self.province_id, building)
        embed = await self._build_building_embed(building)
        await interaction.edit_original_response(content="", embed=embed, view=view)

    async def _build_building_embed(self, building):
        btype = BUILDING_TYPES[building['building_type']]
        embed = discord.Embed(title=f"{building['building_name']} (ур.{building['level']})", color=0x00ff00)
        embed.add_field(name="Тип", value=building['building_type'], inline=True)
        if building['status'] == 'completed':
            embed.add_field(name="Статус", value="✅ Завершена", inline=True)
        else:
            embed.add_field(name="Статус", value="Строится", inline=True)

        if building['status'] == 'completed':
            production = ""
            for res, base in btype.get('resource_production', {}).items():
                prod = int(base * (btype['upgrade_multiplier'] ** building['level']))
                production += f"{res}: {prod} ед. / цикл\n"
            if btype.get('money_production'):
                prod = int(btype['money_production'] * (btype['upgrade_multiplier'] ** building['level']))
                production += f"Доллары: {prod} / цикл\n"
            if production:
                embed.add_field(name="Производство (за 2 часа)", value=production, inline=False)

            effects = btype.get('effects', {})
            if effects:
                eff_str = ""
                for key, value in effects.items():
                    eff_str += f"{key}: {value * (building['level']+1)}\n"  # эффект зависит от уровня
                embed.add_field(name="Эффекты", value=eff_str, inline=False)

            next_level = building['level'] + 1
            if next_level > 5:
                embed.add_field(name="Уровень", value="Максимальный", inline=False)
            else:
                cost = btype['cost']
                mult = btype['upgrade_multiplier'] ** building['level']
                time_sec = int(btype['build_time'] * mult)
                cost_str = ""
                for r, amount in cost.items():
                    if r == "Доллары":
                        cost_str += f"Доллары: {int(amount * mult)} из бюджета\n"
                    else:
                        cost_str += f"{r}: {int(amount * mult)}\n"
                embed.add_field(name=f"Улучшение до уровня {next_level}", value=f"Стоимость:\n{cost_str}Время: {time_sec} сек", inline=False)
        else:
            # Для строящихся – показываем время до завершения
            remaining = int(building['build_end_time'] - time.time()) if building['build_end_time'] else 0
            if remaining > 0:
                embed.add_field(name="Осталось времени", value=f"{remaining} сек", inline=False)
            if building['status'] == 'upgrading':
                embed.add_field(name="Цель", value=f"Улучшение до уровня {building['level'] + 1}", inline=False)
        return embed

class BuildingDetailView(discord.ui.View):
    def __init__(self, country_id, province_id, building):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.province_id = province_id
        self.building = building
        if building['status'] == 'completed':
            btype = BUILDING_TYPES[building['building_type']]
            if building['level'] < 5:
                self.add_item(UpgradeButton(country_id, province_id, building))
        # Кнопка «Назад» возвращает в список построек этой провинции
        back_btn = discord.ui.Button(label="◀ Назад", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.back_to_building_list
        self.add_item(back_btn)

    async def back_to_building_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        buildings = await async_fetch_all(
            "SELECT * FROM buildings WHERE country_id=? AND province_id=? AND status='completed'",
            (self.country_id, self.province_id))
        view = BuildingListView(self.country_id, self.province_id, buildings, mode='completed')
        await interaction.edit_original_response(content="Ваши постройки:", view=view)

class UpgradeButton(discord.ui.Button):
    def __init__(self, country_id, province_id, building):
        super().__init__(label="Улучшить уровень", style=discord.ButtonStyle.success)
        self.country_id = country_id
        self.province_id = province_id
        self.building = building

    async def callback(self, interaction: discord.Interaction):
        # Проверка лимита активных строек (7)
        country = await async_fetch_one("SELECT active_constructions, budget FROM countries WHERE id=?", (self.country_id,))
        if not country:
            await interaction.response.send_message("Ошибка.", ephemeral=True)
            return
        if country['active_constructions'] >= 7:
            await interaction.response.send_message("Достигнут лимит одновременных строек (7).", ephemeral=True)
            return
        btype = BUILDING_TYPES[self.building['building_type']]
        next_level = self.building['level'] + 1
        if next_level > 5:
            await interaction.response.send_message("Максимальный уровень.", ephemeral=True)
            return
        cost = btype['cost']
        multiplier = btype['upgrade_multiplier'] ** self.building['level']
        # Списание ресурсов
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            pass
        # Проверка денег в бюджете
        if "Доллары" in cost:
            money_needed = int(cost["Доллары"] * multiplier)
            if country['budget'] < money_needed:
                await interaction.followup.send("Недостаточно денег в бюджете.", ephemeral=True)
                return
            await async_execute("UPDATE countries SET budget = budget - ? WHERE id=?", (money_needed, self.country_id))
        # Проверка остальных ресурсов
        for res, amount in cost.items():
            if res == "Доллары":
                continue
            needed = int(amount * multiplier)
            # Проверяем в resources
            row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name=?", (self.country_id, res))
            if not row or row['amount'] < needed:
                await interaction.followup.send(f"Недостаточно {res}.", ephemeral=True)
                return
        # Списываем ресурсы
        for res, amount in cost.items():
            if res == "Доллары":
                continue
            needed = int(amount * multiplier)
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?", (needed, self.country_id, res))
        # Увеличиваем счётчик активных строек
        await async_execute("UPDATE countries SET active_constructions = active_constructions + 1 WHERE id=?", (self.country_id,))
        # Запускаем улучшение: устанавливаем статус 'upgrading' и время окончания
        build_time = btype['build_time'] * multiplier
        end_time = time.time() + build_time
        await async_execute(
            "UPDATE buildings SET status='upgrading', build_end_time=? WHERE id=?",
            (end_time, self.building['id'])
        )
        await interaction.followup.send(f"Улучшение запущено. Завершится через {int(build_time)} сек.", ephemeral=True)

class NewBuildingTypeView(discord.ui.View):
    def __init__(self, country_id, province_id, available_types):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.province_id = province_id
        self.available_types = available_types  # сохраняем для кнопки "Назад"
        options = [discord.SelectOption(label=t, value=t) for t in available_types]
        select = discord.ui.Select(placeholder="Тип постройки...", options=options)
        select.callback = self.type_selected
        self.add_item(select)

    async def type_selected(self, interaction: discord.Interaction):
        building_type = interaction.data['values'][0]
        btype = BUILDING_TYPES[building_type]
        await interaction.response.defer()

        # Получаем актуальные данные страны
        country = await async_fetch_one("SELECT * FROM countries WHERE id=?", (self.country_id,))
        if not country:
            await interaction.followup.send("Ошибка загрузки данных.", ephemeral=True)
            return

        # Проверка лимита одновременных строек
        active_limit = 7
        active_ok = country['active_constructions'] < active_limit

        # Национальный лимит
        nat_limit = await async_fetch_one(
            "SELECT max_national FROM building_limits WHERE country_id=? AND building_type=?",
            (self.country_id, building_type))
        max_nat = nat_limit['max_national'] if nat_limit else 0
        current_nat = await async_fetch_one(
            "SELECT COUNT(*) as cnt FROM buildings WHERE country_id=? AND building_type=?",
            (self.country_id, building_type))
        national_ok = current_nat['cnt'] < max_nat

        # Региональный лимит
        reg_limit = await async_fetch_one(
            "SELECT max_per_region FROM building_limits WHERE country_id=? AND building_type=?",
            (self.country_id, building_type))
        max_reg = reg_limit['max_per_region'] if reg_limit else 1
        current_reg = await async_fetch_one(
            "SELECT COUNT(*) as cnt FROM buildings WHERE country_id=? AND province_id=? AND building_type=?",
            (self.country_id, self.province_id, building_type))
        regional_ok = current_reg['cnt'] < max_reg

        # Проверка ресурсов
        cost = btype['cost']
        money_ok = True
        if "Доллары" in cost:
            money_ok = country['budget'] >= cost["Доллары"]
        resources_ok = True
        for res, amount in cost.items():
            if res == "Доллары":
                continue
            row = await async_fetch_one(
                "SELECT amount FROM resources WHERE country_id=? AND resource_name=?",
                (self.country_id, res))
            if not row or row['amount'] < amount:
                resources_ok = False
                break

        can_build = all([active_ok, national_ok, regional_ok, money_ok, resources_ok])

        # Строим информационный embed
        embed = discord.Embed(
            title=f"Новая постройка: {building_type}",
            description=btype.get('description', ''),
            color=0x00ff00)
        embed.add_field(name="Время строительства", value=f"{btype['build_time']} сек", inline=True)

        cost_str = ""
        for r, amt in cost.items():
            cost_str += f"{r}: {amt}\n"
        embed.add_field(name="Стоимость", value=cost_str, inline=False)

        if btype.get('resource_production'):
            prod_str = "\n".join(
                f"{r}: {btype['resource_production'][r]} / цикл" for r in btype['resource_production'])
            embed.add_field(name="Производство (за цикл)", value=prod_str, inline=False)

        if btype.get('money_production'):
            embed.add_field(name="Доход", value=f"{btype['money_production']} долларов / цикл", inline=False)

        if btype.get('effects'):
            eff_str = "\n".join(f"{k}: {v}" for k, v in btype['effects'].items())
            embed.add_field(name="Эффекты", value=eff_str, inline=False)

        # Кнопки
        view = discord.ui.View()
        build_btn = discord.ui.Button(
            label="Построить",
            style=discord.ButtonStyle.success,
            disabled=not can_build)
        build_btn.callback = self._make_build_callback(building_type, btype, cost)
        view.add_item(build_btn)

        back_btn = discord.ui.Button(label="Назад", style=discord.ButtonStyle.secondary)
        back_btn.callback = self._back_to_type_selection
        view.add_item(back_btn)

        await interaction.edit_original_response(content="", embed=embed, view=view)

    def _make_build_callback(self, building_type, btype, cost):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            # Повторная проверка всех условий (могло измениться)
            country_now = await async_fetch_one("SELECT * FROM countries WHERE id=?", (self.country_id,))
            if not country_now:
                await interaction.followup.send("Ошибка данных.", ephemeral=True)
                return

            if country_now['active_constructions'] >= 7:
                await interaction.followup.send("Достигнут лимит одновременных строек (7).", ephemeral=True)
                return

            nat_limit = await async_fetch_one(
                "SELECT max_national FROM building_limits WHERE country_id=? AND building_type=?",
                (self.country_id, building_type))
            max_nat = nat_limit['max_national'] if nat_limit else 0
            current_nat = await async_fetch_one(
                "SELECT COUNT(*) as cnt FROM buildings WHERE country_id=? AND building_type=?",
                (self.country_id, building_type))
            if current_nat['cnt'] >= max_nat:
                await interaction.followup.send(f"Достигнут национальный лимит для {building_type}.", ephemeral=True)
                return

            reg_limit = await async_fetch_one(
                "SELECT max_per_region FROM building_limits WHERE country_id=? AND building_type=?",
                (self.country_id, building_type))
            max_reg = reg_limit['max_per_region'] if reg_limit else 1
            current_reg = await async_fetch_one(
                "SELECT COUNT(*) as cnt FROM buildings WHERE country_id=? AND province_id=? AND building_type=?",
                (self.country_id, self.province_id, building_type))
            if current_reg['cnt'] >= max_reg:
                await interaction.followup.send(f"Достигнут региональный лимит для {building_type}.", ephemeral=True)
                return

            # Проверка ресурсов
            for res, amount in cost.items():
                if res == "Доллары":
                    if country_now['budget'] < amount:
                        await interaction.followup.send("Недостаточно денег в бюджете.", ephemeral=True)
                        return
                else:
                    row = await async_fetch_one(
                        "SELECT amount FROM resources WHERE country_id=? AND resource_name=?",
                        (self.country_id, res))
                    if not row or row['amount'] < amount:
                        await interaction.followup.send(f"Недостаточно {res}.", ephemeral=True)
                        return

            # Списание
            if "Доллары" in cost:
                await async_execute("UPDATE countries SET budget = budget - ? WHERE id=?",
                                    (cost["Доллары"], self.country_id))
            for res, amount in cost.items():
                if res == "Доллары":
                    continue
                await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?",
                                    (amount, self.country_id, res))

            # Увеличиваем счётчик активных строек
            await async_execute("UPDATE countries SET active_constructions = active_constructions + 1 WHERE id=?",
                                (self.country_id,))

            # Запуск строительства
            end_time = time.time() + btype['build_time']
            await async_execute(
                "INSERT INTO buildings (country_id, province_id, building_type, building_name, level, build_end_time, status) "
                "VALUES (?, ?, ?, ?, 0, ?, 'constructing')",
                (self.country_id, self.province_id, building_type, building_type, end_time))

            await interaction.followup.send(f"Строительство **{building_type}** началось! Завершится через {btype['build_time']} сек.", ephemeral=True)

        return callback

    async def _back_to_type_selection(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = NewBuildingTypeView(self.country_id, self.province_id, self.available_types)
        await interaction.edit_original_response(content="Выберите тип постройки:", view=view, embed=None)

class BuildingNameModal(discord.ui.Modal, title="Название постройки"):
    name = discord.ui.TextInput(label="Введите название", placeholder="Моя шахта", required=True)

    def __init__(self, country_id, province_id, building_type):
        super().__init__()
        self.country_id = country_id
        self.province_id = province_id
        self.building_type = building_type

    async def on_submit(self, interaction: discord.Interaction):
        btype = BUILDING_TYPES[self.building_type]
        # Проверка лимита активных строек (7)
        country = await async_fetch_one("SELECT active_constructions, budget FROM countries WHERE id=?", (self.country_id,))
        if not country:
            await interaction.response.send_message("Ошибка.", ephemeral=True)
            return
        if country['active_constructions'] >= 7:
            await interaction.response.send_message("Достигнут лимит одновременных строек (7).", ephemeral=True)
            return
        # Проверка национального лимита
        nat_limit = await async_fetch_one("SELECT max_national FROM building_limits WHERE country_id=? AND building_type=?", (self.country_id, self.building_type))
        max_nat = nat_limit['max_national'] if nat_limit else 0
        current_nat = await async_fetch_one("SELECT COUNT(*) as cnt FROM buildings WHERE country_id=? AND building_type=?", (self.country_id, self.building_type))
        if current_nat['cnt'] >= max_nat:
            await interaction.response.send_message(f"Достигнут национальный лимит для {self.building_type}.", ephemeral=True)
            return
        # Проверка регионального лимита
        reg_limit = await async_fetch_one("SELECT max_per_region FROM building_limits WHERE country_id=? AND building_type=?", (self.country_id, self.building_type))
        max_reg = reg_limit['max_per_region'] if reg_limit else 1
        current_reg = await async_fetch_one("SELECT COUNT(*) as cnt FROM buildings WHERE country_id=? AND province_id=? AND building_type=?", (self.country_id, self.province_id, self.building_type))
        if current_reg['cnt'] >= max_reg:
            await interaction.response.send_message(f"Достигнут региональный лимит для {self.building_type}.", ephemeral=True)
            return

        # Списание ресурсов
        cost = btype['cost']
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            pass
        if "Доллары" in cost:
            if country['budget'] < cost["Доллары"]:
                await interaction.followup.send("Недостаточно денег в бюджете.", ephemeral=True)
                return
            await async_execute("UPDATE countries SET budget = budget - ? WHERE id=?", (cost["Доллары"], self.country_id))
        for res, amount in cost.items():
            if res == "Доллары":
                continue
            row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name=?", (self.country_id, res))
            if not row or row['amount'] < amount:
                await interaction.followup.send(f"Недостаточно {res}.", ephemeral=True)
                return
        for res, amount in cost.items():
            if res == "Доллары":
                continue
            await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?", (amount, self.country_id, res))

        # Увеличиваем счётчик активных строек
        await async_execute("UPDATE countries SET active_constructions = active_constructions + 1 WHERE id=?", (self.country_id,))
        # Создаём запись постройки со статусом constructing
        end_time = time.time() + btype['build_time']
        await async_execute(
            "INSERT INTO buildings (country_id, province_id, building_type, building_name, level, build_end_time, status) VALUES (?, ?, ?, ?, 0, ?, 'constructing')",
            (self.country_id, self.province_id, self.building_type, self.name.value, end_time)
        )
        await interaction.followup.send(f"Постройка '{self.name.value}' начата. Завершится через {btype['build_time']} сек.", ephemeral=True)

class ArmyView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Рекрутировать", style=discord.ButtonStyle.success)
    async def recruit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/recruit <количество>`", ephemeral=True)

    @discord.ui.button(label="Распустить", style=discord.ButtonStyle.danger)
    async def disband_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте команду `/disband <количество>`", ephemeral=True)

    @discord.ui.button(label="Произвести технику", style=discord.ButtonStyle.success)
    async def produce_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Показываем краткий список и предлагаем ввести команду
        items_list = []
        for cat, items in {**MILITARY_EQUIPMENT, **WEAPONS}.items():
            for item in items:
                items_list.append(f"{item['name']} ({item['cost']}$)")
        text = "**Доступная техника и оружие:**\n" + "\n".join(items_list[:20]) + "\n\nИспользуйте `/produce_equipment` для заказа."
        await interaction.response.edit_message(content=text, view=self)

    @discord.ui.button(label="Информация об армии", style=discord.ButtonStyle.secondary)
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        country = await async_fetch_one("SELECT * FROM countries WHERE id=?", (self.country_id,))
        if not country:
            await interaction.response.send_message("Ошибка.", ephemeral=True)
            return
        army = country['army_count']
        pop = country['population']
        max_army = int(pop * 0.05)
        content = f"**Армия**\nЧисленность: {format_number(army)} (макс. {format_number(max_army)})\nНаселение: {format_number(pop)}"
        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

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
            # Отдельно обрабатываем деньги
            if "Доллары" in cost:
                money_needed = cost.pop("Доллары")
                country = await async_fetch_one("SELECT budget FROM countries WHERE id=?", (self.country_id,))
                if not country or country['budget'] < money_needed:
                    await interaction.response.send_message("Недостаточно денег.", ephemeral=True)
                    return
                await async_execute("UPDATE countries SET budget = budget - ? WHERE id = ?", (money_needed, self.country_id))
            # Остальные ресурсы
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

            build_time = BUILDING_TYPES[building_type]["build_time"] * (
                        BUILDING_TYPES[building_type]["upgrade_multiplier"] ** current_level)
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
        await interaction.response.send_message("Используйте команду `/mobilize`.", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

# ========================
# VIEW: ВОЙНЫ (ПОЛНОСТЬЮ ВНУТРИ /GAME)
# ========================
class WarMainMenu(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Объявление войны", style=discord.ButtonStyle.danger)
    async def declare_war_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Выберите тип противника:", view=WarDeclarationTypeMenu(self.country_id))

    @discord.ui.button(label="Ваши войны", style=discord.ButtonStyle.primary)
    async def my_wars_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        view = await self._build_wars_list(interaction.user.id)
        await interaction.edit_original_response(content="Ваши войны:", view=view)

    @discord.ui.button(label="Мобилизация", style=discord.ButtonStyle.success)
    async def mobilization_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Используйте `/mobilize` для переключения мобилизации.", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

    async def _build_wars_list(self, user_id):
        country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (user_id,))
        if not country:
            return WarListEmptyView(self.country_id)
        wars = await async_fetch_all(
            "SELECT w.id, w.attacker_id, w.defender_id, w.status, w.start_time, w.reason "
            "FROM wars w WHERE w.attacker_id=? OR w.defender_id=? ORDER BY w.start_time DESC",
            (country['id'], country['id'])
        )
        if not wars:
            return WarListEmptyView(self.country_id)
        wars_info = []
        for w in wars:
            attacker = await async_fetch_one("SELECT name FROM countries WHERE id=?", (w['attacker_id'],))
            defender = await async_fetch_one("SELECT name FROM countries WHERE id=?", (w['defender_id'],))
            wars_info.append({
                "id": w['id'],
                "attacker_name": attacker['name'] if attacker else "Неизвестно",
                "defender_name": defender['name'] if defender else "Неизвестно",
                "status": w['status']
            })
        return WarListView(self.country_id, wars_info)

class WarDeclarationTypeMenu(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Объявить войну игроку", style=discord.ButtonStyle.danger)
    async def vs_player_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        targets = await async_fetch_all(
            "SELECT id, name, owner_id FROM countries WHERE owner_id IS NOT NULL AND id != ?",
            (self.country_id,)
        )
        if not targets:
            await interaction.response.send_message("Нет доступных игроков.", ephemeral=True)
            return
        view = PlayerSelectView(self.country_id, targets)
        await interaction.response.edit_message(content="Выберите противника:", view=view)

    @discord.ui.button(label="Объявить войну боту", style=discord.ButtonStyle.danger)
    async def vs_bot_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot_countries = await async_fetch_all("SELECT id, name FROM countries WHERE owner_id IS NULL")
        if not bot_countries:
            await interaction.response.send_message("Нет свободных стран.", ephemeral=True)
            return
        view = BotSelectView(self.country_id, bot_countries)
        await interaction.response.edit_message(content="Выберите бота:", view=view)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Военное меню", view=WarMainMenu(self.country_id))

class PlayerSelectView(discord.ui.View):
    def __init__(self, country_id, players):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.players = players
        # Создаём Select со всеми игроками, фильтрация произойдёт при нажатии
        if not players:
            self.add_item(discord.ui.Button(label="Нет доступных игроков", disabled=True, style=discord.ButtonStyle.secondary))
            return
        select = discord.ui.Select(placeholder="Выберите игрока...",
                                   options=[discord.SelectOption(label=f"{p['name']} (ID{p['owner_id']})", value=str(p['id'])) for p in players])
        select.callback = self.player_selected
        self.add_item(select)

    async def player_selected(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target_id = int(interaction.data['values'][0])
        # Проверяем, нет ли активной войны с этим игроком
        existing = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (self.country_id, target_id, target_id, self.country_id)
        )
        if existing:
            await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
            return
        view = WarReasonView(self.country_id, target_id, is_bot=False)
        await interaction.edit_original_response(content="Выберите причину войны:", view=view)

class BotSelectView(discord.ui.View):
    def __init__(self, country_id, bots):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.bots = bots
        if not bots:
            self.add_item(discord.ui.Button(label="Нет доступных ботов", disabled=True, style=discord.ButtonStyle.secondary))
            return
        select = discord.ui.Select(placeholder="Выберите бота...",
                                   options=[discord.SelectOption(label=b['name'], value=str(b['id'])) for b in bots])
        select.callback = self.bot_selected
        self.add_item(select)

    async def bot_selected(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target_id = int(interaction.data['values'][0])
        existing = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (self.country_id, target_id, target_id, self.country_id)
        )
        if existing:
            await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
            return
        view = WarReasonView(self.country_id, target_id, is_bot=True)
        await interaction.edit_original_response(content="Выберите причину войны:", view=view)

class WarReasonView(discord.ui.View):
    def __init__(self, country_id, target_id, is_bot):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.target_id = target_id
        self.is_bot = is_bot
        from data.war_params import WAR_REASONS
        options = [discord.SelectOption(label=reason, value=reason) for reason in WAR_REASONS]
        select = discord.ui.Select(placeholder="Причина войны...", options=options)
        select.callback = self.reason_selected
        self.add_item(select)

    async def reason_selected(self, interaction: discord.Interaction):
        reason = interaction.data['values'][0]
        modal = WarDescriptionModal(self.country_id, self.target_id, self.is_bot, reason)
        await interaction.response.send_modal(modal)

class WarDescriptionModal(discord.ui.Modal, title="Описание войны (опционально)"):
    description = discord.ui.TextInput(label="Дополнительное описание", style=discord.TextStyle.long, required=False)

    def __init__(self, country_id, target_id, is_bot, reason):
        super().__init__()
        self.country_id = country_id
        self.target_id = target_id
        self.is_bot = is_bot
        self.reason = reason

    async def on_submit(self, interaction: discord.Interaction):
        war_cog = interaction.client.get_cog("War")
        if war_cog:
            # Вызываем специальный метод для модального окна (без defer)
            await war_cog._declare_war_from_modal(interaction, self.country_id, self.target_id, self.reason,
                                                  self.description.value or "", is_bot=self.is_bot)
        else:
            await interaction.response.send_message("❌ Ког войны не загружен.", ephemeral=True)

class WarListView(discord.ui.View):
    def __init__(self, country_id, wars_info):
        super().__init__(timeout=None)
        self.country_id = country_id
        self.wars_info = wars_info
        options = []
        for w in wars_info:
            status = "🟢" if w['status'] == 'active' else "⚪"
            label = f"{status} {w['attacker_name']} vs {w['defender_name']} ({w['status']})"
            options.append(discord.SelectOption(label=label[:100], value=str(w['id'])))
        select = discord.ui.Select(placeholder="Выберите войну...", options=options)
        select.callback = self.war_selected
        self.add_item(select)

    async def war_selected(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        war_id = int(interaction.data['values'][0])
        game_cog = interaction.client.get_cog("Game")
        if game_cog:
            embed, error = await game_cog._build_war_detail(war_id)
            if error:
                await interaction.followup.send(error, ephemeral=True)
            else:
                # Добавляем кнопки "Совершить ход" и "Мир" для активной войны
                view = discord.ui.View()
                war = await async_fetch_one("SELECT status, attacker_id, defender_id FROM wars WHERE id=?", (war_id,))
                if war and war['status'] == 'active':
                    view.add_item(WarActionButton(war_id, self.country_id))
                    view.add_item(PeaceOfferButton(war_id, self.country_id))
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.followup.send("Ошибка получения данных.", ephemeral=True)

class WarActionButton(discord.ui.Button):
    def __init__(self, war_id, country_id):
        super().__init__(label="Совершить ход", style=discord.ButtonStyle.green)
        self.war_id = war_id
        self.country_id = country_id

    async def callback(self, interaction: discord.Interaction):
        view = WarMoveSelectView(self.war_id, self.country_id)
        await interaction.response.send_message("Выберите действие:", view=view, ephemeral=True)

class WarMoveSelectView(discord.ui.View):
    def __init__(self, war_id, country_id):
        super().__init__(timeout=None)
        self.war_id = war_id
        self.country_id = country_id
        for action, label in [("attack", "Атака"), ("defend", "Оборона"), ("scout", "Разведка"),
                              ("supply", "Снабжение/Логистика"), ("specops", "Спецоперация"), ("retreat", "Тактическое отступление")]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(action)
            self.add_item(btn)

    def make_callback(self, action):
        async def cb(interaction: discord.Interaction):
            if action == "attack":
                await interaction.response.defer(ephemeral=True)
                war_cog = interaction.client.get_cog("War")
                my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
                if not war_cog or not my_country:
                    await interaction.followup.send("Ошибка.", ephemeral=True)
                    return
                enemy_provinces = await war_cog._get_frontline_provinces(self.war_id, my_country['id'])
                if not enemy_provinces:
                    await interaction.followup.send("Нет доступных провинций для атаки.", ephemeral=True)
                    return
                options = []
                for ep in enemy_provinces:
                    prov = await async_fetch_one("SELECT name FROM provinces WHERE id=?", (ep['province_id'],))
                    options.append(discord.SelectOption(label=prov['name'], value=str(ep['province_id'])))
                select = discord.ui.Select(placeholder="Выберите провинцию для атаки...", options=options)
                async def province_selected(select_interaction: discord.Interaction):
                    target_id = int(select_interaction.data['values'][0])
                    tactic_view = TacticSelectView(self.war_id, self.country_id, target_id)
                    await select_interaction.response.edit_message(content="Выберите тактику атаки:", view=tactic_view)
                select.callback = province_selected
                view = discord.ui.View()
                view.add_item(select)
                await interaction.edit_original_response(content="Выберите провинцию для атаки:", view=view)
            else:
                await interaction.response.defer(ephemeral=True)
                war_cog = interaction.client.get_cog("War")
                if war_cog:
                    await war_cog.war_action(interaction, action=action)
        return cb

class TacticSelectView(discord.ui.View):
    def __init__(self, war_id, country_id, target_province_id):
        super().__init__(timeout=None)
        self.war_id = war_id
        self.country_id = country_id
        self.target_province_id = target_province_id
        for tactic_id, tactic_data in TACTICS.items():
            btn = discord.ui.Button(label=tactic_data["name"], style=discord.ButtonStyle.primary)
            btn.callback = self.make_tactic_callback(tactic_id)
            self.add_item(btn)

    def make_tactic_callback(self, tactic_id):
        async def cb(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            war_cog = interaction.client.get_cog("War")
            if war_cog:
                await war_cog._perform_war_move(interaction, self.country_id, self.war_id, "attack",
                                                attack_type=tactic_id, target_province_id=self.target_province_id)
            else:
                await interaction.followup.send("Ког войны не найден.", ephemeral=True)
        return cb

class PeaceOfferButton(discord.ui.Button):
    def __init__(self, war_id, country_id):
        super().__init__(label="Предложить мир", style=discord.ButtonStyle.blurple)
        self.war_id = war_id
        self.country_id = country_id

    async def callback(self, interaction: discord.Interaction):
        war_cog = interaction.client.get_cog("War")
        if war_cog:
            await war_cog._make_peace(interaction, self.war_id)
        else:
            await interaction.response.send_message("Ког войны не найден.", ephemeral=True)

class WarListEmptyView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Нет войн", disabled=True, style=discord.ButtonStyle.secondary))
        self.add_item(BackButton(country_id))

class BackButton(discord.ui.Button):
    def __init__(self, country_id):
        super().__init__(label="◀ Назад", style=discord.ButtonStyle.secondary)
        self.country_id = country_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

class MarketMenuView(discord.ui.View):
    def __init__(self, country_id):
        super().__init__(timeout=None)
        self.country_id = country_id

    @discord.ui.button(label="Обновить", style=discord.ButtonStyle.secondary)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        lots = await async_fetch_all("SELECT id, resource_name, amount, price, seller_id FROM market WHERE sold=0")
        if not lots:
            content = "На рынке нет активных предложений."
        else:
            content = "**Рынок**\n"
            for lot in lots:
                seller_country = await async_fetch_one("SELECT name, owner_id FROM countries WHERE id=?", (lot['seller_id'],))
                seller_name = seller_country['name'] if seller_country else "Неизвестно"
                content += f"Лот #{lot['id']}: {lot['resource_name']} x{lot['amount']} за {lot['price']}$ (продавец: {seller_name})\n"
            content += "\nИспользуйте `/market buy <id>` для покупки."
        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.danger)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Главное меню", view=GameMenu(self.country_id))

# ========================
# VIEW: РЕГИСТРАЦИЯ /REG
# ========================
class ContinentSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=120)
        self.cog = cog
        for continent in CONTINENTS.keys():
            self.add_item(ContinentButton(continent, cog))

class ContinentButton(discord.ui.Button):
    def __init__(self, continent, cog):
        super().__init__(label=continent, style=discord.ButtonStyle.primary)
        self.continent = continent
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        countries_in_continent = CONTINENTS[self.continent]
        free_countries = []
        for country_name, flag in countries_in_continent.items():
            row = await async_fetch_one(
                "SELECT id FROM countries WHERE name=? AND owner_id IS NULL",
                (country_name,)
            )
            if row:
                free_countries.append((country_name, flag))

        if not free_countries:
            await interaction.response.edit_message(
                content=f"❌ В континенте **{self.continent}** нет свободных стран.",
                view=ContinentSelectView(self.cog)
            )
            return

        groups = []
        for i in range(0, len(free_countries), 25):
            groups.append(free_countries[i:i+25])

        if len(groups) == 1:
            options = [discord.SelectOption(label=country, emoji=flag) for country, flag in groups[0]]
            select = CountrySelect(self.continent, self.cog, options)
            view = discord.ui.View()
            view.add_item(select)
            view.add_item(BackToContinentsButton(self.cog))
            await interaction.response.edit_message(
                content=f"Выберите страну в **{self.continent}**:",
                view=view
            )
        else:
            view = ContinentCountriesView(self.cog, self.continent, groups, 0)
            await interaction.response.edit_message(
                content=f"Выберите страну в **{self.continent}** (группа 1/{len(groups)}):",
                view=view
            )

class BackToContinentsButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="◀ Назад к континентам", style=discord.ButtonStyle.secondary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        view = ContinentSelectView(self.cog)
        await interaction.response.edit_message(content="🌍 Выберите континент:", view=view)

class ContinentCountriesView(discord.ui.View):
    def __init__(self, cog, continent, groups, current_group_index):
        super().__init__(timeout=120)
        self.cog = cog
        self.continent = continent
        self.groups = groups
        self.current_group_index = current_group_index

        options = [discord.SelectOption(label=country, emoji=flag) for country, flag in groups[current_group_index]]
        select = CountrySelect(continent, cog, options)
        self.add_item(select)

        if current_group_index > 0:
            self.add_item(PrevGroupButton(cog, continent, groups, current_group_index))
        if current_group_index < len(groups) - 1:
            self.add_item(NextGroupButton(cog, continent, groups, current_group_index))
        self.add_item(BackToContinentsButton(cog))

class PrevGroupButton(discord.ui.Button):
    def __init__(self, cog, continent, groups, current_index):
        super().__init__(label="◀ Предыдущая группа", style=discord.ButtonStyle.secondary)
        self.cog = cog
        self.continent = continent
        self.groups = groups
        self.index = current_index

    async def callback(self, interaction: discord.Interaction):
        view = ContinentCountriesView(self.cog, self.continent, self.groups, self.index - 1)
        await interaction.response.edit_message(
            content=f"Выберите страну в **{self.continent}** (группа {self.index}/{len(self.groups)}):",
            view=view
        )

class NextGroupButton(discord.ui.Button):
    def __init__(self, cog, continent, groups, current_index):
        super().__init__(label="Следующая группа ▶", style=discord.ButtonStyle.secondary)
        self.cog = cog
        self.continent = continent
        self.groups = groups
        self.index = current_index

    async def callback(self, interaction: discord.Interaction):
        view = ContinentCountriesView(self.cog, self.continent, self.groups, self.index + 1)
        await interaction.response.edit_message(
            content=f"Выберите страну в **{self.continent}** (группа {self.index + 2}/{len(self.groups)}):",
            view=view
        )

class CountrySelect(discord.ui.Select):
    def __init__(self, continent, cog, options, placeholder="Выберите страну..."):
        super().__init__(placeholder=placeholder, options=options)
        self.continent = continent
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        country_name = self.values[0]
        country = await async_fetch_one("SELECT id, name FROM countries WHERE name=? AND owner_id IS NULL", (country_name,))
        if not country:
            await interaction.response.send_message(f"❌ Страна **{country_name}** не найдена или уже занята.", ephemeral=True)
            return
        modal = RulerNameModal(country_name, self.cog, interaction.user, country['id'])
        await interaction.response.send_modal(modal)

class RulerNameModal(discord.ui.Modal, title="Введите имя правителя"):
    ruler_name = discord.ui.TextInput(label="Имя правителя", placeholder="Иван IV", required=True)

    def __init__(self, country_name: str, cog, user: discord.User, country_id: int):
        super().__init__()
        self.country_name = country_name
        self.cog = cog
        self.user = user
        self.country_id = country_id

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog._register_country(interaction, self.country_name, self.ruler_name.value, self.country_id, self.user)

# ========================
# КОГ С КОМАНДАМИ
# ========================
class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _register_country(self, interaction: discord.Interaction, country: str, ruler_name: str, country_id: int, user: discord.User):
        await async_execute(
            "UPDATE countries SET owner_id=?, ruler_name=?, display_name=? WHERE id=?",
            (user.id, ruler_name, country, country_id)
        )
        country_role_id = COUNTRY_ROLES.get(country)
        if country_role_id:
            role = interaction.guild.get_role(country_role_id)
            if role:
                try: await user.add_roles(role)
                except: pass
        if DEFAULT_PLAYER_ROLE_ID:
            role = interaction.guild.get_role(DEFAULT_PLAYER_ROLE_ID)
            if role:
                try: await user.add_roles(role)
                except: pass

        reg_channel_id = CHANNEL_IDS.get("registration")
        if reg_channel_id:
            reg_channel = self.bot.get_channel(reg_channel_id)
        else:
            reg_channel = await self._get_channel_or_create(interaction.guild, "регистрация-стран")
        if reg_channel:
            try:
                await reg_channel.send(f"{user.mention} теперь управляет страной **{country}** как правитель **{ruler_name}**.")
            except Exception as e:
                print(f"Не удалось отправить в канал регистраций: {e}")
        war_cog = self.bot.get_cog("War")
        if war_cog:
            await war_cog._notify_country_at_war(interaction, country_id)
            
        await interaction.response.send_message(f"✅ Вы теперь управляете страной **{country}** как **{ruler_name}**! Используйте `/game`.", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if interaction.response.is_done():
            if isinstance(interaction.response, discord.InteractionResponse) and not interaction.is_expired():
                try:
                    await interaction.followup.send(f"❌ Произошла ошибка: {error}", ephemeral=True)
                except:
                    pass
        else:
            await interaction.response.send_message(f"❌ Произошла ошибка: {error}", ephemeral=True)
        print(f"Ошибка в команде {interaction.command.name if interaction.command else 'unknown'}: {error}")

    async def _get_country(self, user_id):
        try:
            return await async_fetch_one("SELECT * FROM countries WHERE owner_id=?", (user_id,))
        except Exception as e:
            print(f"Ошибка получения страны: {e}")
            return None

    async def _update_buildings_status(self, country_id):
        now = time.time()
        # Завершаем constructing (уровень 0)
        constructing = await async_fetch_all(
            "SELECT * FROM buildings WHERE country_id=? AND status='constructing' AND build_end_time <= ?",
            (country_id, now)
        )
        for b in constructing:
            await async_execute(
                "UPDATE buildings SET status='completed', build_end_time=0 WHERE id=?",
                (b['id'],)
            )
            await self._apply_building_effects(b)

        # Завершаем upgrading
        upgrading = await async_fetch_all(
            "SELECT * FROM buildings WHERE country_id=? AND status='upgrading' AND build_end_time <= ?",
            (country_id, now)
        )
        for b in upgrading:
            new_level = b['level'] + 1
            await async_execute(
                "UPDATE buildings SET level=?, status='completed', build_end_time=0 WHERE id=?",
                (new_level, b['id'])
            )
            await self._apply_building_effects(b)

        # Счётчик активных строек
        total_completed = len(constructing) + len(upgrading)
        if total_completed > 0:
            await async_execute(
                "UPDATE countries SET active_constructions = active_constructions - ? WHERE id=? AND active_constructions >= ?",
                (total_completed, country_id, total_completed)
            )

    async def _apply_building_effects(self, building):
        btype = BUILDING_TYPES.get(building['building_type'])
        if not btype or 'effects' not in btype:
            return
        level = building['level']
        for key, value in btype['effects'].items():
            if key == 'population':
                await async_execute("UPDATE provinces SET population = population + ? WHERE id = ?", (value * (level+1), building['province_id']))
            elif key == 'crime_rate':
                await async_execute("UPDATE provinces SET crime_rate = MAX(0, crime_rate + ?) WHERE id = ?", (value * (level+1), building['province_id']))
            elif key == 'citizen_mood':
                await async_execute("UPDATE provinces SET citizen_mood = MIN(100, citizen_mood + ?) WHERE id = ?", (value * (level+1), building['province_id']))
            elif key == 'health':
                await async_execute("UPDATE provinces SET health = MIN(100, health + ?) WHERE id = ?", (value * (level+1), building['province_id']))
            elif key == 'science_progress':
                await async_execute("UPDATE countries SET science_progress = MIN(100, science_progress + ?) WHERE id = ?", (value * (level+1), building['country_id']))
            elif key == 'ecology':
                await async_execute("UPDATE countries SET ecology = MIN(100, ecology + ?) WHERE id = ?", (value * (level+1), building['country_id']))
            elif key == 'economic_value':
                await async_execute("UPDATE provinces SET economic_value = MIN(10, economic_value + ?) WHERE id = ?", (value * (level+1), building['province_id']))
            elif key == 'army_capacity':
                await async_execute("UPDATE countries SET army_capacity = army_capacity + ? WHERE id = ?", (value * (level+1), building['country_id']))

    async def _notify_user(self, user_id, message):
        user = self.bot.get_user(user_id)
        if user:
            try:
                await user.send(message)
            except discord.Forbidden:
                pass

    async def _notify_country_owner(self, country_id, message):
        country = await async_fetch_one("SELECT owner_id FROM countries WHERE id=?", (country_id,))
        if country and country['owner_id']:
            await self._notify_user(country['owner_id'], message)

    async def _get_channel_or_create(self, guild, name):
        channel = discord.utils.get(guild.text_channels, name=name)
        if not channel:
            channel = await guild.create_text_channel(name)
        return channel

    async def _build_war_detail(self, war_id):
        war = await async_fetch_one("SELECT * FROM wars WHERE id=?", (war_id,))
        if not war:
            return None, "Война не найдена."
        attacker = await async_fetch_one("SELECT name, display_name, ruler_name, army_count, combat_capability FROM countries WHERE id=?", (war['attacker_id'],))
        defender = await async_fetch_one("SELECT name, display_name, ruler_name, army_count, combat_capability FROM countries WHERE id=?", (war['defender_id'],))
        moves = await async_fetch_all("SELECT * FROM war_moves WHERE war_id=? ORDER BY created_at DESC LIMIT 10", (war_id,))
        reports = await async_fetch_all("SELECT report_text, created_at FROM war_reports WHERE war_id=? ORDER BY created_at DESC LIMIT 5", (war_id,))

        embed = discord.Embed(title=f"Война: {attacker['name']} vs {defender['name']}", color=0xff0000 if war['status']=='active' else 0x808080)
        embed.add_field(name="Статус", value="Активна" if war['status']=='active' else "Завершена", inline=True)
        # Исправлено: безопасное получение reason
        reason = war['reason'] if 'reason' in war.keys() else 'Не указана'
        embed.add_field(name="Причина", value=reason, inline=True)
        game_day = war['start_game_day'] if 'start_game_day' in war.keys() else 1
        game_month = war['start_game_month'] if 'start_game_month' in war.keys() else 1
        game_year = war['start_game_year'] if 'start_game_year' in war.keys() else 2000
        embed.add_field(name="Дата начала", value=f"{game_day:02d}.{game_month:02d}.{game_year}", inline=False)
        embed.add_field(name=f"{attacker['name']} (армия)", value=f"{attacker['army_count']} чел.", inline=True)
        embed.add_field(name=f"{defender['name']} (армия)", value=f"{defender['army_count']} чел.", inline=True)

        if moves:
            move_list = []
            for m in moves:
                move_list.append(f"{datetime.datetime.fromtimestamp(m['created_at']).strftime('%H:%M')} – {m['move_type']}")
            embed.add_field(name="Последние ходы", value="\n".join(move_list[:5]), inline=False)
        if reports:
            report_list = [r['report_text'][:100] + "..." for r in reports]
            embed.add_field(name="Сводки", value="\n".join(report_list), inline=False)

        return embed, None

    # --- Основные команды ---
    @app_commands.command(name="reg", description="Зарегистрироваться как правитель свободной страны")
    async def reg(self, interaction: discord.Interaction):
        existing = await self._get_country(interaction.user.id)
        if existing:
            await interaction.response.send_message(f"Вы уже управляете страной: {existing['name']}. Сначала откажитесь от неё.", ephemeral=True)
            return
        view = ContinentSelectView(self)
        await interaction.response.send_message("🌍 Выберите континент:", view=view, ephemeral=True)

    @app_commands.command(name="country_leave", description="Отказаться от управления страной")
    async def country_leave(self, interaction: discord.Interaction):
        row = await self._get_country(interaction.user.id)
        if not row:
            await interaction.response.send_message("Вы не управляете ни одной страной.", ephemeral=True)
            return
        country_role_id = COUNTRY_ROLES.get(row['name'])
        if country_role_id:
            role = interaction.guild.get_role(country_role_id)
            if role:
                await interaction.user.remove_roles(role)
        if DEFAULT_PLAYER_ROLE_ID:
            role = interaction.guild.get_role(DEFAULT_PLAYER_ROLE_ID)
            if role:
                await interaction.user.remove_roles(role)
        await async_execute("UPDATE countries SET owner_id=NULL, ruler_name='' WHERE id=?", (row['id'],))
        await interaction.response.send_message(f"Вы отказались от управления страной **{row['name']}**.")

    @app_commands.command(name="game", description="Открыть главное меню управления страной")
    async def game(self, interaction: discord.Interaction):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной. Используйте `/reg`.", ephemeral=True)
            return
        await interaction.response.send_message("Главное меню", view=GameMenu(country['id']), ephemeral=True)

    @app_commands.command(name="daily", description="Получить ежедневный бонус ресурсов")
    async def daily(self, interaction: discord.Interaction):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Сначала выберите страну.", ephemeral=True)
            return
        now = time.time()
        if country['last_daily'] and (now - country['last_daily']) < 86400:
            remaining = int(86400 - (now - country['last_daily']))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.response.send_message(f"Бонус можно забрать через {hours} ч {minutes} мин.", ephemeral=True)
            return
        # Денежный бонус напрямую в бюджет
        await async_execute("UPDATE countries SET budget = budget + 100_000_000 WHERE id = ?", (country['id'],))
        # Ресурсный бонус
        bonus = {"Продовольствие": 200_000_000}
        for res, amount in bonus.items():
            await async_execute(
                "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
                (country['id'], res, amount, amount)
            )
        await async_execute("UPDATE countries SET last_daily = ? WHERE id = ?", (now, country['id']))
        await interaction.response.send_message("Ежедневный бонус получен! +500$, +200 прод., +100 нефти.", ephemeral=True)

    @app_commands.command(name="date", description="Показать текущую игровую дату")
    async def show_date(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            game_date = await async_get_game_date()
            await interaction.followup.send(f"📅 Текущая игровая дата: {game_date.strftime('%d.%m.%Y')}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при получении даты: {e}", ephemeral=True)

    @app_commands.command(name="stats", description="Статистика страны")
    @app_commands.describe(member="Игрок (оставьте пустым для своей статистики)")
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        target_user = member or interaction.user
        country = await self._get_country(target_user.id)
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

    # --- АРМИЯ ---
    @app_commands.command(name="army", description="Информация об армии")
    async def army_info(self, interaction: discord.Interaction):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        army = country['army_count']
        pop = country['population']
        max_army = int(pop * 0.05)
        content = f"**Армия**\nЧисленность: {format_number(army)} (макс. {format_number(max_army)})\nНаселение: {format_number(pop)}\nСила: {country['combat_capability']}"
        await interaction.response.send_message(content, ephemeral=True)

    @app_commands.command(name="recruit", description="Нанять солдат в армию")
    @app_commands.describe(amount="Количество новобранцев")
    async def recruit(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Укажите положительное число.", ephemeral=True)
            return
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return

        population = country['population']
        current_army = country['army_count']
        max_army = int(population * 0.05)

        if current_army + amount > max_army:
            await interaction.response.send_message(f"❌ Нельзя иметь более 5% населения в армии (максимум {format_number(max_army)} чел.). Сейчас в армии {format_number(current_army)} чел., вы хотите нанять {format_number(amount)}.", ephemeral=True)
            return
        if amount > population - current_army:
            await interaction.response.send_message("Недостаточно свободного населения.", ephemeral=True)
            return

        cost_money = 10 * amount
        cost_food = 5 * amount
        if country['mobilization']:
            cost_money = cost_money // 2
            cost_food = cost_food // 2

        if country['budget'] < cost_money:
            await interaction.response.send_message("Недостаточно денег.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET budget = budget - ? WHERE id = ?", (cost_money, country['id']))
        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'", (cost_food, country['id']))
        new_army_count = current_army + amount
        await async_execute("UPDATE countries SET army_count = ? WHERE id=?", (new_army_count, country['id']))
        new_strength = min(100, country['combat_capability'] + amount / 10000)
        await async_execute("UPDATE countries SET combat_capability = ? WHERE id=?", (new_strength, country['id']))

        await interaction.response.send_message(f"✅ Нанято {format_number(amount)} солдат. Теперь в армии {format_number(new_army_count)} чел. (из максимум {format_number(max_army)}).", ephemeral=True)

    @app_commands.command(name="disband", description="Распустить часть армии")
    @app_commands.describe(amount="Сколько солдат уволить")
    async def disband(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Укажите положительное число.", ephemeral=True)
            return
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        if amount > country['army_count']:
            await interaction.response.send_message("Нельзя распустить больше, чем есть в армии.", ephemeral=True)
            return
        new_army_count = country['army_count'] - amount
        await async_execute("UPDATE countries SET army_count = ? WHERE id=?", (new_army_count, country['id']))
        new_strength = max(1, country['combat_capability'] - amount / 10000)
        await async_execute("UPDATE countries SET combat_capability = ? WHERE id=?", (new_strength, country['id']))
        await interaction.response.send_message(f"Распущено {format_number(amount)} солдат. Новая численность: {format_number(new_army_count)}.", ephemeral=True)

    # --- ДИПЛОМАТИЯ ---
    @app_commands.command(name="propose_pact", description="Предложить дипломатический пакт")
    @app_commands.describe(target="Страна (игрок)", pact_type="Тип: alliance, trade, non_aggression", subtype="Подтип союза (для alliance)")
    async def propose_pact(self, interaction: discord.Interaction, target: discord.Member, pact_type: str, subtype: str = None):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя заключать пакт с самим собой.", ephemeral=True)
            return
        if pact_type not in ['alliance', 'trade', 'non_aggression']:
            await interaction.response.send_message("Неверный тип пакта.", ephemeral=True)
            return
        if pact_type == 'alliance' and subtype not in ALLIANCE_SUBTYPES:
            await interaction.response.send_message(f"Неверный подтип союза. Доступные: {', '.join(ALLIANCE_SUBTYPES)}", ephemeral=True)
            return
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await self._get_country(target.id)
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return

        if pact_type == 'alliance':
            created = await async_fetch_one("SELECT COUNT(*) as cnt FROM pacts WHERE from_country=? AND type='alliance' AND accepted=1", (my_country['id'],))
            if created['cnt'] >= 5:
                await interaction.response.send_message("Вы уже создали максимальное количество союзов (5).", ephemeral=True)
                return
            total = await async_fetch_one("SELECT COUNT(*) as cnt FROM pacts WHERE (from_country=? OR to_country=?) AND type='alliance' AND accepted=1", (my_country['id'], my_country['id']))
            if total['cnt'] >= 10:
                await interaction.response.send_message("Вы уже участвуете в максимальном количестве союзов (10).", ephemeral=True)
                return

        existing = await async_fetch_one("SELECT id FROM pacts WHERE ((from_country=? AND to_country=?) OR (from_country=? AND to_country=?)) AND type=? AND accepted=1", (my_country['id'], target_country['id'], target_country['id'], my_country['id'], pact_type))
        if existing:
            await interaction.response.send_message("Такой пакт уже существует.", ephemeral=True)
            return

        await async_execute("INSERT INTO pacts (from_country, to_country, type, subtype, accepted) VALUES (?, ?, ?, ?, 0)", (my_country['id'], target_country['id'], pact_type, subtype or ""))
        pact_id = (await async_fetch_one("SELECT last_insert_rowid() as id", ()))['id']

        view = PactProposalView(pact_id, target.id, my_country['id'], pact_type, subtype)
        subtype_text = f" ({subtype})" if subtype else ""
        try:
            await target.send(f"{interaction.user.mention} предлагает вам **{pact_type}**{subtype_text} пакт от страны **{my_country['name']}**.\nНажмите кнопку ниже:", view=view)
        except discord.Forbidden:
            pass
        await interaction.response.send_message(f"Предложение пакта '{pact_type}' отправлено стране {target_country['name']}.", ephemeral=True)

    @app_commands.command(name="accept_pact", description="Принять предложенный пакт (по ID)")
    async def accept_pact(self, interaction: discord.Interaction, pact_id: int = None):
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        if pact_id is None:
            proposals = await async_fetch_all("SELECT id, from_country, type, subtype FROM pacts WHERE to_country=? AND accepted=0", (my_country['id'],))
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
        if proposal['to_country'] != my_country['id']:
            await interaction.response.send_message("Это предложение не вам.", ephemeral=True)
            return
        if proposal['type'] == 'alliance':
            total = await async_fetch_one("SELECT COUNT(*) as cnt FROM pacts WHERE (from_country=? OR to_country=?) AND type='alliance' AND accepted=1", (my_country['id'], my_country['id']))
            if total['cnt'] >= 10:
                await interaction.response.send_message("Вы уже участвуете в максимальном количестве союзов (10).", ephemeral=True)
                return
        await async_execute("UPDATE pacts SET accepted=1 WHERE id=?", (pact_id,))
        if proposal['type'] == 'alliance':
            guild = interaction.guild
            partner1 = await async_fetch_one("SELECT name FROM countries WHERE id=?", (proposal['from_country'],))
            partner2 = my_country
            channel_name = f"союз-{partner1['name']}-{partner2['name']}"
            cat_id = CATEGORY_IDS.get("pact")
            category = guild.get_channel(cat_id) if cat_id else None
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            from_owner = await async_fetch_one("SELECT owner_id FROM countries WHERE id=?", (proposal['from_country'],))
            if from_owner and from_owner['owner_id']:
                member = guild.get_member(from_owner['owner_id'])
                if member:
                    overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        from_country = await async_fetch_one("SELECT owner_id, name FROM countries WHERE id=?", (proposal['from_country'],))
        if from_country:
            await self._notify_user(from_country['owner_id'], f"Ваше предложение пакта **{proposal['type']}** было **принято** страной **{my_country['name']}**.")
        await interaction.response.send_message("Пакт принят!", ephemeral=True)

    @app_commands.command(name="break_pact", description="Расторгнуть все пакты с указанной страной")
    async def break_pact(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя разорвать пакт с самим собой.", ephemeral=True)
            return
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await self._get_country(target.id)
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        await async_execute("DELETE FROM pacts WHERE ((from_country=? AND to_country=?) OR (from_country=? AND to_country=?)) AND accepted=1", (my_country['id'], target_country['id'], target_country['id'], my_country['id']))
        await self._notify_country_owner(target_country['id'], f"Страна **{my_country['name']}** расторгла все пакты с вами.")
        await interaction.response.send_message(f"Все пакты с {target_country['name']} расторгнуты.", ephemeral=True)

    @app_commands.command(name="impose_sanction", description="Наложить санкции (выберите тип)")
    @app_commands.describe(target="Страна (игрок)", description="Описание")
    @app_commands.choices(sanction_type=SANCTION_CHOICES)
    async def impose_sanction(self, interaction: discord.Interaction, target: discord.Member, sanction_type: str, description: str = ""):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя наложить санкции на самого себя.", ephemeral=True)
            return
        if sanction_type not in SANCTION_TYPES:
            await interaction.response.send_message(f"Неизвестный тип санкции. Доступные: {', '.join(SANCTION_TYPES.keys())}", ephemeral=True)
            return
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await self._get_country(target.id)
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return

        stype = SANCTION_TYPES[sanction_type]
        param = stype['param']
        amount = stype['amount']
        desc = stype['desc'] if not description else description

        current_val_row = await async_fetch_one(f"SELECT {param} FROM countries WHERE id=?", (target_country['id'],))
        if current_val_row is None:
            await interaction.response.send_message("Ошибка получения параметра страны.", ephemeral=True)
            return
        current_val = current_val_row[param]
        new_val = max(0, current_val - amount)
        await async_execute(f"UPDATE countries SET {param}=? WHERE id=?", (new_val, target_country['id']))

        await async_execute("INSERT INTO sanctions (from_country, to_country, sanction_type, description, affected_param, effect_amount) VALUES (?, ?, ?, ?, ?, ?)", (my_country['id'], target_country['id'], sanction_type, desc, param, amount))
        try:
            await target.send(f"{interaction.user.mention} наложил на вас санкцию: **{desc}** ({sanction_type}).")
        except discord.Forbidden:
            pass
        await interaction.response.send_message(f"Санкция '{desc}' наложена на {target_country['name']}.", ephemeral=True)

    @app_commands.command(name="lift_sanction", description="Снять санкцию по ID")
    async def lift_sanction(self, interaction: discord.Interaction, sanction_id: int):
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        sanction = await async_fetch_one("SELECT * FROM sanctions WHERE id=? AND from_country=?", (sanction_id, my_country['id']))
        if not sanction:
            await interaction.response.send_message("Санкция с таким ID не найдена или вы не её инициатор.", ephemeral=True)
            return

        current_val_row = await async_fetch_one(f"SELECT {sanction['affected_param']} FROM countries WHERE id=?", (sanction['to_country'],))
        if current_val_row:
            current_val = current_val_row[sanction['affected_param']]
            new_val = min(100, current_val + sanction['effect_amount'])
            await async_execute(f"UPDATE countries SET {sanction['affected_param']}=? WHERE id=?", (new_val, sanction['to_country']))
        await async_execute("DELETE FROM sanctions WHERE id=?", (sanction_id,))
        await self._notify_country_owner(sanction['to_country'], f"Страна **{my_country['name']}** сняла с вас санкцию **{sanction['sanction_type']}**.")
        await interaction.response.send_message(f"Санкция ID {sanction_id} снята.", ephemeral=True)

    # --- АЛЬЯНСЫ ---
    @app_commands.command(name="create_alliance", description="Создать новый альянс")
    async def create_alliance(self, interaction: discord.Interaction, alliance_name: str):
        my_country = await self._get_country(interaction.user.id)
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
        cat_id = CATEGORY_IDS.get("alliance")
        if cat_id:
            category = guild.get_channel(cat_id)
        else:
            category = discord.utils.get(guild.categories, name="Альянсы")
            if category is None:
                category = await guild.create_category("Альянсы")
        channel = await guild.create_text_channel(alliance_name, category=category, overwrites=overwrites)
        await async_execute("INSERT INTO alliances (name, leader_id, channel_id) VALUES (?, ?, ?)", (alliance_name, my_country['id'], channel.id))
        alliance_id = (await async_fetch_one("SELECT id FROM alliances WHERE name=? AND leader_id=?", (alliance_name, my_country['id'])))['id']
        await async_execute("INSERT INTO alliance_members (alliance_id, country_id) VALUES (?, ?)", (alliance_id, my_country['id']))
        await interaction.response.send_message(f"Альянс '{alliance_name}' создан, канал {channel.mention}.", ephemeral=True)

    @app_commands.command(name="invite_alliance", description="Пригласить страну в ваш альянс (требуется подтверждение)")
    async def invite_alliance(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя пригласить самого себя.", ephemeral=True)
            return
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        alliance = await async_fetch_one("SELECT a.id, a.name FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id WHERE am.country_id=? AND a.leader_id=?", (my_country['id'], my_country['id']))
        if not alliance:
            await interaction.response.send_message("Вы не лидер альянса или не состоите в нём.", ephemeral=True)
            return
        target_country = await self._get_country(target.id)
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        target_member_count = await async_fetch_one("SELECT COUNT(*) as cnt FROM alliance_members WHERE country_id=?", (target_country['id'],))
        if target_member_count['cnt'] >= 5:
            await interaction.response.send_message(f"Игрок {target.mention} уже состоит в максимальном количестве альянсов (5).", ephemeral=True)
            return

        pending_alliance_invites[target.id] = (alliance['id'], my_country['id'])
        view = AllianceInviteView(alliance['id'], alliance['name'], my_country['id'], target.id)
        try:
            await target.send(f"{interaction.user.mention} приглашает вас в альянс **{alliance['name']}**.\nНажмите кнопку ниже:", view=view)
        except discord.Forbidden:
            pass
        await interaction.response.send_message(f"{target.mention} приглашён в альянс '{alliance['name']}'. Ожидание подтверждения.", ephemeral=True)

    @app_commands.command(name="accept_alliance", description="Принять приглашение в альянс (запасной метод)")
    async def accept_alliance(self, interaction: discord.Interaction):
        target_user = interaction.user
        invite = pending_alliance_invites.pop(target_user.id, None)
        if not invite:
            await interaction.response.send_message("У вас нет активных приглашений в альянс.", ephemeral=True)
            return
        alliance_id, leader_id = invite
        my_country = await self._get_country(target_user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_member_count = await async_fetch_one("SELECT COUNT(*) as cnt FROM alliance_members WHERE country_id=?", (my_country['id'],))
        if target_member_count['cnt'] >= 5:
            await interaction.response.send_message("Вы уже состоите в максимальном количестве альянсов (5).", ephemeral=True)
            return

        await async_execute("INSERT INTO alliance_members (alliance_id, country_id) VALUES (?, ?)", (alliance_id, my_country['id']))
        channel_id_row = await async_fetch_one("SELECT channel_id FROM alliances WHERE id=?", (alliance_id,))
        if channel_id_row:
            channel = self.bot.get_channel(channel_id_row['channel_id'])
            if channel:
                await channel.set_permissions(target_user, read_messages=True, send_messages=True)
        alliance_name = (await async_fetch_one("SELECT name FROM alliances WHERE id=?", (alliance_id,)))['name']
        await self._notify_country_owner(leader_id, f"Игрок {target_user.mention} принял приглашение в альянс **{alliance_name}** (страна **{my_country['name']}**).")
        await interaction.response.send_message(f"Вы вступили в альянс '{alliance_name}'.", ephemeral=True)

    @app_commands.command(name="kick_alliance", description="Исключить участника из альянса (только лидер)")
    async def kick_alliance(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя исключить самого себя.", ephemeral=True)
            return
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        alliance = await async_fetch_one("SELECT a.id, a.name, a.channel_id FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id WHERE am.country_id=? AND a.leader_id=?", (my_country['id'], my_country['id']))
        if not alliance:
            await interaction.response.send_message("Вы не лидер альянса или не состоите в нём.", ephemeral=True)
            return
        target_country = await self._get_country(target.id)
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        await async_execute("DELETE FROM alliance_members WHERE alliance_id=? AND country_id=?", (alliance['id'], target_country['id']))
        channel = self.bot.get_channel(alliance['channel_id'])
        if channel:
            await channel.set_permissions(target, overwrite=None)
        await self._notify_country_owner(target_country['id'], f"Вы были исключены из альянса **{alliance['name']}**.")
        await interaction.response.send_message(f"{target.mention} исключён из альянса '{alliance['name']}'.", ephemeral=True)

    @app_commands.command(name="leave_alliance", description="Покинуть текущий альянс")
    async def leave_alliance(self, interaction: discord.Interaction):
        my_country = await self._get_country(interaction.user.id)
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
        await self._notify_country_owner(alliance['leader_id'], f"Игрок {interaction.user.mention} покинул ваш альянс **{alliance['name']}** (страна **{my_country['name']}**).")
        await interaction.response.send_message(f"Вы покинули альянс '{alliance['name']}'.", ephemeral=True)

    @app_commands.command(name="disband_alliance", description="Распустить альянс (только лидер)")
    async def disband_alliance(self, interaction: discord.Interaction):
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        alliance = await async_fetch_one("SELECT a.id, a.name, a.channel_id FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id WHERE am.country_id=? AND a.leader_id=?", (my_country['id'], my_country['id']))
        if not alliance:
            await interaction.response.send_message("Вы не лидер альянса.", ephemeral=True)
            return
        members = await async_fetch_all("SELECT country_id FROM alliance_members WHERE alliance_id=?", (alliance['id'],))
        channel = self.bot.get_channel(alliance['channel_id'])
        if channel:
            await channel.delete()
        await async_execute("DELETE FROM alliance_members WHERE alliance_id=?", (alliance['id'],))
        await async_execute("DELETE FROM alliances WHERE id=?", (alliance['id'],))
        for m in members:
            if m['country_id'] != my_country['id']:
                await self._notify_country_owner(m['country_id'], f"Альянс **{alliance['name']}** был распущен лидером.")
        await interaction.response.send_message(f"Альянс '{alliance['name']}' распущен.", ephemeral=True)

    # --- МОБИЛИЗАЦИЯ ---
    @app_commands.command(name="mobilize", description="Переключить мобилизацию (макс. 2 раза в день по МСК)")
    async def mobilize(self, interaction: discord.Interaction):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return

        today = datetime.datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d")
        cooldown = await async_fetch_one("SELECT count FROM mobilize_cooldowns WHERE user_id=? AND date=?", (interaction.user.id, today))
        current_uses = cooldown['count'] if cooldown else 0
        if current_uses >= 2:
            await interaction.response.send_message("❌ Вы исчерпали лимит переключений мобилизации на сегодня (2 раза).", ephemeral=True)
            return

        new_mob = 1 - country['mobilization']
        await async_execute("UPDATE countries SET mobilization=? WHERE id=?", (new_mob, country['id']))

        if cooldown:
            await async_execute("UPDATE mobilize_cooldowns SET count = count + 1 WHERE user_id=? AND date=?", (interaction.user.id, today))
        else:
            await async_execute("INSERT INTO mobilize_cooldowns (user_id, date, count) VALUES (?, ?, 1)", (interaction.user.id, today))

        news_channel_id = CHANNEL_IDS.get("news")
        country_name = country['display_name'] or country['name']
        ruler_name = country['ruler_name'] or "Неизвестный правитель"
        if new_mob == 1:
            template = random.choice(MOBILIZE_ON_NEWS)
        else:
            template = random.choice(MOBILIZE_OFF_NEWS)
        news_text = template.format(country=country_name, ruler=ruler_name)
        if news_channel_id:
            channel = self.bot.get_channel(news_channel_id)
            if channel:
                await channel.send(news_text)

        state = "включена" if new_mob else "выключена"
        await interaction.response.send_message(f"Мобилизация {state}. (Осталось переключений сегодня: {1 - current_uses})", ephemeral=True)

    # --- ПЕРЕВОД ДЕНЕГ ---
    @app_commands.command(name="send_money", description="Перевести деньги другой стране")
    @app_commands.describe(target="Игрок-получатель", amount="Сумма в долларах")
    async def send_money(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя перевести деньги самому себе.", ephemeral=True)
            return
        if amount <= 0:
            await interaction.response.send_message("Сумма должна быть положительной.", ephemeral=True)
            return
        sender_country = await self._get_country(interaction.user.id)
        if not sender_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        receiver_country = await self._get_country(target.id)
        if not receiver_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return

        if sender_country['budget'] < amount:
            await interaction.response.send_message("Недостаточно денег для перевода.", ephemeral=True)
            return

        await async_execute("UPDATE countries SET budget = budget - ? WHERE id = ?", (amount, sender_country['id']))
        await async_execute("UPDATE countries SET budget = budget + ? WHERE id = ?", (amount, receiver_country['id']))

        channel_id = CHANNEL_IDS.get("lendlease")
        sender_name = sender_country['display_name'] or sender_country['name']
        receiver_name = receiver_country['display_name'] or receiver_country['name']
        sender_mention = interaction.user.mention
        receiver_mention = target.mention
        template = random.choice(LENDLEASE_MONEY_NEWS)
        news_msg = template.format(sender=f"**{sender_name}** ({sender_mention})", receiver=f"**{receiver_name}** ({receiver_mention})", amount=format_number(amount, 0))
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(news_msg)

        await interaction.response.send_message(f"✅ Переведено {format_number(amount, 0)}$ стране **{receiver_name}**.", ephemeral=True)

    # --- ПЕРЕВОД РЕСУРСОВ ---
    @app_commands.command(name="send_resource", description="Передать ресурс другой стране")
    @app_commands.describe(target="Игрок-получатель", resource="Название ресурса", amount="Количество")
    @app_commands.choices(resource=RESOURCE_CHOICES)
    async def send_resource(self, interaction: discord.Interaction, target: discord.Member, resource: str, amount: int):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя переслать ресурс самому себе.", ephemeral=True)
            return
        if amount <= 0:
            await interaction.response.send_message("Количество должно быть положительным.", ephemeral=True)
            return
        sender_country = await self._get_country(interaction.user.id)
        if not sender_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        receiver_country = await self._get_country(target.id)
        if not receiver_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return

        res_row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name=?", (sender_country['id'], resource))
        if not res_row or res_row['amount'] < amount:
            await interaction.response.send_message(f"У вас недостаточно ресурса '{resource}'.", ephemeral=True)
            return

        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?", (amount, sender_country['id'], resource))
        await async_execute(
            "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
            (receiver_country['id'], resource, amount, amount)
        )

        channel_id = CHANNEL_IDS.get("lendlease")
        sender_name = sender_country['display_name'] or sender_country['name']
        receiver_name = receiver_country['display_name'] or receiver_country['name']
        sender_mention = interaction.user.mention
        receiver_mention = target.mention
        template = random.choice(LENDLEASE_RESOURCE_NEWS)
        news_msg = template.format(sender=f"**{sender_name}** ({sender_mention})", receiver=f"**{receiver_name}** ({receiver_mention})", amount=amount, resource=resource)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(news_msg)

        await interaction.response.send_message(f"✅ Передано {amount} ед. '{resource}' стране **{receiver_name}**.", ephemeral=True)

    # --- РЫНОК (группа команд) ---
    market = app_commands.Group(name="market", description="Торговля на рынке")

    @market.command(name="sell", description="Выставить ресурс на продажу")
    @app_commands.describe(resource="Название ресурса", amount="Количество", price="Цена за весь лот (в долларах)")
    @app_commands.choices(resource=RESOURCE_CHOICES)
    async def market_sell(self, interaction: discord.Interaction, resource: str, amount: int, price: int):
        if amount <= 0 or price <= 0:
            await interaction.response.send_message("Количество и цена должны быть положительными.", ephemeral=True)
            return
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return

        active_lots = await async_fetch_one("SELECT COUNT(*) as cnt FROM market WHERE seller_id=? AND sold=0", (country['id'],))
        if active_lots['cnt'] >= 15:
            await interaction.response.send_message("❌ У вас уже максимальное количество активных лотов (15).", ephemeral=True)
            return

        res_row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name=?", (country['id'], resource))
        if not res_row or res_row['amount'] < amount:
            await interaction.response.send_message(f"У вас недостаточно ресурса '{resource}'.", ephemeral=True)
            return

        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name=?", (amount, country['id'], resource))
        await async_execute("INSERT INTO market (seller_id, resource_name, amount, price, sold) VALUES (?, ?, ?, ?, 0)", (country['id'], resource, amount, price))
        lot_id_row = await async_fetch_one("SELECT last_insert_rowid() as id", ())
        lot_id = lot_id_row['id'] if lot_id_row else "?"
        await interaction.response.send_message(f"✅ Вы выставили на рынок {amount} ед. '{resource}' за {price}$ (лот #{lot_id}).", ephemeral=True)

    @market.command(name="buy", description="Купить лот на рынке")
    @app_commands.describe(lot_id="ID лота")
    async def market_buy(self, interaction: discord.Interaction, lot_id: int):
        buyer_country = await self._get_country(interaction.user.id)
        if not buyer_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return

        lot = await async_fetch_one("SELECT * FROM market WHERE id=? AND sold=0", (lot_id,))
        if not lot:
            await interaction.response.send_message("Лот не найден или уже продан.", ephemeral=True)
            return
        if lot['seller_id'] == buyer_country['id']:
            await interaction.response.send_message("Нельзя купить свой собственный лот.", ephemeral=True)
            return

        if buyer_country['budget'] < lot['price']:
            await interaction.response.send_message("Недостаточно денег для покупки.", ephemeral=True)
            return

        await async_execute("UPDATE countries SET budget = budget - ? WHERE id = ?", (lot['price'], buyer_country['id']))
        await async_execute("UPDATE countries SET budget = budget + ? WHERE id = ?", (lot['price'], lot['seller_id']))
        await async_execute(
            "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
            (buyer_country['id'], lot['resource_name'], lot['amount'], lot['amount'])
        )
        await async_execute("UPDATE market SET sold=1 WHERE id=?", (lot_id,))

        seller_country = await async_fetch_one("SELECT owner_id, name FROM countries WHERE id=?", (lot['seller_id'],))
        if seller_country:
            seller_user = self.bot.get_user(seller_country['owner_id'])
            if seller_user:
                try:
                    await seller_user.send(f"💰 Ваш лот #{lot_id} ({lot['resource_name']} x{lot['amount']}) продан за {lot['price']}$.")
                except:
                    pass

        await interaction.response.send_message(f"✅ Вы купили лот #{lot_id}: {lot['resource_name']} x{lot['amount']} за {lot['price']}$.", ephemeral=True)

    @market.command(name="list", description="Показать список активных лотов на рынке")
    async def market_list(self, interaction: discord.Interaction):
        lots = await async_fetch_all("SELECT id, resource_name, amount, price, seller_id FROM market WHERE sold=0")
        if not lots:
            content = "На рынке нет активных предложений."
        else:
            content = "**Активные лоты на рынке:**\n"
            for lot in lots:
                seller_country = await async_fetch_one("SELECT name FROM countries WHERE id=?", (lot['seller_id'],))
                seller_name = seller_country['name'] if seller_country else "Неизвестно"
                content += f"#{lot['id']}: {lot['resource_name']} x{lot['amount']} за {lot['price']}$ (продавец: {seller_name})\n"
        await interaction.response.send_message(content, ephemeral=True)

    @market.command(name="cancel", description="Снять свой лот с рынка")
    @app_commands.describe(lot_id="ID лота")
    async def market_cancel(self, interaction: discord.Interaction, lot_id: int):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        lot = await async_fetch_one("SELECT * FROM market WHERE id=? AND seller_id=? AND sold=0", (lot_id, country['id']))
        if not lot:
            await interaction.response.send_message("Лот не найден, уже продан или не принадлежит вам.", ephemeral=True)
            return

        await async_execute(
            "INSERT INTO resources (country_id, resource_name, amount) VALUES (?, ?, ?) ON CONFLICT(country_id, resource_name) DO UPDATE SET amount = amount + ?",
            (country['id'], lot['resource_name'], lot['amount'], lot['amount'])
        )
        await async_execute("DELETE FROM market WHERE id=?", (lot_id,))
        await interaction.response.send_message(f"✅ Лот #{lot_id} снят с продажи, ресурс '{lot['resource_name']}' возвращён.", ephemeral=True)

    # --- УПРАВЛЕНИЕ ГОСУДАРСТВОМ ---
    @app_commands.command(name="rename", description="Изменить название страны")
    async def rename(self, interaction: discord.Interaction, new_name: str):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET display_name=? WHERE id=?", (new_name, country['id']))
        await interaction.response.send_message(f"Название страны изменено на {new_name}.", ephemeral=True)

    @app_commands.command(name="set_religion", description="Установить государственную религию")
    @app_commands.choices(religion=RELIGION_CHOICES)
    async def set_religion(self, interaction: discord.Interaction, religion: str):
        await interaction.response.defer(ephemeral=True)
        try:
            country = await self._get_country(interaction.user.id)
            if not country:
                await interaction.followup.send("Вы не управляете страной.", ephemeral=True)
                return
            await async_execute("UPDATE countries SET religion=? WHERE id=?", (religion, country['id']))
            await self._update_role(interaction.user, RELIGION_ROLES, religion)
            await interaction.followup.send(f"✅ Государственная религия изменена на **{religion}**.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при смене религии: {e}", ephemeral=True)

    @app_commands.command(name="set_ideology", description="Установить государственную идеологию")
    @app_commands.choices(ideology=IDEOLOGY_CHOICES)
    async def set_ideology(self, interaction: discord.Interaction, ideology: str):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET ideology=? WHERE id=?", (ideology, country['id']))
        await interaction.response.send_message(f"Идеология изменена на {ideology}.", ephemeral=True)

    @app_commands.command(name="set_government", description="Установить форму правления")
    @app_commands.choices(form=GOVERNMENT_CHOICES)
    async def set_government(self, interaction: discord.Interaction, form: str):
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        await async_execute("UPDATE countries SET government_form=? WHERE id=?", (form, country['id']))
        await interaction.response.send_message(f"Форма правления изменена на {form}.", ephemeral=True)

    async def _update_role(self, member: discord.Member, role_dict: dict, new_value: str):
        for role_name, role_id in role_dict.items():
            if role_id:
                role = member.guild.get_role(role_id)
                if role and role in member.roles:
                    try:
                        await member.remove_roles(role)
                    except:
                        pass
        if new_value in role_dict and role_dict[new_value]:
            role = member.guild.get_role(role_dict[new_value])
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Game(bot))
