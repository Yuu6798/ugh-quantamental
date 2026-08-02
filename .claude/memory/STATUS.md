# STATUS - ugh-quantamental

最終更新: 2026-08-02

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、2026-05 / 2026-06 / 2026-07 engine review とも全フェーズクローズ済み (engine default **v2.6**)。2026-07 月次レビュー (`docs/engine_review_2026_07_findings.md`) で expected_range の系統的欠陥を特定し FX-RANGE-DECOUPLE (#122) を実装: 幅を projection 由来から 実現ボラ (`trailing_mean_range_price` × 1.25) へ置換、recenter 撤去、包含率 45.5% → 95% (中変動帯 0% → 86%)。テール (≥100bp) は明示的に対象外とし警告層へ委譲。magnitude の conviction 依存は逆相関 (−0.282) を確認しつつ代替 5 案が close error を改善せず据え置き。次は監視 (価格アラート) と governance の FLAT-aware 化。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **[新設] 価格アラート層** - findings §7。エンジンは 08:00 JST スナップショットのみを見るため、7/30 22:00 の −321pips を 10 時間検知できなかった。予測の 1h 化ではなく独立した監視として実装する (engine 非改変、`fx-intraday-fetch.yml` が取得経路の実証済み)。v2.6 でテールを明示的に対象外とした以上、この層が受け皿になる。
2. **governance の FLAT-aware 化** - findings §3。`inspect_direction_logic` が 2 ヶ月連続で誤報 (FLAT 除外なら UGH 68.1% > technical 66.7%)。`direction_hit_excl_flat` を追加し閾値判定を移す。engine 非改変、集計層のみ。
3. **regime=choppy の判定保留を継続** - 7 月は全日 trending で標本ゼロのため「choppy/high-vol 全敗が構造的弱点か」は判定不能。high-vol の弱さは市場由来ラベルでも再現したが §5.5 の較正問題と交絡しており、v2.6 後のデータで再判定する。intervention_risk 非 low 日の全敗 (12 obs) も標本蓄積中。
4. **governance spec `Status: Draft` バナーの実態確認** - `docs/specs/fx_monthly_governance_v1.md` は実装 + test + workflow が完備なのにバナーが `Draft`。実態を確認し必要なら shipped 相当へ更新。
5. **売買 / execution レイヤーの planning doc 起草** - engine 出力を入力にした position sizing。conviction は方向信頼度として正しく較正されている (≥0.7 で 86% / <0.7 で 40%) ことが 7 月レビューで確認できたので sizing 入力に使える。大規模新スコープなので `docs/specs/` への planning から着手する。
6. **follow-up (低優先)** - #116 `annotation_source` 8分岐インラインの純関数 `_resolve_annotation_source` + matrix 抽出 (status 側は `_resolve_annotation_status` で固定済)。#119 `state_correctness_hit` の daily/slice/tag scoreboard 集計 rollup。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **PR #122 / 2026-07 月次レビュー** (2026-08-02) - FX-RANGE-DECOUPLE (v2.6)。`expected_range` を実現ボラ基準へ置換 (`trailing_mean_range_price` × `range_width_scale=1.25`、中心 = spot、recenter 撤去)、実装コードでの実データリプレイで包含率 45.5% → 95% / 中変動帯 0% → 86%。テール (≥100bp) は対象外と spec 明記。ENGINE-P3B の variant 固有レンジを意図的に反転。magnitude は代替 5 案が改善せず据え置き (findings §5.6 で訂正記録)。Codex P1 2件 / P2 3件、採用 4 / 却下 1 (根拠提示)。CI の ruff 未ピン留めで main が既に red だった件もピン留めで解消。
- **2026-06 engine review program 実装** (2026-06-28) - 5 briefs を全実装・マージ (#116-#120)。FX-ANNOT-LIVE (#116, OHLC fallback + leakage 除去 + daily 配線, Codex P2 8件) / FX-STATE-HYSTERESIS (#117, v2.4) / FX-MAG-EXPANSION (#118, v2.5) / FX-STATEPROXY-REDEF (#119, state_correctness_hit 新設) / FX-GOV-REGIME-FLAGS (#120, レジーム層別 collapse フラグ, Codex P2 4件)。engine default v2.5。
- **PR #114** (2026-06-27) - 2026-06 engine review program (docs-only)。`docs/engine_review_2026_06_planning.md` + Task Brief 5 本 (`docs/briefs/`)。Codex 8 round/20 thread を全 resolve (P1: state は forecast direction 非入力)。横断契約を planning §5 に一元化。
- **M18 確認 / PLANS 同期** (2026-06-01) - Milestone 18 (FX Monthly Review) が既存実装済み (`run_monthly_review` / `rebuild_monthly_review` + spec 2本 + workflow 2本 + test 1745行) と確認し end-to-end スモーク検証。PLANS.md を実態同期 (branch `claude/remaining-tasks-review-YkIQi`, PR pending)。
- **PR #112** (2026-06-01) - ENGINE-P4 conviction 意味論明文化 (docs-only)。conviction = prediction reliability + magnitude scaler の二重役割を spec/docstring に明記、dormant↔magnitude は Option B (decouple) を記録。engine_version 据え置き。
