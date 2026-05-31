# Session Memory Index

`Yuu6798/semantic-ci-code` から移植した永続記憶ワークフローの索引ファイル。
詳細な convention は `CLAUDE.md` の「Session Memory / 永続記憶ワークフロー」
セクションを参照。

## 構成

各エントリは 1 行サマリー形式 — `- YYYY-MM-DD: <セッションの主題> (PR #NNN, #NNN, ...)`。
詳細サマリーは同じディレクトリの `YYYY-MM-DD.md` に保存。

## エントリ

(セッションが終了 (wrap-up トリガー) するごとに 1 行ずつ追記される。最新が下。)

- 2026-05-08: FX 通知メール改善 + `fx_protocol` リファクタ Phase 1〜3b 完走 + テストカバレッジ整理 spike (白紙化) + 永続記憶 convention 移植 (PR #92 / #93 / #94 / #95 / #96 / #97 / #98 / #99 / #100 / #103、#101 #102 close)
- 2026-05-30: 月末 engine review → 構造的問題 5 件を P0/P1/P2 で整理した planning doc 作成、Codex P2 review 13 rounds で 22 threads 全対応してマージ (PR #104)
- 2026-05-31: semantic-ci-code の dev-flow / session-end protocol / 設計・実装分離スキームを ugh-quantamental にローカライズ移植 (AGENTS.md handoff + CLAUDE.md tiered reading/8-step wrap-up + STATUS.md + wrap-up/new-brief skills + session-start hook + tests/discipline 3 gates)、Codex P2 review 3 件全対応してマージ (PR #106)

<!--
新規エントリのテンプレート:
- YYYY-MM-DD: <主題 1〜2 文> (PR #NNN: <タイトル>, ...)
-->
