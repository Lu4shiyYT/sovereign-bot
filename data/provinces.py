# data/provinces.py
# Все провинции стран с типами местности, климатом, экономической ценностью и природными ресурсами

PROVINCES_DATA = {
    "Сомали": [
        {"name": "Могадишо", "terrain": "urban", "climate_severity": 7, "economic_value": 1.5,
         "resources": {"Нефть": 500, "Пресная вода": 200}},
        {"name": "Харгейса", "terrain": "desert", "climate_severity": 8, "economic_value": 0.8,
         "resources": {"Уголь": 1000}},
        {"name": "Кисмайо", "terrain": "coast", "climate_severity": 6, "economic_value": 1.2,
         "resources": {"Рыба": 300, "Нефть": 400}},
        {"name": "Байдабо", "terrain": "plain", "climate_severity": 7, "economic_value": 0.9,
         "resources": {"Продовольствие": 600}}
    ],
    "Афганистан": [
        {"name": "Кабул", "terrain": "urban", "climate_severity": 7, "economic_value": 1.3,
         "resources": {"Природный газ": 2000}},
        {"name": "Кандагар", "terrain": "desert", "climate_severity": 8, "economic_value": 0.9,
         "resources": {"Железная руда": 1500}},
        {"name": "Герат", "terrain": "desert", "climate_severity": 7, "economic_value": 1.0,
         "resources": {"Уголь": 800}},
        {"name": "Мазари-Шариф", "terrain": "mountain", "climate_severity": 6, "economic_value": 0.8,
         "resources": {"Железная руда": 2000, "Уголь": 1200}}
    ],
    "Чад": [
        {"name": "Нджамена", "terrain": "urban", "climate_severity": 7, "economic_value": 1.2,
         "resources": {"Нефть": 3000}},
        {"name": "Мунду", "terrain": "plain", "climate_severity": 5, "economic_value": 0.9,
         "resources": {"Продовольствие": 800}},
        {"name": "Сарх", "terrain": "plain", "climate_severity": 5, "economic_value": 0.8,
         "resources": {"Хлопок": 500}}
    ],
    "Нигер": [
        {"name": "Ниамей", "terrain": "urban", "climate_severity": 6, "economic_value": 1.1,
         "resources": {"Уран": 1000}},
        {"name": "Зиндер", "terrain": "desert", "climate_severity": 7, "economic_value": 0.7,
         "resources": {"Железная руда": 900}},
        {"name": "Маради", "terrain": "plain", "climate_severity": 6, "economic_value": 0.9,
         "resources": {"Продовольствие": 700}}
    ],
    "ЦАР": [
        {"name": "Банги", "terrain": "urban", "climate_severity": 4, "economic_value": 1.0,
         "resources": {"Древесина": 2000, "Алмазы": 500}},
        {"name": "Берберати", "terrain": "forest", "climate_severity": 3, "economic_value": 0.8,
         "resources": {"Древесина": 3000}},
        {"name": "Бриа", "terrain": "forest", "climate_severity": 3, "economic_value": 0.7,
         "resources": {"Золото": 200}}
    ],
    "Нигерия": [
        {"name": "Абуджа", "terrain": "urban", "climate_severity": 4, "economic_value": 1.8,
         "resources": {"Нефть": 5000, "Природный газ": 3000}},
        {"name": "Лагос", "terrain": "urban", "climate_severity": 3, "economic_value": 2.0,
         "resources": {"Нефть": 4000}},
        {"name": "Кано", "terrain": "plain", "climate_severity": 5, "economic_value": 1.4,
         "resources": {"Продовольствие": 1500, "Хлопок": 1000}},
        {"name": "Порт-Харкорт", "terrain": "coast", "climate_severity": 4, "economic_value": 1.5,
         "resources": {"Нефть": 6000}}
    ]
}

# Модификаторы ландшафта для боя
TERRAIN_MODIFIERS = {
    "plain":    {"attack": 1.0, "defense": 1.0, "movement_cost": 1},
    "forest":   {"attack": 0.8, "defense": 1.3, "movement_cost": 2},
    "mountain": {"attack": 0.5, "defense": 2.0, "movement_cost": 3},
    "desert":   {"attack": 0.9, "defense": 0.7, "movement_cost": 1.5},
    "urban":    {"attack": 0.6, "defense": 1.8, "movement_cost": 1},
    "swamp":    {"attack": 0.7, "defense": 1.2, "movement_cost": 2.5},
    "coast":    {"attack": 0.9, "defense": 1.1, "movement_cost": 1}
}
