import os
import sqlite3
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY must be configured")
app.secret_key = secret_key

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, role TEXT, message TEXT)")


init_db()


@app.route("/")
def index():
    return redirect(url_for("dashboard")) if "user_id" in session else redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return "Benutzername und Passwort erforderlich.", 400
        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, generate_password_hash(password)))
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Benutzername existiert bereits.", 409
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
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
        return jsonify({"error": "Login nötig"}), 401
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()
    if not user_input:
        return jsonify({"error": "message is required"}), 400

    with get_db_connection() as conn:
        history = conn.execute("SELECT role, message FROM chats WHERE user_id=? ORDER BY id DESC LIMIT 10", (session["user_id"],)).fetchall()

    messages = [{"role": "system", "content": "Du bist UltraKI Pro V2, ein hilfreicher Sci-Fi-Assistent."}]
    messages.extend({"role": row["role"], "content": row["message"]} for row in reversed(history))
    messages.append({"role": "user", "content": user_input})

    if client is None:
        reply = "OpenAI ist nicht konfiguriert. Setze OPENAI_API_KEY in der Umgebung."
    else:
        try:
            response = client.chat.completions.create(model=MODEL, messages=messages)
            reply = response.choices[0].message.content or "Keine Antwort erhalten."
        except Exception:
            reply = "Die KI-Schnittstelle ist momentan nicht erreichbar."

    with get_db_connection() as conn:
        conn.execute("INSERT INTO chats (user_id, role, message) VALUES (?, 'user', ?)", (session["user_id"], user_input))
        conn.execute("INSERT INTO chats (user_id, role, message) VALUES (?, 'assistant', ?)", (session["user_id"], reply))
    return jsonify({"reply": reply})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
