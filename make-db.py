import json
import sqlite3

# Load the JSON file
with open("quran_en.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Connect to SQLite3 database (or create it)
conn = sqlite3.connect("quran.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS surahs (
    id INTEGER PRIMARY KEY,
    name TEXT,
    transliteration TEXT,
    translation TEXT,
    type TEXT,
    total_verses INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS verses (
    id INTEGER,
    surah_id INTEGER,
    text TEXT,
    translation TEXT,
    PRIMARY KEY (id, surah_id),
    FOREIGN KEY (surah_id) REFERENCES surahs (id)
)
""")

# Create the roots table
cursor.execute("""
CREATE TABLE IF NOT EXISTS roots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT,
    root TEXT,
    definition TEXT
)
""")

# Insert data into surahs and verses tables
for surah in data:
    # Insert Surah details
    cursor.execute("""
    INSERT OR IGNORE INTO surahs (id, name, transliteration, translation, type, total_verses)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (surah["id"], surah["name"], surah["transliteration"], surah["translation"], surah["type"], surah["total_verses"]))
    
    # Insert verses for the Surah
    for verse in surah["verses"]:
        cursor.execute("""
        INSERT OR IGNORE INTO verses (id, surah_id, text, translation)
        VALUES (?, ?, ?, ?)
        """, (verse["id"], surah["id"], verse["text"], verse["translation"]))

# Insert sample data into the roots table
roots_data = [
    {"word": "المكتبة", "root": "كتب", "definition": "To write"},
    {"word": "العلم", "root": "علم", "definition": "Knowledge or to know"},
    {"word": "القراءة", "root": "قرأ", "definition": "To read"},
    {"word": "الصلاة", "root": "صل", "definition": "To pray or connection"},
]

for root_entry in roots_data:
    cursor.execute("""
    INSERT OR IGNORE INTO roots (word, root, definition)
    VALUES (?, ?, ?)
    """, (root_entry["word"], root_entry["root"], root_entry["definition"]))

# Commit and close the database
conn.commit()
conn.close()

print("Data has been successfully imported into the SQLite3 database.")