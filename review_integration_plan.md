# Review Integration Plan — DSM020 Final Coursework (79 → target ~88)

Source: `DSM020_review_evidence.md` (independent audit of the submitted ZIP).
Target notebook: `notebook.ipynb`, SHA-256 `890550f1…26ccf6`.

## 0. Verification status — do not re-audit

The reviewed artefact is **byte-identical** to the working copy (hash confirmed), and every
figure quoted in the review reproduces exactly against the stored outputs:

| Review claim | Checked against | Verdict |
|---|---|---|
| H4 registers Pearson, not the declared Spearman | cell 108 `report_correlation`, cell 154 output row 3 (`estimate −0.229`, `p_raw 0.1026`, `p_adj 0.2052`) | confirmed |
| Final weekly bin is partial | cell 141 output: "53 complete weeks from 2025-09-07 to **2026-09-06**" vs study end 2026-08-31 | confirmed |
| Ljung-Box ignores model df | cell 143 `ljung_box` — `stats.chi2.cdf(q, lags)`, `lags` hard-wired as df | confirmed |
| Best component picked on test | cell 171 — `component_scores` sorts by `out_of_sample_r2`, which scores on `test` | confirmed |
| Event study: 1 of 3 rises, not 2 | cell 125 output `−0.0004 / +0.0072 / −0.0157` vs cell 127 prose "+0.009 each" | confirmed |
| H3 exclusion: 20 days, +0.281→+0.282 | cell 139 output vs cell 137 prose "13 days … +0.260" | confirmed |
| 22 tests, not twenty | cell 154 output line 1 | confirmed |
| Validation log 229 rows | `data_sample/validation_report.csv` (129 PASS / 55 WARN / 39 INFO / 6 DRILL) vs README "207 checks" | confirmed |
| Instrument swap changes corpus | cell 181 scores `scored_corpus` (n=357); primary H1 uses XRP-specific (n=355) | confirmed |
| Checksum mismatch only warns | cell 21 — `print("WARNING: …")`, no `raise` | confirmed |
| 12 source CSVs, not five | `data_sample/_manifest.json` | confirmed |

**Treat all nine findings as valid.** No triage stage is needed; spend the time on fixing.

---

## 1. The two facts that govern the whole plan

**(a) The fixes do not overturn a single conclusion.** Recomputing BH across the
confirmatory family with H4's declared Spearman substituted gives
`2.66e-07 / 0.113 / 0.391 / 0.559` — H3 stays significant, H1/H2/H4 stay unsupported.
Every verdict in cell 154 survives. So this is an **integrity repair, not a results
rewrite**: the argument of the notebook stands, the numbers supporting it move. That
removes the main risk and means the ~24.7k words of narrative need *number* corrections,
not re-argument.

> **Amended after W1.4.** One exception has since surfaced. F4 was the single finding
> capable of moving a verdict, and it did: correcting the selection rule falsifies two
> claims in cells 170–172 outright. The *downstream* claim — the index is kept for
> description, not prediction — survives and is better supported. Expect W1.3
> (Ljung-Box df) to behave the same way, since it also invalidates a stated pass/fail
> assertion rather than just a number.

**(b) The fixes are entangled, so ordering is not optional.**

```
F2 partial week ─┐
                 ├─→ H4 sample changes ─→ H4 estimate changes ─┐
F1 Spearman   ───┘                                             ├─→ BH recomputes over
                                                               │   ALL 4 confirmatory
F3 Ljung-Box df ──→ AR order reselects ──→ residuals change ───┤   tests → cells 154, 173
                                    └─→ cell 149 cross-corr    │   and every cell quoting
F6 corpus align ──→ cell 181 table changes ────────────────────┘   p_adj
F4 selection    ──→ cell 171 table changes
```

**Hard rule: fix every code cell first, execute the notebook once end to end, then write
the narrative from the produced output.** Do not hand-copy a p-value forward at any point
— that practice is what produced finding 5 in the first place.

---

## 2. Rubric headroom

| Criterion | Now | Findings that bear on it | Target |
|---|---:|---|---:|
| Exceptional Work | 6 | all — consistency is what separates 6 from 9 | 8 |
| Simple Code and Clear Commentary | 7 | **F5** (narrative ≠ output) | 9 |
| Evaluation and Conclusion | 7 | **F1, F2, F8** | 9 |
| Advanced Techniques | 7 | **F3, F4, F6, F7** | 9 |
| Robust Error Checking and Handling | 8 | **F9** | 9 |
| Project Novelty | 8 | F7 (a labelled sample would lift this) | 9 |
| Aims / Data Capture / Pipelines / Tools | 9 | — protect, change nothing | 9 |

F5 is the cheapest four marks in the document: it is proofreading, not statistics.

---

## W1 — Statistical correctness  (blocking; everything downstream depends on it)

### W1.1 · Register the declared statistic — F1  ✅ DONE
`report_correlation` (cell 108) hard-codes Pearson into `estimate`, `p_raw` and the Fisher
interval. Add a `primary: str = "pearson"` argument that selects which statistic populates
those three fields; keep **both** statistics in the row regardless, so nothing is lost.

Two details worth getting right, because they are visible marks:
- When `primary="spearman"`, the Fisher interval needs the **Bonett–Wright** standard
  error `1.06/√(n−3)`, not `1/√(n−3)` — the rank transform inflates the variance.
- Register H4 (cell 141) with `primary="spearman"` so the registered test matches the
  pre-registration in cell 1.

Then audit the other three confirmatory registrations: each must register the statistic
cell 1 declares for it. This is a one-line check per hypothesis and closes the finding
completely rather than patching H4 alone.

### W1.2 · Drop the partial week — F2  ✅ DONE
Cell 141's `.resample("W")` emits a week-ending label of 2026-09-06 holding a single
observation (Monday 2026-08-31), and the print calls all 53 "complete". Carry an explicit
day count through the resample and filter on it:

```python
weekly = ... .agg(..., n_days=("volatility_7d", "size"))
full_weeks = weekly[weekly["n_days"] == 7]
print(f"{len(full_weeks)} complete weeks ({len(weekly) - len(full_weeks)} partial dropped) …")
```

Expected: 52 weeks, 51 lag-one pairs, ρ = −0.262, p = 0.063. H4 stays unsupported. State
the partial-week policy in the markdown rather than leaving it implicit.

### W1.1 + W1.2 — outcome (done together, one execution)

`report_correlation` gained `primary="pearson"|"spearman"`, deciding which statistic fills
`estimate`, `p_raw`, `effect` and the interval — i.e. which one is registered and corrected.
`fisher_ci` gained `se_factor`, set to `SPEARMAN_SE_FACTOR = 1.06` (Bonett–Wright) when rho
is the estimate, because the rank transform inflates the sampling variance of Fisher's z and
the Pearson interval would overstate precision. H4 registers with `primary="spearman"`; §1.3
declares Pearson for H1–H3, which is the default, so those are unchanged by construction.

Cell 141 now carries `days_observed` through the resample and keeps only 7-day weeks:

```
52 complete 7-day weeks from 2025-09-07 to 2026-08-30
1 partial week(s) dropped: 2026-09-06 (1d)
```

| Confirmatory family | Submitted | Now |
|---|---|---|
| H4 statistic registered | Pearson r = −0.229 | **Spearman ρ = −0.262** [−0.51, +0.03] |
| H4 raw p | 0.1026 (Pearson) | **0.0628** (Spearman) |
| H4 BH-adjusted p | 0.2052 | **0.1256** |
| H4 sample | 52 lag-one pairs / 53 "complete" weeks | **51 lag-one pairs / 52 complete weeks** |
| H1 / H2 / H3 | unchanged | unchanged |
| Verdicts | — | **none flipped** |

The conclusions table in cell 173 now pairs each hypothesis's declared statistic with its own
p-value and interval; previously it showed a Spearman estimate beside a BH-adjusted Pearson
p, which was the substance of finding 1.

**One design correction mid-flight.** The first version added `primary`, `pearson_r` and
`pearson_p` to *every* row, which duplicated `estimate`/`p_raw` on all Pearson tests and
widened cell 112's table to state the same number twice. The Pearson columns are now added
only when rho is primary, and `primary` was dropped since `effect` already carries it — so
every pre-existing table renders exactly as before and only the H4 row gains the comparison.

**Cascade caught outside W1.** Cell 1's abstract asserted the index "does not beat its best
single component on a held-out period" — falsified by W1.4. Rewritten to the claim the
evidence now supports. Cells 173 and 195 updated for the new H4 figures and *n*.

Blast radius verified against `HEAD`: cells 141, 154 (intended), 112 (reverted to identical),
and 51, 82, 103, 177, 179, 203 — all blank-line or timing noise.

---

### W1.3 · Ljung-Box degrees of freedom — F3  ✅ DONE
`ljung_box` (cell 143) always tests Q against χ²(lags). On fitted AR(p) residuals that is
anticonservative. Add `model_df: int = 0` and test against χ²(lags − model_df).

Three consequences to handle, not one:
1. `fit_ar`'s inner `whitens()` must pass `model_df=candidate["order"]`, **and** use
   diagnostic lags exceeding the fitted order (e.g. `lags=max(10, order + 5)`).
2. Because `whitens()` drives order selection, the selected order may move off 2 — the fix
   is circular and must be re-run, not reasoned about.
3. Raw-series calls keep `model_df=0`; only fitted-residual calls change.

At df=8 the current AR(2) residuals give p = 0.0246, so the existing "residuals pass at 5%"
assertion in cells 143/149 is false as written and must be rewritten from the new output.

### W1.3 — outcome

`ljung_box` gained `model_df` (default 0) and tests Q against chi-square with
`lags - model_df`, raising if the lag count does not exceed the fitted order. A module-level
`DIAGNOSTIC_LAGS = 15` replaced the hard-wired 10, chosen above `fit_ar`'s `max_order` so a
residual test always has degrees of freedom left, and fixed rather than varied per candidate
so competing orders face the same diagnostic. `fit_ar`'s inner `whitens()` now charges each
candidate's own order; cell 149 charges the fitted order on the filtered series. The two raw
series and the cell 187 self-tests keep `model_df=0`, which is correct — nothing was
estimated from them.

**The circularity resolved in the direction the review predicted, and further.**

| Quantity | Submitted | Now |
|---|---|---|
| Sentiment AR order | AR(2) (AIC 1, escalated to 2) | **AR(8)** (AIC 1, escalated to 8) |
| Ljung-Box on filtered series | Q = 17.6, p = 0.0624 at df = 10 | **Q = 9.2, p = 0.2418** at df = 7 |
| Ljung-Box on raw series | Q = 31.5, p = 0.0005 | Q = 44.0, p = 0.0001 |
| Pre-whitened CCF lag 0 | r = −0.072, n = 356 | r = −0.085, n = 350 |
| H1 verdict | nothing survives BH | **unchanged** |

The submitted AR(2) filter was passing whiteness at p = 0.0624 only because the test ignored
the two fitted coefficients; at the correct df it fails, the escalation rule keeps going, and
AR(8) is the first order that genuinely whitens the series. So this is not a cosmetic df
correction — **the notebook was cross-correlating imperfectly whitened residuals**, which is
precisely the failure mode §3.6 exists to prevent. The whiteness claim is now earned rather
than marginal-and-mismeasured.

The order-8 fit costs six observations of warm-up (n 356 → 350) and every conclusion holds:
no CCF lag exceeds the band, none survives BH, and Granger is null in both directions.

Cell 147's address pre-whitening shifted with it (one fewer lag past the band in two rows),
and cell 187's white-noise self-test moved with the lag count. Both still pass.

**Narrative:** no markdown cell hardcoded AR(2) or the old Q values, so nothing was
falsified. Cell 142's point 2 ("the AR order is chosen by AIC, not assumed") understated the
procedure once AIC's choice of 1 was overridden to 8, so points 2 and 4 were rewritten to
describe escalation and the df charge. Deliberately written without the number 8 in it — the
code prints the selected order, and hardcoding it into prose is how finding 5 happened.

---

### W1.4 · Selection on the held-out set — F4  ✅ DONE

**Implemented** (cells 170–172, notebook re-executed, blast radius verified as cell 171 only).
Selection now happens by expanding-window walk-forward validation *inside* the training
period — five folds, each scored on days strictly after those it was fitted on — and the
frozen choice is scored once on the test period. `out_of_sample_r2` became
`fit_score_r2(columns, fit_frame, score_frame)`, taking both periods as arguments so that
choosing and scoring cannot silently share data.

**This one did change a conclusion — and then changed it back, for a better reason.**

| Quantity | Submitted | After the fix |
|---|---:|---:|
| Component selected | parkinson_daily (by test R²) | fear_greed (by walk-forward, within train) |
| Its test R² | +0.2351 | −0.1730 |
| Axes test R² | +0.1762 | +0.1762 |
| Verdict printed | composite does **not** beat its best component | — see below |

Ranking components honestly reverses the naive verdict, but the reversal is not the
finding. The diagnostic that matters: **0 of 10 components has a positive walk-forward R²
inside the training period, and neither does the composite (−0.3520).** Every candidate
fails to beat the mean of the period it is asked to predict, before the test days are
reached. The axes' +0.1762 and the component's −0.1730 are two signs on one 87-day window,
from constructions that are indistinguishable across the 200 days before it.

So the cell now concludes the weaker and defensible thing: **nothing here demonstrates
out-of-sample predictive validity, and the comparison cannot rank the candidates.** The
0.4081 gap between the hindsight-best and the honestly-selected component is printed as a
measured selection bias — the defect turned into a demonstration.

Downstream text corrected in the same pass:
- **Cell 170** — "worse than predicting the *training* mean" → the scored period's own mean
  (the review's wording mismatch), plus a paragraph on why choosing is itself a use of data.
- **Cell 172** — its closing paragraph asserted "no axis beats its own best component …
  on all days *or* on a held-out period" and that "the two tests agreeing matters more than
  either verdict". Both became false. Rewritten to separate the in-sample ranking (still
  true, still descriptive) from the held-out comparison (underpowered, ranks nothing).
- §3.9's descriptive use of the axes is untouched and is now better supported, since the
  notebook no longer rests it on a prediction claim it had not earned.

**One caveat surfaced that the review did not raise.** The turbulence block's composition
(`FINAL_TURBULENCE`, dropping `reported_inflation`) was fixed in cell 162 using Cronbach's
alpha computed across all days, the test period included. That never saw the target
`next_abs_return`, so it is *not* outcome leakage and does not invalidate the comparison —
but "fixed in advance" cannot mean "blind to these dates", and the cell now says so.

<details><summary>Original W1.4 plan text, for reference</summary>

Cell 171 fits on `train` but ranks candidates by `out_of_sample_r2`, which scores on
`test`; `best_component` is therefore chosen with knowledge of the final outcome.

**Recommended (proper fix, ~1–2h):** carve a chronological validation slice from the
training period — fit on train-inner, rank on validation, freeze the winner, refit on the
full training period, and score **once** on test. This turns a hindsight comparison into a
genuine held-out test and is squarely in "Advanced Techniques" territory.

**Fallback (~10min):** keep the code and relabel the row "hindsight-best component",
stating plainly that it is an upper bound on what a component could have achieved, not a
prediction. Cheaper, and still honest — but it forfeits the marks.

Either way, fix the cell 170 wording: the prose describes a benchmark of the *training*
mean while the code uses `actual.mean()`, the *test* mean. Simplest correction is to the
prose, since test-mean R² is the conventional definition.
</details>

### W1.5 · Align the instrument comparison — F6  ✅ DONE
Cell 181 scores the full cleaned corpus (n=357) while describing itself as the identical
primary specification (n=355, XRP-specific). Point it at the same filtered corpus H1 uses.
The null survives on either corpus, so nothing is at stake in the result — but a
comparison whose stated purpose is to isolate *instrument choice* must hold the corpus
fixed, and a marker will see that.

Also correct the overclaim: the cell prints that the instruments "do not share a single
vocabulary or rule set between them", but three of the four are VADER-derived. Describe
them as **four scoring specifications**, of which one (TextBlob) is lexicon-independent.

### W1.6 · Zero polarity ≠ lexicon blindness — F7  ✅ DONE
Cells 72, 123, 173 and 198 read a zero compound score as the lexicon failing to see the
headline. A zero also arises when recognised terms cancel — the review's example,
*"XRP faces short-term pressure, OPTO Miner becomes a stable income channel"*, carries
`pressure −1.2` and `stable +1.2`. 23 baseline-zero and 42 adapted-zero headlines contain
lexicon matches.

Add a helper that tests whether *any* token hits the VADER lexicon, then report **zero-score
rate** and **no-lexicon-match rate** as two separate numbers. Drop "false neutrality" and
"blindness" framing. A zero→non-zero move is not a demonstrated correction without labelled
ground truth — which leads to the optional extension below.

---

### W1.5 + W1.6 — outcome (done together, one execution)

**W1.5.** Cell 181 now aggregates only `xrp_specific` articles, matching primary H1. All
four specifications land on n = 355, and row 0 reproduces the headline H1 estimate exactly
(r = −0.031), which it did not before — the comparison's own baseline now agrees with the
result it is a comparison against.

| Instrument | n | Pearson r | p |
|---|---:|---:|---:|
| VADER + domain lexicon | 355 | −0.031 | 0.559 |
| VADER as shipped | 355 | −0.010 | 0.851 |
| dictionary counting (LM-style) | 355 | −0.050 | 0.344 |
| TextBlob (Pattern) | 355 | +0.070 | 0.186 |

Matches the review's independently reproduced XRP-specific table to three decimals. The null
survives, as the review said it would. The "they do not share a single vocabulary or rule
set" claim was replaced: three of four read the same VADER lexicon, two differ only by the
§2.1.3 domain terms, and only TextBlob is independent of it.

**W1.6.** A `lexicon_matches` helper counts tokens the analyzer actually recognises,
tokenised through VADER's own `SentiText` so the tokens counted are the tokens scored. Zero
scores are now decomposed by cause:

| | as shipped | domain-adapted |
|---|---:|---:|
| scored exactly 0.0 | 43.8% | 33.8% |
| — no term recognised at all | **43.5%** | **33.2%** |
| — recognised terms cancelled | 0.3% | 0.6% |

**Worth being precise about the size of this one.** The conflation the review identified is
real, and the review's counts reproduce exactly (23 baseline-zero and 42 adapted-zero
headlines contain lexicon matches, including its `pressure`/`stable` example). But the
practical effect is 0.3pp: the notebook's "the lexicon recognising nothing at all" was
overstated, not wrong in substance. The fix is a correctness and framing repair, not a
finding that changes what H1's null means.

"Rescued from a false neutral" became "moved off a zero score" (727 articles), reported
beside the 732 genuine vocabulary gaps closed, with an explicit statement that a move off
zero is not a demonstrated correction without labelled ground truth.

**Narrative:** cells 1 and 198 ("four independent scoring instruments") now say four
specifications, one independent of the lexicon. Cells 2, 123 and 173 had the *numbers*
right — 43.8% is genuinely the zero-score rate — but labelled them "falsely neutral"; they
now name the 43.5% / 33.2% no-match rates where that is the quantity meant.

Blast radius: cells 72, 181 (intended), 101 (the validation-log row text, a consequence of
the new `log_row` wording), 91 blank line, rest timing noise.

---

## W1 — complete

All six items done. The confirmatory family, in full, after W1.1–W1.6:

| | Hypothesis | Registered statistic | BH-adjusted *p* | Verdict |
|---|---|---|---:|---|
| H1 | sentiment → forward volatility | Pearson r = −0.031 | 0.559 | not supported |
| H2 | regulatory news → volume | Pearson r = −0.056 | 0.391 | not supported |
| H3 | on-chain activity ↔ volatility | Pearson r = +0.281 | < 0.0001 | **supported** |
| H4 | developer activity → transaction velocity | Spearman ρ = −0.262 | 0.126 | not supported |

No hypothesis verdict changed across the whole of W1. What changed is that each is now
computed the way §1.3 said it would be. The two results that did move — the index's held-out
comparison (W1.4) and the AR order behind the pre-whitened CCF (W1.3) — were both cases
where a stated pass/fail assertion was falsified rather than a number nudged.

---

## W2 — Inference and conclusion calibration  (F8; wording, but load-bearing)

Mostly prose, one substantive addition. Do after W1 so the numbers are final.

- **The unaddressed rank result (cells 135/137/196).** H3's forward-volatility row is
  Pearson r = +0.052 (p = 0.32) **but Spearman ρ = +0.197, p = 0.00016**. The narrative
  quotes only the Pearson figure and concludes "busy days do not announce volatile
  tomorrows". That is the one place where the current text is not merely imprecise but
  omits a result that points the other way. Discuss it explicitly, subject it to the same
  dependence- and multiplicity-aware treatment as the rest, and qualify the claim. *This is
  the single highest-value item in W2.*
- **Cells 108/154** — separate the three uncertainty statements now conflated: Pearson
  p-values on nominal n, `effective_n` (reported but not used to adjust anything), and the
  block-bootstrap Spearman interval. Say which estimand each describes; stop presenting the
  headline inference as serial-dependence-adjusted when it is not.
- **Cells 173/198** — a non-significant Granger test does not exclude reverse causality; a
  non-significant correlation does not establish the absence of predictive information.
  Rewrite as failures to reject.
- **Cell 145** — ADF/KPSS disagreement is unresolved stationarity evidence, not a
  diagnosis of long memory. Either drop the claim or run an actual long-memory estimate.
- **Cell 137** — `transfers_per_address` is a frequency ratio; "more people, smaller
  transfers" is not supported by it. It is transfers per address, and the later ethical
  caveat about addresses ≠ users belongs here too.
- **Preregistration claims** — "pre-registered" and "unchanged since the midterm" are not
  evidenced by anything in the archive. Either cite a dated artefact (the midterm notebook,
  a commit hash, `w1_decisions.md` if it predates the results) or narrow to "specified in
  §1.3 before the analysis was run". **Check what you actually have before choosing.**

---

## W3 — Narrative/output audit  (F5; the cheap marks)

Six known contradictions, plus a sweep. Do this **last**, against freshly executed output.

| Cell | Current | Correct to |
|---|---|---|
| 3 | "the five acquired CSVs" | twelve (per `_manifest.json`) |
| 115 | "~21-day window" | 358 observed days — a leftover from the midterm sample |
| 127 | "+0.009 each", 2 of 3 rise, "21-point linear test" | −0.0004 / +0.0072 / −0.0157; 1 of 3 rises |
| 137 | "13 days … +0.281 → +0.260" | 20 days … +0.281 → +0.282 |
| 154/173 | "twenty tests" | 22 registered |
| README | 194 cells / 130 functions; 207 checks | 204 cells / 137 defs; 229 log rows |

On the README check count: 229 is the **log row** count, not a count of independent
assertions (129 PASS / 55 WARN / 39 INFO / 6 DRILL). Say "229 logged checks across N
stages" rather than implying 229 independent tests — the review calls this out specifically.

**Then sweep.** 13 markdown cells carry three or more statistical tokens — cells 1, 28, 30,
113, 123, 131, 137, 172, 173, 195, 196, 198, 204 — roughly 158 numbers to verify, plus 3,
115, 127 and 170 from the table above. Budget one focused pass; every one of these is a
number typed by hand that the notebook also computes.

---

## W4 — Provenance and error handling  (F9)

- **`load_or_fetch` (cell 21)** — a checksum mismatch prints a warning and proceeds. In
  `cached` mode it should `raise`, since the entire reproducibility claim rests on the
  cached bytes being the audited bytes. Gate any continue-anyway path behind an explicit
  `CONFIG` opt-in.
- **`enforce_schema` / `validate_stream` (cells 60, 61, 67)** — these log actions labelled
  `STOP`/`stop`, but the label is not executed; invalid data still flows downstream. Make
  fatal schema failures raise. *The current CSVs pass every hash — this is hardening, not
  evidence of corruption.*
- **TLS bypass (cell 12)** — `unverified_ssl_context` disables certificate verification.
  The lexicon is now vendored in `data_sample/nltk_data/`, so **check whether this is
  simply dead code**; if so, delete it outright. That is the cleanest possible resolution
  and removes a standing criticism for free.
- **Stale reproduction instructions** — CoinGecko is no longer a data source (price comes
  from Bitstamp/Kraken; there is no CoinGecko manifest entry), yet cells 3, 5, 18, 19, 20,
  26, 83, 85, 113 and 190 still reference it. NewsAPI *is* still live (`xrp_news`, 399
  rows), so keep that but correct the surrounding text.
- **Hash the vendored NLP artefacts** and record their build configuration, the same way
  the CSVs are covered.
- **Separate offline execution from dependency installation** in the reproduction section —
  the notebook runs with no network; `pip install` does not.
- **Manifest wording** — every entry records "checksum recorded retrospectively", which
  establishes integrity relative to the manifest, not authenticated acquisition. Say so.

---

## W5 — Optional, only if time remains

A **small manually labelled headline sample** (100–150 headlines, two passes) would convert
several hedged claims into measured ones: it gives the sentiment instruments and the
regulatory classifier a ground truth, turns W1.6's zero-score discussion into a precision
figure, and is the one addition the review names as strengthening validation. This is the
most plausible route from "Project Novelty 8" to 9 and from "Exceptional Work 6" to 8.

Do not add further models. The review is explicit: *"Prioritise statistical consistency, a
clean validation comparison, and an output-to-narrative audit rather than adding more
models."* Breadth is already scoring 9s; consistency is what is scoring 6s and 7s.

---

## 6. Execution sequence

1. **Branch.** `git checkout -b review-integration` — the current `main` is the submitted,
   hash-verified state and should stay recoverable.
2. **W1.1 – W1.6**, code only. Do not touch a markdown cell yet. *(W1.4 done — its markdown was corrected in the same pass, since cells 170 and 172 made claims the fix falsified outright rather than merely restating numbers.)*
3. **W4** code changes (raise-on-mismatch, dead TLS removal) — same execution, no extra run.
4. **Execute once, end to end**, in a clean kernel: `.venv/bin/jupyter execute notebook.ipynb`.
   Expect ~36s, no network.
5. **Diff the outputs** against the current notebook — the changed set should be exactly:
   H4 rows, the confirmatory BH column, AR order + Ljung-Box + cross-correlation, cell 171's
   table, cell 181's table. **Anything else that moved is an unintended consequence** — a
   cheap and effective check that W1 did only what it was meant to.
6. **W2**, then **W3**, writing every number from step 4's output.
7. **Re-execute** to confirm the notebook is still clean, refresh the README counts last
   (they depend on the final cell count), and re-hash for the manifest.

## 7. Calls that need your input

- **W1.4** — proper nested validation, or relabel and narrow? Recommendation: do it
  properly; Advanced Techniques has three marks of headroom and this is the clearest place
  to earn them.
- **W2, preregistration** — do you have a dated midterm notebook or a commit predating the
  results? If yes, cite it. If no, the wording narrows. I cannot verify this from the
  archive.
- **W5** — worth it only if W1–W4 are finished and comfortable.

## What this does not fix

`CLAUDE.md` is stale in two ways that will mislead a future run: it names `nobook.ipynb`
(now `notebook.ipynb`) and describes a CoinGecko + NewsAPI two-source pipeline that has
since become twelve streams. Worth a five-minute correction alongside W4, though it is not
part of the submission.
