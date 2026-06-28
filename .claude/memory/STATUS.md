# STATUS - ugh-quantamental

最終更新: 2026-06-28

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、2026-05 / 2026-06 engine review とも全フェーズクローズ済み (engine default **v2.5**)。2026-06 program の Task Brief 5 本を全実装・マージ (#116-#120): FX-ANNOT-LIVE (OHLC fallback + performance leakage 除去 + daily 配線) → FX-STATE-HYSTERESIS (v2.4, single-shock failure 減衰) → FX-MAG-EXPANSION (v2.5, ボラ拡張 magnitude 項) の直列 + FX-STATEPROXY-REDEF (state_correctness_hit 新設) / FX-GOV-REGIME-FLAGS (レジーム層別 collapse フラグ) の独立2本。次は循環ラベル是正後の月次分析の再検証フェーズ。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **月次分析の再検証 (FX-ANNOT-LIVE 後)** - regime/vol ラベルの performance 由来循環は #116 で市場 (OHLC) 由来へ是正済。「choppy/high-vol 全敗が UGH の構造的弱点」が本物のレジーム現象か実データで再評価する。新設の `state_correctness_hit` / regime・volatility direction collapse フラグも実運用データで観測。
2. **governance spec `Status: Draft` バナーの実態確認** - `docs/specs/fx_monthly_governance_v1.md` は実装 + test + workflow が完備なのにバナーが `Draft`。実態を確認し必要なら shipped 相当へ更新。
3. **売買 / execution レイヤーの planning doc 起草** - engine 出力を入力にした position sizing。大規模新スコープなので `docs/specs/` への planning から着手する。
4. **follow-up (低優先)** - #116 `annotation_source` 8分岐インラインの純関数 `_resolve_annotation_source` + matrix 抽出 (status 側は `_resolve_annotation_status` で固定済)。#119 `state_correctness_hit` の daily/slice/tag scoreboard 集計 rollup。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **2026-06 engine review program 実装** (2026-06-28) - 5 briefs を全実装・マージ (#116-#120)。FX-ANNOT-LIVE (#116, OHLC fallback + leakage 除去 + daily 配線, Codex P2 8件) / FX-STATE-HYSTERESIS (#117, v2.4) / FX-MAG-EXPANSION (#118, v2.5) / FX-STATEPROXY-REDEF (#119, state_correctness_hit 新設) / FX-GOV-REGIME-FLAGS (#120, レジーム層別 collapse フラグ, Codex P2 4件)。engine default v2.5。
- **PR #114** (2026-06-27) - 2026-06 engine review program (docs-only)。`docs/engine_review_2026_06_planning.md` + Task Brief 5 本 (`docs/briefs/`)。Codex 8 round/20 thread を全 resolve (P1: state は forecast direction 非入力)。横断契約を planning §5 に一元化。
- **M18 確認 / PLANS 同期** (2026-06-01) - Milestone 18 (FX Monthly Review) が既存実装済み (`run_monthly_review` / `rebuild_monthly_review` + spec 2本 + workflow 2本 + test 1745行) と確認し end-to-end スモーク検証。PLANS.md を実態同期 (branch `claude/remaining-tasks-review-YkIQi`, PR pending)。
- **PR #112** (2026-06-01) - ENGINE-P4 conviction 意味論明文化 (docs-only)。conviction = prediction reliability + magnitude scaler の二重役割を spec/docstring に明記、dormant↔magnitude は Option B (decouple) を記録。engine_version 据え置き。
- **PR #111** (2026-06-01) - ENGINE-P3B variant-specific expected_range。projection width 一本化で range 生成、非 FLAT recenter + 半幅 floor + `range_width_scale=2.0`、`ugh_v2_ensemble` 撤去で per-variant 集計復帰、engine default を v2.3 に bump。
