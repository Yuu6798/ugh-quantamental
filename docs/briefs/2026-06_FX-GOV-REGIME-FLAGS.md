# Task Brief: FX-GOV-REGIME-FLAGS - 月次ガバナンスにレジーム層別フラグを追加

## Phase
engine_review_2026_06 §1 ★3 — 着手順序 §2 で FX-ANNOT-LIVE 後が望ましい
(ライブ週次でも機能させるため)。月次データ単体では独立着手可。
関連 spec: `docs/specs/fx_monthly_review_v1.md`,
`docs/specs/fx_monthly_governance_v1.md`.

## Goal
月次レビューの `compute_review_flags` の閾値が全レジーム混合の集計のみで評価され、
choppy 0% dir / high-vol 0% dir という壊滅的なレジーム別失敗が trending の好成績で
希釈され `keep_current_logic` を素通りする穴を塞ぐ。レジーム / ボラ層別の方向率が
閾値を下回ったら、混合指標が許容内でも flag を立てる。

## Acceptance Criteria
- [ ] `compute_review_flags` に新フラグ条件を追加: confirmed アノテーションが
      存在するレジーム (例 choppy) / ボラ (例 high) スライスで、UGH 方向率が
      新 module-level 閾値定数を下回ったら flag を emit
- [ ] 新閾値は `monthly_review.py` の既存 `THRESHOLD_*` 定数群と同じ様式
      (module-level, 明示, easily-changeable) で定義
- [ ] スライスに十分な観測 (既存 `THRESHOLD_MINIMUM_OBSERVATIONS` を流用) が
      無い場合は誤発火しない
- [ ] 新フラグが立つと governance の change-candidate 経路
      (`monthly_governance.py`) が `keep_current_logic` を出さない
      (5月窓データ: choppy 0% で flag が立つことを fixture で検証)
- [ ] `docs/specs/fx_monthly_review_v1.md` のフラグ一覧に追記、`pytest -q` /
      `ruff check .` clean

## Scope
- IN: `src/ugh_quantamental/fx_protocol/monthly_review.py`
  (`compute_review_flags` + 新 THRESHOLD 定数),
  `monthly_governance.py` (flag → decision の既存分岐への組込み),
  `monthly_review_exports.py` / `monthly_governance_exports.py` (出力に反映),
  `docs/specs/fx_monthly_review_v1.md`,
  `tests/fx_protocol/test_monthly_review*.py`
- OUT: engine 関数、forecast/outcome/eval schemas、persistence/Alembic、
  weekly レポート経路、baseline 戦略、アノテーション生成
  (= FX-ANNOT-LIVE の領分; 本 brief は既存アノテーションを消費するのみ)

## Allowed Dependencies (optional)
なし。

## Implementation Hints (optional)
- 既存フラグ (monthly_review.py:522 `compute_review_flags`) は forecast count /
  close_error_vs_random_walk / direction_deficit_vs_technical /
  state_hit_high+magnitude / annotation_coverage / provider lag-fallback /
  missing_window を集計で見るが、**レジーム層別は無い**。
- レジーム / ボラ別の dir_rate は既に monthly review のスライス集計
  (`## Regime Analysis` / `## Volatility Analysis` を生成する経路) が持っている。
  その集計結果を `compute_review_flags` の入力に渡す形が最小変更。
- フラグ id は既存命名に倣う (例 `regime_direction_collapse`,
  `volatility_direction_collapse`)。`monthly_governance.py:286` の
  `("keep_current_logic", "insufficient_data")` 分岐に新フラグが干渉しないこと。
- レジーム軸の enum 値は FX-ANNOT-LIVE / FX-STATEPROXY-REDEF と完全一致させる
  (trending/choppy, low/normal/high)。axes-mismatch は PR #104 型 churn の主因。

## Required Outputs
- Branch name: `codex/fx-gov-regime-flags`
- PR title: `feat(fx_protocol): regime/volatility-stratified monthly review flags`
- Expected files changed: `monthly_review.py`, `monthly_governance.py`,
  `*_exports.py`, spec, `tests/fx_protocol/test_monthly_review*.py`
- Required tests: choppy 0%/high-vol 0% スライスで flag 発火、観測不足で非発火、
  flag 時に keep_current_logic を出さない

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
