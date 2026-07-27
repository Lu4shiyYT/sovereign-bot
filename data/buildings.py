# data/buildings.py

BUILDING_TYPES = {
    "Шахта": {
        "cost": {"Доллары": 200_000, "Древесина": 30_000},
        "build_time": 300,  # секунд (5 минут)
        "upgrade_multiplier": 2.0,
        "resource_production": {"Уголь": 80},  # базовое количество за 2 часа
        "max_national": 2,
        "max_per_region": 1,
        "description": "Добывает уголь."
    },
    "Ферма": {
        "cost": {"Доллары": 100_000, "Продовольствие": 50_000},
        "build_time": 240,
        "upgrade_multiplier": 1.8,
        "resource_production": {"Продовольствие": 120},
        "max_national": 3,
        "max_per_region": 1,
        "description": "Выращивает продовольствие."
    },
    "Лесопилка": {
        "cost": {"Доллары": 150_000, "Древесина": 20_000},
        "build_time": 360,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Древесина": 100},
        "max_national": 2,
        "max_per_region": 1,
        "description": "Заготавливает древесину."
    },
    "Бизнес-центр": {
        "cost": {"Доллары": 500_000, "Бетон": 20_000, "Сталь": 10_000},
        "build_time": 600,
        "upgrade_multiplier": 2.5,
        "resource_production": {},  # даёт деньги напрямую
        "money_production": 2000,    # базовый доход долларами за цикл
        "max_national": 2,
        "max_per_region": 1,
        "description": "Приносит доход в бюджет."
    },
    "Завод электроники": {
        "cost": {"Доллары": 1_000_000, "Сталь": 50_000, "Медь": 20_000},
        "build_time": 900,
        "upgrade_multiplier": 3.0,
        "resource_production": {"Электроника": 50},
        "max_national": 1,
        "max_per_region": 1,
        "description": "Производит электронику."
    }
}
