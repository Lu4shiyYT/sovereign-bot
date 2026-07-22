import sqlite3
import asyncio

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

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # таблицы (создаются, если нет)
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
            aggression_score REAL DEFAULT 50
        )
    """)
    # Добавляем колонки, если их нет (старые базы)
    new_columns = {
        'ruler_name': 'TEXT DEFAULT ""',
        'display_name': 'TEXT DEFAULT ""',
        'religion': 'TEXT DEFAULT ""',
        'ideology': 'TEXT DEFAULT ""',
        'government_form': 'TEXT DEFAULT ""',
        'mobilization': 'INTEGER DEFAULT 0',
        'aggression_score': 'REAL DEFAULT 50',
        'last_daily': 'REAL DEFAULT 0'
    }
    for col, col_def in new_columns.items():
        try:
            cur.execute(f"ALTER TABLE countries ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS provinces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country_id INTEGER,
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
            FOREIGN KEY (attacker_id) REFERENCES countries(id),
            FOREIGN KEY (defender_id) REFERENCES countries(id)
        )
    """)
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
    # Добавляем колонку subtype для старых версий
    try:
        cur.execute("ALTER TABLE pacts ADD COLUMN subtype TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sanctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_country INTEGER,
            to_country INTEGER,
            description TEXT,
            sanction_type TEXT DEFAULT '',
            affected_param TEXT DEFAULT '',
            effect_amount REAL DEFAULT 0,
            FOREIGN KEY (from_country) REFERENCES countries(id),
            FOREIGN KEY (to_country) REFERENCES countries(id)
        )
    """)
    # Добавляем новые колонки для санкций
    try:
        cur.execute("ALTER TABLE sanctions ADD COLUMN sanction_type TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE sanctions ADD COLUMN affected_param TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE sanctions ADD COLUMN effect_amount REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

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
    conn.commit()
    conn.close()
