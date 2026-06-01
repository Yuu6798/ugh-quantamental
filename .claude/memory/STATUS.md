# STATUS - ugh-quantamental

最終更新: 2026-06-01

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-17 は完了済み。現在は 2026-05 engine review の短期止血から P1 前半までが入り、range_hit ensemble、engine_version auto-stratify、state classifier v2.1、rare FLAT epsilon v2.2 までが main に入った状態。次は Phase B の range per-variant scoreboard と、その後の Phase 4 spec docstring 整理、Milestone 18 monthly FX reporting の順で進める。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **Phase B (P1: range per-variant scoreboard)** - `docs/engine_review_2026_05_planning.md` §6 / §3.2.2。`expected_range` の variant-specific 化と v2.3 bump の設計から入る。
2. **Phase 4 (P2: spec docstring 改訂)** - §5.3 conviction 二重役割の spec 反映。コード変更なしの docs PR として扱う。
3. **Milestone 18 (monthly FX reporting)** - `PLANS.md` Next up。weekly/monthly report 出力を月次集計し、`docs/specs/` に spec を起草してから着手する。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **PR #110** (2026-06-01) - ENGINE-P3A rare FLAT epsilon。UGH variant 限定で fixed 3.0bp FLAT epsilon (`ratio=0.0`, `floor=3.0`) を導入し、engine default を v2.2 に bump。
- **PR #109** (2026-06-01) - ENGINE-P2B state classifier sharpening。softmax T=0.5、fire weighted-sum + catalyst floor、final softmax T=0.12 を導入し、engine default を v2.1 に bump。
- **PR #108** (2026-06-01) - ENGINE-P2A report_window `engine_version` auto-stratify。mixed-version window を theory first, engine second で latest に絞る。
- **PR #107** (2026-06-01) - ENGINE-P1A range_hit aggregation。v2 UGH variants の range metrics を `ugh_v2_ensemble` row に per-batch dedupe 集計。
- **PR #106** (2026-05-31) - semantic-ci-code の dev-flow / session-end protocol / 設計をローカライズ移植。AGENTS.md handoff protocol、CLAUDE.md tiered reading + 8-step wrap-up、STATUS.md、`/wrap-up` + `/new-brief` skills、session-start hook、`tests/discipline/` 3 gates を追加。
