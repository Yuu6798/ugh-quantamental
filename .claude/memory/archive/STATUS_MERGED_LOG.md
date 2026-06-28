# STATUS merged archive

## 2026-06-01

- **PR #105** (2026-05-30) - wrap-up session memory for 2026-05-30。`.claude/memory/2026-05-30.md` + `_index.md` を追記。
- **PR #104** (2026-05-30) - `docs/engine_review_2026_05_planning.md`。計画書のみ、コード変更なし。Codex P2 review 13 rounds / 22 threads を処理してマージ。

## 2026-06-01 (Session 2 wrap-up overflow)

- **PR #108** (2026-06-01) - ENGINE-P2A report_window `engine_version` auto-stratify。mixed-version window を theory first, engine second で latest に絞る。
- **PR #107** (2026-06-01) - ENGINE-P1A range_hit aggregation。v2 UGH variants の range metrics を `ugh_v2_ensemble` row に per-batch dedupe 集計。
- **PR #106** (2026-05-31) - semantic-ci-code の dev-flow / session-end protocol / 設計をローカライズ移植。AGENTS.md handoff protocol、CLAUDE.md tiered reading + 8-step wrap-up、STATUS.md、`/wrap-up` + `/new-brief` skills、session-start hook、`tests/discipline/` 3 gates を追加。

## 2026-06-27 (wrap-up overflow)

- **PR #109** (2026-06-01) - ENGINE-P2B state classifier sharpening。softmax T=0.5、fire weighted-sum + catalyst floor、final softmax T=0.12 を導入し、engine default を v2.1 に bump。

## 2026-06-28 (wrap-up overflow)

- **PR #110** (2026-06-01) - ENGINE-P3A rare FLAT epsilon。UGH variant 限定で fixed 3.0bp FLAT epsilon (`ratio=0.0`, `floor=3.0`) を導入し、engine default を v2.2 に bump。
