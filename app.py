from flask import Flask, render_template, request, g
import sqlite3
from pyarabic import araby
from googletrans import Translator

app = Flask(__name__)

DATABASE = "quran.db"

# Initialize Google Translator
translator = Translator()

# Get a thread-safe database connection
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

# Close the database connection
@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# Thread-safe query function
def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# Generate a phonetic transliteration for Arabic text
def generate_phonetic_transliteration(arabic_word):
    transliteration_map = {
        "ا": "a", "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "h", "خ": "kh", "د": "d",
        "ذ": "dh", "ر": "r", "ز": "z", "س": "s", "ش": "sh", "ص": "s", "ض": "d",
        "ط": "t", "ظ": "z", "ع": "‘", "غ": "gh", "ف": "f", "ق": "q", "ك": "k",
        "ل": "l", "م": "m", "ن": "n", "ه": "h", "و": "w", "ي": "y", "ء": "‘",
        "ة": "h", "ى": "a", "ئ": "y", "ؤ": "w"
    }
    transliteration = ""
    for char in arabic_word:
        transliteration += transliteration_map.get(char, char)
    return transliteration

# Transliteration map for Romanized Arabic to Arabic
def transliterate_to_arabic(word):
    transliteration_map = {
        "3": "ع",      # '3' maps to 'ع' (Ayn)
        "7": "ح",      # '7' maps to 'ح' (Haa)
        "2": "ء",      # '2' maps to 'ء' (Hamza)
        "gh": "غ",     # 'gh' maps to 'غ' (Ghayn)
        "dh": "ذ",     # 'dh' maps to 'ذ' (Thal)
        "S": "ص",      # 'S' maps to 'ص' (Saad)
        "D": "ض",      # 'D' maps to 'ض' (Daad)
        "ee": "ي",     # 'ee' maps to 'ي' (Yaa)
        "ta": "ت",     # 'ta' maps to 'ت' (Ta)
        "tha": "ث",    # 'tha' maps to 'ث' (Tha)
        "ta-marbuta": "ة", # 'ta-marbuta' maps to 'ة' (Taa Marbuta)
        "ah": "ة",     # 'ah' maps to 'ة' (Taa Marbuta - as 'ah' transliteration)
    }
    for key, value in transliteration_map.items():
        word = word.replace(key, value)
    return word

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/root", methods=["GET", "POST"])
def root():
    result = None

    if request.method == "POST":
        word = request.form.get("word")

        # Handle Romanized Arabic input
        word = transliterate_to_arabic(word)

        # Translate English or Romanized Arabic to Arabic
        try:
            translation = translator.translate(word, src="en", dest="ar")
            translated_word = translation.text
            pronunciation = translation.pronunciation or generate_phonetic_transliteration(translated_word)
        except Exception as e:
            return render_template("root.html", result={"error": f"Translation failed: {str(e)}"})

        # Return the result
        result = {
            "input": word,
            "translated_word": translated_word,
            "pronunciation": pronunciation,
        }

    return render_template("root.html", result=result)

@app.route("/search", methods=["GET", "POST"])
def search():
    results = None

    if request.method == "POST":
        search_term = request.form.get("search_term")

        # Transliterate Romanized Arabic to Arabic
        search_term = transliterate_to_arabic(search_term)

        # Query Quran database for matches in Arabic text or translation
        rows = query_db("""
            SELECT verses.id AS verse_number, verses.text AS arabic, verses.translation, 
                   surahs.name AS surah_name, surahs.id AS surah_number
            FROM verses
            JOIN surahs ON verses.surah_id = surahs.id
            WHERE verses.text LIKE ? OR verses.translation LIKE ?
        """, (f"%{search_term}%", f"%{search_term}%"))

        # Add pronunciation for Arabic verses
        results = []
        for row in rows:
            arabic_text = row["arabic"] if row["arabic"] else ""
            pronunciation = generate_phonetic_transliteration(arabic_text)

            results.append({
                "surah_name": row["surah_name"],
                "surah_number": row["surah_number"],
                "verse_number": row["verse_number"],
                "arabic": arabic_text,
                "translation": row["translation"],
                "pronunciation": pronunciation
            })

    return render_template("search.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)