"""
Local runner for the EGX alert bot.
------------------------------------
Keeps running in a loop on your own machine (terminal, background process,
or Task Scheduler/cron). It only checks prices during EGX trading hours
(Sunday-Thursday, 10:00-14:30 Cairo time) and sleeps the rest of the time
to save API calls.

Usage:
    python local_runner.py

Leave the terminal window open (or run it in the background — see the
instructions file for how to do that on Windows/Mac).
"""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from egx_price_alert import check_prices

CAIRO = ZoneInfo("Africa/Cairo")
CHECK_INTERVAL_SECONDS = 30 * 60   # check every 30 minutes during trading hours
IDLE_SLEEP_SECONDS = 15 * 60       # re-check every 15 minutes whether market opened

# EGX trading days: Sunday(6)-Thursday(3) in Python's weekday() (Mon=0..Sun=6)
TRADING_WEEKDAYS = {6, 0, 1, 2, 3}  # Sun, Mon, Tue, Wed, Thu
MARKET_OPEN = (10, 0)
MARKET_CLOSE = (14, 30)


def market_is_open(now: datetime) -> bool:
    if now.weekday() not in TRADING_WEEKDAYS:
        return False
    open_t = now.replace(hour=MARKET_OPEN[0], minute=MARKET_OPEN[1], second=0, microsecond=0)
    close_t = now.replace(hour=MARKET_CLOSE[0], minute=MARKET_CLOSE[1], second=0, microsecond=0)
    return open_t <= now <= close_t


def main():
    print("EGX alert bot started. Press Ctrl+C to stop.")
    while True:
        now = datetime.now(CAIRO)
        if market_is_open(now):
            print(f"[{now:%Y-%m-%d %H:%M}] Market open — checking prices...")
            try:
                check_prices()
            except Exception as e:
                print(f"Error during check: {e}")
            time.sleep(CHECK_INTERVAL_SECONDS)
        else:
            print(f"[{now:%Y-%m-%d %H:%M}] Market closed — sleeping...")
            time.sleep(IDLE_SLEEP_SECONDS)


if __name__ == "__main__":
    main()
