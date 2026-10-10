# Study — LULD Halt Behavior

Intraday event study of LULD volatility trading pauses: pre-halt conditions,
reopening behavior, continuation, reversal, and re-halt probability in U.S. equities.

This is a separate research project from the main Trade100 app — nothing here touches
the `trade100-deploy-v26` codebase.

## Current status: architecture + feasibility phase (see `PROJECT_STATUS.md`)

Before any event data was collected, this pass established what data this environment
can actually reach. **The short version: there is no accessible source, free or
already-connected, for multi-year historical LULD halt records or tick/second-level
market data.** `DATA_SOURCE_PLAN.md` documents every source checked and the evidence
for that conclusion. `PROJECT_STATUS.md` lays out the realistic paths forward and asks
for a decision on which to take, since it involves either spending money on a data
vendor or accepting a materially smaller scope than the original brief.

## Directory layout

- `config/` — rule-regime tables and other reference config (to be built)
- `data/raw/` — never modified after collection; subfolders per data type
- `data/intermediate/`, `data/processed/` — pipeline outputs
- `src/` — one subfolder per pipeline stage (data_collection, cleaning, validation,
  features, event_study, controls, modeling, statistics, visualization)
- `notebooks/` — exploratory work
- `results/tables/`, `results/figures/`, `results/models/`
- `reports/` — final report and article-prep notes
- `audit/` — validation passes, accuracy checks, spot checks
- `tests/` — automated tests (timezone handling, etc.)

## Key documents so far

- `LULD_RULE_HISTORY.md` — LULD Plan mechanics and rule-regime timeline, with open
  items flagged for verification before any regime-dependent feature is computed.
- `halt_type_dictionary.csv` — official NASDAQ halt reason codes classified by whether
  they belong in the primary LULD study.
- `DATA_SOURCE_PLAN.md` — every data source checked, with live test evidence.
- `RESEARCH_LOG.md` — dated methodological decisions.
- `PROJECT_STATUS.md` — the current blocker and the options for resolving it.

## Ground rule carried through every stage

The data must determine the conclusions. No assumption from the brief ("stocks
continue after halting up," "low float means continuation," etc.) is treated as true
until the evidence says so — and if the evidence shows no reliable relationship, that
is reported as a valid result, not a failure.
