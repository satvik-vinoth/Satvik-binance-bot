import sys
import logging
import requests
from binance.um_futures import UMFutures
from dotenv import load_dotenv
import os

# =====================================================
# Setup
# =====================================================
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL", "https://testnet.binancefuture.com")

client = UMFutures(key=API_KEY, secret=API_SECRET, base_url=BASE_URL)

# Logging setup

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_FILE = os.path.join(PROJECT_ROOT, "bot.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =====================================================
# Helper: Validate if symbol exists
# =====================================================
def is_valid_symbol(symbol):
    try:
        info = client.exchange_info()
        symbols = [s["symbol"] for s in info["symbols"]]
        return symbol in symbols
    except Exception as e:
        print(f"⚠️ Could not verify symbol (network issue): {e}")
        return True

# =====================================================
# Helper: Get current market price
# =====================================================
def get_current_price(symbol):
    try:
        ticker = client.ticker_price(symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"⚠️ Could not fetch current price: {e}")
        return None

# =====================================================
# Helper: Get minimum notional requirement
# =====================================================
def get_min_notional(symbol):
    try:
        info = client.exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                for f in s["filters"]:
                    if f["filterType"] == "MIN_NOTIONAL":
                        return float(f["notional"])
        return 100.0
    except Exception as e:
        print(f"⚠️ Could not fetch minimum notional info: {e}")
        return 100.0

# =====================================================
# NEW: Live Fear & Greed Index Fetcher
# =====================================================
def get_live_fear_greed_index():
    """
    Fetches latest Fear & Greed Index from alternative.me API.
    Returns value (0–100) and textual classification.
    """
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        value = int(data["data"][0]["value"])
        classification = data["data"][0]["value_classification"]
        print(f"📊 Live Fear & Greed Index: {value} ({classification})")
        return value, classification
    except Exception as e:
        print(f"⚠️ Could not fetch live Fear & Greed Index: {e}")
        return 50, "Neutral"  # fallback

# =====================================================
# Helper: Validate user input
# =====================================================
def validate_args(args):
    if len(args) < 6:
        print("Usage: python grid_orders_with_sentiment.py <symbol> <lower_price> <upper_price> <num_grids> <quantity>")
        sys.exit(1)

    symbol = args[1].upper()
    lower_price = float(args[2])
    upper_price = float(args[3])
    num_grids = int(args[4])
    quantity = float(args[5])

    # 1️⃣ Symbol validation
    if not is_valid_symbol(symbol):
        print(f"❌ Invalid trading symbol: {symbol}")
        sys.exit(1)

    # 2️⃣ Logical range check
    if lower_price <= 0 or upper_price <= 0 or lower_price >= upper_price:
        print("❌ Invalid price range. Lower price must be < Upper price.")
        sys.exit(1)

    # 3️⃣ Grid and quantity checks
    if num_grids < 2:
        print("❌ You need at least 2 grids to form a range.")
        sys.exit(1)
    if quantity <= 0:
        print("❌ Quantity must be greater than 0.")
        sys.exit(1)

    # 4️⃣ Notional validation
    current_price = get_current_price(symbol)
    if current_price:
        notional = current_price * quantity
        min_notional = get_min_notional(symbol)
        if notional < min_notional:
            print(f"❌ Order notional ({notional:.2f}) is below minimum required ({min_notional:.2f} USDT).")
            sys.exit(1)
    else:
        print("⚠️ Could not verify notional value (price unavailable). Proceed with caution.")

    print(f"\n📊 Current {symbol} Price: {current_price:.2f} USDT" if current_price else "")
    print(f"✅ Validation Passed!")
    print(f"→ Range: {lower_price} - {upper_price}, Grids: {num_grids}, Quantity: {quantity}\n")

    return symbol, lower_price, upper_price, num_grids, quantity

# =====================================================
# Main logic: Place Grid Orders (Sentiment-Adaptive)
# =====================================================
def place_grid_orders(symbol, lower_price, upper_price, num_grids, quantity):
    # 1️⃣ Get live market sentiment
    index_value, classification = get_live_fear_greed_index()

    # 2️⃣ Adjust grid parameters based on sentiment
    if index_value <= 25:
        print("😨 Market in Extreme Fear → Widening grid & increasing buy size.")
        lower_price *= 0.98        # extend lower bound
        upper_price *= 1.02        # extend upper bound
        quantity *= 1.2            # buy more per level
    elif index_value >= 75:
        print("🚀 Market in Extreme Greed → Tightening grid & reducing buy size.")
        lower_price *= 1.01        # shift range up
        upper_price *= 0.99
        quantity *= 0.8            # smaller buys
    else:
        print("🙂 Market Neutral → Standard grid parameters.")

    print(f"\n🚀 Starting Grid Trading Strategy for {symbol}")
    print(f"Market Sentiment: {classification} ({index_value})")
    print(f"Range: {lower_price:.2f} → {upper_price:.2f} | Grids: {num_grids} | Qty: {quantity:.6f}")
    print("----------------------------------------------------")

    logging.info(f"Grid Strategy Started for {symbol}: {lower_price}-{upper_price} ({num_grids} grids) | Sentiment: {classification} ({index_value})")

    # 3️⃣ Calculate grid spacing
    grid_gap = (upper_price - lower_price) / (num_grids - 1)
    grid_prices = [round(lower_price + i * grid_gap, 2) for i in range(num_grids)]

    # 4️⃣ Split into BUYs and SELLs
    mid_index = num_grids // 2
    buy_prices = grid_prices[:mid_index]
    sell_prices = grid_prices[mid_index + 1:]

    # 5️⃣ Place BUY orders below midpoint
    for i, price in enumerate(buy_prices):
        try:
            order = client.new_order(
                symbol=symbol,
                side="BUY",
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=price
            )
            msg = f"✅ BUY Limit [{i+1}] at {price} for {quantity} {symbol}"
            print(msg)
            logging.info(msg)
        except Exception as e:
            err = f"❌ Failed to place BUY order at {price}: {e}"
            print(err)
            logging.error(err)

    # 6️⃣ Place SELL orders above midpoint
    for i, price in enumerate(sell_prices):
        try:
            order = client.new_order(
                symbol=symbol,
                side="SELL",
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=price
            )
            msg = f"✅ SELL Limit [{i+1}] at {price} for {quantity} {symbol}"
            print(msg)
            logging.info(msg)
        except Exception as e:
            err = f"❌ Failed to place SELL order at {price}: {e}"
            print(err)
            logging.error(err)

    print("\n🎯 Grid Orders Successfully Placed!")
    print("💡 The bot will automatically profit from market oscillations based on sentiment.")
    logging.info("Grid Strategy Execution Completed.\n")

# =====================================================
# Entry Point
# =====================================================
if __name__ == "__main__":
    symbol, lower_price, upper_price, num_grids, quantity = validate_args(sys.argv)
    place_grid_orders(symbol, lower_price, upper_price, num_grids, quantity)
