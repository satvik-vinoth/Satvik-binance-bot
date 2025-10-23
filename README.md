# ==========================================================

# 💹 Binance Futures Trading Bot (Python – Testnet)

# ==========================================================

# Author: Satvik Vinoth

# Description:

# A modular Binance Futures trading bot supporting Market,

# Limit, Stop-Limit, OCO, TWAP, and Grid strategies with

# full logging and sentiment-based AI adjustments.

# ==========================================================

# ==========================================================

# 🧩 1️⃣ Project Structure

# ==========================================================

# Project Folder Layout:

# Satvik-binance-bot/

# ├── src/

# │ ├── market_orders.py

# │ ├── limit_orders.py

# │ ├── advanced/

# │ │ ├── stop_limit_orders.py

# │ │ ├── oco.py

# │ │ ├── twap.py

# │ │ ├── twap_with_sentiment.py

# │ │ ├── grid_orders.py

# │ │ └── grid_orders_with_sentiment.py

# ├── bot.log

# ├── .env.example

# ├── requirements.txt

# └── report.pdf

# ==========================================================

# ⚙️ 2️⃣ Setup Instructions

# ==========================================================

# ---- Step 1: Clone the repository ----

git clone https://github.com/<your-username>/Satvik-binance-bot.git
cd Satvik-binance-bot

# ---- Step 2: Create a virtual environment (recommended) ----

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# ---- Step 3: Install dependencies ----

pip install -r requirements.txt

# ---- Step 4: Set up environment variables ----

# Create a .env file in the root folder based on .env.example

# Example contents:

cat > .env <<EOF
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
BASE_URL=https://testnet.binancefuture.com
EOF

# ---- Step 5: Verify setup ----

python -m pip show python-binance dotenv

# Should show installed versions.

# ==========================================================

# 💡 3️⃣ Running the Bot (Order Examples)

# ==========================================================

# Run each script directly from the project root.

# -------------------------------

# 🟢 MARKET ORDER

# -------------------------------

# Places an instant BUY or SELL at market price.

python src/market_orders.py BTCUSDT BUY 0.002

# -------------------------------

# 🟣 LIMIT ORDER

# -------------------------------

# Places a limit order to buy/sell at a specific price.

python src/limit_orders.py BTCUSDT SELL 0.002 109000

# -------------------------------

# 🟠 STOP-LIMIT ORDER

# -------------------------------

# Executes when stop price is hit, placing a limit order.

python src/advanced/stop_limit_orders.py BTCUSDT SELL 0.002 107000 106800

# -------------------------------

# 🔵 OCO ORDER (One-Cancels-the-Other)

# -------------------------------

# Places take-profit and stop-loss together.

python src/advanced/oco.py BTCUSDT SELL 0.002 110000 105000

# -------------------------------

# 🟡 TWAP STRATEGY

# -------------------------------

# Splits large orders into smaller timed chunks.

python src/advanced/twap.py BTCUSDT BUY 0.01 5 30

# (BUY 0.01 BTC in 5 slices, every 30 seconds)

# -------------------------------

# 🧠 TWAP WITH SENTIMENT

# -------------------------------

# Adjusts order aggressiveness based on live Fear & Greed Index.

python src/advanced/twap_with_sentiment.py BTCUSDT BUY 0.01 5 30

# -------------------------------

# 🧮 GRID TRADING STRATEGY

# -------------------------------

# Automatically places buy/sell limit orders across price range.

python src/advanced/grid_orders.py BTCUSDT 105000 115000 5 0.002

# (Range: 105000–115000 | 5 grid levels | 0.002 qty each)

# -------------------------------

# 🧩 GRID WITH SENTIMENT

# -------------------------------

# Integrates live market sentiment into grid spacing/position sizing.

python src/advanced/grid_orders_with_sentiment.py BTCUSDT 105000 115000 5 0.002

# ==========================================================

# 🧾 4️⃣ Logging

# ==========================================================

# All logs are automatically stored in:

cat bot.log

# Example log entries:

# 2025-10-23 11:28:01 - INFO - ✅ Market BUY order placed for 0.002 BTCUSDT.

# 2025-10-23 13:05:15 - INFO - ✅ Stop-Limit SELL order placed for 0.002 BTCUSDT.

# 2025-10-23 21:27:10 - INFO - ✅ [1/5] BUY 0.002 BTCUSDT at ~109946.50 USDT

# 2025-10-23 21:39:28 - INFO - ✅ SELL Limit [2] at 115000.0 for 0.001 BTCUSDT

# ==========================================================

# 📊 5️⃣ Sentiment Data (Fear & Greed Index)

# ==========================================================

# Used by twap_with_sentiment.py & grid_orders_with_sentiment.py.

# Pulled live from: https://api.alternative.me/fng/

# Example Output:

# 📊 Live Fear & Greed Index: 27 (Fear)

# 😨 Market in Extreme Fear → Increasing buy aggressiveness.

# ==========================================================

# 👨‍💻 6️⃣ Developer Info

# ==========================================================

# Author: Satvik Vinoth

# Role: Python Developer – Trading Automation

# Focus: Algorithmic trading, AI-integrated strategies, and analytics.

# GitHub: https://github.com/<your-username>/Satvik-binance-bot

# Email: satvikvinoth@gmail.com (optional for recruiters)

# ==========================================================

# ⚠️ 7️⃣ Disclaimer

# ==========================================================

# This bot uses Binance FUTURES TESTNET.

# It is built for EDUCATIONAL and DEMONSTRATION purposes only.

# DO NOT use with real funds without proper authorization.
