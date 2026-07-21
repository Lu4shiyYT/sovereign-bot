import sqlite3

DB_PATH = "sovereign.db"

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
            info_security REAL DEFAULT 50,
            counter_intelligence REAL DEFAULT 50,
            demographic_growth REAL DEFAULT 0.5
        )
    """)
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
            FOREIGN KEY (attacker_id) REFERENCES countries(id),
            FOREIGN KEY (defender_id) REFERENCES countries(id)
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
    conn.commit()
    conn.close()