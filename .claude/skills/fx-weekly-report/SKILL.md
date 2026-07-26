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

1. **Weekly v2 artifact** (source of truth for aggregates): the analysis
   pipeline writes `csv/analytics/weekly/<saturday YYYYMMDD>/weekly_report.md`
   on Friday ~12:00–13:00 UTC with window `<start>`–`<end>` — verify the
   window in its title line. If it is missing or the window is wrong,
   regenerate without touching the branch:
   `FX_CSV_OUTPUT_DIR=<scratchpad>/fxdata/csv FX_REPORT_DATE=<next Monday> FX_WEEK_DAYS=5 python scripts/run_fx_weekly_report.py`
   (report date = next Monday makes the window land on `<start>`–`<end>`).
2. **Daily detail + carry-over** (per-day narrative):
   `python .claude/skills/fx-weekly-report/scripts/build_weekly_detail.py --csv-dir <scratchpad>/fxdata/csv --week-start <start>`
   — prints per-day forecast vs realized per strategy, the UGH alpha
   state/conviction trajectory, annotation labels, failure reasons, and the
   previous-Friday carry-over row. Read-only.

## 4. Write the report

File: `docs/reports/fx_weekly_report_<start>_<end>.md`, same section skeleton
as the existing reports (keep headings verbatim so the series stays greppable):

1. Title + metadata bullets (対象 / 評価済み観測 / 元データ artifact path /
   前週レポート link)
2. `## TL;DR` — the week's conclusion in one paragraph, not a metrics dump
3. `## 先週持ち越し: …` — how the previous Friday's pending forecast resolved
4. `## 週間値動きと日次結果` — the 5-row day table (Friday row = 未確定)
5. `## 戦略別サマリー` — per-strategy table from the weekly artifact
6. One section for **the week's structural observation** — the thing worth
   remembering (e.g. magnitude under-call in strong trends, retreat-release
   lag). This is the report's reason to exist beyond the tables.
7. `## スライス別の傾向` / `## 運用ヘルス` / `## 次週への持ち越し` (numbered,
   each item either new or explicitly carried from last week)

Interpretation rules learned over the series — apply, don't re-derive:

- Direction hit is binary; a FLAT forecast on a small-move day scores as miss.
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

## 5. Deliver

1. Commit the report to the session's working branch (never main, never
   `fx-daily-data`) and `git push -u origin <branch>`. Do not open a PR
   unless asked.
2. Send the file to the user (SendUserFile if available).
3. Reply in Japanese: 結論 first (bold, one sentence), the day table, then
   3–6 bullets — carry-over resolution, structural observation, continuing
   multi-week patterns with week counts, ops health one-liner — and close by
   noting the pending Friday forecast and when it resolves. No PR unless
   asked.
