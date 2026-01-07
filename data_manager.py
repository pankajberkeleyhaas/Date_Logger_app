import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_FILE = "date_log.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Entries table
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    partner_name TEXT NOT NULL,
                    social_media TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Check for tags column
    c.execute("PRAGMA table_info(entries)")
    columns = [info[1] for info in c.fetchall()]
    if 'tags' not in columns:
        c.execute("ALTER TABLE entries ADD COLUMN tags TEXT")
    
    # Media table
    c.execute('''CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id INTEGER,
                    file_path TEXT NOT NULL,
                    media_type TEXT,
                    FOREIGN KEY (entry_id) REFERENCES entries (id)
                )''')

    # User Profile Table
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    name TEXT,
                    age INTEGER,
                    gender TEXT,
                    dating_goals TEXT,
                    interests TEXT
                )''')
    
    # Custom Tags Table
    c.execute('''CREATE TABLE IF NOT EXISTS custom_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT UNIQUE
                )''')
    
    # Seed default tags if empty
    c.execute("SELECT count(*) FROM custom_tags")
    if c.fetchone()[0] == 0:
        default_tags = [
            "Good Conversation", "Shared Hobbies", "Great Sense of Humor", 
            "Attractive", "Good Food", "Romantic Connection", 
            "Awkward Silence", "No Chemistry", "Red Flag", "Casual/Friends",
            "Intellectual", "Outdoorsy", "Artsy"
        ]
        c.executemany("INSERT OR IGNORE INTO custom_tags (tag_name) VALUES (?)", [(t,) for t in default_tags])

    conn.commit()
    conn.close()

# --- ENTRY OPERATIONS ---
def add_entry(date, partner_name, social_media, notes, tags, media_files):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    tags_str = ", ".join(tags) if tags else ""
    
    try:
        c.execute('''INSERT INTO entries (date, partner_name, social_media, notes, tags)
                     VALUES (?, ?, ?, ?, ?)''', (date, partner_name, social_media, notes, tags_str))
        entry_id = c.lastrowid
        
        for file_path, media_type in media_files:
            c.execute('''INSERT INTO media (entry_id, file_path, media_type)
                         VALUES (?, ?, ?)''', (entry_id, file_path, media_type))
        
        conn.commit()
        return True, "Entry saved successfully!"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_entries():
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM entries ORDER BY date DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_media_for_entry(entry_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT file_path, media_type FROM media WHERE entry_id = ?", (entry_id,))
    media = c.fetchall()
    conn.close()
    return media

def search_entries(query_text):
    conn = sqlite3.connect(DB_FILE)
    query = f"%{query_text}%"
    sql = '''SELECT * FROM entries 
             WHERE partner_name LIKE ? 
             OR notes LIKE ? 
             OR date LIKE ?
             OR tags LIKE ?'''
    df = pd.read_sql_query(sql, conn, params=(query, query, query, query))
    conn.close()
    return df

def get_all_context_for_ai():
    df = get_all_entries()
    context = ""
    for index, row in df.iterrows():
        context += f"Date: {row['date']}, Partner: {row['partner_name']}, Tags: {row['tags']}, Notes: {row['notes']}\n"
    return context

# --- PROFILE OPERATIONS ---
def get_user_profile():
    conn = sqlite3.connect(DB_FILE)
    # Using row_factory to get dictionary-like access if needed, but pandas is easier
    df = pd.read_sql_query("SELECT * FROM user_profile WHERE id=1", conn)
    conn.close()
    if not df.empty:
        return df.iloc[0].to_dict()
    return {}

def update_user_profile(name, age, gender, goals, interests):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Upsert logic for SQLite
    c.execute('''INSERT INTO user_profile (id, name, age, gender, dating_goals, interests)
                 VALUES (1, ?, ?, ?, ?, ?)
                 ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name,
                 age=excluded.age,
                 gender=excluded.gender,
                 dating_goals=excluded.dating_goals,
                 interests=excluded.interests
              ''', (name, age, gender, goals, interests))
    conn.commit()
    conn.close()

# --- TAG OPERATIONS ---
def get_custom_tags():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT tag_name FROM custom_tags ORDER BY tag_name ASC")
    tags = [row[0] for row in c.fetchall()]
    conn.close()
    return tags

def add_custom_tag(tag_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO custom_tags (tag_name) VALUES (?)", (tag_name,))
        conn.commit()
        return True, "Tag added!"
    except sqlite3.IntegrityError:
        return False, "Tag already exists."
    finally:
        conn.close()

def delete_custom_tag(tag_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM custom_tags WHERE tag_name = ?", (tag_name,))
    conn.commit()
    conn.close()
