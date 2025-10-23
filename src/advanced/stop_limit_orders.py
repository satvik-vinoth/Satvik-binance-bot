import sys
import logging
from binance.um_futures import UMFutures
from dotenv import load_dotenv
import os

# -----------------------------------------------------
# Setup
# -----------------------------------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL", "https://testnet.binancefuture.com")

client = UMFutures(key=API_KEY, secret=API_SECRET, base_url=BASE_URL)

# -----------------------------------------------------
# Setup logging (always write to Satvik-binance-bot/bot.log)
# -----------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_FILE = os.path.join(PROJECT_ROOT, "bot.log")

# Reset old log handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
print(f"📝 Logging to: {LOG_FILE}")

# -----------------------------------------------------
# Helper: Validate if symbol exists
# -----------------------------------------------------
def is_valid_symbol(symbol):
    try:
        info = client.exchange_info()
        symbols = [s["symbol"] for s in info["symbols"]]
        return symbol in symbols
    except Exception as e:
        print(f"⚠️ Could not verify symbol (network issue): {e}")
        return True  # assume valid if Binance unreachable

# -----------------------------------------------------
# Helper: Get Minimum Notional Requirement
# -----------------------------------------------------
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

# -----------------------------------------------------
# Helper: Validate user input
# -----------------------------------------------------
def validate_args(args):
    if len(args) < 6:
        print("Usage: python stop_limit_orders.py <symbol> <BUY/SELL> <quantity> <stopPrice> <limitPrice>")
        sys.exit(1)

    symbol = args[1].upper()
    side = args[2].upper()

    # Handle invalid numeric inputs
    try:
        quantity = float(args[3])
        stop_price = float(args[4])
        limit_price = float(args[5])
    except ValueError:
        print("❌ Invalid input. Quantity, stop price, and limit price must be numbers.")
        sys.exit(1)

    # Validate side
    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side. Use BUY or SELL.")
        sys.exit(1)

    # Validate positive values
    if quantity <= 0 or stop_price <= 0 or limit_price <= 0:
        print("❌ Quantity and prices must be greater than 0.")
        sys.exit(1)

    # Validate symbol
    if not is_valid_symbol(symbol):
        print(f"❌ Invalid trading symbol: {symbol}")
        sys.exit(1)

    # Validate notional value
    notional = limit_price * quantity
    min_notional = get_min_notional(symbol)
    if notional < min_notional:
        print(f"❌ Order notional ({notional:.2f}) is below the minimum required ({min_notional:.2f} USDT).")
        sys.exit(1)

    # Validate relationship between stop & limit price
    try:
        ticker = client.ticker_price(symbol)
        current_price = float(ticker["price"])

        if side == "BUY":
            # stop should be ABOVE current price, limit slightly above stop
            if stop_price <= current_price:
                print(f"❌ For BUY stop-limit, stop price must be ABOVE current market price ({current_price:.2f}).")
                sys.exit(1)
            if limit_price < stop_price:
                print(f"❌ For BUY stop-limit, limit price should be >= stop price.")
                sys.exit(1)

        elif side == "SELL":
            # stop should be BELOW current price, limit slightly below stop
            if stop_price >= current_price:
                print(f"❌ For SELL stop-limit, stop price must be BELOW current market price ({current_price:.2f}).")
                sys.exit(1)
            if limit_price > stop_price:
                print(f"❌ For SELL stop-limit, limit price should be <= stop price.")
                sys.exit(1)

    except Exception as e:
        print(f"⚠️ Could not fetch current price: {e}")

    return symbol, side, quantity, stop_price, limit_price

# -----------------------------------------------------
# Main logic
# -----------------------------------------------------
def place_stop_limit_order(symbol, side, quantity, stop_price, limit_price):
    try:
        order = client.new_order(
            symbol=symbol,
            side=side,
            type="STOP",
            timeInForce="GTC",
            quantity=quantity,
            stopPrice=stop_price,
            price=limit_price
        )

        msg = (
            f"✅ Stop-Limit {side} order placed for {quantity} {symbol} "
            f"(Stop: {stop_price}, Limit: {limit_price})."
        )
        print(msg)
        logging.info(msg)
        logging.info(f"Order response: {order}")

    except Exception as e:
        err = f"❌ Failed to place stop-limit order: {e}"
        print(err)
        logging.error(err)

# -----------------------------------------------------
# Entry point
# -----------------------------------------------------
if __name__ == "__main__":
    symbol, side, quantity, stop_price, limit_price = validate_args(sys.argv)
    place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
