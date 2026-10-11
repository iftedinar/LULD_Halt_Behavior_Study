"""
Step 5a — Add SPY market-adjusted (abnormal) returns to the event windows.

For each event, computes SPY's return over the same absolute pre-halt and
post-halt clock windows already used in event_windows.csv, then derives
abnormal_ret_Xm = stock post_ret_Xm - spy post_ret_Xm for each post-halt
horizon. This is the standard market-model / market-adjusted-return approach
for an event study: it controls for market-wide moves happening at the same
time as the halt (important since many LULD pauses cluster on high-volatility
market days).

Reads: data/processed/event_windows.csv, data/processed/luld_master_events.csv,
       data/raw/market_control/spy_minute_bars_rth.csv
Writes: data/processed/event_windows_full.csv (adds market-adjusted columns +
        selected master-event fields for downstream analysis)
"""
import csv
from datetime import datetime, timedelta
from collections import defaultdict

EVENT_WINDOWS = "/home/claude/luld_halt_study/data/processed/event_windows.csv"
MASTER = "/home/claude/luld_halt_study/data/processed/luld_master_events.csv"
SPY_BARS = "/home/claude/luld_halt_study/data/raw/market_control/spy_minute_bars_rth.csv"
OUT = "/home/claude/luld_halt_study/data/processed/event_windows_full.csv"

POST_HORIZONS_MIN = [1, 5, 15, 30, 60]


def parse_dt(date_str, time_str):
    return datetime.strptime(date_str + " " + time_str, "%m/%d/%Y %H:%M:%S")


def load_spy():
    bars = defaultdict(list)
    with open(SPY_BARS, newline="") as f:
        for row in csv.DictReader(f):
            dt = parse_dt(row["date_et"], row["time_et"])
            bars[row["date_et"]].append((dt, float(row["open"]), float(row["close"])))
    for k in bars:
        bars[k].sort(key=lambda x: x[0])
    return bars


def bars_after(bar_list, start_dt, window_minutes):
    hi = start_dt + timedelta(minutes=window_minutes)
    return [b for b in bar_list if start_dt <= b[0] < hi]


def pct_return(p0, p1):
    if p0 is None or p1 is None or p0 == 0:
        return None
    return (p1 - p0) / p0


def main():
    print("Loading SPY bars...")
    spy = load_spy()
    print(f"SPY bars loaded for {len(spy)} dates.")

    print("Loading master events...")
    master = {}
    with open(MASTER, newline="") as f:
        for row in csv.DictReader(f):
            master[row["event_id"]] = row

    print("Loading event windows...")
    with open(EVENT_WINDOWS, newline="") as f:
        events = list(csv.DictReader(f))
    print(f"{len(events)} event-window rows loaded.")

    out_fields = list(events[0].keys()) + [
        "primary_reason_code", "category", "market", "luld_classification_confidence",
    ]
    for m in POST_HORIZONS_MIN:
        out_fields.append(f"spy_ret_{m}m")
        out_fields.append(f"abnormal_ret_{m}m")
    out_fields += ["abnormal_direction_5m", "abnormal_direction_30m",
                    "abnormal_continuation_or_reversal_5m", "abnormal_continuation_or_reversal_30m"]

    n_with_market = 0

    with open(OUT, "w", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=out_fields)
        writer.writeheader()

        for row in events:
            ev_id = row["event_id"]
            m = master.get(ev_id, {})
            row["primary_reason_code"] = m.get("primary_reason_code", "")
            row["category"] = m.get("category", "")
            row["market"] = m.get("market", "")
            row["luld_classification_confidence"] = m.get("luld_classification_confidence", "")

            resumption_dt_str = row["resumption_trade_datetime"]
            resume_dt = None
            if resumption_dt_str:
                try:
                    resume_dt = datetime.strptime(resumption_dt_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    resume_dt = None

            resumption_date = m.get("resumption_date") or row["halt_date"]
            spy_bar_list = spy.get(resumption_date, [])

            got_market = False
            spy_ref_open = None
            if resume_dt is not None and spy_bar_list:
                w1 = bars_after(spy_bar_list, resume_dt, 1)
                if w1:
                    spy_ref_open = w1[0][1]

            for hm in POST_HORIZONS_MIN:
                spy_ret = None
                abn_ret = None
                if resume_dt is not None and spy_bar_list and spy_ref_open is not None:
                    wbars = bars_after(spy_bar_list, resume_dt, hm)
                    if wbars:
                        spy_ret = pct_return(spy_ref_open, wbars[-1][2])
                        stock_ret_str = row.get(f"post_ret_{hm}m")
                        if stock_ret_str not in (None, ""):
                            try:
                                stock_ret = float(stock_ret_str)
                                abn_ret = stock_ret - spy_ret
                                got_market = True
                            except ValueError:
                                pass
                row[f"spy_ret_{hm}m"] = spy_ret
                row[f"abnormal_ret_{hm}m"] = abn_ret

            if got_market:
                n_with_market += 1

            def direction(x):
                if x is None or x == "":
                    return None
                return "up" if x > 0 else ("down" if x < 0 else "flat")

            abn5 = row.get("abnormal_ret_5m")
            abn30 = row.get("abnormal_ret_30m")
            row["abnormal_direction_5m"] = direction(abn5)
            row["abnormal_direction_30m"] = direction(abn30)

            pre_dir = row.get("pre_halt_direction") or None

            def classify(pre, post):
                if not pre or not post or pre == "flat" or post == "flat":
                    return None
                return "continuation" if pre == post else "reversal"

            row["abnormal_continuation_or_reversal_5m"] = classify(pre_dir, row["abnormal_direction_5m"])
            row["abnormal_continuation_or_reversal_30m"] = classify(pre_dir, row["abnormal_direction_30m"])

            writer.writerow(row)

    print(f"Wrote {len(events)} rows to {OUT}")
    print(f"Events with usable market-adjusted return: {n_with_market}")


if __name__ == "__main__":
    main()
