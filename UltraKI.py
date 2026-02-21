from flask import Flask, render_template, request, redirect, session, jsonify, url_for
import sqlite3
import os
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "magischer_schluessel_99")


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, role TEXT, message TEXT)")
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    return redirect(url_for("dashboard")) if "user_id" in session else redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username, password = request.form["username"], generate_password_hash(request.form["password"])
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect(url_for("login"))
        except:
            return "Name vergeben!"
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (request.form["username"],)).fetchone()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user_id"], session["username"] = user["id"], user["username"]
            return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])


@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session: return jsonify({"error": "Login nötig"})
    user_input = request.json.get("message")

    conn = get_db_connection()
    history = conn.execute("SELECT role, message FROM chats WHERE user_id=? ORDER BY id DESC LIMIT 10",
                           (session["user_id"],)).fetchall()

    messages = [{"role": "system", "content": "Du bist die UltraKI Pro V2. Antworte mystisch und weise."}]
    for row in reversed(history): messages.append({"role": row["role"], "content": row["message"]})
    messages.append({"role": "user", "content": user_input})

    ai_reply = client.chat.completions.create(model="gpt-4o-mini", messages=messages).choices[0].message.content

    conn.execute("INSERT INTO chats (user_id, role, message) VALUES (?, 'user', ?)", (session["user_id"], user_input))
    conn.execute("INSERT INTO chats (user_id, role, message) VALUES (?, 'assistant', ?)",
                 (session["user_id"], ai_reply))
    conn.commit()
    return jsonify({"reply": ai_reply})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)