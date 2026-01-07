import sqlite3
import pandas as pd
import os
from datetime import datetime

DB_FILE = "date_log.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Entries table - ensure tags column exists
    c.execute('''CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    partner_name TEXT NOT NULL,
                    social_media TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Check if tags column exists, if not add it
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

    conn.commit()
    conn.close()

def add_entry(date, partner_name, social_media, notes, tags, media_files):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Convert tags list to comma-separated string
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
    # Search in tags as well
    sql = '''SELECT * FROM entries 
             WHERE partner_name LIKE ? 
             OR notes LIKE ? 
             OR date LIKE ?
             OR tags LIKE ?'''
    df = pd.read_sql_query(sql, conn, params=(query, query, query, query))
    conn.close()
    return df

def get_all_context_for_ai():
    """Returns all entries formatted as a string for AI context."""
    df = get_all_entries()
    context = ""
    for index, row in df.iterrows():
        context += f"Date: {row['date']}, Partner: {row['partner_name']}, Tags: {row['tags']}, Notes: {row['notes']}\n"
    return context
