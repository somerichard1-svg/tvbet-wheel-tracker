
from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB = "wheel.db"

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def get_results(limit=500):
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        return con.execute(
            "SELECT * FROM results ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()

@app.route("/")
def home():
    results = get_results()
    numbers = [r["number"] for r in results]
    total = len(numbers)
    even = sum(n % 2 == 0 for n in numbers)
    odd = total - even

    counts = {str(n): numbers.count(n) for n in range(37)}

    rows = "".join(
        f"<tr><td>{r['number']}</td><td>{r['created_at']}</td></tr>"
        for r in results
    )

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta charset="utf-8">
      <title>Wheel Tracker</title>
      <style>
        body {{ background:#10141e; color:#eee; font-family:Arial;
               margin:0; padding:18px; }}
        .card {{ background:#20283a; padding:16px; border-radius:14px;
                margin-bottom:12px; }}
        h1 {{ color:#7ea7ff; }}
        input,button {{ padding:12px; border-radius:8px; border:0;
                      font-size:16px; }}
        button {{ background:#4779ef; color:white; }}
        table {{ width:100%; border-collapse:collapse; }}
        td,th {{ padding:10px; border-bottom:1px solid #39445a;
                text-align:left; }}
        .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
      </style>
    </head>
    <body>
      <h1>🎡 Wheel Tracker</h1>
      <div class="card">
        <h2>Ajouter un résultat</h2>
        <form action="/add" method="post">
          <input type="number" name="number" min="0" max="36"
                 placeholder="Numéro 0–36" required>
          <button type="submit">Enregistrer</button>
        </form>
      </div>
      <div class="grid">
        <div class="card"><b>Total</b><h2>{total}</h2></div>
        <div class="card"><b>Pairs</b><h2>{even}</h2></div>
        <div class="card"><b>Impairs</b><h2>{odd}</h2></div>
        <div class="card"><b>Numéros distincts</b><h2>{len(set(numbers))}</h2></div>
      </div>
      <div class="card">
        <h2>Fréquences (0–36)</h2>
        <p>{counts}</p>
      </div>
      <div class="card">
        <h2>Historique récent</h2>
        <table><tr><th>Numéro</th><th>Date</th></tr>{rows}</table>
      </div>
      <p>Tracker de résultats — statistiques descriptives, pas prédictives.</p>
    </body>
    </html>
    """

@app.route("/add", methods=["POST"])
def add():
    try:
        n = int(request.form.get("number", -1))
        if n < 0 or n > 36:
            return "Numéro invalide (0–36)", 400
        with sqlite3.connect(DB) as con:
            con.execute(
                "INSERT INTO results (number, created_at) VALUES (?, ?)",
                (n, datetime.utcnow().isoformat())
            )
        return '<meta http-equiv="refresh" content="0;url=/">'
    except Exception as e:
        return str(e), 500

@app.route("/api/result", methods=["POST"])
def api_result():
    data = request.get_json(silent=True) or {}
    try:
        n = int(data.get("number", -1))
        if n < 0 or n > 36:
            return jsonify(error="Numéro invalide"), 400
        with sqlite3.connect(DB) as con:
            con.execute(
                "INSERT INTO results (number, created_at) VALUES (?, ?)",
                (n, datetime.utcnow().isoformat())
            )
        return jsonify(status="ok", number=n)
    except Exception:
        return jsonify(error="Données invalides"), 400

@app.route("/api/results")
def api_results():
    return jsonify([
        dict(r) for r in get_results()
    ])

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
