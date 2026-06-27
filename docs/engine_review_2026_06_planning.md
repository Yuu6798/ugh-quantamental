# Engine Review 2026-06 — End-of-Month Planning

最終更新: 2026-06-27

`docs/engine_review_2026_05_planning.md` の後継。2026-05 review は全フェーズ
(P0–P4 + Phase B) クローズ済みで、engine は v2.3 (variant-specific
`expected_range`、state v2.1、rare FLAT epsilon、conviction 意味論明文化) まで
landing 済み。本 doc は **6月のライブ運用ログ (6/1–6/26, 20 営業日)** を踏まえた
次サイクルの改良プログラムを定義し、`docs/briefs/` 配下の 5 本の Task Brief を
1 つの優先順位付きプログラムに束ねる。

## 0. 背景と Goal

### 背景 — 6月の定量観測

UGH (gamma 代表, 週次集計 16 評価) の月間集計:

| 週 | 相場 | 方向率 | レンジ率 | state率 | mean err |
|---|---|---|---|---|---|
| 第1週 6/1-5 | 小幅 | 75% | 75% | 100% | 7.0bp |
| 第2週 6/8-12 | 急落あり | 75% | 50% | 0% | 15.9bp |
| 第3週 6/15-19 | 急騰あり | 100% | 75% | 100% | 13.5bp |
| 第4週 6/22-26 | 穏やか | 100% | 75% | 0% | 9.7bp |
| **月計** | — | **87.5% (14/16)** | **69% (11/16)** | **50% (8/16)** | **≈11.5bp** |

誤差は大変動 3 日 (6/2 実+22bp, 6/12 実−36bp, 6/19 実+44bp) にほぼ集中。穏当日の
median は 5–9bp。

月次ガバナンスレビュー (`csv/analytics/monthly/202606/`、実体は 5 月窓 15 営業日・
アノテーション 100%) のレジーム別内訳が「なぜ外すか」を定量化している:

- regime: trending 100% dir / 12.2bp err vs **choppy 0% dir / 32.4bp err**
- volatility: low 83% / 10.4bp、normal 35% / 28.3bp、**high 0% / 64.5bp**

→ UGH の弱点は「平均的に少しズレる」ではなく **choppy / high-vol レジームでの
ほぼ全敗** という二極構造。6月の誤差 3 日はこの high-vol バケットそのもの。

### Primary Goal

二極構造の「悪い極」を縮める。具体的には (a) 大変動日の magnitude 過小予測の構造的
解消、(b) 急変動直後の過剰防御 (failure/FLAT 誤発火) の抑制、(c) これらを
レジーム別に**即時検知・検証できる観測基盤**の確立。

### Non-Goals

- baseline 戦略のロジック変更 (比較アンカーとして固定)
- 新しい外部データソース連携の追加
- variant 数の増減 (整理は将来サイクルの検討事項として §3 に記録のみ)
- core engine 不変条件 (pure functions / frozen schemas / naive-UTC /
  flush-only / import isolation / read-only replay / review-audit boundary) の逸脱

## 1. 観測から導いた 5 つの改良ポイント

| # | 主題 | 症状 | 根因 (file:line) | Brief |
|---|---|---|---|---|
| ★1 | magnitude 過小予測 | 6/19 実+44bp に予測+7bp | `forecasting.py:340-342` 平均アンカー × 係数≤1.0 | FX-MAG-EXPANSION |
| ★2 | 急変動直後の過剰防御 | 6/12 failure→FLAT が翌日反発を逸失 | `state.py:134-135` 単一 `regime_shock` で failure 発火 | FX-STATE-HYSTERESIS |
| ★2' | state_proxy が逆を測る | state率が週ごと 0↔100 振動 | `outcomes.py:254` 翌日 forecast state との一致 = 持続性指標 | FX-STATEPROXY-REDEF |
| ★3 | governance がレジーム失敗を覆い隠す | choppy 0% でも `keep_current_logic` | `monthly_review.py:522` 閾値が全集計のみ | FX-GOV-REGIME-FLAGS |
| ★4 | ライブのアノテーション欠落 | 週次 28/28 unannotated | `ai_annotations.py` が CI で 0 件産出 | FX-ANNOT-LIVE |

## 2. 着手順序と依存関係

```text
FX-ANNOT-LIVE (★4, enabler)  ──┐
                               ├─> FX-GOV-REGIME-FLAGS (★3)
FX-STATE-HYSTERESIS (★2) ──────┼─> FX-MAG-EXPANSION (★1)   [engine_version 直列]
                               └─> FX-STATEPROXY-REDEF (★2')[独立]
```

1. **FX-ANNOT-LIVE を最優先**。§1 の通りレジームが精度の最大決定因子であり、
   これがライブで付かないと ★1/★2/★3 の効果をレジーム別に検証できない。実は
   ★4 が他全ての検証の前提条件。
2. **FX-STATE-HYSTERESIS (v2.3→v2.4) → FX-MAG-EXPANSION (v2.4→v2.5)** を直列。
   magnitude 増幅は防御改善が landing した後でないと 6/12 型 (方向ミス+大変動)
   で裏目になりうるため。各 PR が単一 `engine_version` bump を持つ既存 cadence
   (#109 v2.1 / #110 v2.2 / #111 v2.3) を踏襲。
3. **FX-STATEPROXY-REDEF** は eval メトリクス変更で engine_version に非依存、
   いつでも着手可。
4. **FX-GOV-REGIME-FLAGS** は月次データ (既にアノテーション有) で独立に動くが、
   ライブ週次でも機能させるには ★4 を待つのが望ましい。

## 3. メモ — 将来サイクルの検討事項 (本サイクル Non-Goal)

- **variant の冗長性**: 6月を通じ alpha/gamma と beta/delta が分岐したのは 6/22
  の 1 回のみ。4 variants はほぼ相関。★1/★2 の検証と並行して ensemble 正式化 or
  variant 削減の余地を観測しておく。
- **月次レビューの窓ズレ / 命名**: `202606/` の中身が 5 月窓 (generated 6/1)。
  6/8–26 を反映した月次は 6/27 時点で未走行。次回 ~7/1 ラン前にディレクトリ命名
  規約 (レビュー実行月 vs レビュー対象月) を確認。
- **`ugh_v2_ensemble` 残存**: 月次成果物に ensemble 行が残るが STATUS では撤去
  済み。月次レビューが古い集計を参照していないか確認。

## 4. Acceptance Criteria (プログラム全体)

- [ ] 5 本の Task Brief が `docs/briefs/` に存在し、AGENTS.md フォーマット準拠
- [ ] 各 brief が名指す symbol / file:line が grep で実在確認済 (§1a gate)
- [ ] engine_version を bump する brief (★1/★2) が **3 箇所** の default を
      sync する旨を明記: `automation_models.py` default、
      `.github/workflows/fx-daily-protocol.yml` の `FX_ENGINE_VERSION`、
      `scripts/run_fx_daily_protocol.py` の `_env("FX_ENGINE_VERSION", ...)`
      default (+ 同 docstring)。後者を漏らすと手動/ローカル実行が旧バージョンで
      forecast を永続化し version-based audit/stratify を壊す
- [ ] 着手順序 (§2) と依存関係が各 brief の Scope に反映
- [ ] 各 brief が §5 の横断契約に矛盾しない

## 5. 横断契約 (cross-cutting contracts) — single source of truth

PR #114 のレビュー (4 round / 10 thread) で表面化した、複数 brief に跨る契約を
ここに一元化する。各 brief は本節を参照し、**ここと矛盾する記述を持たないこと**
(restate する場合も本節を canonical とする)。AGENTS.md §5.2 の「self-consistency
崩れを二度起こさない encode work」に該当。

### 5.1 ラベル語彙コントラクト ⚠️ axes-mismatch は PR #104 型 churn の主因

| 軸 | 値 | 共有する brief | 共有しない brief |
|---|---|---|---|
| regime | `trending` / `choppy` | FX-ANNOT-LIVE, FX-GOV-REGIME-FLAGS | — |
| volatility | `low` / `normal` / `high` | FX-ANNOT-LIVE, FX-GOV-REGIME-FLAGS | — |
| lifecycle state | `dormant`/`setup`/`fire`/`expansion`/`exhaustion`/`failure` (`LifecycleState`, `schemas/enums.py:25-33`) | FX-STATEPROXY-REDEF | regime/vol 軸とは**別物** |

- regime/vol と lifecycle-state は**絶対に混同しない**。FX-STATEPROXY-REDEF の
  realized ラベルは LifecycleState で導出する (regime/vol 軸の流用は category
  error)。
- AI suggestion 経路 (`generate_ai_annotations`) は現状 `mixed` を出すため、
  共有語彙に正規化してから effective label に昇格させる (AI > fallback precedence)。
- ⚠️ **regime/volatility は市場由来であって performance 由来であってはならない**。
  現状 live AI/default 経路は regime を `direction_hit`、volatility を
  `close_error_bp` から導出しており (循環)、これだと「choppy 0% dir」が定義上
  自明になり ★3 GOV フラグの前提が崩れる。これら 2 軸は OHLC/市場統計のみから
  導出する (FX-ANNOT-LIVE で是正)。

### 5.2 engine_version の 3 箇所 sync

bump 時は必ず: `automation_models.py` default / `fx-daily-protocol.yml` の
`FX_ENGINE_VERSION` / `scripts/run_fx_daily_protocol.py` の `_env` default
(+ docstring)。漏れると手動/ローカル実行が旧バージョンで永続化し audit/stratify
を破壊。

### 5.3 live-path E2E 原則

「単体テストは通るが live artifact は変わらない」抜けを禁止。アノテーション・
state・governance の変更は、実エントリポイント (`run_annotation_analytics` /
`rebuild_weekly_report` / `run_full_workflow` / `compute_review_flags`→
`classify_judgment`) を通すテストで効果を assert する。

### 5.4 メトリクス semantics の versioning

永続メトリクス列の意味を rollout 跨ぎで in-place 変更しない。rename / 新メトリクス
追加、または schema/protocol version bump + 集計時 filtering のいずれかを採る
(report 経路は theory/engine version でしか stratify しないため)。
