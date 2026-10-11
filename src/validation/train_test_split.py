"""
Step 6c — Chronological train/test split: are the headline findings stable
across time, or an artifact of one unusual period? Split events by
halt_datetime into the first 70% (train) and last 30% (test) chronologically,
and recompute the headline statistics on each half independently.

Also checks the time-of-day right-censoring concern: late-day halts have less
than 30 minutes of remaining trading before the 16:00 close, so their
"re-halted within 30m" flag is mechanically less likely to be True even if the
underlying propensity to re-halt is unchanged. Reports the re-halt rate
separately for late-day events with full 30-minute runway vs. those without.
"""
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

df = pd.read_csv("/home/claude/luld_halt_study/data/processed/event_windows_full.csv")
df["halt_dt"] = pd.to_datetime(df["halt_datetime"])
df = df.sort_values("halt_dt").reset_index(drop=True)

split_idx = int(len(df) * 0.7)
train = df.iloc[:split_idx]
test = df.iloc[split_idx:]
print(f"Train: {train['halt_dt'].min()} to {train['halt_dt'].max()}  (n={len(train)})")
print(f"Test:  {test['halt_dt'].min()} to {test['halt_dt'].max()}  (n={len(test)})")


def rehalt_rate(d):
    v = (d["re_halted_within_30m"].astype(str) == "True")
    n = len(v)
    s = int(v.sum())
    return s, n, s / n if n else None


def car_stats(d, col):
    vals = d[col].dropna()
    n = len(vals)
    if n < 2:
        return n, None, None
    mean = vals.mean()
    t_res = stats.ttest_1samp(vals, 0.0)
    return n, mean, t_res.pvalue


def cont_rate(d, col):
    v = d[col].dropna()
    v = v[v.isin(["continuation", "reversal"])]
    n = len(v)
    c = int((v == "continuation").sum())
    return c, n, c / n if n else None


print("\n=== Re-halt rate (headline finding #1) ===")
for name, d in [("TRAIN", train), ("TEST", test), ("FULL", df)]:
    s, n, p = rehalt_rate(d)
    print(f"  {name}: {s}/{n} = {p:.4f}" if p is not None else f"  {name}: n=0")

print("\n=== CAR 60m, all events (headline finding #2) ===")
for name, d in [("TRAIN", train), ("TEST", test), ("FULL", df)]:
    n, mean, p = car_stats(d, "abnormal_ret_60m")
    print(f"  {name}: n={n}, mean={mean:.5f}, p={p:.3e}" if mean is not None else f"  {name}: n={n} insufficient")

print("\n=== Raw continuation rate 30m (headline finding #3 - null result) ===")
for name, d in [("TRAIN", train), ("TEST", test), ("FULL", df)]:
    c, n, p = cont_rate(d, "continuation_or_reversal_30m")
    print(f"  {name}: {c}/{n} = {p:.4f}" if p is not None else f"  {name}: n=0")

print("\n=== Re-halt rate by primary_reason_code, train vs test ===")
for name, d in [("TRAIN", train), ("TEST", test)]:
    g = d.groupby("primary_reason_code").apply(
        lambda x: pd.Series({"n": len(x), "rehalt_rate": (x["re_halted_within_30m"].astype(str) == "True").mean()})
    )
    print(f"  {name}:\n{g}")

print("\n=== Right-censoring check: late-day (15:00-16:00) halts, split by whether "
      "a full 30-min runway to close (16:00) existed ===")
late = df[(df["halt_dt"].dt.hour == 15)].copy()
late["minutes_to_close"] = (late["halt_dt"].dt.normalize() + pd.Timedelta(hours=16) - late["halt_dt"]).dt.total_seconds() / 60
# also need runway from RESUMPTION time, not halt time, since the 30-min window starts at resumption
late["resume_dt"] = pd.to_datetime(late["resumption_trade_datetime"], errors="coerce")
late["runway_from_resume_min"] = (late["resume_dt"].dt.normalize() + pd.Timedelta(hours=16) - late["resume_dt"]).dt.total_seconds() / 60
full_runway = late[late["runway_from_resume_min"] >= 30]
partial_runway = late[late["runway_from_resume_min"] < 30]
for name, d in [("full 30min+ runway", full_runway), ("partial (<30min) runway", partial_runway)]:
    s, n, p = rehalt_rate(d)
    print(f"  {name}: {s}/{n} = {p}" if n else f"  {name}: n=0")
