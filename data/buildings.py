BUILDING_TYPES = {
    "Ферма": {
        "cost": {"Продовольствие": 50},
        "build_time": 60,          # секунд
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
