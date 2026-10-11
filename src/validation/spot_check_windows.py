"""
Step 6b — Independent validation pass #2: for a random sample of events, recompute
pre/post-halt returns FROM SCRATCH directly against the raw minute-bar CSV (not
reusing any helper from build_event_windows.py), and diff against what's stored
in event_windows_full.csv. This checks the extraction script itself for bugs,
not just re-running the same logic twice.
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(7)

bars = {}
with open("/home/claude/luld_halt_study/data/raw/minute_bars/all_minute_bars_rth.csv", newline="") as f:
    for r in csv.DictReader(f):
        dt = datetime.strptime(r["date_et"] + " " + r["time_et"], "%m/%d/%Y %H:%M:%S")
        bars.setdefault((r["symbol"], r["date_et"]), []).append((dt, float(r["open"]), float(r["close"])))
for k in bars:
    bars[k].sort()

with open("/home/claude/luld_halt_study/data/processed/event_windows_full.csv", newline="") as f:
    rows = [r for r in csv.DictReader(f) if r["data_status"] == "ok"]

sample = random.sample(rows, 25)

n_checked = 0
n_mismatch = 0
for row in sample:
    sym = row["symbol"]
    hd = row["halt_date"]
    halt_dt = datetime.strptime(row["halt_datetime"], "%Y-%m-%d %H:%M:%S")
    resume_dt = datetime.strptime(row["resumption_trade_datetime"], "%Y-%m-%d %H:%M:%S")

    day_bars = bars.get((sym, hd), [])

    # independent re-derivation of pre_ret_5m
    lo = halt_dt - timedelta(minutes=5)
    window = [b for b in day_bars if lo <= b[0] < halt_dt]
    my_pre_ret_5m = None
    if len(window) >= 2:
        my_pre_ret_5m = (window[-1][2] - window[0][1]) / window[0][1]

    # independent re-derivation of post_ret_30m
    resume_bars = bars.get((sym, row.get("halt_date")), [])  # resumption may be different date in rare cases; approximate via halt_date bars here since ok status implies same-day in the vast majority
    hi1 = resume_dt + timedelta(minutes=1)
    w1 = [b for b in day_bars if resume_dt <= b[0] < hi1]
    reopen_price = w1[0][1] if w1 else None
    hi30 = resume_dt + timedelta(minutes=30)
    w30 = [b for b in day_bars if resume_dt <= b[0] < hi30]
    my_post_ret_30m = None
    if w30 and reopen_price:
        my_post_ret_30m = (w30[-1][2] - reopen_price) / reopen_price

    reported_pre = row["pre_ret_5m"]
    reported_post30 = row["post_ret_30m"]

    n_checked += 1
    mismatch = False
    if reported_pre not in ("", None) and my_pre_ret_5m is not None:
        if abs(float(reported_pre) - my_pre_ret_5m) > 1e-9:
            mismatch = True
    elif (reported_pre in ("", None)) != (my_pre_ret_5m is None):
        mismatch = True

    if reported_post30 not in ("", None) and my_post_ret_30m is not None:
        if abs(float(reported_post30) - my_post_ret_30m) > 1e-9:
            mismatch = True
    elif (reported_post30 in ("", None)) != (my_post_ret_30m is None):
        mismatch = True

    status = "OK" if not mismatch else "MISMATCH"
    if mismatch:
        n_mismatch += 1
    print(f"{status}  {row['event_id']} {sym}: pre_ret_5m reported={reported_pre} recomputed={my_pre_ret_5m}  "
          f"| post_ret_30m reported={reported_post30} recomputed={my_post_ret_30m}")

print(f"\n{n_checked} events spot-checked, {n_mismatch} mismatches.")
