# Session Memory Index

`Yuu6798/semantic-ci-code` から移植した永続記憶ワークフローの索引ファイル。詳細な convention は `CLAUDE.md` の Session Memory セクションを参照する。

## 構成

各エントリは 1 行サマリー形式。詳細サマリーは同じディレクトリの `YYYY-MM-DD.md` に保存する。

## エントリ

- 2026-05-08: FX 通知メール改善 / `fx_protocol` refactor Phase 1 / 永続記憶 convention 移植 ほか (PR #92-#100/#103)。詳細は `archive/2026-05/2026-05-08.md`
- 2026-05-30: engine review 2026-05 planning doc (P0/P1/P2)、Codex 13 rounds / 22 threads (PR #104)。詳細は `archive/2026-05/2026-05-30.md`
- 2026-05-31: dev-flow / session-end protocol を移植 (AGENTS.md、tiered CLAUDE.md、wrap-up / new-brief skills、discipline gates、PR #106)。詳細は `archive/2026-05/2026-05-31.md`
- 2026-06-01 (S1/S2): engine review 2026-05 を全クローズ — v2.1〜v2.3 (#107〜#111)、conviction spec + Option B (#112)、Milestone 18 の PLANS.md 同期。詳細は `archive/2026-06/2026-06-01.md`
- 2026-06-27: 2026-06 engine review program (planning doc + Task Brief 5 本、PR #114、Codex 8 rounds)。regime ラベルの循環を検出。詳細は `archive/2026-06/2026-06-27.md`
- 2026-06-28: 2026-06 の 5 briefs を全実装 (#116〜#120)、engine default v2.5 (ANNOT-LIVE / HYSTERESIS / MAG-EXPANSION / STATEPROXY-REDEF / GOV-REGIME-FLAGS)。詳細は `archive/2026-06/2026-06-28.md`
- 2026-10-01: 2026-09 月次レビュー — 9 月の RW 比 +141bp は 3 日 (conviction 上限の順張り反転 × v2.5 拡張項) に集中。replay で拡張項無効化が 6 か月すべて改善 → **engine v2.7** (#134)、fixing 前着地の繰り越し (#135)、findings + briefs + replay script (#133、Codex 9 rounds / 13 件)、policy encode (#136)。
- 2026-10-08: UGH の売買価値の切り分け (方向 60% は実在、conviction 逆相関で magnitude が打ち消す、合議は最悪部分集合、順位は政策ショック 8 日) と仮想売買試算 (合議・GPT-M3・Fable-VR1・1 月拡張・v2.7 再計算)。執行層 v1 の spec + brief FX-EXEC-LAYER / FX-EXEC-REPORTING を起草。9/29 yahoo 退化 bar を発見・訂正。
- 2026-10-08 (2): PR #138 merge (Codex 21 rounds / 50 件、ユーザー判断で締切) → FX-EXEC-LAYER を並列 agent 3 体 + レビュー agent 2 体で実装、PR #139 (open)。REPORTING brief はゲート整合性 (期待日 = 営業日 − 明示除外、live 欠落は除外まで block) に収束。follow-up: labeled_observations の版列、/new-brief の欠落経路 checklist。

<!--
新規エントリのテンプレート:
- YYYY-MM-DD: <主題 1-2 文> (PR #NNN: <タイトル>, ...)
-->
