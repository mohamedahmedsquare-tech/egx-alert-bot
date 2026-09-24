"""
EGX Price Alert - core logic
------------------------------
Checks a watchlist of Egyptian Exchange (EGX) stocks and sends a Telegram
message whenever a stock's price falls inside your configured "buy zone".

This module is used by both:
  - local_runner.py   (keeps running on your machine, loops automatically)
  - GitHub Actions     (.github/workflows/egx_alert.yml, runs in the cloud)

Required environment variables (set in a local .env file OR as GitHub secrets):
  TELEGRAM_BOT_TOKEN  - token from @BotFather
  TELEGRAM_CHAT_ID    - your personal or group chat id
"""

import os
import requests

# Load a local .env file if python-dotenv is installed and the file exists.
# On GitHub Actions this simply does nothing (no .env file there) and the
# secrets come from the environment instead — same script, both contexts.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import yfinance as yf

# ---------------------------------------------------------------------------
# WATCHLIST: ticker (Yahoo Finance EGX tickers use the ".CA" suffix)
#   -> (buy_zone_low, buy_zone_high, display_name)
# Edit this dict to add/remove stocks or adjust your buy zones.
# ---------------------------------------------------------------------------
WATCHLIST = {
    "SWDY.CA": (105, 115, "السويدي إليكتريك"),
    "TMGH.CA": (90, 97, "طلعت مصطفى"),
    "FWRY.CA": (17, 18.5, "فوري"),
    "ETEL.CA": (112, 120, "المصرية للاتصالات"),
    "ADIB.CA": (46, 50, "أبوظبي الإسلامي مصر"),
}

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID — skipping send.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"Telegram send failed: {resp.status_code} {resp.text}")
    else:
        print("Telegram message sent.")


def get_price(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        price = info.get("last_price") or info.get("lastPrice")
        if price is None:
            hist = stock.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        return float(price) if price is not None else None
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def check_prices() -> None:
    alerts = []
    lines = []
    for ticker, (low, high, name) in WATCHLIST.items():
        price = get_price(ticker)
        if price is None:
            lines.append(f"{ticker}: تعذر جلب السعر")
            continue
        lines.append(f"{ticker} ({name}): {price:.2f}ج")
        if low <= price <= high:
            alerts.append(
                f"🟢 {name} ({ticker}) بسعر {price:.2f}ج — داخل منطقة الشراء ({low}-{high}ج)"
            )

    print("\n".join(lines))

    if alerts:
        message = "📈 فرصة شراء محتملة على EGX:\n\n" + "\n".join(alerts)
        send_telegram(message)
    else:
        send_telegram("No stocks in buy zone right now — no alert sent.")


if __name__ == "__main__":
    check_prices()
