# LULD Plan — Rule History and Mechanics

Status: DRAFT — compiled from official sources retrieved 2026-09-18. Exact effective
dates for some amendments are approximate and flagged; before any empirical claim is
tied to a specific regime boundary, the corresponding SEC/FINRA release must be
re-verified against the primary document (listed in Sources below).

## 1. Why this document exists

LULD price bands, tier assignments, and pause mechanics have changed multiple times
since 2012. Applying today's rules to a 2014 event, or vice versa, silently corrupts
any pre-halt or band-distance feature. Every event in the master dataset must be
tagged with the rule regime in effect on its date, and every feature that depends on
band width or reference-price methodology must use that regime's parameters.

## 2. Origin

- The Limit Up-Limit Down Plan was developed by the national securities exchanges and
  FINRA in response to the May 6, 2010 "Flash Crash," replacing the older single-stock
  circuit breaker (price-and-time pilot) approach.
- Filed as an NMS Plan; approved on a pilot basis by the SEC (Release No. 34-67091,
  May 2012), later extended repeatedly, and eventually approved on a permanent basis.
  CONFIRM exact "made permanent" release/date before citing (not independently
  verified in this pass — see Open Items).

## 3. Phase-in timeline (as documented by FINRA Notice 13-12 and related releases)

| Regime | Approx. effective window | Scope |
|---|---|---|
| Phase I | April 8, 2013 (initial subset of Tier 1 securities) → full Tier 1 within ~3 months | Tier 1 NMS stocks only; Phase I band monitoring active 9:45 a.m.–3:30 p.m. ET only |
| Phase II | ~6 months after Phase I start (commonly cited as Oct 2013) | Extends to Tier 2 NMS stocks and to the full 9:30 a.m.–4:00 p.m. ET session |

CONFIRM exact calendar dates for Phase II start before using it as a hard regime
boundary in code; the "~6 months after Phase I" phrasing is from secondary
description of the Plan text, not a directly retrieved release date.

## 4. Tier definitions (current, per FINRA Notice 13-12 description)

- **Tier 1 NMS Stocks**: S&P 500 Index components, Russell 1000 Index components, and
  select exchange-traded products (ETPs).
- **Tier 2 NMS Stocks**: All other NMS stocks (common stock, etc.), excluding rights
  and warrants, that are not Tier 1.
- Tier lists are reconstituted periodically (index reconstitution) — a stock's tier
  can change over the life of the study. Point-in-time tier assignment, not current
  tier, must be used for every event.

### 4.1 Twenty-Third Amendment (2023) — ETP tier reclassification

Per SEC Release No. 34-98928 (2023): almost all ETPs move to Tier 1 (single-stock
ETPs excepted, which take the tier of their underlying, adjusted for leverage); the
$2M consolidated-average-daily-volume eligibility threshold for Tier 1 ETPs is
eliminated; most Tier 2 ETPs move from 10% to 5% bands (above $3.00). Effective date
was set by subsequent Participant announcement after Commission approval — CONFIRM
the actual implementation date reached market before treating any date as the
boundary; not retrieved in this pass.
This amendment affects ETP events (which the primary LULD study for common stock
excludes; see `universe_exclusion_log.csv`) more than common stock, but is recorded
here for completeness and because it signals a live evaluated rule (band widths
inside)

## 5. Price bands (as documented by FINRA Notice 13-12; treat as the baseline
"current-at-2013" regime — CONFIRM whether later amendments changed these
percentages for the periods actually covered by the study sample)

Reference price = mean price of regular-way, last-sale-eligible trades over the
immediately preceding 5-minute period (rolling).

| Tier | Reference price | Band (% of reference price) |
|---|---|---|
| Tier 1 | > $3.00 | 5% |
| Tier 1 | $0.75–$3.00 | 20% |
| Tier 1 | < $0.75 | lesser of $0.15 or 75% |
| Tier 2 | > $3.00 | 10% |
| Tier 2 | $0.75–$3.00 | 20% |
| Tier 2 | < $0.75 | lesser of $0.15 or 75% |

Leveraged ETPs: percentages multiplied by the product's leverage ratio.

### 5.1 Double-wide bands

Band widths are doubled during:
- The opening period: 9:30–9:45 a.m. ET
- The closing period: 3:35–4:00 p.m. ET (or the final 25 minutes of the session on an
  early-close day)

Phase I (initial rollout) monitored bands only 9:45 a.m.–3:30 p.m. ET; Phase II
extended monitoring to the full 9:30 a.m.–4:00 p.m. ET session, which is what makes
the opening/closing double-wide-band provisions meaningful in the first place.
CONFIRM this Phase I/II distinction against the primary Plan text (paraphrased from
secondary description here) before relying on it for pre-Phase-II events, which in
practice will mostly be excluded by the "at least 5 years" sourcing constraint below.

## 6. Limit State and trading pause mechanics

1. When the National Best Bid (or Offer) breaches the applicable band, the SIP marks
   that quotation "non-executable" — this is a **Limit State** on one side.
2. If the opposite side's quotation *also* reaches its band while the first side is
   still in a Limit State, this is sometimes referred to distinctly (straddle
   condition — see `LUDS` halt code).
3. A Limit State that persists uninterrupted for 15 seconds (i.e., not resolved by all
   limit-state quotations executing or being canceled) triggers a **trading pause**,
   declared by the primary listing exchange.
4. The trading pause is a 5-minute halt of trading (quotes may still be displayed; no
   trades execute) in that single security.
5. **Straddle state**: price moves outside the band on the *opposite* side from an
   active Limit State without 15 continuous seconds in a Limit State first — this can
   also trigger a pause (`LUDS` code).

## 7. Reopening procedure

- After the 5-minute pause, the primary listing exchange reopens the security via its
  standard reopening auction/procedure.
- If the primary market cannot reopen the security within 10 minutes of the pause
  being declared, other trading centers may begin trading it (subject to Plan
  provisions) — CONFIRM the exact mechanics and any exceptions before encoding
  "resume timestamp" logic; the retrieved summary only establishes the 10-minute
  threshold exists, not the full procedural detail.
- The reopening (auction) price becomes the new reference price going forward.

## 8. Historical amendments not yet independently verified in this pass

The Plan has been amended more than 20 times since 2012 (informal count based on
"Twenty-Third Amendment" being current as of the 2023 release retrieved above).
Amendments the project should specifically research and date before drawing
conclusions that span multiple years:
- Any amendment altering band percentages for Tier 1/Tier 2 common stock (as opposed
  to ETPs) within the study period.
- The "made permanent" (pilot → permanent Plan) approval date.
- Any amendment altering the 15-second Limit State timer, or the 5-minute pause
  duration itself.
- Any change to reopening-auction mechanics.

## 9. Methodological consequence for this study

- Every event in `luld_master_events.csv` must carry a `rule_regime_id` field mapping
  to a row in a (to-be-built) `config/luld_rule_regimes.csv` table, itself built only
  from primary-source effective dates, not the approximations above.
- No band-distance or tier-dependent feature is computed until that regime table is
  built and every approximate date above is either confirmed or the event is dropped
  from band-distance analysis and flagged `LOW CONFIDENCE — rule regime unconfirmed`.

## Sources (retrieved 2026-09-18)

- FINRA Regulatory Notice 13-12 — https://www.finra.org/rules-guidance/notices/13-12
- SEC Release No. 34-98928 (Twenty-Third Amendment to the LULD NMS Plan) —
  https://www.sec.gov/files/rules/sro/nms/2023/34-98928.pdf
- SEC DERA working papers on LULD (for later deeper review, not yet fully read):
  - https://www.sec.gov/files/marketstructure/research/dera_wp_the_effect_of_amendment_10_of_the_luld_plan.pdf
  - https://www.sec.gov/files/marketstructure/research/dera_wp_luld_and_extraordinary_transitory_volatility.pdf
  - https://www.sec.gov/files/dera-luld-white-paper.pdf
- NASDAQ Trading Halt Codes reference (for Section 2 of halt_type_dictionary.csv) —
  https://www.nasdaqtrader.com/trader.aspx?id=tradehaltcodes

## Open items (must close before any publication-quality claim)

- [ ] Confirm Phase I / Phase II exact calendar dates from primary Plan text or SEC
      approval order, not secondary paraphrase.
- [ ] Confirm pilot → permanent approval date.
- [ ] Enumerate all amendments 1–23 with effective dates (at minimum, all amendments
      whose effective window overlaps the study's actual sample period once that
      period is finalized in `DATA_SOURCE_PLAN.md`).
- [ ] Confirm whether Tier 1/Tier 2 *common stock* band percentages changed at any
      point 2013–present (Amendment 23 only touched ETPs).
