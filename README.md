# News Sentiment vs. XRP Price Volatility

Coursework for **DSM020 — Data Programming in Python** (University of London, MSc Data Science).

An end-to-end, self-contained data pipeline investigating one question:

> **Do shifts in crypto-news sentiment coincide with — or precede — changes in XRP price volatility?**

All work lives in a single notebook, [`notebook.ipynb`](notebook.ipynb): acquisition → automated
validation → feature engineering → hypothesis testing → critical evaluation, with inline
commentary and visualisations throughout. The study covers **365 days** (2025-09-01 to
2026-08-31) across **twelve streams from seven providers**.

## Reproduce from scratch

**No API key and no network access are required.** The notebook runs from the checksummed
sample committed under [`data_sample/`](data_sample/).

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/jupyter execute notebook.ipynb          # ~16 s, top to bottom
```

To work through it interactively: `.venv/bin/jupyter notebook notebook.ipynb`, then
_Run ▸ Run All Cells_.

Dependencies are pinned to exact versions in [`requirements.txt`](requirements.txt); the
outputs stored in the notebook were produced on **Python 3.13.2**.

### What makes the run deterministic

| Mechanism                              | Effect                                                                                                                                                                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CONFIG["run_mode"] = "cached"`        | Reads the committed sample. A missing file raises rather than silently fetching, so a "cached" run cannot quietly produce different numbers.                                                                              |
| `CONFIG["analysis_end"]`               | A fixed date anchor. Acquisition windows are measured back from it, never from `datetime.now()`.                                                                                                                          |
| `CONFIG["random_seed"]`                | Fixes the block-bootstrap resampling — every confidence interval reproduces exactly.                                                                                                                                      |
| Vendored VADER lexicon + NLP artefacts | `data_sample/nltk_data/` and `data_sample/nlp/` (77 KB), so nothing is downloaded and no TLS exception is needed. WordNet is **not** a dependency; it is used once, at authoring time, by `tools_build_nlp_artifacts.py`. |
| `data_sample/_manifest.json`           | Endpoint, parameters, row count and SHA-256 per stream, re-verified on every load.                                                                                                                                        |

Both acceptance conditions are exercised: the notebook executes top-to-bottom with `.env`
absent _and_ with the network blackholed.

### Re-acquiring live data (optional)

Set `CONFIG["run_mode"] = "live"` and delete the `data_sample/*.csv` files to refresh. Only
two streams can use a key, and neither needs one: `GITHUB_TOKEN` raises GitHub's rate limit,
and `NEWS_API_KEY` is required only for the retired NewsAPI comparison stream.

> A live run **will not reproduce these outputs**. GDELT's index is revised, and the
> retired NewsAPI tier serves only a sliding ~30-day window. §3.4 documents a result whose
> _sign reversed_ between the 91-day and 365-day windows with no code change — the single
> most transferable finding in the project.

## Data sources

| Stream                           | Provider · endpoint                                     | Grain · window               | API key  |
| -------------------------------- | ------------------------------------------------------- | ---------------------------- | -------- |
| Price, volume, VWAP, trade count | Kraken · `/0/public/OHLC`                               | daily · 365                  | none     |
| Second venue (cross-check)       | Bitstamp · `/api/v2/ohlc/xrpusd`                        | daily · 365                  | none     |
| On-chain activity (10 metrics)   | Coin Metrics community · `/v4/timeseries/asset-metrics` | daily · 365                  | none     |
| News articles                    | GDELT DOC 2.0 · `artlist`                               | per-article · 8,048 articles | none     |
| News tone & volume               | GDELT DOC 2.0 · `timelinetone`, `timelinevolraw`        | daily · 361                  | none     |
| Developer activity               | GitHub · `/repos/{repo}/commits`, `/releases`           | per-commit · 1,684           | optional |
| Crypto Fear & Greed Index        | alternative.me · `/fng`                                 | daily · 365                  | none     |
| News (retired, retained)         | NewsAPI · `/v2/everything`                              | per-article · 399            | required |

CoinGecko was dropped after testing: `market_chart/range` returns HTTP 401 beyond 365 days on
the free tier and `/ohlc` degrades to 4-day candles past 180. NewsAPI is retained but demoted
— its 21 overlapping days let §2.1.3 measure _corpus selection_ by comparing two providers
over identical dates, which is the only reason the older sample was kept.

Acquisition runs through one shared helper with retries and exponential backoff on 429/5xx,
`Retry-After` compliance, per-host rate limiting, and per-source payload validation that
catches the failures these APIs report _inside_ an HTTP 200 response.

## Method

- **Write-once stage pipeline (§2.0).** `RAW → TYPED → CLEAN → FEATURES → MERGED`. Each stage
  refuses to rebind a name and returns copies, so the recorded lineage is the lineage that
  ran. 44 stage transitions, each timed and logged.
- **Automated validation.** Declarative schema contracts plus a reusable check library:
  **233 logged checks across 28 stages**, written to `data_sample/validation_report.csv`
  (129 PASS, 56 WARN, 40 INFO, 8 DRILL). A logged row is one recorded check, not necessarily
  an independent assertion — several stages log the same contract per column.
  Missing-value handling is declared as data (`MISSING_POLICY`); 13 post-conditions run
  _inside_ `Stage.bind`, so a frame that fails what its stage promised never becomes reachable.
- **Leakage detection (§2.0.1).** Every engineered column's lookahead horizon is _measured_,
  by rebuilding it from a prefix and comparing: a backward-looking column is bit-identical,
  one reading _h_ days ahead differs in exactly its last _h_ values. All 12 columns match
  their declared horizons. The detector is itself tested against three constructions that
  leak on purpose.
- **NLP (§2.1).** Tokenisation tuned to GDELT's punctuation padding, syndication
  de-duplication, a vendored lemma map derived from WordNet, and VADER extended with 75
  finance terms — which cuts the "lexicon recognised nothing" rate from 43.8% to 33.8%.
- **Features.** Daily returns and 7-/14-day rolling volatility; an independent **Parkinson
  high–low** estimator; on-chain activity; developer activity; four systemic-noise detectors
  (wash-trading and exchange-migration signatures) that flag days without dropping them.
- **Statistics (§3.0).** Every test reports an effect size with a confidence interval, a
  minimum detectable effect beside every null, assumption checks, an effective sample size
  adjusted for serial correlation, and a seeded moving-block bootstrap. The confirmatory
  family is corrected with Benjamini–Hochberg. Pre-whitened cross-correlation and Granger
  tests (§3.6) are hand-rolled on `numpy`/`scipy` and validated by a 9-check suite (§4.0.5).

## Findings

**22 tests** in total: 4 confirmatory (BH-corrected), 12 robustness, 2 sensitivity,
2 diagnostic, 2 exploratory.

| Hypothesis                                  | Result                                                                                    | Verdict           |
| ------------------------------------------- | ----------------------------------------------------------------------------------------- | ----------------- |
| **H1** sentiment → forward 3-day volatility | _r_ = −0.031 [−0.135, +0.073], BH _p_ = 0.559, n = 355                                    | **Not supported** |
| **H2** regulatory news → trading volume     | _r_ = −0.056 [−0.158, +0.048], BH _p_ = 0.391, n = 358                                    | **Not supported** |
| **H3** on-chain activity ↔ volatility       | _r_ = +0.281 [+0.182, +0.373], BH _p_ < 0.0001, n = 358; block bootstrap [+0.102, +0.450] | **Supported**     |
| **H4** development → ledger usage           | _r_ = −0.229 [−0.472, +0.047], BH _p_ = 0.205, n = 52                                     | **Not supported** |

One positive result out of four, and the honest reading of it is narrow. H3 survives a
bootstrap that assumes serial dependence, an alternate venue, and the exclusion of
noise-flagged days — but §3.6 shows the association does not localise at _any_ lag once each
series is stripped of its own dynamics. Active addresses and volatility are two slow-moving
series that are high in the same periods, not two series where a move in one follows a move
in the other. That is a weaker and more precise claim than "on-chain activity drives
volatility", and it is the one the evidence supports.

**H3's sign reversed** between the midterm's 91-day window and this 365-day one
(−0.44 → +0.281) with no change to the code. §4.4 argues this is the project's most
transferable result: the methodology outlived its own finding.

Four results changed materially because a check was run that could have been skipped —
de-duplicating syndicated reprints, correcting a lookahead window in H1, restricting the
corpus to articles that actually mention XRP, and discovering that the index's apparent
response to regulatory events was an artefact of who chose the events.

Three defects were found by checks with no particular reason to find anything: §4.0.6 was
written to _justify_ the vendored lemma map and found it corrupting 1,281 tokens; §2.0.1 was
written to _detect_ leakage and did; and the deliberate controls in §3.2 showed that detector
under-powered against sparse leakage before it had ever missed anything real.

## Project structure

```text
.
├── notebook.ipynb                  # the single master notebook (204 cells, 114 top-level
│                                 #   functions; 139 including nested and methods)
├── data_sample/                  # deliverable sample (relative paths throughout)
│   ├── xrp_*.csv                 #   twelve acquired streams
│   ├── _manifest.json            #   provenance + SHA-256 per stream, verified on load
│   ├── validation_report.csv     #   every data-quality check and its outcome
│   ├── nltk_data/                #   vendored VADER lexicon (92 KB)
│   └── nlp/                      #   lemma map, known lemmas, stop words, finance lexicon
├── tools_build_nlp_artifacts.py  # authoring-time only; uses WordNet, NOT on the run path
├── requirements.txt              # exact pinned dependencies + reproduction steps
├── README.md                     # this file
└── .env                          # optional API keys (git-ignored)
```

## Notes

- This project is one subfolder of a multi-module repository; the git root is two levels up.
- Total deliverable size is **5.3 MB** against a 10 MB limit; all 14 figures are inline.
- The notebook is not investment advice, and §4.4 sets out explicitly what the results do and
  do not license. §4.5 discusses what it means to measure a public ledger without consent.
