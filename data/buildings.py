# data/buildings.py

BUILDING_TYPES = {
    # ========================
    # ВНЕУРОВНЕВЫЕ ПОСТРОЙКИ (tech_level = 0)
    # ========================
    "Жилой дом": {
        "cost": {"Доллары": 50_000, "Бетон": 10_000, "Древесина": 5_000},
        "build_time": 1800,
        "upgrade_multiplier": 1.5,
        "resource_production": None,
        "money_production": None,
        "max_national": 20,
        "max_per_region": 5,
        "tech_level": 0,
        "description": "Увеличивает население провинции на 1000 за уровень.",
        "effects": {"population": 1000}
    },
    "Казарма": {
        "cost": {"Доллары": 100_000, "Сталь": 20_000, "Бетон": 15_000},
        "build_time": 2400,
        "upgrade_multiplier": 1.8,
        "resource_production": None,
        "money_production": None,
        "max_national": 10,
        "max_per_region": 2,
        "tech_level": 0,
        "description": "Увеличивает лимит армии на 50 солдат за уровень.",
        "effects": {"army_capacity": 50}
    },
    "Полицейский участок": {
        "cost": {"Доллары": 80_000, "Бетон": 8_000, "Электроника": 500},
        "build_time": 1500,
        "upgrade_multiplier": 1.6,
        "resource_production": None,
        "money_production": None,
        "max_national": 15,
        "max_per_region": 3,
        "tech_level": 0,
        "description": "Снижает уровень преступности в провинции на 5% за уровень.",
        "effects": {"crime_rate": -5}
    },
    "Пожарная станция": {
        "cost": {"Доллары": 60_000, "Бетон": 6_000, "Сталь": 4_000},
        "build_time": 1200,
        "upgrade_multiplier": 1.5,
        "resource_production": None,
        "money_production": None,
        "max_national": 10,
        "max_per_region": 2,
        "tech_level": 0,
        "description": "Снижает ущерб от пожаров, повышает экологию на 2% за уровень.",
        "effects": {"ecology": 2}
    },
    "Поликлиника": {
        "cost": {"Доллары": 120_000, "Бетон": 10_000, "Медикаменты": 2_000},
        "build_time": 2000,
        "upgrade_multiplier": 1.7,
        "resource_production": None,
        "money_production": None,
        "max_national": 12,
        "max_per_region": 2,
        "tech_level": 0,
        "description": "Повышает здоровье населения провинции на 3% за уровень.",
        "effects": {"health": 3}
    },
    "Школа": {
        "cost": {"Доллары": 90_000, "Бетон": 12_000, "Древесина": 8_000},
        "build_time": 1800,
        "upgrade_multiplier": 1.6,
        "resource_production": None,
        "money_production": None,
        "max_national": 15,
        "max_per_region": 3,
        "tech_level": 0,
        "description": "Повышает научный прогресс страны на 1% за уровень.",
        "effects": {"science_progress": 1}
    },
    "Университет": {
        "cost": {"Доллары": 300_000, "Бетон": 20_000, "Электроника": 5_000},
        "build_time": 3600,
        "upgrade_multiplier": 2.0,
        "resource_production": None,
        "money_production": None,
        "max_national": 5,
        "max_per_region": 1,
        "tech_level": 0,
        "description": "Значительно повышает научный прогресс (3% за уровень). Требуется хотя бы одна школа 3-го уровня в стране.",
        "effects": {"science_progress": 3}
    },
    "Детский сад": {
        "cost": {"Доллары": 40_000, "Бетон": 5_000, "Древесина": 3_000},
        "build_time": 900,
        "upgrade_multiplier": 1.4,
        "resource_production": None,
        "money_production": None,
        "max_national": 20,
        "max_per_region": 5,
        "tech_level": 0,
        "description": "Повышает настроение граждан на 2% и демографический рост на 0.1% за уровень.",
        "effects": {"citizen_mood": 2, "demographic_growth": 0.1}
    },
    "Завод простейшего вооружения": {
        "cost": {"Доллары": 200_000, "Сталь": 30_000, "Древесина": 10_000},
        "build_time": 3000,
        "upgrade_multiplier": 1.8,
        "resource_production": {"Пистолеты": 10, "Винтовки": 5},
        "money_production": None,
        "max_national": 5,
        "max_per_region": 1,
        "tech_level": 0,
        "description": "Производит стрелковое оружие (пистолеты и винтовки)."
    },
    "Автосалон": {
        "cost": {"Доллары": 150_000, "Сталь": 10_000, "Стекло": 5_000},
        "build_time": 2400,
        "upgrade_multiplier": 1.6,
        "resource_production": None,
        "money_production": 3000,
        "max_national": 8,
        "max_per_region": 2,
        "tech_level": 0,
        "description": "Приносит доход от продажи автомобилей (требуются поставки с автозавода)."
    },
    "Бизнес-центр": {
        "cost": {"Доллары": 500_000, "Бетон": 20_000, "Сталь": 10_000},
        "build_time": 3600,
        "upgrade_multiplier": 2.0,
        "resource_production": None,
        "money_production": 2000,
        "max_national": 5,
        "max_per_region": 2,
        "tech_level": 0,
        "description": "Генерирует доход в бюджет."
    },
    "Небоскрёб": {
        "cost": {"Доллары": 2_000_000, "Сталь": 50_000, "Бетон": 40_000, "Стекло": 20_000},
        "build_time": 7200,
        "upgrade_multiplier": 2.5,
        "resource_production": None,
        "money_production": 8000,
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 0,
        "description": "Огромный жилой и офисный комплекс. Сильно увеличивает население (5000 за уровень) и приносит доход.",
        "effects": {"population": 5000}
    },
    "Больница": {
        "cost": {"Доллары": 500_000, "Бетон": 25_000, "Медикаменты": 10_000, "Электроника": 5_000},
        "build_time": 4500,
        "upgrade_multiplier": 2.2,
        "resource_production": None,
        "money_production": None,
        "max_national": 8,
        "max_per_region": 1,
        "tech_level": 0,
        "description": "Значительно повышает здоровье населения (5% за уровень). Требуется поликлиника 2-го уровня в провинции.",
        "effects": {"health": 5}
    },
    "Торговый центр": {
        "cost": {"Доллары": 300_000, "Сталь": 15_000, "Бетон": 20_000},
        "build_time": 2800,
        "upgrade_multiplier": 1.7,
        "resource_production": None,
        "money_production": 4000,
        "max_national": 10,
        "max_per_region": 3,
        "tech_level": 0,
        "description": "Увеличивает экономическую ценность провинции на 0.5 за уровень и приносит доход.",
        "effects": {"economic_value": 0.5}
    },
    "Кинозал": {
        "cost": {"Доллары": 80_000, "Бетон": 8_000, "Электроника": 2_000},
        "build_time": 1200,
        "upgrade_multiplier": 1.4,
        "resource_production": None,
        "money_production": 500,
        "max_national": 12,
        "max_per_region": 3,
        "tech_level": 0,
        "description": "Повышает настроение граждан на 3% за уровень.",
        "effects": {"citizen_mood": 3}
    },
    "Стадион": {
        "cost": {"Доллары": 600_000, "Бетон": 30_000, "Сталь": 20_000},
        "build_time": 5000,
        "upgrade_multiplier": 2.0,
        "resource_production": None,
        "money_production": 1500,
        "max_national": 5,
        "max_per_region": 1,
        "tech_level": 0,
        "description": "Повышает настроение граждан на 5% и приносит доход от мероприятий.",
        "effects": {"citizen_mood": 5}
    },
    "Метро": {
        "cost": {"Доллары": 1_000_000, "Сталь": 50_000, "Бетон": 60_000},
        "build_time": 10000,
        "upgrade_multiplier": 1.5,
        "resource_production": None,
        "money_production": None,
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 0,
        "description": "Улучшает транспортную доступность: снижает преступность на 2%, повышает экономическую ценность на 1.0 за уровень.",
        "effects": {"crime_rate": -2, "economic_value": 1.0}
    },

    # ========================
    # УРОВЕНЬ 1 – Базовое производство
    # ========================
    "Ферма": {
        "cost": {"Доллары": 30_000, "Древесина": 5_000},
        "build_time": 600,
        "upgrade_multiplier": 1.8,
        "resource_production": {"Продовольствие": 120},
        "money_production": None,
        "max_national": 20,
        "max_per_region": 5,
        "tech_level": 1,
        "description": "Выращивает зерно и овощи."
    },
    "Лесопилка": {
        "cost": {"Доллары": 40_000, "Древесина": 3_000},
        "build_time": 720,
        "upgrade_multiplier": 2.0,
        "resource_production": {"Древесина": 100},
        "money_production": None,
        "max_national": 10,
        "max_per_region": 2,
        "tech_level": 1,
        "description": "Заготавливает древесину."
    },
    "Каменоломня": {
        "cost": {"Доллары": 50_000, "Древесина": 8_000},
        "build_time": 900,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Камень": 80, "Бетон": 40},
        "money_production": None,
        "max_national": 8,
        "max_per_region": 2,
        "tech_level": 1,
        "description": "Добывает камень и производит бетон."
    },
    "Рыболовецкий порт": {
        "cost": {"Доллары": 60_000, "Древесина": 10_000},
        "build_time": 1200,
        "upgrade_multiplier": 1.9,
        "resource_production": {"Рыба": 150},
        "money_production": None,
        "max_national": 6,
        "max_per_region": 1,
        "tech_level": 1,
        "description": "Ловит рыбу (продовольствие). Требует побережья."
    },
    "Ветряная электростанция": {
        "cost": {"Доллары": 80_000, "Сталь": 12_000, "Электроника": 2_000},
        "build_time": 1500,
        "upgrade_multiplier": 1.7,
        "resource_production": {"Электроэнергия": 50},
        "money_production": None,
        "max_national": 10,
        "max_per_region": 3,
        "tech_level": 1,
        "description": "Вырабатывает электроэнергию (зависит от ветра)."
    },

    # ========================
    # УРОВЕНЬ 2 – Лёгкая промышленность
    # ========================
    "Текстильная фабрика": {
        "cost": {"Доллары": 100_000, "Бетон": 8_000, "Хлопок": 5_000},
        "build_time": 1500,
        "upgrade_multiplier": 1.8,
        "resource_production": {"Текстиль": 200},
        "max_national": 8,
        "max_per_region": 2,
        "tech_level": 2,
        "description": "Производит текстиль и одежду."
    },
    "Мебельная мастерская": {
        "cost": {"Доллары": 70_000, "Древесина": 15_000},
        "build_time": 1200,
        "upgrade_multiplier": 1.6,
        "resource_production": {"Мебель": 100},
        "max_national": 10,
        "max_per_region": 3,
        "tech_level": 2,
        "description": "Изготавливает мебель из древесины."
    },
    "Пекарня": {
        "cost": {"Доллары": 50_000, "Продовольствие": 10_000},
        "build_time": 900,
        "upgrade_multiplier": 1.5,
        "resource_production": {"Хлеб": 300},
        "max_national": 15,
        "max_per_region": 5,
        "tech_level": 2,
        "description": "Выпекает хлебобулочные изделия."
    },
    "Кирпичный завод": {
        "cost": {"Доллары": 80_000, "Уголь": 5_000, "Глина": 20_000},
        "build_time": 1200,
        "upgrade_multiplier": 1.7,
        "resource_production": {"Кирпичи": 250},
        "max_national": 8,
        "max_per_region": 2,
        "tech_level": 2,
        "description": "Производит кирпичи и бетонные блоки."
    },
    "Малая гидроэлектростанция": {
        "cost": {"Доллары": 120_000, "Бетон": 15_000, "Сталь": 10_000},
        "build_time": 1800,
        "upgrade_multiplier": 1.6,
        "resource_production": {"Электроэнергия": 80},
        "max_national": 5,
        "max_per_region": 1,
        "tech_level": 2,
        "description": "Вырабатывает электроэнергию (требуется река)."
    },

    # ========================
    # УРОВЕНЬ 3 – Добыча ископаемых
    # ========================
    "Шахта": {
        "cost": {"Доллары": 200_000, "Древесина": 30_000, "Сталь": 20_000},
        "build_time": 2400,
        "upgrade_multiplier": 2.0,
        "resource_production": {"Уголь": 150, "Железная руда": 100, "Медь": 50},
        "max_national": 10,
        "max_per_region": 2,
        "tech_level": 3,
        "description": "Добывает уголь, железную руду, медь (в зависимости от ресурсов провинции)."
    },
    "Нефтяная вышка": {
        "cost": {"Доллары": 500_000, "Сталь": 50_000, "Электроника": 10_000},
        "build_time": 3600,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Нефть": 200},
        "max_national": 6,
        "max_per_region": 1,
        "tech_level": 3,
        "description": "Добывает нефть."
    },
    "Газовый промысел": {
        "cost": {"Доллары": 400_000, "Сталь": 40_000, "Бетон": 30_000},
        "build_time": 3000,
        "upgrade_multiplier": 2.1,
        "resource_production": {"Природный газ": 180},
        "max_national": 6,
        "max_per_region": 1,
        "tech_level": 3,
        "description": "Добывает природный газ."
    },
    "Карьер по добыче урана": {
        "cost": {"Доллары": 800_000, "Сталь": 60_000, "Химикаты": 20_000},
        "build_time": 4200,
        "upgrade_multiplier": 2.5,
        "resource_production": {"Уран": 20},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 3,
        "description": "Добывает урановую руду (требуется геологоразведка)."
    },
    "Золотодобывающая шахта": {
        "cost": {"Доллары": 600_000, "Сталь": 30_000, "Химикаты": 15_000},
        "build_time": 3600,
        "upgrade_multiplier": 2.3,
        "resource_production": {"Золото": 10},
        "max_national": 4,
        "max_per_region": 1,
        "tech_level": 3,
        "description": "Добывает золото."
    },

    # ========================
    # УРОВЕНЬ 4 – Металлургия и химия
    # ========================
    "Сталелитейный завод": {
        "cost": {"Доллары": 1_000_000, "Железная руда": 50_000, "Уголь": 20_000},
        "build_time": 3600,
        "upgrade_multiplier": 2.0,
        "resource_production": {"Сталь": 300},
        "max_national": 6,
        "max_per_region": 1,
        "tech_level": 4,
        "description": "Выплавляет сталь из руды и угля."
    },
    "Алюминиевый завод": {
        "cost": {"Доллары": 1_200_000, "Бокситы": 40_000, "Электроэнергия": 50},
        "build_time": 4200,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Алюминий": 200},
        "max_national": 4,
        "max_per_region": 1,
        "tech_level": 4,
        "description": "Производит алюминий (требуется много энергии)."
    },
    "Нефтеперерабатывающий завод": {
        "cost": {"Доллары": 2_000_000, "Сталь": 80_000, "Электроника": 30_000},
        "build_time": 5400,
        "upgrade_multiplier": 2.3,
        "resource_production": {"Бензин": 150, "Дизель": 100, "Мазут": 80},
        "max_national": 4,
        "max_per_region": 1,
        "tech_level": 4,
        "description": "Перерабатывает нефть в топливо."
    },
    "Химический комбинат": {
        "cost": {"Доллары": 1_500_000, "Нефть": 20_000, "Минералы": 10_000},
        "build_time": 4800,
        "upgrade_multiplier": 2.1,
        "resource_production": {"Химикаты": 200, "Удобрения": 150},
        "max_national": 5,
        "max_per_region": 1,
        "tech_level": 4,
        "description": "Производит химикаты и удобрения."
    },
    "Цементный завод": {
        "cost": {"Доллары": 800_000, "Известняк": 60_000, "Уголь": 10_000},
        "build_time": 3000,
        "upgrade_multiplier": 1.9,
        "resource_production": {"Цемент": 250},
        "max_national": 6,
        "max_per_region": 1,
        "tech_level": 4,
        "description": "Производит цемент."
    },

    # ========================
    # УРОВЕНЬ 5 – Машиностроение и электроника
    # ========================
    "Автомобильный завод": {
        "cost": {"Доллары": 3_000_000, "Сталь": 100_000, "Алюминий": 50_000, "Электроника": 20_000},
        "build_time": 7200,
        "upgrade_multiplier": 2.5,
        "resource_production": {"Автомобили": 50},
        "max_national": 4,
        "max_per_region": 1,
        "tech_level": 5,
        "description": "Производит гражданские автомобили."
    },
    "Завод электроники": {
        "cost": {"Доллары": 2_500_000, "Кремний": 30_000, "Редкоземельные металлы": 5_000, "Золото": 2_000},
        "build_time": 6000,
        "upgrade_multiplier": 2.8,
        "resource_production": {"Электроника": 100},
        "max_national": 5,
        "max_per_region": 1,
        "tech_level": 5,
        "description": "Производит микрочипы и электронные компоненты."
    },
    "Станкостроительный завод": {
        "cost": {"Доллары": 2_000_000, "Сталь": 80_000, "Электроника": 10_000},
        "build_time": 5400,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Станки": 40},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 5,
        "description": "Производит станки для других заводов."
    },
    "Завод бытовой техники": {
        "cost": {"Доллары": 1_800_000, "Сталь": 60_000, "Электроника": 15_000, "Пластик": 10_000},
        "build_time": 4800,
        "upgrade_multiplier": 2.0,
        "resource_production": {"Бытовая техника": 80},
        "max_national": 4,
        "max_per_region": 1,
        "tech_level": 5,
        "description": "Производит холодильники, стиральные машины и т.д."
    },
    "Аккумуляторный завод": {
        "cost": {"Доллары": 2_200_000, "Литий": 10_000, "Кобальт": 5_000, "Электроника": 8_000},
        "build_time": 5400,
        "upgrade_multiplier": 2.4,
        "resource_production": {"Аккумуляторы": 60},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 5,
        "description": "Производит литий-ионные батареи."
    },

    # ========================
    # УРОВЕНЬ 6 – Тяжёлое машиностроение и энергетика
    # ========================
    "Тракторный завод": {
        "cost": {"Доллары": 2_500_000, "Сталь": 90_000, "Двигатели": 10_000},
        "build_time": 6000,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Тракторы": 30},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 6,
        "description": "Производит сельскохозяйственную технику."
    },
    "Завод строительной техники": {
        "cost": {"Доллары": 3_000_000, "Сталь": 100_000, "Гидравлика": 20_000},
        "build_time": 7200,
        "upgrade_multiplier": 2.3,
        "resource_production": {"Экскаваторы": 20, "Краны": 10},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 6,
        "description": "Производит строительную технику."
    },
    "Солнечная электростанция": {
        "cost": {"Доллары": 1_800_000, "Кремний": 40_000, "Стекло": 30_000, "Сталь": 50_000},
        "build_time": 5400,
        "upgrade_multiplier": 1.8,
        "resource_production": {"Электроэнергия": 120},
        "max_national": 5,
        "max_per_region": 2,
        "tech_level": 6,
        "description": "Вырабатывает электроэнергию (эффективно в пустынях/равнинах)."
    },
    "Геотермальная электростанция": {
        "cost": {"Доллары": 2_200_000, "Сталь": 70_000, "Бетон": 50_000},
        "build_time": 6000,
        "upgrade_multiplier": 1.7,
        "resource_production": {"Электроэнергия": 100},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 6,
        "description": "Вырабатывает электроэнергию (требуется вулканическая зона)."
    },
    "Приливная электростанция": {
        "cost": {"Доллары": 2_500_000, "Бетон": 60_000, "Сталь": 40_000},
        "build_time": 6500,
        "upgrade_multiplier": 1.6,
        "resource_production": {"Электроэнергия": 90},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 6,
        "description": "Вырабатывает электроэнергию (требуется побережье)."
    },

    # ========================
    # УРОВЕНЬ 7 – Высокие технологии
    # ========================
    "Завод программного обеспечения": {
        "cost": {"Доллары": 1_500_000, "Электроника": 20_000, "Офисная техника": 10_000},
        "build_time": 3600,
        "upgrade_multiplier": 2.0,
        "resource_production": {"Программное обеспечение": 50},
        "max_national": 8,
        "max_per_region": 2,
        "tech_level": 7,
        "description": "Разрабатывает и продаёт лицензии на ПО."
    },
    "Центр обработки данных": {
        "cost": {"Доллары": 3_000_000, "Электроника": 50_000, "Сталь": 30_000, "Электроэнергия": 200},
        "build_time": 7200,
        "upgrade_multiplier": 2.5,
        "resource_production": {"Облачные услуги": 80},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 7,
        "description": "Предоставляет облачные сервисы (требует много энергии)."
    },
    "Фармацевтический завод": {
        "cost": {"Доллары": 2_500_000, "Химикаты": 20_000, "Биопрепараты": 10_000},
        "build_time": 5400,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Медикаменты": 100},
        "max_national": 4,
        "max_per_region": 1,
        "tech_level": 7,
        "description": "Производит лекарства уровней J–G."
    },
    "Биотехнологическая лаборатория": {
        "cost": {"Доллары": 3_500_000, "Электроника": 30_000, "Химикаты": 15_000},
        "build_time": 6000,
        "upgrade_multiplier": 2.8,
        "resource_production": {"Биоматериалы": 30},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 7,
        "description": "Разрабатывает биопрепараты и генную инженерию."
    },
    "Завод оптоволокна": {
        "cost": {"Доллары": 2_000_000, "Кремний": 25_000, "Редкоземельные металлы": 3_000},
        "build_time": 4800,
        "upgrade_multiplier": 2.1,
        "resource_production": {"Оптоволокно": 60},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 7,
        "description": "Производит оптоволоконные кабели."
    },

    # ========================
    # УРОВЕНЬ 8 – Военно-промышленный комплекс
    # ========================
    "Завод стрелкового оружия": {
        "cost": {"Доллары": 3_000_000, "Сталь": 60_000, "Древесина": 20_000},
        "build_time": 6000,
        "upgrade_multiplier": 2.3,
        "resource_production": {"Пистолеты": 20, "Автоматы": 15, "Пулемёты": 5},
        "max_national": 4,
        "max_per_region": 1,
        "tech_level": 8,
        "description": "Производит стрелковое оружие."
    },
    "Танковый завод": {
        "cost": {"Доллары": 8_000_000, "Сталь": 200_000, "Электроника": 50_000},
        "build_time": 10800,
        "upgrade_multiplier": 2.8,
        "resource_production": {"Танки": 3, "БМП": 5},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 8,
        "description": "Производит танки, БМП и БТР."
    },
    "Авиастроительный завод": {
        "cost": {"Доллары": 10_000_000, "Алюминий": 100_000, "Титан": 50_000, "Электроника": 80_000},
        "build_time": 14400,
        "upgrade_multiplier": 3.0,
        "resource_production": {"Истребители": 1, "Бомбардировщики": 1, "Вертолёты": 2},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 8,
        "description": "Производит военную авиацию."
    },
    "Судостроительный завод": {
        "cost": {"Доллары": 9_000_000, "Сталь": 250_000, "Электроника": 60_000},
        "build_time": 12000,
        "upgrade_multiplier": 2.7,
        "resource_production": {"Эсминцы": 1, "Фрегаты": 1, "Подводные лодки": 1},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 8,
        "description": "Строит военные корабли."
    },
    "Завод ракетных систем": {
        "cost": {"Доллары": 7_000_000, "Сталь": 150_000, "Электроника": 70_000},
        "build_time": 9000,
        "upgrade_multiplier": 2.6,
        "resource_production": {"Ракеты": 10, "ПВО": 5},
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 8,
        "description": "Производит ракеты и системы ПВО."
    },

    # ========================
    # УРОВЕНЬ 9 – Специальное вооружение
    # ========================
    "Завод ядерных реакторов": {
        "cost": {"Доллары": 15_000_000, "Сталь": 300_000, "Бетон": 200_000, "Уран": 5_000},
        "build_time": 18000,
        "upgrade_multiplier": 3.0,
        "resource_production": {"Ядерные реакторы": 1},
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 9,
        "description": "Производит ядерные реакторы для АЭС. Высокий шанс аварии при низкой квалификации персонала."
    },
    "Завод по обогащению урана": {
        "cost": {"Доллары": 20_000_000, "Сталь": 250_000, "Электроэнергия": 500},
        "build_time": 20000,
        "upgrade_multiplier": 3.2,
        "resource_production": {"Обогащённый уран": 5},
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 9,
        "description": "Обогащает уран для ядерного топлива и оружия."
    },
    "Завод химического оружия": {
        "cost": {"Доллары": 18_000_000, "Химикаты": 100_000, "Сталь": 150_000},
        "build_time": 15000,
        "upgrade_multiplier": 2.9,
        "resource_production": {"Химическое оружие": 20},
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 9,
        "description": "Производит химические боеприпасы. Строжайшие санкции при обнаружении."
    },
    "Кибернетический центр": {
        "cost": {"Доллары": 5_000_000, "Электроника": 80_000, "Серверы": 30_000},
        "build_time": 8000,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Кибероружие": 15},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 9,
        "description": "Разрабатывает кибероружие и системы защиты."
    },
    "Центр подготовки спецназа": {
        "cost": {"Доллары": 4_000_000, "Бетон": 50_000, "Сталь": 30_000},
        "build_time": 6000,
        "upgrade_multiplier": 2.0,
        "resource_production": None,
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 9,
        "description": "Тренирует элитные подразделения (увеличивает силу армии)."
    },

    # ========================
    # УРОВЕНЬ 10 – Ядерная энергетика и мирный атом
    # ========================
    "Атомная электростанция": {
        "cost": {"Доллары": 25_000_000, "Бетон": 500_000, "Сталь": 300_000, "Ядерный реактор": 1},
        "build_time": 25000,
        "upgrade_multiplier": 2.5,
        "resource_production": {"Электроэнергия": 500},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 10,
        "description": "Мощный источник электроэнергии. Требуется ядерный реактор."
    },
    "Радиоизотопный центр": {
        "cost": {"Доллары": 8_000_000, "Обогащённый уран": 2_000, "Электроника": 30_000},
        "build_time": 12000,
        "upgrade_multiplier": 2.0,
        "resource_production": {"Медицинские изотопы": 10},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 10,
        "description": "Производит изотопы для медицины."
    },
    "Исследовательский ядерный реактор": {
        "cost": {"Доллары": 20_000_000, "Сталь": 200_000, "Обогащённый уран": 1_000},
        "build_time": 18000,
        "upgrade_multiplier": 2.8,
        "resource_production": None,
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 10,
        "description": "Ускоряет научные исследования (повышает science_progress)."
    },
    "Хранилище радиоактивных отходов": {
        "cost": {"Доллары": 15_000_000, "Бетон": 300_000, "Свинец": 100_000},
        "build_time": 15000,
        "upgrade_multiplier": 1.5,
        "resource_production": None,
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 10,
        "description": "Безопасно хранит радиоактивные отходы, снижая экологический ущерб."
    },
    "Завод по производству тепловыделяющих сборок": {
        "cost": {"Доллары": 18_000_000, "Обогащённый уран": 5_000, "Цирконий": 10_000},
        "build_time": 20000,
        "upgrade_multiplier": 2.2,
        "resource_production": {"ТВЭЛы": 20},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 10,
        "description": "Производит топливные сборки для АЭС."
    },

    # ========================
    # УРОВЕНЬ 11 – Космическая промышленность
    # ========================
    "Завод по производству спутников": {
        "cost": {"Доллары": 30_000_000, "Алюминий": 100_000, "Электроника": 80_000, "Золото": 5_000},
        "build_time": 20000,
        "upgrade_multiplier": 3.0,
        "resource_production": {"Спутники": 1},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 11,
        "description": "Производит спутники связи и разведки."
    },
    "Завод по производству космических ракет": {
        "cost": {"Доллары": 50_000_000, "Титан": 200_000, "Алюминий": 150_000, "Электроника": 100_000},
        "build_time": 30000,
        "upgrade_multiplier": 3.5,
        "resource_production": {"Ракеты-носители": 1},
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 11,
        "description": "Строит ракеты-носители для космических запусков."
    },
    "Космодром": {
        "cost": {"Доллары": 100_000_000, "Бетон": 1_000_000, "Сталь": 500_000},
        "build_time": 50000,
        "upgrade_multiplier": 2.0,
        "resource_production": None,
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 11,
        "description": "Инфраструктура для запуска космических ракет."
    },
    "Центр управления полётами": {
        "cost": {"Доллары": 20_000_000, "Электроника": 50_000, "Серверы": 40_000},
        "build_time": 15000,
        "upgrade_multiplier": 2.0,
        "resource_production": None,
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 11,
        "description": "Управляет спутниками и космическими миссиями."
    },
    "Завод космических скафандров": {
        "cost": {"Доллары": 12_000_000, "Текстиль": 50_000, "Электроника": 30_000},
        "build_time": 10000,
        "upgrade_multiplier": 2.2,
        "resource_production": {"Скафандры": 2},
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 11,
        "description": "Производит снаряжение для космонавтов."
    },

    # ========================
    # УРОВЕНЬ 12 – Ядерное оружие
    # ========================
    "Завод по производству ядерных боеголовок": {
        "cost": {"Доллары": 100_000_000, "Обогащённый уран": 50_000, "Плутоний": 20_000, "Электроника": 100_000},
        "build_time": 60000,
        "upgrade_multiplier": 4.0,
        "resource_production": {"Ядерные боеголовки": 1},
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 12,
        "description": "Производит ядерные боеголовки. Требуется стратегический командный центр."
    },
    "Стратегический командный центр": {
        "cost": {"Доллары": 80_000_000, "Бетон": 500_000, "Электроника": 200_000},
        "build_time": 40000,
        "upgrade_multiplier": 3.0,
        "resource_production": None,
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 12,
        "description": "Координирует ядерный арсенал."
    },
    "Система противоракетной обороны": {
        "cost": {"Доллары": 120_000_000, "Сталь": 300_000, "Электроника": 150_000},
        "build_time": 50000,
        "upgrade_multiplier": 3.5,
        "resource_production": None,
        "max_national": 2,
        "max_per_region": 1,
        "tech_level": 12,
        "description": "Защищает от баллистических ракет."
    },
    "Испытательный полигон": {
        "cost": {"Доллары": 60_000_000, "Бетон": 200_000, "Сталь": 100_000},
        "build_time": 30000,
        "upgrade_multiplier": 2.5,
        "resource_production": None,
        "max_national": 1,
        "max_per_region": 1,
        "tech_level": 12,
        "description": "Позволяет тестировать ядерное оружие (сильно вредит экологии и международному авторитету)."
    },
    "Хранилище ядерных боеголовок": {
        "cost": {"Доллары": 40_000_000, "Бетон": 150_000, "Свинец": 50_000},
        "build_time": 20000,
        "upgrade_multiplier": 2.0,
        "resource_production": None,
        "max_national": 3,
        "max_per_region": 1,
        "tech_level": 12,
        "description": "Безопасно хранит до 3 ядерных боеголовок на уровне 0."
    }
}
