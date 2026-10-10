# LULD Halt Behavior Study — Corrected Final Report

**Study period:** 2025-09-18 to 2026-09-18 (approximately 12 months)
**Status:** Corrected and validated following a full pre-publication audit (17 issues; see `audit/PRE_PUBLICATION_CORRECTION_AUDIT.md`). This report supersedes all prior drafts of the "Full Research Report."

---

## 1. Overview

This study examines the behavior of U.S.-equity trading pauses triggered by the Limit Up-Limit Down (LULD) mechanism: how likely a halted stock is to halt again shortly after reopening, how its price behaves relative to the broader market in the hour after resumption, and whether the direction of the pre-halt move predicts what happens afterward. It is an observational, descriptive event study — not a backtest, not a trading strategy, and not a causal analysis of the halt mechanism itself.

**Total halt records collected:** 11,991 paired/deduplicated halt events across 1,650 unique symbols and 4,695 unique symbol-days, drawn from 27,682 raw NASDAQ halt-search rows (pre-deduplication). Of the 11,991 events, 10,320 (86.1%) are confirmed primary LULD pauses (`LUDP`); 1,671 (13.9%) carry an uncertain market-wide/other code (`M`) that is not independently confirmed as LULD-specific.

**Primary analysis sample:** Confirmed LUDP events. All-events statistics are reported as secondary/contextual and always labeled as such (see §3, Issue 4 of the audit).

## 2. Data and Methodology

### 2.1 Data sources
- NASDAQ trading-halt search results (raw halt records), paired into a deduplicated master event database.
- 1-minute OHLCV bars (677,836 rows) for halted symbols and SPY, covering the pre-halt and post-halt windows around each event.
- SPY used as the market benchmark for return adjustment.

### 2.2 Sample-size populations (reconciled — Issue 1)

| Population | N | Used for |
|---|---|---|
| All halt events (master) | 11,991 | Sample description, re-halt-rate denominators |
| Confirmed LUDP | 10,320 | Primary re-halt-rate analysis |
| Post-halt-bar-eligible | 7,501 | All post-return / market-adjusted-return (CAR) statistics |
| Both-sides-eligible (`data_status == 'ok'`) | 7,327 | Continuation/reversal classification, pre-halt-direction-dependent statistics |
| Confirmed LUDP ∩ post-halt-bar-eligible | 6,838 | Primary return-distribution statistics |

Full funnel: `results/tables/SAMPLE_FLOW_AUDIT.csv`.

### 2.3 Market-adjusted return
Post-halt return at horizon *h*, minus SPY's contemporaneous return over the same window: `abnormal_ret_h = post_ret_h − spy_ret_h`. This **reduces the influence of contemporaneous broad-market movements** on the measured return — it does not isolate or establish a causal effect of the halt itself, and this study makes no causal claim about the halt mechanism.

### 2.4 Dependence structure
Halt events are not independent draws: 4,695 unique symbol-days underlie 11,991 events (57% of events come from symbol-days with 4+ halts, max 45 in one symbol-day). Every headline inferential statistic in this report is computed three ways — naive/pooled, symbol-day cluster bootstrap (2,000 resamples), and first-halt-per-symbol-day-only (an approximately independent subsample) — and the dependence-aware treatment is what is emphasized. Full detail: `audit/DEPENDENCE_ROBUSTNESS.md`.

### 2.5 Right-censoring
A halt reopening late in the trading day mechanically has less time remaining before the 16:00 close to "prove" a re-halt within a fixed 30-minute window. All re-halt-rate statistics are also reported restricted to events with a full, observable 30-minute runway before the close. Full detail: audit Issue 8/13.

## 3. Results

All figures below are **confirmed-LUDP-primary**, with all-events sensitivity noted where it differs materially. See `audit/PRE_PUBLICATION_CORRECTION_AUDIT.md` for the complete derivation and every intermediate number.

### 3.1 Re-halt probability within 30 minutes

| Treatment | N | Re-halt rate | 95% CI |
|---|---|---|---|
| Naive/pooled, Confirmed LUDP | 10,320 | 56.07% | [55.11%, 57.02%] |
| Naive/pooled, all events | 11,991 | 53.01% | [52.11%, 53.90%] |
| First-halt-per-symbol-day only, Confirmed LUDP | 3,675 | 36.27% | [34.73%, 37.84%] |
| First-halt-per-symbol-day only, all events | 4,695 | 31.80% | — |
| Full 30-min runway only, all events | 11,369 | 54.60% | [53.68%, 55.51%] |
| **Combined (first-halt AND full 30-min runway), all events — most conservative estimate** | **4,460** | **33.07%** | **[31.71%, 34.47%]** |

The naive pooled re-halt rate (53–56%) is substantially inflated by repeat-halt dependence: a relatively small number of chronically re-halting symbol-days are counted many times over. Once restricted to one independent observation per symbol-day and adjusted for the fact that late-day halts have less time to show a re-halt, the best-supported estimate is roughly **one in three** halted symbols halting again within 30 minutes — not "more likely than not."

### 3.2 Post-reopen returns: mean and median, Confirmed LUDP (market-adjusted vs. SPY)

| Horizon | N | Mean | Median | IQR (Q1, Q3) | Positive % |
|---|---|---|---|---|---|
| 1m | 6,838 | −0.09% | −0.01% | [−3.61%, 3.14%] | 48.7% |
| 5m | 6,838 | −0.91% | −0.43% | [−7.00%, 4.11%] | 43.7% |
| 15m | 6,838 | −1.74% | −2.34% | [−11.15%, 5.70%] | 40.9% |
| 30m | 6,838 | −2.43% | −3.69% | [−14.03%, 6.48%] | 38.9% |
| **60m** | **6,838** | **−3.30%** | **−5.24%** | **[−17.10%, 6.65%]** | **37.4%** |

All-events figures (n=7,501) are similar in shape but slightly smaller in magnitude (60m: mean −2.93%, median −4.80%) — the negative drift is specifically a **Confirmed-LUDP** result. By contrast, the M/other (uncertain-code) subgroup (n=663) shows a small, **statistically non-significant positive** mean 60-minute return (+0.91%, 95% CI [−1.04%, +2.86%], p=0.36) — the opposite sign, previously unreported. This CAR finding is robust to the dependence correction (naive −2.93% vs. first-halt-only −2.92% at 60m, all events).

**The median is more negative than the mean from the 15-minute horizon onward**, and the gap widens with horizon. This indicates a right-skewed distribution: a relatively small number of large positive outliers pull the mean up, while the typical (median) outcome is worse than the mean alone suggests.

### 3.3 Continuation vs. reversal (30-minute horizon)

Raw continuation rate, all events: 48.76% (n=5,878, 95% CI [47.48%, 50.04%], p=0.059 vs. 50%) — a **null result** under the pooled/primary treatment: pre-halt direction alone did not predict continuation in this sample. A secondary, correctly-caveated nuance: restricted to the first-halt-per-symbol-day-only subsample (n=2,337, approximately independent), continuation falls to 44.37% (95% CI [42.37%, 46.40%] — excludes 50%), suggesting a small reversal tendency that the pooled/dependent analysis masks. Both results are reported; neither is stated as a universal predictive claim.

### 3.4 Pre-halt magnitude subgroup (≥30% pre-halt move) — EXPLORATORY, not confirmed

| Bucket | N | Continuation rate | 95% CI | Status |
|---|---|---|---|---|
| 0–5% | 297 | 50.5% | [44.8%, 56.1%] | not significant |
| 5–15% | 3,524 | 49.8% | [48.2%, 51.5%] | not significant |
| 15–30% | 1,483 | 49.0% | [46.5%, 51.6%] | not significant |
| 30%+ | 227 | 58.1% | [51.6%, 64.4%] | raw p=0.017, but **BH-FDR q=0.067 (fails at 0.05)** |
| 30%+, first-halt-only (n=183) | 183 | 54.1% | [46.9%, 61.2%] (includes 50%) | fails independence check |

This subgroup was flagged in earlier drafts as a "robust association." Under a formal multiple-testing correction across the four buckets and a check for repeat-halt dependence, **it does not survive either test** and is downgraded to explicitly labeled EXPLORATORY — a hypothesis worth pre-registered testing in future work, not a confirmed finding.

### 3.5 Time-of-day patterns, censoring-corrected

| Hour (ET) | Unrestricted rate | Full-runway-corrected rate |
|---|---|---|
| 09:30–10:00 | 45.6% (n=3,136) | 45.6% (n=3,135) |
| 10:00–11:00 | 55.4% (n=2,677) | 55.4% (n=2,676) |
| 11:00–12:00 | 59.8% (n=1,745) | 59.9% (n=1,742) |
| 12:00–14:00 | 59.9% (n=2,441) | 59.9% (n=2,439) |
| 14:00–15:00 | 58.8% (n=995) | 58.8% (n=992) |
| 15:00–16:00 | 35.3% (n=997) | **53.8% (n=385)** |

Once corrected for the shrinking observation window near the close, the apparent "close-hour halts are safest" pattern almost entirely disappears — it was largely a censoring artifact. Some residual difference remains at the close (53.8% vs. ~60% midday), but the gap shrinks from 24.6 percentage points to about 6. "Midday is the riskiest hour" is therefore stated only as a modest, censoring-corrected observation, not a dramatic effect.

### 3.6 Maximum favorable/adverse excursion (MFE/MAE), Confirmed LUDP (n=6,838)

One-minute-bar excursion estimates — **not executable P&L** (no accounting for actual fill price, spread, slippage, or size).

| Horizon | MFE mean / median | MAE mean / median |
|---|---|---|
| 5m | +6.19% / +4.49% | −6.61% / −5.69% |
| 15m | +10.64% / +7.20% | −11.22% / −9.52% |
| 30m | +14.43% / +8.92% | −14.74% / −12.15% |
| 60m | +18.75% / +10.50% | −18.05% / −14.76% |

Both favorable and adverse excursions widen substantially with horizon, and — consistent with §3.2 — median excursions are meaningfully smaller in magnitude than mean excursions, again pointing to a right-skewed, outlier-influenced distribution of outcomes.

## 4. Robustness and Validation

- **Dependence-aware inference** (cluster bootstrap, first-halt-only): confirms the CAR/drift finding is robust; confirms the re-halt-rate finding requires substantial downward revision; confirms the ≥30% magnitude finding does not survive.
- **Right-censoring correction**, extended across the full trading day, not just the close hour: explains the apparent close-hour dip almost entirely, and is itself a validation of the study's methodology (a naive artifact was found and corrected, not missed).
- **Missing-data / selection-bias audit**: the return-eligible sample is predominantly NASDAQ-reported (BATS and NYSE Arca halts are 12–61× underrepresented relative to their share of excluded events), skews away from the final trading hour, and skews toward chronically re-halting symbol-days. Findings are stated for this specific population, not generalized to "all LULD halts." Full detail: `audit/MISSING_DATA_SELECTION_BIAS.md`.
- **Chronological (70/30) stability check**: Confirmed-LUDP re-halt rate is nearly identical in the early (56.07%, n=8,393) and late (56.06%, n=3,598) sub-periods of the study window — a strong stability signal for the primary finding. Labeled a within-study chronological check, not an independent out-of-sample test. Full detail: `audit/CHRONOLOGICAL_STABILITY_CHECK.md`.
- **Independent accuracy certification**: every headline metric above was independently re-derived with a second, non-pandas implementation and passed at a 0.1-percentage-point tolerance. Full detail: `audit/FINAL_ACCURACY_CERTIFICATION.md`.
- **A genuine data-integrity bug** (a pandas CSV-parsing pitfall affecting the literal ticker "NA") was found and fixed during this audit, and is documented in full as part of the audit trail — see the "Zero-th finding" in `audit/PRE_PUBLICATION_CORRECTION_AUDIT.md`.

## 5. Limitations

- **Single ~12-month study period.** Findings may not generalize to other market regimes, volatility environments, or regulatory periods.
- **1-minute bars, not tick data.** Cannot reconstruct exact tick-level LULD band-breach timing and does not guarantee the reopening print was executable at the stated reference price; no second-by-second claim is made anywhere in this study.
- **No execution model.** No entry-timing, spread, slippage, fee, or liquidity model exists. MFE/MAE are descriptive path-risk estimates from bar highs/lows, not tradeable outcomes.
- **No float/market-cap data**, and no SEC EDGAR catalyst tagging — EDGAR's APIs were confirmed unreachable from this project's network access (tested directly, not assumed), and no current float/market-cap figure is substituted for a historical one, nor is any catalyst inferred from price action alone.
- **Non-random missingness** in the return-eligible sample: predominantly NASDAQ-reported, under-represents the final trading hour and BATS/NYSE-Arca-reported halts, and over-represents chronically re-halting symbol-days.
- **Repeated-event dependence**, even after correction: the cluster-bootstrap and first-halt-only treatments reduce but do not perfectly eliminate residual within-symbol-day correlation structure that a fully specified mixed-effects or GEE model could further refine.
- **Uncertain M-code events** are not independently confirmed as LULD-specific; they are reported separately, not pooled into the primary sample.
- **Observational design; market-adjusted is not causal.** No claim is made that a halt *causes* any subsequent price behavior.
- **The ≥30% pre-halt-move subgroup did not survive multiple-testing or dependence correction** and is reported only as an exploratory, unconfirmed hypothesis.

## 6. Practical Interpretation — Risk and Market-Microstructure Implications

This study describes historical statistical associations in a specific, well-documented sample of U.S. equity LULD halts. It is not a trading strategy, and no buy/short/fade/chase/position-sizing recommendation follows from it, because no execution model, transaction-cost estimate, or liquidity model exists to translate a historical average or median return into an actionable, risk-adjusted trade. Readers interested in market microstructure may find the following observations useful as research questions rather than trading rules: the post-reopen drift is concentrated in confirmed LULD-coded events and not in uncertain-coded events; the drift's distribution is right-skewed, meaning typical outcomes are somewhat worse than the mean average suggests; and the raw re-halt probability, once corrected for dependence and censoring, is meaningfully lower than a naive pooled count would suggest.

## 7. Data and Code Availability

The analysis code (`src/`, including the full audit pipeline `src/audit/pre_publication_audit.py` and the independent verification script `src/audit/independent_accuracy_check.py`) and the aggregated, publication-safe statistical tables (`results/tables/*.csv`) referenced throughout this report are available on request. The underlying raw NASDAQ halt-search records and raw per-symbol 1-minute price bars are **not** redistributable under the data source's terms of service and are not shared beyond this project's internal research use; only the derived, aggregated statistics in this report and its supporting tables are shareable.

## 8. Disclaimer

This report is a student/independent research project for educational and portfolio purposes. It is not investment advice, and nothing in it should be used as the basis for a trading or investment decision. Past statistical associations do not predict future returns, and this study does not establish that any strategy based on LULD halts would be profitable after accounting for real-world execution costs and risks.
