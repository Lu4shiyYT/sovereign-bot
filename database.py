cur.execute("""
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        owner_id INTEGER,
        type TEXT,
        ruler_name TEXT DEFAULT 'Правитель',
        economic_stability REAL DEFAULT 50,
        health REAL DEFAULT 50,
        combat_capability REAL DEFAULT 50,
        industry_level REAL DEFAULT 50,
        science_progress REAL DEFAULT 50,
        citizen_mood REAL DEFAULT 50,
        crime_rate REAL DEFAULT 50,
        ecology REAL DEFAULT 50,
        international_prestige REAL DEFAULT 50,
        government_efficiency REAL DEFAULT 50,
        info_security REAL DEFAULT 50,
        counter_intelligence REAL DEFAULT 50,
        demographic_growth REAL DEFAULT 0.5,
        last_daily REAL DEFAULT 0
    )
""")
# Попытка добавить колонку ruler_name, если её ещё нет (для старых баз)
try:
    cur.execute("ALTER TABLE countries ADD COLUMN ruler_name TEXT DEFAULT 'Правитель'")
except sqlite3.OperationalError:
    pass
