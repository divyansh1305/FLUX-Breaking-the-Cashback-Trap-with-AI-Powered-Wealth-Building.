import sqlite3
import os

DATABASE_NAME = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print("Initializing database...")
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            otp TEXT,
            otp_expiry DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add missing columns to users for Gamification/Economy
    new_columns = [
        ("income", "REAL DEFAULT 0"),
        ("streak_days", "INTEGER DEFAULT 0"),
        ("points", "INTEGER DEFAULT 0"),
        ("level", "INTEGER DEFAULT 1"),
        ("score", "INTEGER DEFAULT 0"),
        ("last_streak_date", "TEXT"),
        ("coins", "INTEGER DEFAULT 0"),
        ("is_pro", "BOOLEAN DEFAULT 0"),
        ("pro_expiry", "TEXT")
    ]
    for col_name, col_type in new_columns:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass 
    
    # Streaks Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            streak_type TEXT DEFAULT 'login',
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_checkin TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Badges Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            condition_type TEXT,
            condition_value INTEGER,
            coin_reward INTEGER DEFAULT 0,
            rarity TEXT DEFAULT 'common'
        )
    ''')

    # UserBadge Mapping
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_badges (
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL,
            unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, badge_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(badge_id) REFERENCES badges(id)
        )
    ''')

    # Coin Ledger
    c.execute('''
        CREATE TABLE IF NOT EXISTS coin_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            amount INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Game Sessions
    c.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            coins_earned INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Reward Pool
    c.execute('''
        CREATE TABLE IF NOT EXISTS reward_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reward_type TEXT NOT NULL,
            probability REAL NOT NULL,
            value INTEGER DEFAULT 0
        )
    ''')

    # Phase 1: Create existing tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            source TEXT DEFAULT 'cashback_conversion',
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            target_amount REAL NOT NULL,
            saved_amount REAL DEFAULT 0.0,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # We also need pure 'income' table
    c.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            source TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Phase 2: Groww / Shoonya Trading Orders
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL DEFAULT 0.0,
            side TEXT NOT NULL,
            order_id TEXT NOT NULL,
            status TEXT DEFAULT 'Executed',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Seed Badges and Reward Pool if empty
    c.execute("SELECT COUNT(*) FROM badges")
    if c.fetchone()[0] == 0:
        badges = [
            ('Wealth Starter', 'streak', 'login', 1, 10, 'common'),
            ('Consistency King', 'streak', 'login', 7, 50, 'rare'),
            ('Discipline Master', 'streak', 'finance', 7, 100, 'epic'),
            ('Game Addict', 'engagement', 'game_played', 10, 30, 'common'),
            ('Saver Pro', 'growth', 'savings', 5000, 200, 'epic')
        ]
        c.executemany("INSERT INTO badges (name, type, condition_type, condition_value, coin_reward, rarity) VALUES (?, ?, ?, ?, ?, ?)", badges)

    c.execute("SELECT COUNT(*) FROM reward_pool")
    if c.fetchone()[0] == 0:
        rewards = [
            ('coins', 0.4, 5),
            ('coins', 0.3, 20),
            ('coins', 0.2, 50),
            ('coins', 0.08, 100),
            ('jackpot', 0.02, 500)
        ]
        c.executemany("INSERT INTO reward_pool (reward_type, probability, value) VALUES (?, ?, ?)", rewards)

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
