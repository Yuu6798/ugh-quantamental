# Session Memory Index

`Yuu6798/semantic-ci-code` から移植した永続記憶ワークフローの索引ファイル。詳細な convention は `CLAUDE.md` の Session Memory セクションを参照する。

## 構成

各エントリは 1 行サマリー形式。詳細サマリーは同じディレクトリの `YYYY-MM-DD.md` に保存する。

## エントリ

- 2026-05-08: FX 通知メール改善 / `fx_protocol` refactor Phase 1 / 永続記憶 convention 移植 ほか (PR #92-#100/#103)。詳細は `archive/2026-05/2026-05-08.md`
- 2026-05-30: 月末 engine review の構造的問題 5 件を P0/P1/P2 で整理し planning doc を作成。Codex P2 review 13 rounds / 22 threads を処理 (PR #104)
- 2026-05-31: semantic-ci-code の dev-flow / session-end protocol / 設計を ugh-quantamental に移植。AGENTS.md handoff、CLAUDE.md tiered reading、wrap-up/new-brief skills、session-start hook、discipline gates を追加 (PR #106)
- 2026-06-01: ENGINE-P1A/P2A/P2B/P3A を小 PR で処理し、range_hit ensemble (#107)、report_window stratify (#108)、state v2.1 (#109)、rare FLAT epsilon v2.2 (#110) を main に反映。P2B/P3A の長期論点は spec/tests に外部化。
- 2026-06-01 (S2): engine review 2026-05 を全クローズ。Phase B variant-specific expected_range + v2.3 (#111)、Phase 4 conviction spec + §8 Option B (#112)。Milestone 18 monthly reporting が既存実装済みと判明し PLANS.md を実態同期 (branch, PR pending)。次は売買レイヤー planning。
- 2026-06-27: 6月デイリーログ分析→週報3本→月次集計→2026-06 engine review program (planning doc + Codex 用 Task Brief 5本) を起草し PR #114 マージ。Codex 8 round/20 thread を全 resolve (P1: state は forecast direction 非入力)。regime ラベルが performance 由来=循環と判明、要再検証。

<!--
新規エントリのテンプレート:
- YYYY-MM-DD: <主題 1-2 文> (PR #NNN: <タイトル>, ...)
-->
