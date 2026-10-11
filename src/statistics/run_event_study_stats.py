"""
Step 5b — Formal statistical analysis of LULD halt behavior.

Reads data/processed/event_windows_full.csv (event windows + SPY market-adjusted
returns + master-event metadata) and produces:
  - results/tables/*.csv  (every table quoted in the report, in machine-checkable form)
  - results/stats_summary.json (every headline number, with its test statistic,
    p-value, sample size and confidence interval, for citation in the report)

All tests are run on data_status == 'ok' (both pre- and post-halt bars present)
unless noted. Every percentage/mean reported includes n and, where applicable,
a 95% CI, so nothing in the final report is an unqualified point estimate.
"""
import csv
import json
import math
from collections import defaultdict, Counter
from datetime import datetime

import numpy as np
from scipy import stats

IN_PATH = "/home/claude/luld_halt_study/data/processed/event_windows_full.csv"
TABLES_DIR = "/home/claude/luld_halt_study/results/tables"
SUMMARY_PATH = "/home/claude/luld_halt_study/results/stats_summary.json"

import os
os.makedirs(TABLES_DIR, exist_ok=True)


def to_float(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def wilson_ci(successes, n, z=1.96):
    if n == 0:
        return (None, None)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def load_rows():
    with open(IN_PATH, newline="") as f:
        return list(csv.DictReader(f))


def binomial_test_summary(label, successes, n, expected_p=0.5):
    if n == 0:
        return {"label": label, "n": 0}
    result = stats.binomtest(successes, n, expected_p, alternative="two-sided")
    ci = wilson_ci(successes, n)
    return {
        "label": label,
        "n": n,
        "successes": successes,
        "proportion": successes / n,
        "ci_95_low": ci[0],
        "ci_95_high": ci[1],
        "expected_p": expected_p,
        "p_value_vs_expected": result.pvalue,
    }


def one_sample_ttest(label, values):
    values = [v for v in values if v is not None]
    n = len(values)
    if n < 2:
        return {"label": label, "n": n}
    arr = np.array(values)
    mean = float(np.mean(arr))
    se = float(np.std(arr, ddof=1) / math.sqrt(n))
    t_result = stats.ttest_1samp(arr, 0.0)
    return {
        "label": label,
        "n": n,
        "mean": mean,
        "std": float(np.std(arr, ddof=1)),
        "se": se,
        "ci_95_low": mean - 1.96 * se,
        "ci_95_high": mean + 1.96 * se,
        "t_statistic": float(t_result.statistic),
        "p_value": float(t_result.pvalue),
    }


def main():
    rows = load_rows()
    print(f"Loaded {len(rows)} event rows.")

    ok_rows = [r for r in rows if r["data_status"] == "ok"]
    print(f"data_status == 'ok': {len(ok_rows)}")

    summary = {"generated_at": datetime.utcnow().isoformat() + "Z", "n_total_events": len(rows),
               "n_ok_both_sides": len(ok_rows)}

    # ---- 1. Data status breakdown (always report this alongside any headline stat) ----
    status_counts = Counter(r["data_status"] for r in rows)
    summary["data_status_breakdown"] = dict(status_counts)

    # ---- 2. Continuation vs reversal — RAW price, 5m and 30m ----
    for horizon in ["5m", "30m"]:
        vals = [r[f"continuation_or_reversal_{horizon}"] for r in ok_rows]
        vals = [v for v in vals if v in ("continuation", "reversal")]
        n = len(vals)
        cont = sum(1 for v in vals if v == "continuation")
        summary[f"raw_continuation_rate_{horizon}"] = binomial_test_summary(
            f"raw continuation rate ({horizon})", cont, n)

    # ---- 3. Continuation vs reversal — MARKET-ADJUSTED (abnormal return), 5m and 30m ----
    for horizon in ["5m", "30m"]:
        vals = [r[f"abnormal_continuation_or_reversal_{horizon}"] for r in ok_rows]
        vals = [v for v in vals if v in ("continuation", "reversal")]
        n = len(vals)
        cont = sum(1 for v in vals if v == "continuation")
        summary[f"abnormal_continuation_rate_{horizon}"] = binomial_test_summary(
            f"market-adjusted continuation rate ({horizon})", cont, n)

    # ---- 4. Re-halt rate, overall and by reason code ----
    rehalt_vals = [r["re_halted_within_30m"] for r in ok_rows]
    n = len(rehalt_vals)
    true_n = sum(1 for v in rehalt_vals if v == "True")
    summary["rehalt_rate_overall"] = binomial_test_summary("re-halt within 30m (overall, ok rows)", true_n, n,
                                                             expected_p=0.5)
    # also report on the FULL 11,991 (re-halt detection doesn't require bar data, only event timestamps)
    rehalt_vals_full = [r["re_halted_within_30m"] for r in rows]
    n_full = len(rehalt_vals_full)
    true_n_full = sum(1 for v in rehalt_vals_full if v == "True")
    summary["rehalt_rate_full_sample"] = {
        "n": n_full, "successes": true_n_full, "proportion": true_n_full / n_full if n_full else None,
        "ci_95": wilson_ci(true_n_full, n_full),
        "note": "computed on all 11,991 events (uses only halt/resumption timestamps, not bar data)",
    }

    by_reason = defaultdict(lambda: [0, 0])
    for r in rows:
        code = r["primary_reason_code"] or "unknown"
        by_reason[code][1] += 1
        if r["re_halted_within_30m"] == "True":
            by_reason[code][0] += 1
    reason_table = []
    for code, (succ, n_) in by_reason.items():
        ci = wilson_ci(succ, n_)
        reason_table.append({"reason_code": code, "n": n_, "rehalt_rate": succ / n_ if n_ else None,
                              "ci_95_low": ci[0], "ci_95_high": ci[1]})
    summary["rehalt_rate_by_reason_code"] = reason_table
    with open(os.path.join(TABLES_DIR, "rehalt_rate_by_reason_code.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["reason_code", "n", "rehalt_rate", "ci_95_low", "ci_95_high"])
        w.writeheader()
        w.writerows(reason_table)

    # ---- 5. Cumulative abnormal return (CAR) at each horizon, all events + split by pre-halt direction ----
    horizons = [1, 5, 15, 30, 60]
    car_table = []
    for hm in horizons:
        vals = [to_float(r[f"abnormal_ret_{hm}m"]) for r in rows]
        res = one_sample_ttest(f"CAR_{hm}m_all", vals)
        res["horizon_min"] = hm
        res["subgroup"] = "all"
        car_table.append(res)

        for direction in ["up", "down"]:
            sub = [to_float(r[f"abnormal_ret_{hm}m"]) for r in rows if r["pre_halt_direction"] == direction]
            res_d = one_sample_ttest(f"CAR_{hm}m_pre_{direction}", sub)
            res_d["horizon_min"] = hm
            res_d["subgroup"] = f"pre_halt_{direction}"
            car_table.append(res_d)

    summary["car_analysis"] = car_table
    with open(os.path.join(TABLES_DIR, "cumulative_abnormal_returns.csv"), "w", newline="") as f:
        fieldnames = ["horizon_min", "subgroup", "n", "mean", "std", "se", "ci_95_low", "ci_95_high",
                      "t_statistic", "p_value"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in car_table:
            w.writerow({k: row.get(k) for k in fieldnames})

    # ---- 6. Time-of-day effect: bucket halt hour (ET), compare re-halt rate + continuation rate ----
    tod_buckets = defaultdict(lambda: {"n": 0, "rehalt": 0, "cont5": 0, "n_dir": 0})
    for r in rows:
        try:
            hdt = datetime.strptime(r["halt_datetime"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        hour = hdt.hour
        if hour < 10:
            bucket = "09:30-10:00" if hour == 9 else "10:00-11:00"
        elif hour < 11:
            bucket = "10:00-11:00"
        elif hour < 12:
            bucket = "11:00-12:00"
        elif hour < 14:
            bucket = "12:00-14:00"
        elif hour < 15:
            bucket = "14:00-15:00"
        else:
            bucket = "15:00-16:00"
        tod_buckets[bucket]["n"] += 1
        if r["re_halted_within_30m"] == "True":
            tod_buckets[bucket]["rehalt"] += 1
        if r["continuation_or_reversal_5m"] in ("continuation", "reversal"):
            tod_buckets[bucket]["n_dir"] += 1
            if r["continuation_or_reversal_5m"] == "continuation":
                tod_buckets[bucket]["cont5"] += 1

    tod_table = []
    for bucket, d in sorted(tod_buckets.items()):
        rehalt_rate = d["rehalt"] / d["n"] if d["n"] else None
        cont_rate = d["cont5"] / d["n_dir"] if d["n_dir"] else None
        tod_table.append({"time_bucket_et": bucket, "n_events": d["n"], "rehalt_rate": rehalt_rate,
                           "n_with_direction": d["n_dir"], "continuation_rate_5m": cont_rate})
    summary["time_of_day"] = tod_table
    with open(os.path.join(TABLES_DIR, "time_of_day_effects.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["time_bucket_et", "n_events", "rehalt_rate", "n_with_direction",
                                           "continuation_rate_5m"])
        w.writeheader()
        w.writerows(tod_table)

    # ---- 7. Pre-halt move magnitude vs. reversal probability (does a bigger spike predict more reversal?) ----
    magnitude_buckets = [(0, 0.05, "0-5%"), (0.05, 0.15, "5-15%"), (0.15, 0.30, "15-30%"), (0.30, float("inf"), "30%+")]
    mag_table = []
    for lo, hi, label in magnitude_buckets:
        sub = []
        for r in ok_rows:
            pre = to_float(r["pre_ret_5m"])
            crr = r["continuation_or_reversal_5m"]
            if pre is None or crr not in ("continuation", "reversal"):
                continue
            mag = abs(pre)
            if lo <= mag < hi:
                sub.append(crr)
        n_ = len(sub)
        cont = sum(1 for v in sub if v == "continuation")
        ci = wilson_ci(cont, n_) if n_ else (None, None)
        mag_table.append({"pre_halt_move_magnitude_bucket": label, "n": n_,
                           "continuation_rate": cont / n_ if n_ else None,
                           "ci_95_low": ci[0], "ci_95_high": ci[1]})
    summary["magnitude_vs_reversal"] = mag_table
    with open(os.path.join(TABLES_DIR, "magnitude_vs_reversal.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pre_halt_move_magnitude_bucket", "n", "continuation_rate",
                                           "ci_95_low", "ci_95_high"])
        w.writeheader()
        w.writerows(mag_table)

    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Wrote summary to {SUMMARY_PATH}")
    print(f"Wrote tables to {TABLES_DIR}")
    print(json.dumps({k: v for k, v in summary.items() if k in (
        "raw_continuation_rate_5m", "raw_continuation_rate_30m",
        "abnormal_continuation_rate_5m", "abnormal_continuation_rate_30m",
        "rehalt_rate_overall", "rehalt_rate_full_sample")}, indent=2, default=str))


if __name__ == "__main__":
    main()
