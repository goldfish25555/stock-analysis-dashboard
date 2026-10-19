import os
from datetime import datetime, timedelta
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import sqlite3

load_dotenv()

app = Flask(__name__)
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
DB_PATH = os.getenv("DB_PATH", "stocks.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            shares REAL NOT NULL,
            avg_cost REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Add a small default portfolio so the UI looks populated on first run
def add_default_portfolio_if_empty():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT COUNT(*) FROM portfolio")
    count = cur.fetchone()[0]
    if count == 0:
        conn.execute("""
            INSERT INTO portfolio (symbol, shares, avg_cost)
            VALUES
                ('AAPL', 10, 170.00),
                ('MSFT', 6, 310.00),
                ('NVDA', 5, 720.00)
        """)
        conn.commit()
    conn.close()

def get_watchlist():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT symbol FROM watchlist ORDER BY id DESC").fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_symbol(symbol):
    conn = sqlite3.connect(DB_PATH)
    symbol = symbol.strip().upper()
    if symbol:
        try:
            conn.execute("INSERT INTO watchlist (symbol) VALUES (?)", (symbol,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    conn.close()

def get_portfolio():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT symbol, shares, avg_cost FROM portfolio").fetchall()
    conn.close()
    portfolio = []
    for symbol, shares, avg_cost in rows:
        quote = fetch_quote(symbol)
        current_price = quote.get("c", 0)
        value = shares * current_price
        gain = value - (shares * avg_cost)
        pct = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost else 0
        portfolio.append({
            "symbol": symbol,
            "shares": shares,
            "avg_cost": avg_cost,
            "current_price": current_price,
            "value": round(value, 2),
            "gain": round(gain, 2),
            "pct": round(pct, 2)
        })
    return portfolio

# --- External API helpers ---

def fetch_profile(symbol):
    if not FINNHUB_API_KEY:
        return {}
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API_KEY}"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return {}
    return r.json() or {}

def fetch_quote(symbol):
    if not FINNHUB_API_KEY:
        return {}
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return {}
    return r.json() or {}

def fetch_history(symbol, days=30):
    if not FINNHUB_API_KEY:
        return {"dates": [], "prices": []}
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=days)).timestamp())
    url = f"https://finnhub.io/api/v1/stock/candle?symbol={symbol}&resolution=D&from={start}&to={end}&token={FINNHUB_API_KEY}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if not data or "c" not in data:
        return {"dates": [], "prices": []}
    dates = []
    prices = []
    for i in range(len(data.get("t", []))):
        dates.append(datetime.fromtimestamp(data["t"][i]).strftime("%Y-%m-%d"))
        prices.append(data["c"][i])
    return {"dates": dates, "prices": prices}

# We render Plotly HTML snippets so the page remains a single Flask template
import plotly.graph_objects as go

def build_chart(symbol):
    hist = fetch_history(symbol)
    if not hist["prices"]:
        return "<p class=\"text-muted\">No chart data available.</p>"
    fig = go.Figure(data=[go.Scatter(x=hist["dates"], y=hist["prices"], mode="lines", line={"color": "#06b6d4", "width": 3})])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis={"title": "", "showgrid": False},
        yaxis={"title": "", "showgrid": False},
        font={"family": "Arial"},
        height=260
    )
    return fig.to_html(full_html=False, config={"displayModeBar": False})

@app.route("/", methods=["GET", "POST"])
def home():
    symbol = request.args.get("symbol", "AAPL").upper()
    if request.method == "POST":
        symbol = request.form.get("symbol", "").upper()
        if symbol:
            add_symbol(symbol)
            return redirect(url_for("home", symbol=symbol))

    watchlist = get_watchlist()
    profile = fetch_profile(symbol)
    quote = fetch_quote(symbol)
    chart_html = build_chart(symbol)
    portfolio = get_portfolio()

    total_value = round(sum(p["value"] for p in portfolio), 2)
    total_gain = round(sum(p["gain"] for p in portfolio), 2)

    return render_template(
        "index.html",
        symbol=symbol,
        quote=quote,
        profile=profile,
        watchlist=watchlist,
        chart_html=chart_html,
        portfolio=portfolio,
        total_value=total_value,
        total_gain=total_gain
    )

# Minimal API endpoints for possible frontend additions or integrations
@app.route("/api/watchlist", methods=["GET","POST"])
def api_watchlist():
    if request.method == "GET":
        return jsonify(get_watchlist())
    data = request.get_json() or {}
    symbol = (data.get("symbol") or "").upper()
    if symbol:
        add_symbol(symbol)
    return jsonify({"status":"ok","symbol":symbol})

@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    return jsonify(fetch_quote(symbol.upper()))

if __name__ == "__main__":
    init_db()
    add_default_portfolio_if_empty()
    app.run(debug=True)
