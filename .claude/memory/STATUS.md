# STATUS - ugh-quantamental

最終更新: 2026-06-27

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、2026-05 engine review も全フェーズクローズ済み (engine default v2.3)。2026-06 はライブ運用ログ (6/1-26) を分析し、観測された 5 つの改良点を束ねた `docs/engine_review_2026_06_planning.md` + Codex 用 Task Brief 5 本 (`docs/briefs/`) を起草して PR #114 でマージ (Codex 8 round/20 thread を全 resolve)。次は 5 briefs を Codex 実装フェーズへ渡す段階で、着手順序は FX-ANNOT-LIVE (enabler) → FX-STATE-HYSTERESIS (v2.4) → FX-MAG-EXPANSION (v2.5)、FX-STATEPROXY-REDEF / FX-GOV-REGIME-FLAGS は独立。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **2026-06 engine review の Codex 実装** - `docs/briefs/` の 5 briefs を着手順序どおり Codex へ。FX-ANNOT-LIVE (enabler) → FX-STATE-HYSTERESIS (v2.4) → FX-MAG-EXPANSION (v2.5)、FX-STATEPROXY-REDEF / FX-GOV-REGIME-FLAGS は独立。横断契約は planning §5 参照。
2. **月次分析の再検証 (FX-ANNOT-LIVE 後)** - regime/vol ラベルが performance 由来 (`direction_hit`/`close_error_bp`) で循環している。市場由来ラベルへ是正後、「choppy/high-vol 全敗が UGH の構造的弱点」が本物のレジーム現象か再評価する。
3. **governance spec `Status: Draft` バナーの実態確認** - `docs/specs/fx_monthly_governance_v1.md` は実装 + test + workflow が完備なのにバナーが `Draft`。実態を確認し必要なら shipped 相当へ更新。
4. **売買 / execution レイヤーの planning doc 起草** - engine 出力を入力にした position sizing。大規模新スコープなので `docs/specs/` への planning から着手する。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **PR #114** (2026-06-27) - 2026-06 engine review program (docs-only)。`docs/engine_review_2026_06_planning.md` + Task Brief 5 本 (`docs/briefs/`)。Codex 8 round/20 thread を全 resolve (P1: state は forecast direction 非入力)。横断契約を planning §5 に一元化。
- **M18 確認 / PLANS 同期** (2026-06-01) - Milestone 18 (FX Monthly Review) が既存実装済み (`run_monthly_review` / `rebuild_monthly_review` + spec 2本 + workflow 2本 + test 1745行) と確認し end-to-end スモーク検証。PLANS.md を実態同期 (branch `claude/remaining-tasks-review-YkIQi`, PR pending)。
- **PR #112** (2026-06-01) - ENGINE-P4 conviction 意味論明文化 (docs-only)。conviction = prediction reliability + magnitude scaler の二重役割を spec/docstring に明記、dormant↔magnitude は Option B (decouple) を記録。engine_version 据え置き。
- **PR #111** (2026-06-01) - ENGINE-P3B variant-specific expected_range。projection width 一本化で range 生成、非 FLAT recenter + 半幅 floor + `range_width_scale=2.0`、`ugh_v2_ensemble` 撤去で per-variant 集計復帰、engine default を v2.3 に bump。
- **PR #110** (2026-06-01) - ENGINE-P3A rare FLAT epsilon。UGH variant 限定で fixed 3.0bp FLAT epsilon (`ratio=0.0`, `floor=3.0`) を導入し、engine default を v2.2 に bump。
