# Task Brief: FX-MAG-EXPANSION - 大変動日の magnitude 過小予測の構造的解消

## Phase
engine_review_2026_06 §1 ★1 — 着手順序 §2 で FX-STATE-HYSTERESIS (v2.4) の
landing 後に着手 (engine_version v2.4 → v2.5)。

## Goal
`expected_close_change_bp` が直近平均変動幅にアンカーされ係数 ≤ 1.0 で縮むため、
平均超えの値幅を**原理的に出せない**現状 (6/19 実+44bp に予測+7bp, 誤差39bp) を
是正する。catalyst / urgency / fire が強い局面で magnitude が trailing mean を
**上回れる**ボラ拡張項を導入し、方向が正しい大変動日の range_hit と close error を
改善する。

## Acceptance Criteria
- [ ] 高 catalyst/urgency/fire の合成入力で `expected_close_change_bp` が
      `trailing_mean_abs_close_change_bp` を上回りうる (現状は構造的に不可)
- [ ] 平常 (低 catalyst) 入力では現状とほぼ同等の magnitude を維持し、過剰増幅で
      穏当日の誤差を悪化させない (回帰テストで境界を固定)
- [ ] 方向 (sign) と FLAT epsilon 判定 (`_direction_from_bp_with_epsilon`) の挙動は
      不変 — 本 brief は magnitude のみを対象
- [ ] `engine_version` を v2.5 に bump し、**3 箇所** の default を sync:
      `automation_models.py` default、`.github/workflows/fx-daily-protocol.yml`
      の `FX_ENGINE_VERSION`、`scripts/run_fx_daily_protocol.py` の
      `_env("FX_ENGINE_VERSION", ...)` default (+ 同 docstring L19)。
      script default を漏らすと手動/ローカル実行が旧バージョンで永続化し
      version-based audit/stratify を壊す
- [ ] `docs/specs/fx_ugh_engine_v2.md` に v2.5 magnitude 変更を追記

## Scope
- IN: `src/ugh_quantamental/fx_protocol/forecasting.py`
  (`build_ugh_variant_forecast` の magnitude 算出, 必要なら
  `engine/projection_models.py` に新 config field),
  `automation_models.py` (engine_version),
  `.github/workflows/fx-daily-protocol.yml`,
  `scripts/run_fx_daily_protocol.py` (FX_ENGINE_VERSION default + docstring),
  `tests/fx_protocol/test_forecasting*.py`, `tests/engine/`, spec doc
- OUT: state classifier (= FX-STATE-HYSTERESIS の領分)、`expected_range` の
  width/floor ロジック (`_build_range_from_projection_width`; center は magnitude
  経由で自然に追従するが scale/floor 定数は変更しない)、protocol schemas、
  persistence/Alembic、baseline 戦略

## Allowed Dependencies (optional)
なし。

## Implementation Hints (optional)
- 現状 (forecasting.py:340-342):
  `conviction_factor = 0.5 + 0.5 * projection_res.conviction` (∈[0.5,1.0]);
  `expected_close_change_bp = e_star * trailing_mean_abs_close_change_bp * conviction_factor`。
  上限 1.0 が平均超えを封じている。
- 案: catalyst/urgency/fire_probability から導く volatility-expansion multiplier
  (例 ∈[1.0, k], k は新 config 定数) を追加し、conviction_factor とは別系統で
  乗じる。これにより conviction (= reliability、§7 で magnitude scaler と明文化済)
  との二重役割を再混同させない (P2/§8 Option B decouple 決定を維持)。
- expansion multiplier の入力は projection/state が既に算出している量
  (`fire_probability`, `urgency`, `catalyst_strength` 等) を再利用し、新たな
  外部入力を増やさない。純関数・clamp 済・determinism を維持。
- FX-STATE-HYSTERESIS が先行する理由: magnitude 増幅は方向が当たっている前提で
  有効。6/12 型 (方向ミス+大変動) では増幅が裏目なので、防御 state 改善が
  landing してから入れる。Scope OUT に sign 不変を明記済。
- 検証: 6/19 相当 (高 catalyst + 正 e_star) で magnitude が平均超え、6/3 相当
  (穏当) で magnitude 据え置きの 2 ケースを test 化。

## Required Outputs
- Branch name: `codex/fx-mag-expansion`
- PR title: `feat(fx_protocol): volatility-expansion magnitude term for high-catalyst days (v2.5)`
- Expected files changed: `forecasting.py`, `projection_models.py`,
  `automation_models.py`, `.github/workflows/fx-daily-protocol.yml`,
  `scripts/run_fx_daily_protocol.py`, `tests/fx_protocol/`, `tests/engine/`, spec
- Required tests: 大変動日の magnitude 平均超え、穏当日据え置き、sign/epsilon 不変、
  engine_version sync

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
