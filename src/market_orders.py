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

# Setup logging
logging.basicConfig(
    filename="../bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------------------------------
# Helper: Validate symbol existence
# -----------------------------------------------------
def is_valid_symbol(symbol):
    """
    Checks if the provided symbol exists on Binance Futures.
    """
    try:
        info = client.exchange_info()
        symbols = [s["symbol"] for s in info["symbols"]]
        return symbol in symbols
    except Exception as e:
        print(f"⚠️ Could not verify symbol (network issue): {e}")
        return True  # Assume valid if network fails

# -----------------------------------------------------
# Helper: Validate user input
# -----------------------------------------------------
def validate_args(args):
    if len(args) < 4:
        print("Usage: python market_orders.py <symbol> <BUY/SELL> <quantity>")
        sys.exit(1)

    symbol = args[1].upper()
    side = args[2].upper()
    quantity = float(args[3])

    # Validate side
    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side. Use BUY or SELL.")
        sys.exit(1)

    # Validate quantity
    if quantity <= 0:
        print("❌ Quantity must be greater than 0.")
        sys.exit(1)

    # Validate symbol
    if not is_valid_symbol(symbol):
        print(f"❌ Invalid trading symbol: {symbol}")
        sys.exit(1)

    # Validate notional value (quantity * price >= 100)
    try:
        ticker = client.ticker_price(symbol)
        price = float(ticker["price"])
        notional = price * quantity
        if notional < 100:
            print(f"❌ Order notional ({notional:.2f} USDT) is below the minimum required (100 USDT).")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️ Could not fetch current price for notional check: {e}")

    return symbol, side, quantity

# -----------------------------------------------------
# Main logic
# -----------------------------------------------------
def place_market_order(symbol, side, quantity):
    """
    Places a MARKET order for the given symbol, side, and quantity.
    Logs all actions and handles Binance API errors gracefully.
    """
    try:
        order = client.new_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity
        )
        msg = f"✅ Market {side} order placed for {quantity} {symbol}."
        print(msg)
        logging.info(msg)
        logging.info(f"Order response: {order}")
    except Exception as e:
        err = f"❌ Failed to place order: {e}"
        print(err)
        logging.error(err)

# -----------------------------------------------------
# Entry point
# -----------------------------------------------------
if __name__ == "__main__":
    symbol, side, quantity = validate_args(sys.argv)
    place_market_order(symbol, side, quantity)
