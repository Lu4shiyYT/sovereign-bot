# data/provinces.py

PROVINCES_DATA = {
    "Сомали": [
        {"name": "Могадишо", "terrain": "urban", "climate_severity": 7, "economic_value": 1.5, "crime_rate": 60, "population": 2_000_000, "resources": {"Нефть": 200_000_000, "Пресная вода": 20_000_000_000, "Рыба": 500_000}},
        {"name": "Харгейса", "terrain": "desert", "climate_severity": 8, "economic_value": 0.8, "crime_rate": 60, "population": 2_000_000, "resources": {"Уголь": 50_000_000, "Золото": 5_000}},
        {"name": "Кисмайо", "terrain": "coast", "climate_severity": 6, "economic_value": 1.2, "crime_rate": 60, "population": 2_000_000, "resources": {"Нефть": 150_000_000, "Рыба": 800_000}},
        {"name": "Байдабо", "terrain": "plain", "climate_severity": 7, "economic_value": 0.9, "crime_rate": 60, "population": 2_000_000, "resources": {"Продовольствие": 10_000_000, "Древесина": 5_000_000}}
    ],
    "Афганистан": [
        {"name": "Кабул", "terrain": "urban", "climate_severity": 7, "economic_value": 1.3, "crime_rate": 60, "population": 2_000_000, "resources": {"Природный газ": 500_000_000_000, "Уголь": 80_000_000}},
        {"name": "Кандагар", "terrain": "desert", "climate_severity": 8, "economic_value": 0.9, "crime_rate": 60, "population": 2_000_000, "resources": {"Железная руда": 40_000_000, "Медь": 5_000_000}},
        {"name": "Герат", "terrain": "desert", "climate_severity": 7, "economic_value": 1.0, "crime_rate": 60, "population": 2_000_000, "resources": {"Уголь": 30_000_000, "Литий": 10_000}},
        {"name": "Мазари-Шариф", "terrain": "mountain", "climate_severity": 6, "economic_value": 0.8, "crime_rate": 60, "population": 2_000_000, "resources": {"Железная руда": 60_000_000, "Золото": 2_000}}
    ],
    # ... все остальные страны и провинции ...
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
