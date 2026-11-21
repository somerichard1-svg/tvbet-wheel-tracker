
from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB = "wheel.db"

RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16, 18,
    19, 21, 23, 25, 27, 30, 32, 34, 36
}

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

def format_date(value):
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return value

@app.route("/")
def home():
    results = get_results()
    numbers = [r["number"] for r in results]
    total = len(numbers)
    even = sum(n % 2 == 0 for n in numbers)
    odd = total - even

    counts = {n: numbers.count(n) for n in range(37)}
    max_count = max(counts.values()) if total else 0

    frequency_cards = ""
    for n in range(37):
        count = counts[n]
        color = (
            "green" if n == 0 else
            "red" if n in RED_NUMBERS else "black"
        )
        width = (count / max_count * 100) if max_count else 0

        frequency_cards += f"""
        <div class="number-card {color}">
            <div class="ball">{n}</div>
            <div class="count">{count} fois</div>
            <div class="bar-bg">
                <div class="bar" style="width:{width}%"></div>
            </div>
        </div>
        """

    history_rows = ""
    for r in results:
        history_rows += f"""
        <tr>
            <td><span class="mini-ball">{r['number']}</span></td>
            <td>{format_date(r['created_at'])}</td>
        </tr>
        """

    ranking = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    top = ranking[:5]
    top_html = "".join(
        f'<span class="rank">{n} <b>{c}</b></span>'
        for n, c in top
    )

    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Wheel Tracker</title>
      <style>
        * {{ box-sizing:border-box; }}
        body {{
          background:#10141e; color:#f2f4f8;
          font-family:Arial,sans-serif; margin:0;padding:15px;
        }}
        h1 {{color:#7ea7ff;text-align:center;}}
        h2 {{font-size:21px;}}
        .card {{
          background:#20283a;padding:18px;border-radius:17px;
          margin-bottom:15px;
        }}
        input,button {{
          padding:14px;border-radius:10px;border:0;
          font-size:17px;margin:4px 0;
        }}
        input {{width:130px;}}
        button {{background:#4779ef;color:white;font-weight:bold;}}
        .grid {{
          display:grid;grid-template-columns:1fr 1fr;gap:12px;
        }}
        .stat {{min-height:110px;}}
        .stat h2 {{margin:0 0 15px;}}
        .value {{font-size:30px;font-weight:bold;}}
        .freq-grid {{
          display:grid;grid-template-columns:repeat(4,1fr);gap:8px;
        }}
        .number-card {{
          background:#151c2c;border-radius:12px;padding:9px;
          text-align:center;min-width:0;
        }}
        .ball {{
          width:35px;height:35px;border-radius:50%;
          display:flex;align-items:center;justify-content:center;
          color:white;font-weight:bold;margin:auto auto 5px;
        }}
        .red .ball {{background:#d43c45;}}
        .black .ball {{background:#111; border:1px solid #666;}}
        .green .ball {{background:#168b55;}}
        .count {{font-size:13px;margin-bottom:5px;}}
        .bar-bg {{height:5px;background:#30394b;border-radius:5px;}}
        .bar {{height:5px;background:#5c91ff;border-radius:5px;}}
        .rank {{
          display:inline-block;background:#151c2c;
          padding:9px;border-radius:9px;margin:3px;
        }}
        .mini-ball {{
          display:inline-flex;background:#4779ef;color:white;
          width:32px;height:32px;border-radius:50%;
          align-items:center;justify-content:center;font-weight:bold;
        }}
        table {{width:100%;border-collapse:collapse;}}
        th,td {{padding:10px 5px;border-bottom:1px solid #39445a;text-align:left;}}
        .history {{overflow-x:auto;}}
        @media(min-width:600px) {{
          .freq-grid {{grid-template-columns:repeat(6,1fr);}}
        }}
      </style>
    </head>
    <body>
      <h1>🎡 Wheel Tracker</h1>

      <div class="card">
        <h2>Ajouter un résultat</h2>
        <form action="/add" method="post">
          <input type="number" name="number" min="0" max="36"
                 placeholder="0 à 36" required>
          <button type="submit">Enregistrer</button>
        </form>
      </div>

      <div class="grid">
        <div class="card stat"><h2>Total</h2><div class="value">{total}</div></div>
        <div class="card stat"><h2>Pairs</h2><div class="value">{even}</div></div>
        <div class="card stat"><h2>Impairs</h2><div class="value">{odd}</div></div>
        <div class="card stat"><h2>Distincts</h2><div class="value">{len(set(numbers))}</div></div>
      </div>

      <div class="card">
        <h2>Top fréquences observées</h2>
        {top_html}
      </div>

      <div class="card">
        <h2>Fréquences — 0 à 36</h2>
        <div class="freq-grid">
          {frequency_cards}
        </div>
      </div>

      <div class="card history">
        <h2>Historique récent</h2>
        <table>
          <tr><th>Numéro</th><th>Date / heure (UTC)</th></tr>
          {history_rows}
        </table>
      </div>

      <p style="text-align:center;color:#9ba8c0">
        Statistiques descriptives des résultats enregistrés.
        Elles ne prédisent pas les tirages futurs.
      </p>
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
    except Exception:
        return "Erreur d'enregistrement", 500

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
    return jsonify([dict(r) for r in get_results()])

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
