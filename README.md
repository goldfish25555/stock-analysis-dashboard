# Stock Analysis Dashboard

A small personal stock analysis dashboard built with Flask, SQLite, Bootstrap and Plotly. This starter project provides a one-page dashboard with a watchlist, a simple portfolio, live quotes (via Finnhub), and a 30-day price chart.

Features
- Add tickers to a watchlist
- Live quote lookup (Finnhub)
- 30-day price chart (Plotly)
- Simple portfolio view with value and P/L

Quickstart (local)
1. Clone the repository
   git clone https://github.com/goldfish25555/stock-analysis-dashboard.git
2. Create a virtual environment and activate it
   python -m venv .venv
   source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
3. Install dependencies
   pip install -r requirements.txt
4. Copy .env.example to .env and add your FINNHUB_API_KEY
   cp .env.example .env
5. Run the app
   python app.py
6. Open http://127.0.0.1:5000

Notes
- The app creates a small SQLite database (stocks.db) on first run.
- Keep your API key secret — .env is in .gitignore.

Ideas to extend (good for CV bullets)
- Add authentication and per-user portfolios
- Add technical indicators (RSI, SMA, EMA)
- Add caching for API results and background updates
- Deploy backend to Render and add a React frontend on Vercel

License: MIT
