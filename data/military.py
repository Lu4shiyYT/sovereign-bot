# data/military.py
# Полный справочник военной техники и оружия с характеристиками

# Техника: (название, категория, сила, стоимость, топливо_на_ход, экипаж)
MILITARY_EQUIPMENT = {
    "сухопутные": [
        {"name": "танки", "power": 5.0, "cost": 5000, "fuel_per_tick": 10, "crew": 4},
        {"name": "БМП", "power": 3.5, "cost": 3000, "fuel_per_tick": 6, "crew": 3},
        {"name": "БТР", "power": 2.5, "cost": 1500, "fuel_per_tick": 4, "crew": 2},
        {"name": "бронеавтомобили", "power": 1.5, "cost": 800, "fuel_per_tick": 3, "crew": 3},
        {"name": "самоходные установки", "power": 4.0, "cost": 4000, "fuel_per_tick": 8, "crew": 5},
        {"name": "РСЗО", "power": 4.5, "cost": 6000, "fuel_per_tick": 12, "crew": 6},
        {"name": "наземные пусковые установки баллистических/крылатых ракет", "power": 8.0, "cost": 20000, "fuel_per_tick": 20, "crew": 10},
        {"name": "гаубицы", "power": 3.0, "cost": 2000, "fuel_per_tick": 2, "crew": 5},
        {"name": "пушки", "power": 2.0, "cost": 1000, "fuel_per_tick": 1, "crew": 4},
        {"name": "минометы", "power": 1.5, "cost": 500, "fuel_per_tick": 0, "crew": 3},
        {"name": "противотанковые пушки", "power": 2.5, "cost": 1200, "fuel_per_tick": 0, "crew": 3},
        {"name": "зенитные ракетные комплексы ПЗРК", "power": 2.0, "cost": 800, "fuel_per_tick": 0, "crew": 1}
    ],
    "воздушные": [
        {"name": "истребители", "power": 6.0, "cost": 15000, "fuel_per_tick": 30, "crew": 1},
        {"name": "фронтовые бомбардировщики", "power": 7.0, "cost": 20000, "fuel_per_tick": 40, "crew": 2},
        {"name": "штурмовики", "power": 5.0, "cost": 12000, "fuel_per_tick": 25, "crew": 1},
        {"name": "стратегические бомбардировщики", "power": 10.0, "cost": 50000, "fuel_per_tick": 80, "crew": 5},
        {"name": "самолёты дальнего радиолокационного обнаружения и управления", "power": 1.0, "cost": 30000, "fuel_per_tick": 35, "crew": 10},
        {"name": "самолёты радиоэлектронной борьбы и разведки", "power": 0.5, "cost": 25000, "fuel_per_tick": 30, "crew": 8},
        {"name": "военно-транспортные самолёты", "power": 0.2, "cost": 10000, "fuel_per_tick": 50, "crew": 3},
        {"name": "противолодочные самолёты", "power": 4.0, "cost": 18000, "fuel_per_tick": 35, "crew": 4},
        {"name": "ударные вертолеты", "power": 4.5, "cost": 8000, "fuel_per_tick": 15, "crew": 2},
        {"name": "многоцелевые вертолеты", "power": 2.0, "cost": 5000, "fuel_per_tick": 12, "crew": 2},
        {"name": "транспортные вертолеты", "power": 0.3, "cost": 4000, "fuel_per_tick": 18, "crew": 3}
    ],
    "морские": [
        {"name": "авианосцы", "power": 20.0, "cost": 200000, "fuel_per_tick": 200, "crew": 500},
        {"name": "крейсера", "power": 10.0, "cost": 80000, "fuel_per_tick": 100, "crew": 300},
        {"name": "эсминцы", "power": 6.0, "cost": 50000, "fuel_per_tick": 70, "crew": 200},
        {"name": "фрегаты", "power": 4.0, "cost": 30000, "fuel_per_tick": 50, "crew": 150},
        {"name": "корветы", "power": 3.0, "cost": 20000, "fuel_per_tick": 40, "crew": 80},
        {"name": "атомные подводные лодки стратегического назначения", "power": 15.0, "cost": 150000, "fuel_per_tick": 50, "crew": 120},
        {"name": "атомные подводные лодки", "power": 8.0, "cost": 100000, "fuel_per_tick": 30, "crew": 100},
        {"name": "патрульные катера", "power": 1.5, "cost": 5000, "fuel_per_tick": 10, "crew": 10},
        {"name": "десантные корабли", "power": 2.0, "cost": 25000, "fuel_per_tick": 60, "crew": 50}
    ],
    "беспилотные аппараты": [
        {"name": "БПЛА", "power": 0.8, "cost": 200, "fuel_per_tick": 1, "crew": 0}
    ],
    "разведка": [
        {"name": "радиолокационные станции", "power": 0.1, "cost": 5000, "fuel_per_tick": 5, "crew": 10},
        {"name": "оптико-электронные комплексы разведки", "power": 0.2, "cost": 3000, "fuel_per_tick": 2, "crew": 5},
        {"name": "звукометрические и сейсмические датчики", "power": 0.05, "cost": 500, "fuel_per_tick": 0, "crew": 1},
        {"name": "комплексы артиллерийской разведки", "power": 0.3, "cost": 2000, "fuel_per_tick": 1, "crew": 3}
    ]
}

# Оружие: (название, категория, сила, стоимость, тип боеприпасов, расход патронов на ход)
WEAPONS = {
    "стрелковое и лёгкое": [
        {"name": "пистолеты", "power": 0.1, "cost": 50, "ammo_type": "патроны 9мм", "ammo_per_tick": 2},
        {"name": "пистолеты-пулеметы", "power": 0.3, "cost": 150, "ammo_type": "патроны 9мм", "ammo_per_tick": 5},
        {"name": "штурмовые винтовки", "power": 0.5, "cost": 300, "ammo_type": "патроны 5.56мм", "ammo_per_tick": 3},
        {"name": "пулеметы", "power": 0.8, "cost": 800, "ammo_type": "патроны 7.62мм", "ammo_per_tick": 10},
        {"name": "снайперские винтовки", "power": 0.6, "cost": 600, "ammo_type": "патроны 7.62мм", "ammo_per_tick": 1},
        {"name": "гранатометы", "power": 1.0, "cost": 400, "ammo_type": "гранаты", "ammo_per_tick": 1},
        {"name": "ручные огнеметы", "power": 1.2, "cost": 500, "ammo_type": "огнесмесь", "ammo_per_tick": 2},
        {"name": "ручные осколочные гранаты", "power": 0.7, "cost": 30, "ammo_type": "гранаты", "ammo_per_tick": 1},
        {"name": "холодное оружие", "power": 0.05, "cost": 10, "ammo_type": "нет", "ammo_per_tick": 0},
        {"name": "малокалиберная ствольная артиллерия", "power": 1.5, "cost": 1000, "ammo_type": "снаряды", "ammo_per_tick": 5}
    ],
    "ракеты": [
        {"name": "ракета класса 'Земля-Земля'", "power": 4.0, "cost": 3000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "ракета класса 'Земля-Воздух'", "power": 3.0, "cost": 2000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "ракета класса 'Воздух-Земля'", "power": 4.5, "cost": 4000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "ракета класса 'Воздух-Воздух'", "power": 3.5, "cost": 3500, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "межконтинентальные баллистические ракеты", "power": 50.0, "cost": 100000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "тактические баллистические ракеты", "power": 20.0, "cost": 50000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "крылатые ракеты", "power": 10.0, "cost": 15000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "зенитные управляемые ракеты", "power": 3.0, "cost": 5000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "противотанковые ракеты", "power": 2.5, "cost": 2000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "противокорабельные ракеты", "power": 8.0, "cost": 12000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "противолодочные ракеты", "power": 6.0, "cost": 10000, "ammo_type": "нет", "ammo_per_tick": 1},
        {"name": "химическое оружие", "power": 15.0, "cost": 50000, "ammo_type": "химикаты", "ammo_per_tick": 1},
        {"name": "атомное оружие", "power": 100.0, "cost": 500000, "ammo_type": "ядерные боеголовки", "ammo_per_tick": 1}
    ]
}
