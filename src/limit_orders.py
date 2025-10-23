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
# Helper: Get Minimum Notional Requirement
# -----------------------------------------------------
def get_min_notional(symbol):
    """
    Fetches the minimum notional value (in USDT) required for a valid order
    for the given symbol from Binance Futures exchange info.
    """
    try:
        info = client.exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                for f in s["filters"]:
                    if f["filterType"] == "MIN_NOTIONAL":
                        return float(f["notional"])
        return 100.0  # default fallback
    except Exception as e:
        print(f"⚠️ Could not fetch minimum notional info: {e}")
        return 100.0

# -----------------------------------------------------
# Helper: Validate user input
# -----------------------------------------------------
def validate_args(args):
    if len(args) < 5:
        print("Usage: python limit_orders.py <symbol> <BUY/SELL> <quantity> <price>")
        sys.exit(1)

    symbol = args[1].upper()
    side = args[2].upper()
    quantity = float(args[3])
    price = float(args[4])

    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side. Use BUY or SELL.")
        sys.exit(1)

    if quantity <= 0 or price <= 0:
        print("❌ Quantity and price must be greater than 0.")
        sys.exit(1)

    # Check notional value
    notional = price * quantity
    min_notional = get_min_notional(symbol)

    if notional < min_notional:
        print(f"❌ Order notional ({notional:.2f}) is below the minimum required ({min_notional:.2f} USDT).")
        sys.exit(1)

    # Check against current market price
    try:
        ticker = client.ticker_price(symbol)
        current_price = float(ticker["price"])
        if side == "BUY" and price >= current_price:
            print(f"❌ For BUY orders, limit price must be BELOW current market price ({current_price:.2f}).")
            sys.exit(1)
        if side == "SELL" and price <= current_price:
            print(f"❌ For SELL orders, limit price must be ABOVE current market price ({current_price:.2f}).")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️ Could not fetch current price: {e}")

    return symbol, side, quantity, price

# -----------------------------------------------------
# Main logic
# -----------------------------------------------------
def place_limit_order(symbol, side, quantity, price):
    try:
        order = client.new_order(
            symbol=symbol,
            side=side,
            type="LIMIT",
            timeInForce="GTC",  # Good Till Cancelled
            quantity=quantity,
            price=price
        )

        msg = f"✅ Limit {side} order placed for {quantity} {symbol} at {price}."
        print(msg)
        logging.info(msg)
        logging.info(f"Order response: {order}")

    except Exception as e:
        err = f"❌ Failed to place limit order: {e}"
        print(err)
        logging.error(err)

# -----------------------------------------------------
# Entry point
# -----------------------------------------------------
if __name__ == "__main__":
    symbol, side, quantity, price = validate_args(sys.argv)
    place_limit_order(symbol, side, quantity, price)
