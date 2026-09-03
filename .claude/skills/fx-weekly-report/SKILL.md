---
name: fx-weekly-report
description: Generate the weekly FX prediction report (USDJPY daily-protocol results) from the fx-daily-data branch artifacts, write it to docs/reports/, push it, and reply with a Japanese summary. Use when the user asks for a 週間レポート / 週間サマリー / weekly report of prediction results, names a specific week (e.g. 「7月4週」「6/29から7/3」), or when the scheduled weekly-report Routine fires. Also use for follow-up questions about a past week's prediction results that a report would answer.
---

# fx-weekly-report — 週間予測レポートの定型作成

Turns the persisted `fx-daily-data` artifacts for one Mon–Fri week into a
Japanese weekly report committed under `docs/reports/`, plus a chat summary.
This skill is the **executor**; the numbers' source of truth is always the
pipeline-generated weekly v2 artifact on `fx-daily-data` — never re-run
forecast logic, and never hand-compute a metric the artifact already provides.

Established by the 2026-06-29 → 2026-07-24 reports in `docs/reports/`
(4 consecutive weeks). Read the most recent one before writing a new one:
each report's 「次週への持ち越し」 items must be resolved or carried forward,
and multi-week patterns (e.g. high-vol day range misses) count consecutive
weeks — keep those counters accurate.

## 1. Target week

Default (scheduled run / 「今週」): the most recent completed Mon–Fri week.
An explicit week in the request (「7月4週」= 4th week of that month, or a date
range) wins. Call the Monday `<start>`, the Friday `<end>`.

Timing contract of the protocol — this drives everything below:

- A forecast issued on day D covers window D → next business day; it is
  evaluated the morning after the window closes.
- Therefore Friday `<end>`'s forecast is **always pending** when the report is
  written on the weekend (its evaluation lands Monday). The week has
  7 strategies × 4 evaluated days = 28 observations, not 35.
- The **previous Friday's** forecast (pending in last week's report) resolved
  on `<start>` — report it as the 先週持ち越し section.

## 2. Data refresh

The data lives on the `fx-daily-data` branch (never push to it). Keep a
checkout in the session scratchpad:

```bash
git fetch origin fx-daily-data
# first time:
git worktree add <scratchpad>/fxdata origin/fx-daily-data
# subsequent runs:
git -C <scratchpad>/fxdata checkout -f origin/fx-daily-data && git -C <scratchpad>/fxdata clean -fdq
```

## 3. Collect the numbers

1. **Weekly v2 artifact** (source of truth for aggregates):
   `csv/analytics/weekly/<saturday YYYYMMDD>/weekly_report.md`, written Friday
   ~12:00–13:00 UTC with window `<start>`–`<end>`. **Always verify the window
   in its title line** — two directories exist per week and they cover
   different weeks: the Saturday-dated one is the week that just closed, while
   `fx-analysis-pipeline.yml`'s Monday run writes a *Monday*-dated directory
   covering the **previous** week. Reading the Monday directory silently gives
   you last week's numbers. If it is missing or the window is wrong,
   regenerate without touching the branch:
   `FX_CSV_OUTPUT_DIR=<scratchpad>/fxdata/csv FX_REPORT_DATE=<next Monday> FX_WEEK_DAYS=5 python scripts/run_fx_weekly_report.py`
   (report date = next Monday makes the window land on `<start>`–`<end>`).
2. **Daily detail + carry-over** (per-day narrative):
   `python .claude/skills/fx-weekly-report/scripts/build_weekly_detail.py --csv-dir <scratchpad>/fxdata/csv --week-start <start>`
   — prints per-day forecast vs realized per strategy, the UGH alpha
   state/conviction trajectory, annotation labels, failure reasons, and the
   previous-Friday carry-over row. Read-only.
3. **Ops health is two-layered** — `provider_health.csv` / the artifact's
   Provider Health section only see runs that *executed the protocol script*.
   Check the `fx-daily-protocol.yml` Actions run conclusions covering the
   whole `<start>`–`<end>` interval as well (`actions_list` — the workflow
   schedules three runs per weekday, so ~15 newest entries cover only about
   one current week; for an explicitly requested past week, paginate until
   the target dates are covered): a red conclusion needs its **failed step
   inspected (`get_job_logs` with `failed_only`) before assigning a cause** —
   data being present does not prove a post-protocol failure, because an
   earlier retry can have committed the data while the final 11:23 UTC retry
   still fails hard on a fetch error (`FX_LAST_RETRY=1`). The 2026-08 Gmail-535
   case (every inspected run from 8/17 onward was red at the mail step while data flowed; the confirmed 8/17–8/21 weekly report
   said 安定稼働, pre-8/17 Actions runs were not inspected, and the user's daily emails silently stopped) was one cause
   among several possible; missing runs or runs landing on the wrong
   JST day mean scheduler delay (the 2026-08-28 gap: crons fired ~11h late,
   landed on Saturday JST, and the business-day guard refused them — no Friday
   forecast, no Thursday evaluation, no weekly artifact). A missing Saturday
   artifact is a symptom: find which run failed to produce it and report why.
4. **Market context** — invoke the `fx-market-context` skill. The protocol
   records no reason for anything it sees (`event_tags` is auto-derived and
   near-empty), so a policy event and a technical pattern look identical in the
   OHLC. The 2026-07-30 week showed why: 8/3 looks like a textbook selling
   climax on the chart, and an official intervention is a documented candidate
   cause of the 163→155 selloff around it — but neither the chart nor the public
   record establishes what produced that particular low. Run it every week, and
   treat it as mandatory before writing any sentence about tops, bottoms,
   reversals or regime change.

## 4. Write the report

File: `docs/reports/fx_weekly_report_<start>_<end>.md`, same section skeleton
as the existing reports (keep headings verbatim so the series stays greppable):

1. Title + metadata bullets (対象 / 評価済み観測 / 元データ artifact path /
   前週レポート link)
2. `## TL;DR` — the week's conclusion in one paragraph, not a metrics dump
3. `## 先週持ち越し: …` — how the previous Friday's pending forecast resolved
4. `## 週間値動きと日次結果` — the 5-row day table (Friday row = 未確定)
5. `## 相場コンテキスト (公開情報)` — from `fx-market-context`. Omit only when
   the week was genuinely quiet and the search turned up nothing that changes
   the reading; never omit it after a shock day.
6. `## 戦略別サマリー` — per-strategy table from the weekly artifact
7. One section for **the week's structural observation** — the thing worth
   remembering (e.g. magnitude under-call in strong trends, retreat-release
   lag). This is the report's reason to exist beyond the tables.
8. `## スライス別の傾向` / `## 運用ヘルス` / `## 次週への持ち越し` (numbered,
   each item either new or explicitly carried from last week)

Interpretation rules learned over the series — apply, don't re-derive:

- **Direction scoring remains binary.** `direction_hit` follows exact forecast-direction
  equality with the realized direction in `src/ugh_quantamental/fx_protocol/outcomes.py`. A
  `FLAT` forecast on any nonzero realized close move is therefore a direction miss, even when
  the move is small. Do not reinterpret the legacy direction rate as epsilon-aware; any
  tolerance-based metric must be separately named and reported.
- **Before committing, verify every aggregate or chronology claim in prose
  against the day table it summarizes.** This series' recurring failure mode
  (PR #124: five review rounds) is prose contradicted by its own tables:
  a "9/9" that was 12/12, an "all up days missed" beside a β up-HIT row, an
  e_star turn dated 8 business days late. Three mechanical checks: (a) recount
  any N/M by multiplying the table out; (b) an `up`/`down` forecast implies
  the same e_star sign — never narrate a sign transition later than the first
  such forecast in the table; (c) count business-day spans on a calendar, don't
  estimate them.
  Quote median close error and range hit alongside direction rate whenever
  FLAT days distort it (e.g. 7/13 week: 25% direction but best-in-series
  median error).
- `baseline_simple_technical` carries a standing up-bias; its direction rate
  flatters it in rising weeks. Compare via close error, not rate alone.
- `state_correctness_hit` compares forecast dominant_state against the
  OHLC-derived realized state (`classify_realized_state` in
  `src/ugh_quantamental/fx_protocol/outcomes.py`); `state_proxy_hit` is
  persistence only. High stC in quiet weeks / 0% in strong trends is the
  expected signature, not noise.
- FLAT retreats after shocks (hysteresis v2.4) are judged by range hit +
  close error, not direction. Track the retreat/release timing vs what the
  market did next — the 7/3 (worked) vs 7/10 (didn't) pair is the reference.

## 4b. リピート注文モニタ (live position watch)

The user runs a Rakuten FX repeat-order grid, live since **2026-07-27**:
buy USDJPY 161.500–163.500, 25 pips grid / 25 pips take-profit, 10,000
units per order (9 levels, no stop configured).

**Policy tracking is closed** (2026-08-30, user decision): the exit
question, the 160.50 line, and any reset definition are the user's own
call — do not track them, escalate them, or carry a 方針判断 item in
次週への持ち越し. The section reports the week's facts only.

While this grid is active, add a `## リピート注文モニタ` section to the
weekly report (after 運用ヘルス) answering, from the week's OHLC:

- Weekly low / high / close vs the band 161.50–163.50 — held below,
  dipped into, or spent above (above 163.50 = grid idle, not at risk).
- Days whose range overlapped the band, and estimated fills/take-profits.
- Any shock day (−0.9 円級, the 7/2 / 7/13 pattern) that would have
  filled multiple levels at once.
- Unrealized P/L at the week's close and the margin-ratio estimate,
  stated with the usual assumptions.

Estimated fill counts from daily OHLC are order-of-magnitude only — say
so rather than implying precision. If the user reports changed or closed
settings, update this section (or delete it) in the same commit as the
report.

## 5. Deliver

1. **Only commit and push when the report was asked for as a deliverable** —
   a scheduled run, or a request to write/save/update the weekly report. When
   someone is just asking what happened last week, answer with the summary and
   leave the tree alone; an unrequested commit is a side effect they did not
   ask for. When you do commit, use the session's working branch (never main,
   never `fx-daily-data`) and `git push -u origin <branch>`. Never open a PR
   unless asked.
2. Send the file to the user (SendUserFile if available).
3. Reply in Japanese: 結論 first (bold, one sentence), the day table, then
   3–6 bullets — carry-over resolution, structural observation, continuing
   multi-week patterns with week counts, ops health one-liner — and close by
   noting the pending Friday forecast and when it resolves. No PR unless
   asked.
