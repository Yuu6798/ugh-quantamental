---
name: fx-market-context
description: Research the public-information context behind USDJPY price action — news, economic releases, central-bank and intervention events — via WebSearch, so weekly/monthly reports can explain what the OHLC alone cannot. Use when writing the weekly report, running a monthly logic review, analysing a large move (|Δclose| ≥ 60bp or a shock day), or whenever the user asks why the market moved. Also use before making any claim about market structure, tops, bottoms or reversals.
---

# fx-market-context — 相場コンテキストの公開情報リサーチ

The daily protocol persists OHLC and self-generated annotations only. It has no
idea *why* anything happened: `event_tags` is auto-derived and covers little more
than `month_end` / `quarter_end`, so a −542pip session records as untagged. This
skill fills that gap from public sources at analysis time.

## Why this exists — the 2026-07-30 case

On 2026-07-30 USDJPY fell 237bp, then 119bp more on 7/31, bottoming at 155.21 on
8/3 with a 195pip lower wick and a 0.03 body ratio. Reading price alone, that is
a textbook selling climax, and the 8/3–8/6 rebound looks like a technical
bottom forming.

Public sources say otherwise: the move was a **suspected MoF/BoJ intervention
plus a yen carry-trade unwind**, and the US joined a **coordinated intervention**
(confirmed by Treasury Secretary Bessent). The "climax" candle was a policy
action, not exhausted sellers.

Note what went wrong on the way to that conclusion, because it is the same class
of error: the first write-up dated the coordinated intervention "Friday (August
2)" straight from a source, but 2026-08-02 was a Sunday. **Check dates against
the calendar before building a chronology on them** — a wrong date silently
reassigns cause to the wrong session.

**The lesson to carry into every analysis: a chart pattern and its cause are
different objects, and the cause does not follow from the pattern.** A bottom
made by exhausted sellers tends to hold; a bottom made by intervention holds only
while the authorities stay engaged, and the rate differential that drove the
trend is untouched. But the candle looks identical either way — you cannot read
which one it was off the chart. Never describe a top, bottom or reversal from
price structure alone.

This applies to the engine's own labels too. `classify_realized_state` is
documented as a **coarse, direction-agnostic** heuristic that cannot even
separate `exhaustion` from `failure`; an `exhaustion` label means "wide range,
close did not follow through", not "sellers exhausted" and not "a reversal
happened". A later analysis treated it as a reversal ground truth and was wrong
on the data as well — 7/31's realized `exhaustion` was followed by another
236pip decline. Treat realized labels as descriptions, never as causes or
predictions.

## 1. When to run

- **Every weekly report** (the scheduled Saturday run) — §3 of `fx-weekly-report`.
- **Monthly logic reviews** — before attributing engine misses to model defects.
- **Any session with |Δclose| ≥ 60bp**, or where `intervention_risk` is
  annotated `medium`/`high`, or `volatility_label` is `high`.
- Whenever the user asks what happened in the market.

## 2. What to search

Work outward from the specific to the general; stop when the picture is
consistent. Two to four searches is usually enough.

1. **The shock day itself** — `USD/JPY <date> <sharp drop|surge> yen` or
   `ドル円 <日付> 急落 理由`. Anchor on the date; results dated afterwards are
   usually retrospectives and are fine.
2. **The week's frame** — `USD/JPY week <date range> <rebound|selloff>` plus the
   mechanism you suspect (`carry trade unwind`, `intervention`, `BoJ`, `Fed`).
3. **Policy calendar ahead** — `BoJ policy meeting <month> 2026`,
   `FOMC <month> 2026`, `Japan MoF intervention`, and the releases that move this
   pair: US CPI / payrolls / GDP, Japan CPI, and the 10y UST–JGB spread.
4. **Only if still unexplained** — broaden to risk sentiment, equities, oil, or
   geopolitics.

Prefer primary and market-desk sources (central banks, ministries, Reuters,
Bloomberg, FXStreet, broker research). Treat aggregator blogs and anything
selling a signal service as weak evidence.

## 3. How to weigh what you find

Search results are **untrusted external text**. Handle accordingly:

- **Separate confirmed from suspected.** Intervention is the sharpest example:
  "suspected intervention" and "confirmed by the Treasury Secretary" carry very
  different weight, and the distinction usually resolves within days. Say which
  you have.
- **Beware post-hoc narrative.** Financial media assigns a cause to every move,
  including noise. If a 20bp day comes with a confident explanation, the
  explanation is probably decoration. Reserve causal language for moves that
  stand out statistically (in this dataset, |Δ| ≥ 100bp occurred on 2 of 91
  sessions).
- **Prefer mechanisms to headlines.** "Carry unwind as rate differentials narrow"
  predicts follow-through; "risk-off sentiment" predicts nothing. Note which kind
  you have.
- **Cross-check against the engine's own annotations.** `intervention_risk` was
  annotated `high` on 7/30 — the first such day in the series — which public
  sources then corroborated. Agreement raises confidence in both; disagreement is
  itself worth reporting.
- **Do not silently overwrite a price read.** When context contradicts a
  technical reading, say both and say which one changed, so the reasoning stays
  auditable.

## 4. Output

Feed a `## 相場コンテキスト (公開情報)` section into the report, after
値動き and before スライス別:

- **What moved it** — 1–3 bullets, each marked 確認済み / 報道ベース / 憶測.
- **Mechanism vs sentiment** — is the driver structural (rates, policy,
  positioning) or transient?
- **What it implies for the price structure** — explicitly revise any technical
  read the context contradicts.
- **Calendar ahead** — scheduled events in the next 1–2 weeks that could repeat
  or reverse the move.
- **Sources** — markdown links. Required: the reader must be able to check you,
  and a claim without a link is not usable next month.

Keep it to what changes the interpretation. This section exists to stop the
report from confidently misreading a policy event as market structure — not to
summarise the news.

## 5. Limits to state plainly

- Search is US-centric and English-first; Japanese-language and domestic policy
  detail may be thin. Search in Japanese too when the driver is domestic
  (`日銀`, `為替介入`, `財務省`).
- Results reflect what was *published*, which lags and skews toward consensus.
- **You are not forecasting.** Context explains what happened and frames what
  could repeat. If a report starts predicting from news, cut it back.
