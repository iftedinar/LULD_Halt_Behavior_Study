# What Happens After a Volatility Halt? Evidence From Confirmed LULD Events in U.S. Equities

*An intraday event study of 10,320 confirmed LULD trading pauses across 1,650 symbols, September 2025–September 2026*

## Abstract

I built an event-study dataset of 11,991 U.S. equity trading pauses triggered by the Limit Up-Limit Down (LULD) mechanism over a 12-month period, of which 10,320 are confirmed LULD pauses. Using 1-minute price bars and SPY as a market benchmark, I measured re-halt probability, post-reopen returns, and continuation versus reversal behavior. After correcting for two things naive event studies often get wrong — treating repeated halts of the same stock on the same day as independent observations, and multiple-hypothesis testing across subgroups — I find a materially smaller re-halt probability than a first pass suggested (roughly one in three, not one in two), a genuine and dependence-robust negative post-reopen drift concentrated in confirmed LULD events, and an initially promising subgroup result that did not survive stricter testing. This is a descriptive, observational study, not a trading strategy.

## Introduction

I've been curious about LULD halts since I started paying closer attention to intraday volatility in small- and mid-cap names. A stock gets halted, trading pauses for a few minutes, and then it reopens — sometimes calmly, sometimes into another halt within seconds. I wanted to know what the data actually says about what happens next, rather than relying on trading-forum folklore. So I built a full pipeline: collect halt records, pair them with 1-minute price data, benchmark against SPY, and run the statistics properly.

I also want to be upfront about something: my first pass at this analysis had real methodological gaps, and I caught most of them myself during a second, more adversarial audit of my own work. That process changed some of my headline numbers — in one case fairly dramatically — and I think "here's what I initially found, and here's what held up under scrutiny" is a more honest way to share research than presenting only the final polished numbers.

## Research Questions

1. How likely is a halted stock to halt again within 30 minutes of reopening, once you account for the fact that many halts on the same stock on the same day are not independent events?
2. How does price behave, on average and typically, in the hour after a halt reopens, relative to the broader market?
3. Does the direction of the pre-halt move predict what happens after reopening?
4. Does the size of the pre-halt move matter, and does that result hold up to a multiple-testing check?

## Data

I collected 11,991 deduplicated LULD-related halt events from NASDAQ's halt-search records, spanning September 18, 2025 through September 18, 2026, across 1,650 unique symbols. Of these, 10,320 (86%) carry a confirmed primary LULD-pause code; the remaining 1,671 carry an uncertain market-wide/other code and are analyzed separately rather than pooled in. I matched each event to 1-minute OHLCV bars (677,836 bars total) for the halted symbol and for SPY, before and after the halt.

Two sample sizes show up throughout this study, and I want to name them clearly rather than let a reader wonder why the N changes: 7,501 events have at least one usable post-halt price bar (this is the population behind every return statistic), and a stricter subset of 7,327 events has usable bars on *both* sides of the halt (needed for anything that depends on the pre-halt direction). Both are correct; they're just answering slightly different questions.

## Methodology

For each halt, I computed the raw return and a market-adjusted return (raw return minus SPY's return over the same window) at 1, 5, 15, 30, and 60 minutes after reopening. I want to be precise about what "market-adjusted" means here: it reduces the influence of contemporaneous broad-market movements on the measured return. It does not isolate a causal effect of the halt itself, and this is an observational study throughout — I'm describing associations, not claiming the halt *caused* anything.

The part I initially underweighted: 11,991 events sit on only 4,695 unique symbol-days, and a small number of extremely volatile symbol-days account for a disproportionate share of the data (57% of all events come from symbol-days with 4 or more halts; the max in one symbol-day was 45). Treating every event as statistically independent inflates confidence and can distort rates. So for every headline number, I computed it three ways: pooled/naive (the simple approach), a symbol-day cluster bootstrap (resampling whole symbol-days, not individual events, 2,000 times), and a "first halt of the symbol-day only" subsample that is close to genuinely independent. I lead with the dependence-aware version throughout.

I also checked the ≥30%-pre-halt-move subgroup (more on this below) for multiple-testing exposure using a Benjamini-Hochberg false discovery rate correction across the four magnitude buckets I'd defined, since those bucket boundaries were set in the same script that produced the result rather than pre-registered ahead of time.

## Results

**1. Re-halt probability within 30 minutes — smaller than it first looked.** A naive, pooled count says a confirmed LULD event halts again within 30 minutes 56.1% of the time (n=10,320). But once I restrict to one independent observation per symbol-day, and separately correct for the fact that halts reopening late in the day mechanically have less time to "prove" a re-halt before the market closes, the picture changes: the most defensible estimate is **33.1%** (95% CI 31.7%–34.5%, n=4,460) — roughly one in three, not "more likely than not." I think this is the most important correction in the whole study, and I'd rather report the smaller, better-supported number than the larger, flashier one.

**2. Post-reopen returns are negative on average, specifically for confirmed LULD events, and the typical outcome is worse than the average.** For confirmed LULD events with usable price data (n=6,838), the market-adjusted return one hour after reopening averages −3.30%. But the *median* is −5.24% — more negative than the mean — and that gap between mean and median widens the longer you wait after reopening. That's a right-skewed distribution: a relatively small number of big positive outcomes pull the average up, while the typical stock did worse than the average alone would suggest.

| Horizon | Eligible N | Mean market-adjusted return | Median market-adjusted return | IQR | Positive return % |
|---|---|---|---|---|---|
| 1m | 6,838 | −0.09% | −0.01% | [−3.61%, 3.14%] | 48.7% |
| 5m | 6,838 | −0.91% | −0.43% | [−7.00%, 4.11%] | 43.7% |
| 15m | 6,838 | −1.74% | −2.34% | [−11.15%, 5.70%] | 40.9% |
| 30m | 6,838 | −2.43% | −3.69% | [−14.03%, 6.48%] | 38.9% |
| 60m | 6,838 | −3.30% | −5.24% | [−17.10%, 6.65%] | 37.4% |

I also checked whether this drift is robust to the dependence problem above, and it is — the estimate barely moves whether I use the naive pooled sample or the independent-only subsample (−2.93% vs. −2.92% at 60 minutes, all-events basis). That gives me real confidence in this finding specifically, separate from the re-halt-rate correction above.

One thing I hadn't expected: the drift is specific to confirmed LULD events. The 1,671 uncertain-coded (M/other) events show a small, *positive*, and not statistically significant average 60-minute return (+0.91%, 95% CI −1.0% to +2.9%). That's a genuinely different result from the LULD-specific finding, and it's a good example of why I split confirmed LULD out as the primary sample rather than pooling everything together.

**3. Direction after reopening was not predictable from pre-halt direction alone — with one caveat.** In the pooled sample, 48.8% of eligible events continued in the same direction they were already moving before the halt (n=5,878, 95% CI 47.5%–50.0%) — a clean null, statistically indistinguishable from a coin flip. Restricted to the independent (first-halt-per-symbol-day) subsample, continuation drops to 44.4% (95% CI 42.4%–46.4%, excluding 50%) — a mild reversal tendency the pooled, dependent sample was masking. I'm reporting both: no strong universal pattern, with a smaller, more careful subsample hinting at something worth testing further.

**4. The "large pre-halt move" subgroup looked promising and didn't hold up.** I initially found that halts preceded by a ≥30% pre-halt price move showed a higher continuation rate (58.1%, n=227) than smaller pre-halt moves. That's an appealing, intuitive story — a huge move plus a halt equals more move to come. But I'd defined four magnitude buckets from the same data that produced this result, without pre-registering the 30% cutoff, so I ran a multiple-testing correction across all four buckets. After that correction, the finding's significance level (q=0.067) crosses the conventional 0.05 threshold. It also doesn't survive the independence check — restricted to first-halt-only events, the confidence interval widens to include 50% entirely. I'm reporting this as an **exploratory, unconfirmed** result rather than a finding, and I think that's the right call even though it's the less exciting version of the story.

**5. Time-of-day patterns were mostly a measurement artifact, not a real effect — except at the very close.** A first look suggested halts near market close were much less likely to re-halt (35.3%) than midday halts (~60%). That gap almost entirely disappears once I correct for the fact that a 3:45pm halt simply doesn't have 30 minutes left in the trading day to show a re-halt: the corrected close-hour rate is 53.8% (n=385, restricted to halts with a genuine 30-minute runway before the close), compared to ~60% at midday. There's still a modest residual difference, but it's a fraction of what the naive numbers suggested — a good example of why I think the censoring check mattered.

## Robustness and Validation

Every finding above went through the same treatment: naive/pooled, cluster-bootstrap (accounting for symbol-day correlation), and a first-halt-per-symbol-day independent subsample. A chronological 70/30 split of the study period showed the confirmed-LULD re-halt rate nearly identical in the earlier period (56.07%, n=8,393) and the later period (56.06%, n=3,598) — a good stability signal, though this is a within-study temporal check, not a true out-of-sample test on new data. Finally, I independently re-derived every headline number using a second, completely separate piece of code as a final accuracy check before publishing, and everything matched within 0.1 percentage points.

## Limitations

This study covers one 12-month period and may not generalize to other volatility regimes. It uses 1-minute price bars, not tick data, so it cannot reconstruct exact tick-level halt-triggering mechanics and makes no second-by-second claims. There is no execution model — no spread, slippage, fee, or fill-probability estimate — so nothing here should be read as a statement about what's achievable in a live trade. I don't have float, market cap, or news-catalyst data (SEC EDGAR's APIs were unreachable from my research environment, and I decided not to substitute a lower-integrity workaround). The return-eligible sample is predominantly NASDAQ-reported and somewhat skewed toward chronically re-halting names, so these findings describe that specific population, not "all LULD halts" everywhere. And even after my dependence corrections, some residual correlation between halts likely remains; a fully specified statistical model could refine this further.

## Implications for Intraday Risk Research

I want to be direct about what this study is not: it's not a trading strategy, and I'm not going to suggest one. There's no execution model here, so I can't translate a historical average or median return into anything about what's actually achievable after accounting for real spreads, slippage, and fill risk at the reopen. What I think is genuinely useful for anyone researching intraday risk is the shape of the findings: the post-reopen drift is concentrated in confirmed LULD events specifically, not uncertain-coded halts; the distribution of outcomes is right-skewed, meaning the typical outcome is somewhat worse than the average suggests; and the re-halt probability, once you handle dependence and censoring properly, is meaningfully lower than a first pass would tell you. Those are useful inputs to a risk model, not instructions for a trade.

## Discussion

I think the most interesting part of this project ended up being the corrections themselves. A naive pass would have reported that a halted stock is *more likely than not* to halt again shortly after reopening, and that large pre-halt moves reliably predict continuation — both sounded good, and both weakened once I checked for dependence and multiple testing. A null or non-significant result isn't a failure here: the pooled continuation-rate finding (48.8%, indistinguishable from 50%) and the downgraded magnitude subgroup are both valid, informative outcomes that tell me where the data doesn't support a clean story.

## Conclusion

Confirmed LULD halts in this sample show a real, dependence-robust negative average return in the hour after reopening, with a typical (median) outcome somewhat worse than the mean. The probability of halting again within 30 minutes, once measured carefully, is closer to one in three than one in two. A promising-looking subgroup result around large pre-halt moves did not survive stricter testing and is reported as exploratory. None of this establishes a trading edge — it establishes a set of descriptive, statistically careful facts about how this specific, well-documented sample of U.S. equity volatility halts behaved over one 12-month period.

## Data and Code Availability

My analysis code and the aggregated statistical tables behind every number in this article are available on request. The underlying raw NASDAQ halt-search records and per-symbol 1-minute price bars are not redistributable under the data provider's terms of service, so I'm not able to share the raw dataset itself — only the derived, aggregated results.

## Disclaimer

This is an independent research project for educational purposes, not investment advice. Nothing here should be used as the basis for a trading or investment decision.
