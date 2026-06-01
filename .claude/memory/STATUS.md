# STATUS - ugh-quantamental

最終更新: 2026-06-01

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、2026-05 engine review も全フェーズ (P0-P4 + Phase B) クローズ済み。range_hit ensemble、engine_version auto-stratify、state v2.1、rare FLAT epsilon v2.2、variant-specific expected_range v2.3、conviction 意味論明文化までが main に入り、Milestone 18 monthly reporting は既存実装済みと確認した。engine 側の前提整備は完了し、次の大方向は engine 出力を入力にした売買 / execution レイヤーの planning doc 起草 (大規模新スコープ)。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **PLANS.md M18 同期を PR 化** - branch `claude/remaining-tasks-review-YkIQi` に push 済み (M18 を完了 milestone 表に追加、Next up を実態化)。PR 作成 → merge する。あわせて governance spec の `Status: Draft` バナーを実態 (実装+test+workflow 完備) に合わせるか確認する。
2. **売買 / execution レイヤーの planning doc 起草** - 次の大方向。engine 出力 (state lifecycle / conviction / expected_close_change_bp / per-variant expected_range) を入力にした position sizing。大規模新スコープなので `docs/specs/` への planning から着手する。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **M18 確認 / PLANS 同期** (2026-06-01) - Milestone 18 (FX Monthly Review) が既存実装済み (`run_monthly_review` / `rebuild_monthly_review` + spec 2本 + workflow 2本 + test 1745行) と確認し end-to-end スモーク検証。PLANS.md を実態同期 (branch `claude/remaining-tasks-review-YkIQi`, PR pending)。
- **PR #112** (2026-06-01) - ENGINE-P4 conviction 意味論明文化 (docs-only)。conviction = prediction reliability + magnitude scaler の二重役割を spec/docstring に明記、dormant↔magnitude は Option B (decouple) を記録。engine_version 据え置き。
- **PR #111** (2026-06-01) - ENGINE-P3B variant-specific expected_range。projection width 一本化で range 生成、非 FLAT recenter + 半幅 floor + `range_width_scale=2.0`、`ugh_v2_ensemble` 撤去で per-variant 集計復帰、engine default を v2.3 に bump。
- **PR #110** (2026-06-01) - ENGINE-P3A rare FLAT epsilon。UGH variant 限定で fixed 3.0bp FLAT epsilon (`ratio=0.0`, `floor=3.0`) を導入し、engine default を v2.2 に bump。
- **PR #109** (2026-06-01) - ENGINE-P2B state classifier sharpening。softmax T=0.5、fire weighted-sum + catalyst floor、final softmax T=0.12 を導入し、engine default を v2.1 に bump。
