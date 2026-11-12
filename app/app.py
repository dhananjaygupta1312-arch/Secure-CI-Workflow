import os
import sqlite3
import yaml
from flask import Flask, request

app = Flask(__name__)
API_KEY = os.environ.get("API_KEY")          # FIX: from environment

@app.route("/user")
def user():
    name = request.args.get("name", "")
    conn = sqlite3.connect("db.sqlite")
    rows = conn.execute(
        "SELECT * FROM users WHERE name = ?", (name,)   # FIX: parameterized
    ).fetchall()
    return str(rows)

@app.route("/config", methods=["POST"])
def config():
    return str(yaml.safe_load(request.data))            # FIX: safe_load

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(debug=False)                                # FIX: no debug
