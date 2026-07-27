import sqlite3
import asyncio
import datetime

DB_PATH = "sovereign.db"

def _fetch_all(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def _fetch_one(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row

def _execute(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()

def _execute_many(query, params_list):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executemany(query, params_list)
    conn.commit()
    conn.close()

async def async_fetch_all(query, params=()):
    return await asyncio.to_thread(_fetch_all, query, params)

async def async_fetch_one(query, params=()):
    return await asyncio.to_thread(_fetch_one, query, params)

async def async_execute(query, params=()):
    await asyncio.to_thread(_execute, query, params)

async def async_execute_many(query, params_list):
    await asyncio.to_thread(_execute_many, query, params_list)

async def async_get_game_date():
    row = await async_fetch_one("SELECT day, month, year FROM game_date WHERE id=1")
    if row:
        return datetime.date(row['year'], row['month'], row['day'])
    return datetime.date(2000, 1, 1)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            owner_id INTEGER,
            type TEXT,
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
            info_security REAL DEFAULT 10,
            counter_intelligence REAL DEFAULT 10,
            demographic_growth REAL DEFAULT 0.5,
            last_daily REAL DEFAULT 0,
            ruler_name TEXT DEFAULT '',
            display_name TEXT DEFAULT '',
            religion TEXT DEFAULT '',
            ideology TEXT DEFAULT '',
            government_form TEXT DEFAULT '',
            mobilization INTEGER DEFAULT 0,
            aggression_score REAL DEFAULT 50,
            population INTEGER DEFAULT 0,
            army_count INTEGER DEFAULT 0
        )
    """)
    for col, col_def in [
        ('army_count', 'INTEGER DEFAULT 0'),
        ('religion', 'TEXT DEFAULT ""'),
        ('government_form', 'TEXT DEFAULT ""'),
        ('ideology', 'TEXT DEFAULT ""'),
        ('bot_strength', 'INTEGER DEFAULT 1'),
        ('budget', 'REAL DEFAULT 0')
    ]:
        try:
            cur.execute(f"ALTER TABLE countries ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_date (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            year INTEGER DEFAULT 2000,
            month INTEGER DEFAULT 1,
            day INTEGER DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS war_battles (
            war_id INTEGER PRIMARY KEY,
            last_battle_time REAL,
            FOREIGN KEY (war_id) REFERENCES wars(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS provinces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country_id INTEGER,
            terrain_type TEXT DEFAULT 'plain',
            climate_severity INTEGER DEFAULT 1,
            economic_value REAL DEFAULT 1.0,
            fortification_level INTEGER DEFAULT 0,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER,
            building_type TEXT NOT NULL,
            level INTEGER DEFAULT 0,
            build_end_time REAL,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            country_id INTEGER,
            resource_name TEXT,
            amount REAL DEFAULT 0,
            PRIMARY KEY (country_id, resource_name),
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS technologies (
            country_id INTEGER,
            branch TEXT,
            level INTEGER DEFAULT 0,
            PRIMARY KEY (country_id, branch),
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attacker_id INTEGER,
            defender_id INTEGER,
            status TEXT DEFAULT 'active',
            start_time REAL,
            reason TEXT DEFAULT '',
            description TEXT DEFAULT '',
            FOREIGN KEY (attacker_id) REFERENCES countries(id),
            FOREIGN KEY (defender_id) REFERENCES countries(id)
        )
    """)
    # Добавляем колонки reason и description на случай старых баз
    for col, col_def in [('reason', 'TEXT DEFAULT ""'), ('description', 'TEXT DEFAULT ""')]:
        try:
            cur.execute(f"ALTER TABLE wars ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    for col, col_def in [('start_game_day', 'INTEGER DEFAULT 1'), ('start_game_month', 'INTEGER DEFAULT 1'), ('start_game_year', 'INTEGER DEFAULT 2000')]:
        try:
            cur.execute(f"ALTER TABLE wars ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_country INTEGER,
            to_country INTEGER,
            type TEXT,
            subtype TEXT DEFAULT '',
            accepted INTEGER DEFAULT 0,
            FOREIGN KEY (from_country) REFERENCES countries(id),
            FOREIGN KEY (to_country) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sanctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_country INTEGER,
            to_country INTEGER,
            sanction_type TEXT DEFAULT '',
            description TEXT DEFAULT '',
            affected_param TEXT DEFAULT '',
            effect_amount REAL DEFAULT 0,
            FOREIGN KEY (from_country) REFERENCES countries(id),
            FOREIGN KEY (to_country) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alliances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            leader_id INTEGER,
            channel_id INTEGER,
            FOREIGN KEY (leader_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alliance_members (
            alliance_id INTEGER,
            country_id INTEGER,
            PRIMARY KEY (alliance_id, country_id),
            FOREIGN KEY (alliance_id) REFERENCES alliances(id),
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS puppets (
            master_id INTEGER,
            puppet_id INTEGER,
            PRIMARY KEY (master_id, puppet_id),
            FOREIGN KEY (master_id) REFERENCES countries(id),
            FOREIGN KEY (puppet_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS war_moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            war_id INTEGER NOT NULL,
            country_id INTEGER NOT NULL,
            move_type TEXT NOT NULL,
            details TEXT DEFAULT '',
            created_at REAL NOT NULL,
            FOREIGN KEY (war_id) REFERENCES wars(id),
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS military_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER NOT NULL,
            asset_type TEXT NOT NULL,
            asset_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS war_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            war_id INTEGER NOT NULL,
            report_text TEXT NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY (war_id) REFERENCES wars(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS frontlines (
            war_id INTEGER NOT NULL,
            province_id INTEGER NOT NULL,
            controlled_by_id INTEGER NOT NULL,
            last_change REAL,
            FOREIGN KEY (war_id) REFERENCES wars(id),
            FOREIGN KEY (province_id) REFERENCES provinces(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            rank TEXT DEFAULT 'Лейтенант',
            attack_skill REAL DEFAULT 0.5,
            defense_skill REAL DEFAULT 0.5,
            logistic_skill REAL DEFAULT 0.5,
            experience REAL DEFAULT 0,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            province_id INTEGER NOT NULL,
            season TEXT DEFAULT 'summer',
            temperature REAL DEFAULT 20.0,
            precipitation REAL DEFAULT 0,
            FOREIGN KEY (province_id) REFERENCES provinces(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS supply_stocks (
            country_id INTEGER NOT NULL,
            resource_name TEXT NOT NULL,
            amount REAL DEFAULT 0,
            PRIMARY KEY (country_id, resource_name),
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_wars_attacker ON wars(attacker_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_wars_defender ON wars(defender_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pacts_from ON pacts(from_country)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_pacts_to ON pacts(to_country)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sanctions_to ON sanctions(to_country)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alliance_members_country ON alliance_members(country_id)")

    conn.commit()
    conn.close()
