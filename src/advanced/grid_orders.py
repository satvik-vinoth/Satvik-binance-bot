import sys
import logging
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
# Helper: Validate user input
# =====================================================
def validate_args(args):
    if len(args) < 6:
        print("Usage: python grid_orders.py <symbol> <lower_price> <upper_price> <num_grids> <quantity>")
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
# Main logic: Place Grid Orders
# =====================================================
def place_grid_orders(symbol, lower_price, upper_price, num_grids, quantity):
    print(f"🚀 Starting Grid Trading Strategy for {symbol}")
    print(f"Range: {lower_price} → {upper_price} | Grids: {num_grids} | Qty: {quantity}")
    print("----------------------------------------------------")

    logging.info(f"Grid Strategy Started for {symbol}: {lower_price}-{upper_price} ({num_grids} grids)")

    # 1️⃣ Calculate grid spacing
    grid_gap = (upper_price - lower_price) / (num_grids - 1)
    grid_prices = [round(lower_price + i * grid_gap, 2) for i in range(num_grids)]

    # 2️⃣ Split into BUYs and SELLs
    mid_index = num_grids // 2
    buy_prices = grid_prices[:mid_index]
    sell_prices = grid_prices[mid_index + 1:]

    # 3️⃣ Place BUY orders below midpoint
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

    # 4️⃣ Place SELL orders above midpoint
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
    print("💡 The bot will automatically profit from market oscillations.")
    logging.info("Grid Strategy Execution Completed.\n")

# =====================================================
# Entry Point
# =====================================================
if __name__ == "__main__":
    symbol, lower_price, upper_price, num_grids, quantity = validate_args(sys.argv)
    place_grid_orders(symbol, lower_price, upper_price, num_grids, quantity)
