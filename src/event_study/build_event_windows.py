"""
Step 4 — Event window extraction for Study B (LULD Halt Behavior).

For every event in data/processed/luld_master_events.csv, joins against the
collected Webull 1-minute RTH bars (data/raw/minute_bars/all_minute_bars_rth.csv)
to build:

  - a pre-halt window (price action leading into the pause)
  - a post-halt / reopening window (price action after the pause resumes),
    at several horizons: 1, 5, 15, 30, 60 minutes
  - a continuation-vs-reversal classification (does the post-halt direction
    match or oppose the pre-halt direction?)
  - a re-halt flag (did the same symbol halt again within 30 minutes of this
    event's reopening?)
  - explicit data-availability flags — this study does NOT fabricate or
    interpolate bars. Any event whose minute-bar coverage is missing or
    incomplete around the halt is flagged, not silently dropped or filled.

Output: data/processed/event_windows.csv (one row per master event, event_id
is the join key back to luld_master_events.csv).

No raw input file is modified. This script only reads
data/processed/luld_master_events.csv and data/raw/minute_bars/all_minute_bars_rth.csv
and writes data/processed/event_windows.csv.
"""

import csv
from datetime import datetime, timedelta
from collections import defaultdict

MASTER_PATH = "/home/claude/luld_halt_study/data/processed/luld_master_events.csv"
BARS_PATH = "/home/claude/luld_halt_study/data/raw/minute_bars/all_minute_bars_rth.csv"
OUT_PATH = "/home/claude/luld_halt_study/data/processed/event_windows.csv"

POST_HORIZONS_MIN = [1, 5, 15, 30, 60]
PRE_HORIZONS_MIN = [5, 15]
REHALT_WINDOW_MIN = 30


def parse_dt(date_str, time_str):
    # date_str: MM/DD/YYYY, time_str: HH:MM:SS
    return datetime.strptime(date_str + " " + time_str, "%m/%d/%Y %H:%M:%S")


def load_bars():
    """Returns dict: (symbol, date_et MM/DD/YYYY) -> sorted list of (datetime, open, high, low, close, volume)."""
    bars = defaultdict(list)
    with open(BARS_PATH, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            sym = row["symbol"]
            date_et = row["date_et"]
            try:
                dt = parse_dt(date_et, row["time_et"])
            except ValueError:
                continue
            try:
                o, h, l, c, v = (
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["volume"]),
                )
            except (ValueError, TypeError):
                continue
            bars[(sym, date_et)].append((dt, o, h, l, c, v))
    for key in bars:
        bars[key].sort(key=lambda x: x[0])
    return bars


def load_events():
    with open(MASTER_PATH, newline="") as f:
        return list(csv.DictReader(f))


def bars_before(bar_list, cutoff_dt, window_minutes):
    """Bars strictly before cutoff_dt, within window_minutes of it."""
    lo = cutoff_dt - timedelta(minutes=window_minutes)
    return [b for b in bar_list if lo <= b[0] < cutoff_dt]


def bars_after(bar_list, start_dt, window_minutes):
    """Bars at/after start_dt, within window_minutes of it."""
    hi = start_dt + timedelta(minutes=window_minutes)
    return [b for b in bar_list if start_dt <= b[0] < hi]


def pct_return(p0, p1):
    if p0 is None or p1 is None or p0 == 0:
        return None
    return (p1 - p0) / p0


def main():
    print("Loading minute bars...")
    bars = load_bars()
    print(f"Loaded bars for {len(bars)} distinct (symbol, date) keys.")

    print("Loading master events...")
    events = load_events()
    print(f"Loaded {len(events)} events.")

    # Build per-symbol, per-date sorted event list for re-halt detection
    events_by_sym_date = defaultdict(list)
    for ev in events:
        events_by_sym_date[(ev["symbol"], ev["halt_date"])].append(ev)
    for key in events_by_sym_date:
        events_by_sym_date[key].sort(key=lambda e: e["halt_datetime"])

    fieldnames = [
        "event_id", "symbol", "halt_date", "halt_datetime", "resumption_trade_datetime",
        "pre_halt_bars_available", "post_halt_bars_available",
        "pre_halt_price_ref", "reopen_price_ref",
    ]
    for m in PRE_HORIZONS_MIN:
        fieldnames.append(f"pre_ret_{m}m")
    for m in POST_HORIZONS_MIN:
        fieldnames.append(f"post_ret_{m}m")
        fieldnames.append(f"post_bars_{m}m")
    fieldnames += [
        "pre_halt_direction", "post_halt_direction_5m", "post_halt_direction_30m",
        "continuation_or_reversal_5m", "continuation_or_reversal_30m",
        "re_halted_within_30m", "re_halt_event_id",
        "data_status",
    ]

    n_written = 0
    n_no_pre = 0
    n_no_post = 0
    n_both_missing = 0

    with open(OUT_PATH, "w", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        for ev in events:
            sym = ev["symbol"]
            halt_date = ev["halt_date"]
            resumption_date = ev["resumption_date"] or halt_date

            try:
                halt_dt = datetime.strptime(ev["halt_datetime"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                halt_dt = None

            resumption_dt_str = ev["resumption_trade_datetime"]
            resume_dt = None
            if resumption_dt_str:
                try:
                    resume_dt = datetime.strptime(resumption_dt_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    resume_dt = None

            row = {
                "event_id": ev["event_id"],
                "symbol": sym,
                "halt_date": halt_date,
                "halt_datetime": ev["halt_datetime"],
                "resumption_trade_datetime": resumption_dt_str,
            }

            pre_bar_list = bars.get((sym, halt_date), [])
            post_bar_list = bars.get((sym, resumption_date), [])

            # --- Pre-halt window ---
            pre_available = 0
            pre_ref_price = None
            if halt_dt is not None and pre_bar_list:
                pre_bars_max = bars_before(pre_bar_list, halt_dt, max(PRE_HORIZONS_MIN))
                pre_available = len(pre_bars_max)
                if pre_bars_max:
                    pre_ref_price = pre_bars_max[-1][4]  # close of last pre-halt bar
            row["pre_halt_bars_available"] = pre_available
            row["pre_halt_price_ref"] = pre_ref_price

            for m in PRE_HORIZONS_MIN:
                ret = None
                if halt_dt is not None and pre_bar_list:
                    wbars = bars_before(pre_bar_list, halt_dt, m)
                    if len(wbars) >= 2:
                        ret = pct_return(wbars[0][1], wbars[-1][4])  # open of window -> close of last bar
                row[f"pre_ret_{m}m"] = ret

            # --- Post-halt / reopening window ---
            post_available_1m = 0
            reopen_ref_price = None
            if resume_dt is not None and post_bar_list:
                post_bars_1m = bars_after(post_bar_list, resume_dt, 1)
                if post_bars_1m:
                    reopen_ref_price = post_bars_1m[0][1]  # open of first post-halt bar
            row["reopen_price_ref"] = reopen_ref_price

            max_post_bars_available = 0
            for m in POST_HORIZONS_MIN:
                ret = None
                nb = 0
                if resume_dt is not None and post_bar_list and reopen_ref_price is not None:
                    wbars = bars_after(post_bar_list, resume_dt, m)
                    nb = len(wbars)
                    if wbars:
                        ret = pct_return(reopen_ref_price, wbars[-1][4])
                row[f"post_ret_{m}m"] = ret
                row[f"post_bars_{m}m"] = nb
                max_post_bars_available = max(max_post_bars_available, nb)
            row["post_halt_bars_available"] = max_post_bars_available

            # --- Direction / continuation / reversal ---
            pre_dir = None
            if row["pre_ret_5m"] is not None:
                pre_dir = "up" if row["pre_ret_5m"] > 0 else ("down" if row["pre_ret_5m"] < 0 else "flat")
            row["pre_halt_direction"] = pre_dir

            post_dir_5m = None
            if row["post_ret_5m"] is not None:
                post_dir_5m = "up" if row["post_ret_5m"] > 0 else ("down" if row["post_ret_5m"] < 0 else "flat")
            row["post_halt_direction_5m"] = post_dir_5m

            post_dir_30m = None
            if row["post_ret_30m"] is not None:
                post_dir_30m = "up" if row["post_ret_30m"] > 0 else ("down" if row["post_ret_30m"] < 0 else "flat")
            row["post_halt_direction_30m"] = post_dir_30m

            def classify(pre, post):
                if pre is None or post is None or pre == "flat" or post == "flat":
                    return None
                return "continuation" if pre == post else "reversal"

            row["continuation_or_reversal_5m"] = classify(pre_dir, post_dir_5m)
            row["continuation_or_reversal_30m"] = classify(pre_dir, post_dir_30m)

            # --- Re-halt detection: another event, same symbol/date, halt_datetime
            #     within REHALT_WINDOW_MIN of THIS event's resumption ---
            re_halted = False
            re_halt_event_id = None
            if resume_dt is not None:
                same_day_events = events_by_sym_date.get((sym, halt_date), [])
                for other in same_day_events:
                    if other["event_id"] == ev["event_id"]:
                        continue
                    try:
                        other_halt_dt = datetime.strptime(other["halt_datetime"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                    if resume_dt <= other_halt_dt <= resume_dt + timedelta(minutes=REHALT_WINDOW_MIN):
                        re_halted = True
                        re_halt_event_id = other["event_id"]
                        break
            row["re_halted_within_30m"] = re_halted
            row["re_halt_event_id"] = re_halt_event_id

            # --- Data status flag (never silently drop — always mark) ---
            if pre_available == 0 and max_post_bars_available == 0:
                status = "no_data_either_side"
                n_both_missing += 1
            elif pre_available == 0:
                status = "no_pre_halt_data"
                n_no_pre += 1
            elif max_post_bars_available == 0:
                status = "no_post_halt_data"
                n_no_post += 1
            else:
                status = "ok"
            row["data_status"] = status

            writer.writerow(row)
            n_written += 1

    print(f"Wrote {n_written} event-window rows to {OUT_PATH}")
    print(f"  no_pre_halt_data: {n_no_pre}")
    print(f"  no_post_halt_data: {n_no_post}")
    print(f"  no_data_either_side: {n_both_missing}")
    print(f"  ok (both sides have data): {n_written - n_no_pre - n_no_post - n_both_missing}")


if __name__ == "__main__":
    main()
