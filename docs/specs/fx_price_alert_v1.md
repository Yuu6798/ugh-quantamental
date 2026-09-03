# FX Price Alert v1 — Specification

**Status**: Implemented
**Depends on**: `fx-daily-data` branch layout (`docs/specs/fx_daily_csv_exports_v1.md`,
`docs/specs/fx_observability_artifacts_v1.md`) for read access only
**Scope**: New, independent GitHub-native monitoring layer — no changes to
the prediction stack

---

## 1. Motivation

The daily forecast protocol only looks at the market once per business day
(three retry attempts ending 20:23 JST). Two incidents exposed the gap:

- **2026-07-30**: a −321 pip USDJPY move went undetected for ~10 hours,
  because nothing watches the market between forecast runs.
- **2026-08-28**: a scheduled run silently failed to produce a forecast and
  the pipeline passed through a zero-forecast path without anyone noticing
  until the following Monday.

`scripts/run_fx_price_alert.py` + `.github/workflows/fx-price-alert.yml`
close both gaps with a small, independent monitor: it polls USDJPY on a
tighter cadence than the daily protocol and reports threshold breaches,
monitored-line crossings, and pipeline stalls as comments on a GitHub Issue.

---

## 2. Independence from the prediction stack

This is a deliberate architectural boundary, not an oversight:

- `scripts/run_fx_price_alert.py` imports **stdlib only**
  (`urllib`, `json`, `os`, `re`, `sys`, `dataclasses`, `datetime`). It does
  **not** import `ugh_quantamental` or `fx_protocol` — enforced by
  `tests/ops/test_run_fx_price_alert.py::TestIndependenceContract`, which
  parses the script's AST and asserts every import resolves to the stdlib.
- It re-implements its own minimal Yahoo Finance chart-API client rather
  than importing `fx_protocol.data_sources.YahooFinanceFxMarketDataProvider`
  — same endpoint (`query2.finance.yahoo.com/v8/finance/chart/USDJPY=X`,
  already proven in `fx-intraday-fetch.yml`), independent code path.
- It reads `fx-daily-data` CSV/JSON artifacts as plain files — it never
  imports the persistence layer, never touches the SQLite/Alembic-backed
  run database, and performs no `fx-daily-data` writes.
- Consequence: this monitor keeps working even when `fx_protocol` fails to
  import, has a broken dependency, or its own workflow is red. A daily
  protocol outage is exactly the scenario (2026-08-28) this layer exists to
  catch, so it cannot depend on the thing it is watching.
- The one test that *does* import `fx_protocol`
  (`tests/fx_protocol/test_input_snapshot_invariant.py`) is a regression
  test of an invariant this monitor's baseline computation *depends on*
  holding on the producer side (§4) — it does not test the monitor script
  itself, and the script stays import-free regardless.

---

## 3. Threshold semantics

### 3.1 Move alert (AC a) — `FX_ALERT_MOVE_BP`, default `60`

```
move_bp = |live_spot - baseline_spot| / baseline_spot * 10_000
active  = move_bp >= FX_ALERT_MOVE_BP
```

- `live_spot`: the current `meta.regularMarketPrice` from the Yahoo Finance
  chart API — a live tick, not a completed-bar close.
- `baseline_spot`: **`current_spot` from the last forecast batch's
  `input_snapshot.json`** — the exact spot the engine saw when that
  forecast was generated. **Never** a rebuilt/completed OHLC close: Yahoo's
  `regularMarketPrice` is fetched independently from completed daily bars,
  and reconstructing the baseline from a bar close would silently drift
  from what the engine actually used as input. See §4 for why this baseline
  is safe to read even across an idempotent retry.
- `FX_ALERT_MOVE_BP` is **true basis points** of the baseline spot
  (`|diff| / baseline * 10_000`), matching the env var's own `_BP` suffix
  and the rest of the system's bp conventions — not a fixed 1/100-yen
  "pip" count (`|diff| * 100`), which does not scale with the pair's
  magnitude. At the default threshold of `60` bp this is roughly 95 pips
  at USDJPY ~159 — comparable in practice to how the triggering 2026-07-30
  incident was described (`-321 pips`, itself well past this threshold
  either way); `60` bp is a deliberately loose default, tuned for "notify
  before the position is 10 hours stale," not for scalping precision.
- Direction-agnostic: a move up or down of equal magnitude fires equally.

### 3.2 Monitored-line alert (AC b) — `FX_ALERT_LINES`, default `"161.50"`

```
active = latest_bar.low <= line <= latest_bar.high
```

- `latest_bar` is the most recent **daily** bar from the same Yahoo
  `interval=1d` chart response used for `live_spot` — while the current JST
  day's session is still open this is a live, still-accumulating bar, so
  its low/high update through the day exactly like a live "has today
  touched this line yet" check.
- One HTTP call serves both the move-alert spot and the line-alert bars —
  keeping the monitor to a single external dependency.
- Default line `161.50` is the strategy grid's lower bound — "price is
  approaching the trading band" is itself operationally useful information,
  independent of any directional call. `160.50` was tracked previously but
  the user ended that tracking on 2026-08-30 and it is intentionally
  **not** in the default; add it back via the `FX_ALERT_LINES` repository
  variable if needed again.
- Multiple lines are supported (comma-separated); each gets its own
  suppression/re-arm state keyed by the exact configured token (e.g.
  `line:161.50`), so `161.50` and `161.5` would — deliberately — be tracked
  as distinct lines if both were ever configured simultaneously.

### 3.3 Data-gap alert (AC c) — schedule-aware, not age-based

```
target_date = today (JST)                        if today is Mon-Fri
            = most recent Mon-Fri on or before today   if today is Sat/Sun
cutoff_reached = now.time() >= 22:00 JST          if today is Mon-Fri
               = True                             if today is Sat/Sun
stale  = (last_forecast_as_of is None) or (last_forecast_as_of < target_date)
active = stale                     if the alert was already active last run
       = cutoff_reached and stale  otherwise (a fresh activation)
```

- **22:00 JST** cutoff = the daily protocol's final retry cron (11:23 UTC /
  20:23 JST) plus a ~1.5-hour grace window. The constant predates the move
  of the crons from :00 to :23 (when the grace was a full 2 hours) and is
  kept at 22:00 on purpose: the run itself takes about a minute, and the
  alert is sticky once active, so a shorter grace only advances detection.
- This is intentionally **schedule-aware, not age-based**. An "older than 1
  business day" rule would have masked the 2026-08-28 incident exactly the
  way it actually played out: a Friday run failure leaves the last good
  forecast at Thursday's date, which is precisely 1 business day old all
  through the weekend — an age threshold would not have tripped until
  Monday. Checking "does *today's* (or, on a weekend, *Friday's*) forecast
  exist" catches it as soon as Friday's 22:00 JST cutoff passes.
- **Sticky once active** (self-review fix): `target_date` rolls forward every
  calendar day (Friday's target becomes Monday's once Monday is itself a
  business day) and `cutoff_reached` resets to `False` at the start of each
  new business day. Gating a *fresh* activation on `cutoff_reached` is
  correct — it avoids crying wolf before the day's run has had its chance to
  complete — but re-applying that same gate to an *already-active* alert is
  not: on a Monday morning, before Monday's own 22:00 cutoff, both would
  flip `active` to `False` even though the actually-missing forecast
  (Friday's) still hasn't appeared, producing a false `Cleared: gap` every
  business morning during a multi-day stall. `evaluate_data_gap` therefore
  takes the alert's own prior-run state (`was_active`, threaded through from
  `evaluate_alerts`'s `prev_state`) and, once active, computes `active` from
  `stale` alone — clearing only once a forecast whose `as_of_jst` is no
  longer behind *today's* `target_date` genuinely exists.
- Both sides of the cutoff are covered by
  `tests/ops/test_run_fx_price_alert.py::TestBusinessDayRules` (21:59:59 vs
  22:00:00 vs 22:00:01 JST),
  `TestEvaluateDataGap::test_weekend_checks_friday_not_age_in_business_days`
  pins the weekend-detection regression, and
  `TestEvaluateDataGap::test_monday_morning_stays_active_no_false_clear` /
  `test_true_clear_when_mondays_forecast_appears` /
  `TestEvaluateAlertsSuppression::test_evaluate_alerts_end_to_end_monday_morning_no_false_clear`
  pin the sticky-clear regression directly.

### 3.4 Fetch-failure alerts

A failure to fetch the live spot/bars, or to read the last forecast's
metadata, is reported the same way as a data gap — **never** silently
skipped. Each source gets its own suppression key
(`fetch_failure:spot`, `fetch_failure:forecast`) so a sustained outage does
not spam the issue on every poll, but the first occurrence and every
clear→re-fire transition are always visible.

- **Yahoo payload shape validation** (self-review fix): the chart API can
  return HTTP 200 with `{"chart": {"result": null, "error": {...}}}` (an
  invalid/unrecognized symbol) or `{"chart": {"result": []}}`, neither of
  which is a transport-level failure `main()`'s
  `(urllib.error.URLError, ValueError, KeyError, TimeoutError, OSError)`
  guard would catch on its own — subscripting `None` raises `TypeError`,
  indexing an empty list raises `IndexError`. `fetch_yahoo_daily` validates
  the response shape explicitly and raises `ValueError` for both, which the
  guard already catches, so these surface as a normal
  `fetch_failure:spot` alert instead of crashing the run.
- **Config-error alert** `fetch_failure:config` (self-review fix): parsing
  `FX_ALERT_MOVE_BP` / `FX_ALERT_LINES` used to happen before any guarded
  region in `main()`, so a malformed repository variable raised `ValueError`
  and crashed the run before it ever reached the alert path. Parsing now
  happens inside a guarded region; on failure the offending setting falls
  back to its default (so the rest of the run's checks still proceed) and
  the failure is reported through the same `evaluate_alerts` flow, naming
  the variable and its invalid value in the alert body.

---

## 4. Reading the forecast baseline safely across idempotent retries

`scripts/run_fx_price_alert.py::read_forecast_meta` reads
`csv/latest/input_snapshot.json` directly from the read-only `fx-daily-data`
checkout (plus `csv/latest/manifest.json` for `forecast_batch_id`, used only
for issue-body context, never for the baseline computation).

This is safe because of an existing, tested invariant in
`ugh_quantamental.fx_protocol.automation.run_fx_daily_protocol_once` step 7a
(`automation.py`, "input_snapshot.json"): on an idempotent retry
(`forecast_created is False`), the artifact is **copied verbatim** from the
immutable `history/{date}/{batch_id}/input_snapshot.json` written by the
original run, rather than rebuilt from the retry-time market snapshot. So
`latest/input_snapshot.json`'s `current_spot` always reflects the spot at
the moment the forecast was actually generated, never a later retry's spot
— exactly the semantics AC (a) requires.

`tests/fx_protocol/test_input_snapshot_invariant.py` pins this with a
regression test: a stub provider returns a different `current_spot` on a
same-batch retry, and the test asserts the persisted `input_snapshot.json`
still reports the original run's spot after the retry. This is the only
place FX-PRICE-ALERT's tests import `fx_protocol` — see §2.

---

## 5. State-from-Issue design (no file, no database)

The runner (`scripts/run_fx_price_alert.py`) is **stateless between runs** —
each GitHub Actions job is a fresh container with no persisted disk. State
lives entirely in the `fx-alert` labeled GitHub Issue itself:

1. On each run, look up the open Issue labeled `fx-alert` (`state=open`,
   `labels=fx-alert`). If found, fetch all of its comments (oldest-first).
2. `parse_alert_state(comment_bodies)` scans those comment bodies for a
   hidden marker — `<!-- fx-price-alert-state: {...json...} -->` — and
   returns the payload of the **most recent** comment that has one (or `{}`
   if the issue has none yet, or no open issue exists at all). This is a
   pure function, unit-tested without any GitHub API access.
3. `evaluate_alerts(...)` (pure — §6) computes the new state, and which
   keys newly fired or newly cleared, against that previous state.
4. `render_state_comment(...)` builds one comment body containing: any
   newly-fired alerts, any newly-cleared keys, and the encoded new state
   marker. If nothing fired **and** nothing cleared, it returns `None` and
   the run writes nothing — an alert-free run stays fully silent and the
   workflow ends green with no API writes at all.
5. If there is something to post and no open `fx-alert` issue exists, one
   is created; otherwise the comment is appended to the existing issue.

**Design choice — manual close resets tracked state.** The runner never
closes the issue itself. If a human closes it (after reviewing), the next
`state=open` lookup finds nothing and starts from `{}` — a deliberate,
conservative re-arm: a closed issue means a human has seen the history, so
starting fresh rather than reopening or hunting through closed issues for
state keeps the design simple and avoids ever silently reusing stale state
from an issue nobody is looking at anymore.

---

## 6. Suppression and re-arm state machine

Every condition (`move`, one `line:<token>` per configured line, `gap`,
`fetch_failure:spot`, `fetch_failure:forecast`) is tracked as a boolean
"active" flag in the state dict — never a bar timestamp or poll counter, so
a condition that stays true across many polls (the exact 2026-07-30 failure
mode — the same breach sat undetected/unrepeated for 10 hours) cannot be
"suppressed" by construction; it is suppressed because the flag simply
doesn't change:

```
new_state[key] = active
if active and not was_active:      fires — new alert appended
elif (not active) and was_active:  clears — key appended to cleared_keys,
                                    the clear is recorded (§5 step 4) even
                                    if nothing else fired this run
else:                              no-op — steady state, nothing written
```

A condition this run's fetch could not evaluate (spot/forecast fetch
failed) is left exactly as `prev_state` had it — carried forward, never
guessed at or force-cleared — while the fetch failure itself is evaluated
and reported as its own alert key.

`tests/ops/test_run_fx_price_alert.py::TestEvaluateAlertsSuppression`
covers: first breach fires, steady-state repeats write nothing, a full
fire→clear→re-fire sequence (both for the move alert and for a line cross)
where the second fire is **not** suppressed, and fetch-failure carry-forward
of unrelated condition state.

---

## 7. Simplified business-day rule (deliberate trade-off)

`is_business_day_jst` / `target_business_date_jst` use a **JST-weekend-only**
rule (`weekday() < 5`) — no market-holiday calendar. This monitor
deliberately does **not** import `fx_protocol.calendar` (which does model
holidays) to preserve independence (§2): importing it would reintroduce the
exact coupling this layer exists to avoid.

Trade-off accepted: on an actual JST market holiday that falls on a
weekday, this monitor will (incorrectly) expect a forecast and may fire a
data-gap alert that the daily protocol's own holiday-aware calendar would
not raise. This is judged an acceptable false positive rate in exchange for
independence — a holiday false alarm is a minor inconvenience; a monitor
that goes down with the pipeline it watches is a repeat of 2026-08-28.

The cron schedule in `.github/workflows/fx-price-alert.yml` is likewise
expressed in UTC day-of-week as an approximation of JST weekday/weekend
(the same convention `fx-daily-protocol.yml` already uses for its JST-timed
crons) — the script's own JST-aware cutoff logic (§3.3) is authoritative
regardless of exact invocation time, so the day-boundary fuzziness near UTC
midnight affects cadence only, never correctness.

---

## 8. Delivery: GitHub Issues via REST (`urllib` + `GITHUB_TOKEN`)

- `scripts/run_fx_price_alert.py` calls the GitHub REST API directly with
  `urllib.request` and a `Bearer $GITHUB_TOKEN` header — no `gh` CLI, no
  `PyGithub` dependency, keeping the independence contract (§2).
- `.github/workflows/fx-price-alert.yml` declares
  `permissions: { issues: write, contents: read }` explicitly. The
  workflow-default `GITHUB_TOKEN` is otherwise read-only for Issues on a
  restricted default, and Issue creation would 403 without this — every
  other workflow in this repository declares its `permissions:` block
  explicitly for the same reason.
- The `fx-daily-data` branch is checked out **read-only**, into a separate
  path (`FX_ALERT_DATA_DIR`, default `fx-daily-data-readonly/` under the
  workspace) from the code checkout, and is never written to or pushed —
  this monitor makes no `fx-daily-data` commits.

---

## 9. Non-goals (Scope OUT, per Task Brief FX-PRICE-ALERT)

- No changes to `src/ugh_quantamental/` (this monitor does not import it at
  all — §2).
- No email notification channel (superseded by GitHub Issues only, per
  2026-08-29 user decision).
- No changes to any existing workflow file.
