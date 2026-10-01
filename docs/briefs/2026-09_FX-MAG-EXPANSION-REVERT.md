# Task Brief: FX-MAG-EXPANSION-REVERT - v2.5 ボラ拡張項の無効化 (engine v2.7)

> **2026-10-01 ユーザー承認済。** 2026-09 月次レビュー (`docs/engine_review_2026_09_findings.md` §5・§8) の
> `version_promotion_candidate`。governance spec (`docs/specs/fx_monthly_governance_v1.md` §3 末尾・§6)
> により logic 変更は人の判断を要し、その判断は得られている。

## Phase
2026-09 月次レビュー §8.1 (`docs/engine_review_2026_09_findings.md`)。engine_version v2.6 → **v2.7**。
spec §6.2 の 1 layer (engine) / 1 変更。

## Goal
v2.5 (FX-MAG-EXPANSION, PR #118) で導入した `_volatility_expansion_multiplier` を **config default で
無効化**する: `ProjectionConfig.volatility_expansion_max` の default を `1.8` → `1.0` に変える。
§5.1.3 の式 `multiplier = 1 + (max − 1) × activation` により乗数は恒等的に 1.0 となり、
`expected_close_change_bp = e_star × trailing_mean_abs_close_change_bp × (0.5 + 0.5 × conviction)`
(v2.4 までの magnitude) に戻る。コード (関数・不変量・FLAT 判定) は変えない。

根拠 (findings §5.1、4〜9 月 120 営業日 × 4 variant の replay、無介入系列は本番 forecast 164 件と
bit-identical): 平均誤差 −1.33bp (30.90 → 29.57、α)、中央値 −2.66bp、6 か月すべてで平均誤差が改善、
方向・FLAT 判定は不変。9 月の `inspect_magnitude_mapping` (RW 比 +7.41bp) は +3.19bp に下がり閾値 5.0 を
割る。

## Acceptance Criteria
- [ ] `src/ugh_quantamental/engine/projection_models.py` の `volatility_expansion_max` default が `1.0`。
      `Field(..., ge=1.0)` の下限はそのまま (1.0 は有効値)。`volatility_expansion_activation_floor` は触らない
- [ ] default config で `_volatility_expansion_multiplier(...)` が **任意の** catalyst / urgency /
      fire_probability に対して `1.0` を返す test (境界 0.0 / 1.0 と中間値を parametrize)。
      `volatility_expansion_max=1.8` を**明示**した config では従来の値を返す test を残す
      (式は変えていないことの固定)
- [ ] `engine_version` を **v2.7 に bump し、3 箇所の default を同期**:
      `src/ugh_quantamental/fx_protocol/automation_models.py` (`FxDailyAutomationConfig.engine_version`
      default)、`.github/workflows/fx-daily-protocol.yml` (`FX_ENGINE_VERSION: ${{ vars.FX_ENGINE_VERSION || 'v2.6' }}`)、
      `scripts/run_fx_daily_protocol.py` (`_env("FX_ENGINE_VERSION", "v2.6")` と docstring の
      `FX_ENGINE_VERSION : UGH engine version (default: v2.6)`)。3 箇所の不同期は v2.6 の出力が
      v2.5 として記録された実害 (#122) の再発になる。`tests/fx_protocol/test_automation.py` の
      `assert cfg.engine_version == "v2.6"` を v2.7 に更新する
- [ ] 既存の拡張 test の扱い: `tests/fx_protocol/test_forecasting.py` の
      `test_high_signals_reach_toward_max` / `test_monotonic_and_bounded` は `ProjectionConfig()`
      (default) を使っており、default 1.0 では `max == 1.0` で trivially 通るか、
      `test_high_catalyst_magnitude_exceeds_trailing_mean` のように**失敗する**。後者は
      「拡張を明示的に有効化した config (`volatility_expansion_max=1.8`) では trailing mean を超える」
      という形に書き換えて式の生存を固定し、default では超えないことを別 test で固定する。
      既存 test の変更はこの範囲に限る
- [ ] `docs/specs/fx_ugh_engine_v2.md` §5.1.3 に v2.7 の節 (または末尾の追記) を加える:
      default 1.0 で無効化した事実、理由 (findings §5.1 の数値を引用)、式と不変量は維持、
      再有効化は config で可能、`engine_version` v2.6 → v2.7 と 3 箇所 sync。§5.1.3 本文の
      「Defaults: `volatility_expansion_max = 1.8`」は v2.5〜v2.6 の値として残し、v2.7 の default を併記
- [ ] `scripts/replay_magnitude_counterfactual.py`: mode A は `REPLAY_EXPANSION_MAX = 1.8` に**固定済**
      (default 変更後も「v2.6 ならどう予測したか」を返し、C に畳まれない — 10 月の rollback 判定は
      この A と v2.7 実績の比較)。persisted forecast の検証は `EXPANSION_MAX_BY_ENGINE_VERSION`
      で version 別の上限を使うので、**`"v2.7": 1.0` を追加**する。それ以外は変えない。
      実装後に 2026-04-01〜実装日で実行し、v2.6 期間 164 件 + v2.7 期間の全件が検証されること
      (件数不足は script が fail する)
- [ ] `ruff check .` / `pytest -q` pass

## Scope
- IN: `src/ugh_quantamental/engine/projection_models.py` (default 1 行)、
      `src/ugh_quantamental/fx_protocol/automation_models.py`、`.github/workflows/fx-daily-protocol.yml`、
      `scripts/run_fx_daily_protocol.py` (version default + docstring)、
      `scripts/replay_magnitude_counterfactual.py` (version 別 check)、
      `tests/fx_protocol/test_forecasting.py` (上記の拡張 test のみ)、`tests/fx_protocol/test_automation.py`
      (version 文字列のみ)、`tests/engine/` (default 値 test があれば)、`docs/specs/fx_ugh_engine_v2.md`
- OUT: `forecasting.py` の関数本体 (`_volatility_expansion_multiplier` / `_direction_from_bp_with_epsilon` /
      magnitude 式)、`market_ugh_builder.py`、conviction 係数 (`0.5 + 0.5 × conviction` — findings §5.1 の
      mode B は 10 月に別途判断)、`expected_range` (v2.6 のまま)、state / hysteresis、baseline 戦略、
      protocol / schema / theory version、persistence / Alembic、`fx-analysis-pipeline.yml`

## Allowed Dependencies (optional)
なし。

## Implementation Hints (optional)
- 乗数の式は `forecasting.py` `_volatility_expansion_multiplier`: `1.0 + (config.volatility_expansion_max - 1.0) * activation`。
  max=1.0 で activation に関係なく 1.0。
- findings §5.1 の mode C は「乗数を 1.0 に強制」で、本 brief の default 変更と数値的に同値
  (script の `expansion=False` 分岐)。実装後、`python scripts/replay_magnitude_counterfactual.py` の
  mode A (default) が旧 mode C と一致することが最終確認になる。
- v2.7 の最初の週報は 10/9 (10/5〜10/9 週)。`.claude/skills/fx-weekly-report/SKILL.md` に v2.7 開始日の
  注記は不要 (version は forecast 行に記録される) だが、月次の `engine_versions_in_window` が 2 値になる
  10 月は stratify の確認を 11 月月次に残す。

## Required Outputs
- Branch name: `codex/fx-mag-expansion-revert`
- PR title: `feat(engine): disable the v2.5 volatility expansion by default (v2.7)`
- Expected files changed: 上記 IN の 8〜9 ファイル
- Required tests: default で乗数 1.0 (parametrize)、明示 1.8 で従来値、version 文字列 3 箇所の sync

## Done When
- All acceptance criteria are checked
- Completion Summary に、`replay_magnitude_counterfactual.py` を 9 月窓 (2026-09-03〜09-30) で実行した
  **mode C** の α `mean_error_delta_vs_random_walk_bp` (期待値 +3.19、findings §5.1) と、同じ run で
  mode A が +7.41 のまま (固定が効いている) であることを記載する
