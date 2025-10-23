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
        return True  # Assume valid if connection issue

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
# Helper: Fetch and show current price hint
# -----------------------------------------------------
def show_price_hint(symbol, side):
    try:
        ticker = client.ticker_price(symbol)
        current_price = float(ticker["price"])
        print(f"\n📊 Current {symbol} Price: {current_price:.2f} USDT")

        if side == "BUY":
            print(f"👉 For BUY OCO: takeProfit < {current_price:.2f} < stopLoss")
        else:
            print(f"👉 For SELL OCO: takeProfit > {current_price:.2f} > stopLoss")
        print()
        return current_price
    except Exception as e:
        print(f"⚠️ Could not fetch current market price: {e}")
        return None

# -----------------------------------------------------
# Helper: Validate user input
# -----------------------------------------------------
def validate_args(args):
    if len(args) < 6:
        print("Usage: python oco_orders.py <symbol> <BUY/SELL> <quantity> <takeProfitPrice> <stopLossPrice>")
        sys.exit(1)

    symbol = args[1].upper()
    side = args[2].upper()

    # Validate numeric input
    try:
        quantity = float(args[3])
        take_profit = float(args[4])
        stop_loss = float(args[5])
    except ValueError:
        print("❌ Invalid input. Quantity, takeProfit, and stopLoss must be numeric values.")
        sys.exit(1)

    # Validate side
    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side. Use BUY or SELL.")
        sys.exit(1)

    # Validate positive values
    if quantity <= 0 or take_profit <= 0 or stop_loss <= 0:
        print("❌ Quantity and prices must be greater than 0.")
        sys.exit(1)

    # Validate symbol
    if not is_valid_symbol(symbol):
        print(f"❌ Invalid trading symbol: {symbol}")
        sys.exit(1)

    # Fetch live market price
    current_price = show_price_hint(symbol, side)

    # Validate notional
    try:
        if current_price:
            notional = current_price * quantity
            min_notional = get_min_notional(symbol)
            if notional < min_notional:
                print(f"❌ Order notional ({notional:.2f}) is below the minimum required ({min_notional:.2f} USDT).")
                sys.exit(1)
    except Exception as e:
        print(f"⚠️ Could not fetch current price for validation: {e}")

    # Validate logical price relationship
    if current_price:
        if side == "SELL":
            if not (take_profit > current_price > stop_loss):
                print(f"❌ For SELL OCO, expected takeProfit > {current_price:.2f} > stopLoss.")
                sys.exit(1)
        elif side == "BUY":
            if not (take_profit < current_price < stop_loss):
                print(f"❌ For BUY OCO, expected takeProfit < {current_price:.2f} < stopLoss.")
                sys.exit(1)

    return symbol, side, quantity, take_profit, stop_loss

# -----------------------------------------------------
# Main logic: Place OCO order
# -----------------------------------------------------
def place_oco_order(symbol, side, quantity, take_profit, stop_loss):
    try:
        # Take-Profit Limit Order
        tp_order = client.new_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            timeInForce="GTC",
            quantity=quantity,
            price=take_profit
        )

        # Stop-Loss Order
        sl_order = client.new_order(
            symbol=symbol,
            side=side,
            type="STOP",
            timeInForce="GTC",
            quantity=quantity,
            stopPrice=stop_loss,
            price=stop_loss
        )

        msg = (
            f"✅ OCO {side} order placed for {quantity} {symbol} "
            f"(Take Profit: {take_profit}, Stop Loss: {stop_loss})."
        )
        print(msg)
        logging.info(msg)
        logging.info(f"TP Order: {tp_order}")
        logging.info(f"SL Order: {sl_order}")

    except Exception as e:
        err = f"❌ Failed to place OCO order: {e}"
        print(err)
        logging.error(err)

# -----------------------------------------------------
# Entry Point
# -----------------------------------------------------
if __name__ == "__main__":
    symbol, side, quantity, take_profit, stop_loss = validate_args(sys.argv)
    place_oco_order(symbol, side, quantity, take_profit, stop_loss)
