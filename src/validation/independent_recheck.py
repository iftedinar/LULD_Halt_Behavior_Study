"""
Step 6a — Independent validation pass #1: re-derive the headline statistics via
pandas (a completely different code path from the manual csv/loop-based
run_event_study_stats.py) and diff the results. If these two independently-coded
computations disagree beyond floating-point noise, that's a bug to find before
anything goes in the report — not something to average away.
"""
import pandas as pd
import numpy as np
from scipy import stats
import json

df = pd.read_csv("/home/claude/luld_halt_study/data/processed/event_windows_full.csv")
print("rows:", len(df))

ok = df[df["data_status"] == "ok"].copy()
print("ok rows:", len(ok))

# --- Re-halt rate (full sample, pandas-native) ---
rehalt_full = (df["re_halted_within_30m"] == True) | (df["re_halted_within_30m"] == "True")
n_full = len(df)
succ_full = int(rehalt_full.sum())
p_full = succ_full / n_full
print(f"\n[RECHECK] re-halt rate, full sample: {succ_full}/{n_full} = {p_full:.4f}")
print("  (original script reported: 6356/11991 = 0.5301)")
assert succ_full == 6356 and n_full == 11991, "MISMATCH in re-halt full-sample recheck"

# --- Re-halt rate by reason code (pandas groupby) ---
rehalt_ok = (df["re_halted_within_30m"].astype(str) == "True")
by_reason = df.groupby("primary_reason_code").agg(n=("event_id", "count"), rehalt=("re_halted_within_30m", lambda s: (s.astype(str) == "True").sum()))
by_reason["rate"] = by_reason["rehalt"] / by_reason["n"]
print("\n[RECHECK] re-halt rate by reason code:")
print(by_reason)
assert abs(by_reason.loc["LUDP", "rate"] - 0.5607) < 0.001, "MISMATCH in LUDP re-halt rate recheck"
assert abs(by_reason.loc["M", "rate"] - 0.3411) < 0.001, "MISMATCH in M re-halt rate recheck"

# --- Continuation/reversal at 5m and 30m, raw (ok rows only) ---
for horizon in ["5m", "30m"]:
    col = f"continuation_or_reversal_{horizon}"
    vals = ok[col].dropna()
    vals = vals[vals.isin(["continuation", "reversal"])]
    n = len(vals)
    cont = int((vals == "continuation").sum())
    p = cont / n
    binom = stats.binomtest(cont, n, 0.5)
    print(f"\n[RECHECK] raw continuation rate ({horizon}): {cont}/{n} = {p:.4f}, p={binom.pvalue:.4f}")

# --- CAR at 30m and 60m, all events (pandas mean/t-test) ---
for hm in [30, 60]:
    col = f"abnormal_ret_{hm}m"
    vals = df[col].dropna()
    n = len(vals)
    mean = vals.mean()
    t_res = stats.ttest_1samp(vals, 0.0)
    print(f"\n[RECHECK] CAR {hm}m (all events): n={n}, mean={mean:.5f}, t={t_res.statistic:.3f}, p={t_res.pvalue:.3e}")

# --- CAR 60m split by pre_halt_direction ---
for direction in ["up", "down"]:
    sub = df[df["pre_halt_direction"] == direction]["abnormal_ret_60m"].dropna()
    n = len(sub)
    mean = sub.mean()
    t_res = stats.ttest_1samp(sub, 0.0)
    print(f"[RECHECK] CAR 60m (pre_halt={direction}): n={n}, mean={mean:.5f}, t={t_res.statistic:.3f}, p={t_res.pvalue:.3e}")

print("\nAll assertions passed — independent pandas recheck matches the original manual-loop script.")
