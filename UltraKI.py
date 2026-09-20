import os
import sqlite3
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")
WEB = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"
MAX_INPUT = max(1000, min(int(os.getenv("MAX_INPUT_CHARS", "12000")), 30000))

SYSTEM = """Du bist UltraKI Pro V2, ein hilfreicher Forschungs-, Coding- und Projektassistent.
Antworte in der Sprache des Nutzers. Arbeite strukturiert und konkret.
Trenne Fakten, Annahmen und Unsicherheit. Nutze Web-Recherche für aktuelle Informationen, wenn aktiviert.
Erfinde keine Quellen, Daten oder ausgeführten Aktionen. Bei Code achte auf Sicherheit, Wartbarkeit und Tests."""

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, role TEXT, message TEXT)")
        conn.commit()

init_db()

@app.route("/")
def index():
    return redirect(url_for("dashboard")) if "user_id" in session else redirect(url_for("login"))

@app.route("/health")
@app.route("/api/health")
def health():
    return jsonify({"status":"ok","project":"UltraKI.AI","model":MODEL,"ai_enabled":AI_ENABLED,"web_search":WEB,"openai_configured":bool(client)})

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return "Benutzername und Passwort erforderlich.", 400
        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, generate_password_hash(password)))
                conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Benutzername existiert bereits.", 409
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        return "Ungültige Anmeldedaten.", 401
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"error":"Login nötig"}), 401

    data = request.get_json(silent=True) or {}
    user_input = str(data.get("message") or "").strip()
    if not user_input:
        return jsonify({"error":"message is required"}), 400
    if len(user_input) > MAX_INPUT:
        return jsonify({"error":f"message is too long (max {MAX_INPUT} characters)"}), 413

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT role, message FROM chats WHERE user_id=? ORDER BY id DESC LIMIT 12",
            (session["user_id"],)
        ).fetchall()

    history = [{"role": row["role"], "content": row["message"]} for row in reversed(rows)]
    if not AI_ENABLED:
        reply = "Die KI ist derzeit deaktiviert."
    elif client is None:
        reply = "OPENAI_API_KEY ist in Render nicht gesetzt."
    else:
        try:
            kwargs = {
                "model": MODEL,
                "store": False,
                "input": [{"role":"system","content":SYSTEM}, *history, {"role":"user","content":user_input}],
            }
            if WEB:
                kwargs["tools"] = [{"type":"web_search","search_context_size":"medium"}]
                kwargs["tool_choice"] = "auto"
            response = client.responses.create(**kwargs)
            reply = response.output_text or "Keine Antwort erhalten."
        except Exception:
            app.logger.exception("AI API failure")
            reply = "Die KI-Schnittstelle ist momentan nicht erreichbar. Prüfe API-Key, Guthaben und Render-Logs."

    with get_db_connection() as conn:
        conn.execute("INSERT INTO chats (user_id, role, message) VALUES (?, 'user', ?)", (session["user_id"], user_input))
        conn.execute("INSERT INTO chats (user_id, role, message) VALUES (?, 'assistant', ?)", (session["user_id"], reply))
        conn.commit()

    return jsonify({"ok":True,"reply":reply,"response":reply,"model":MODEL,"web_search":WEB})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","10000")), debug=False)
