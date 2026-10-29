import sqlite3
import yaml
from flask import Flask, request

app = Flask(__name__)
API_KEY = "NO_TRANING_KEY"   # VULNERABILITY: hardcoded secret

@app.route("/user")
def user():
    name = request.args.get("name", "")
    conn = sqlite3.connect("db.sqlite")
    # VULNERABILITY: SQL injection (string formatting in query)
    query = f"SELECT * FROM users WHERE name = '{name}'"
    return str(conn.execute(query).fetchall())

@app.route("/config", methods=["POST"])
def config():
    # VULNERABILITY: unsafe deserialization
    return str(yaml.load(request.data))

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(debug=True)   # VULNERABILITY: debug mode (Semgrep flags this)