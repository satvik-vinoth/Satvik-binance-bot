import sys
import time
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

# Logging configuration

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_FILE = os.path.join(PROJECT_ROOT, "bot.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =====================================================
# Helper: Symbol Validation
# =====================================================
def is_valid_symbol(symbol):
    try:
        info = client.exchange_info()
        symbols = [s["symbol"] for s in info["symbols"]]
        return symbol in symbols
    except Exception as e:
        print(f"⚠️ Could not verify symbol (network issue): {e}")
        return True  # assume valid if Binance API unavailable

# =====================================================
# Helper: Current Price
# =====================================================
def get_current_price(symbol):
    try:
        ticker = client.ticker_price(symbol)
        return float(ticker["price"])
    except Exception as e:
        print(f"⚠️ Could not fetch current market price: {e}")
        return None

# =====================================================
# Helper: Minimum Notional Check
# =====================================================
def get_min_notional(symbol):
    try:
        info = client.exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                for f in s["filters"]:
                    if f["filterType"] == "MIN_NOTIONAL":
                        return float(f["notional"])
        return 100.0  # fallback
    except Exception as e:
        print(f"⚠️ Could not fetch minimum notional info: {e}")
        return 100.0

# =====================================================
# Helper: Validate user arguments
# =====================================================
def validate_args(args):
    if len(args) < 6:
        print("Usage: python twap_orders.py <symbol> <BUY/SELL> <total_qty> <num_slices> <interval_seconds>")
        sys.exit(1)

    symbol = args[1].upper()
    side = args[2].upper()
    total_qty = float(args[3])
    num_slices = int(args[4])
    interval = int(args[5])

    # 1️⃣ Side validation
    if side not in ["BUY", "SELL"]:
        print("❌ Invalid side. Use BUY or SELL.")
        sys.exit(1)

    # 2️⃣ Quantity, slices, and interval checks
    if total_qty <= 0 or num_slices <= 0 or interval <= 0:
        print("❌ Quantities and interval must be greater than 0.")
        sys.exit(1)

    # 3️⃣ Symbol validation
    if not is_valid_symbol(symbol):
        print(f"❌ Invalid trading symbol: {symbol}")
        sys.exit(1)

    # 4️⃣ Split into equal chunks
    chunk_qty = total_qty / num_slices

    # 5️⃣ Notional validation for each chunk
    current_price = get_current_price(symbol)
    if current_price:
        notional = current_price * chunk_qty
        min_notional = get_min_notional(symbol)
        if notional < min_notional:
            print(f"❌ Each chunk notional ({notional:.2f}) is below the minimum required ({min_notional:.2f} USDT).")
            sys.exit(1)
    else:
        print("⚠️ Could not verify notional value (price unavailable). Proceed with caution.")

    print(f"\n📊 Current {symbol} Price: {current_price:.2f} USDT" if current_price else "")
    print(f"✅ Validation Passed!")
    print(f"→ Total Qty: {total_qty}, Slices: {num_slices}, Chunk Size: {chunk_qty:.6f}, Interval: {interval}s\n")

    return symbol, side, total_qty, num_slices, interval, chunk_qty

# =====================================================
# TWAP Execution Logic
# =====================================================
def execute_twap(symbol, side, total_qty, num_slices, interval, chunk_qty):
    print(f"🚀 Starting TWAP Execution for {symbol}")
    print(f"Side: {side}")
    print(f"Total Quantity: {total_qty}")
    print(f"Split: {num_slices} × {chunk_qty:.6f}")
    print(f"Interval: {interval} seconds")
    print("----------------------------------------------------")

    logging.info(f"Starting TWAP for {symbol}: {side} {total_qty} in {num_slices} slices every {interval}s")

    for i in range(1, num_slices + 1):
        try:
            current_price = get_current_price(symbol)
            if not current_price:
                print("⚠️ Price unavailable, skipping this slice.")
                continue

            # Execute order
            order = client.new_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=round(chunk_qty, 6)
            )

            msg = f"✅ [{i}/{num_slices}] {side} {chunk_qty:.6f} {symbol} at ~{current_price:.2f} USDT"
            print(msg)
            logging.info(msg)
            logging.info(f"Order Response: {order}")

            # Wait for next slice
            if i < num_slices:
                print(f"⏳ Waiting {interval}s before next order...")
                time.sleep(interval)

        except Exception as e:
            err = f"❌ Failed at slice {i}: {e}"
            print(err)
            logging.error(err)
            break

    print("\n🎯 TWAP Execution Completed Successfully!")
    logging.info("TWAP Strategy Finished.\n")

# =====================================================
# Entry point
# =====================================================
if __name__ == "__main__":
    symbol, side, total_qty, num_slices, interval, chunk_qty = validate_args(sys.argv)
    execute_twap(symbol, side, total_qty, num_slices, interval, chunk_qty)
