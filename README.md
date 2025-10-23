# 💹 Binance Futures Trading Bot (Python – Testnet)

**Description:**  
A modular Binance Futures trading bot supporting Market, Limit, Stop-Limit, OCO, TWAP, and Grid strategies with full logging and sentiment-based AI adjustments.


## 🧩 Project Structure

```
Satvik-binance-bot/
├── src/
│ ├── market_orders.py
│ ├── limit_orders.py
│ ├── advanced/
│ │ ├── stop_limit_orders.py
│ │ ├── oco.py
│ │ ├── twap.py
│ │ ├── twap_with_sentiment.py
│ │ ├── grid_orders.py
│ │ └── grid_orders_with_sentiment.py
├── bot.log
├── .env.example
├── requirements.txt
└── report.pdf
```

## ⚙️ Setup Instructions

### Step 1: Clone the repository
```
git clone https://github.com/<your-username>/Satvik-binance-bot.git
cd Satvik-binance-bot
```

### Step 2: Create a virtual environment (recommended)

```
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
```

### Step 3: Install dependencies

```
pip install -r requirements.txt
```

### Step 4: Set up environment variables

```
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
BASE_URL=https://testnet.binancefuture.com
```

### Step 5: Run python scripts

#### Market Order
Places an instant BUY or SELL at market price.
```
python src/market_orders.py BTCUSDT BUY 0.002
```

#### Limit Order
Places a limit order to buy/sell at a specific price.
```
python src/limit_orders.py BTCUSDT SELL 0.002 109000
```
#### Stop-Limit Order
Executes when stop price is hit, placing a limit order.
```
python src/advanced/stop_limit_orders.py BTCUSDT SELL 0.002 107000 106800
```
#### OCO Order (One-Cancels-the-Other)
Places take-profit and stop-loss together.
```
python src/advanced/oco.py BTCUSDT SELL 0.002 110000 105000
```
#### TWAP Strategy
Splits large orders into smaller timed chunks.
```
python src/advanced/twap.py BTCUSDT BUY 0.01 5 30
```

#### TWAP with Sentiment
Adjusts order aggressiveness based on the live Fear & Greed Index.
```
python src/advanced/twap_with_sentiment.py BTCUSDT BUY 0.01 5 30
```
#### Grid Trading Strategy
Automatically places buy/sell limit orders across a price range.
```
python src/advanced/grid_orders.py BTCUSDT 105000 115000 5 0.002
```

#### Grid with Sentiment
Integrates live market sentiment into grid spacing and position sizing.
```
python src/advanced/grid_orders_with_sentiment.py BTCUSDT 105000 115000 5 0.002
```




