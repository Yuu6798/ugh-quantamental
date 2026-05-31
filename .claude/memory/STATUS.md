# STATUS — ugh-quantamental

最終更新: 2026-05-31

このファイルは日々動く project snapshot（現在フェーズ・次の発行順序・直近
merged）を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、本ファイルは
自由に編集する。canonical な milestone 表は `PLANS.md`、フェーズ計画は
`docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序`
にリンクする（`CLAUDE.md` ではなく）。

## Phase

Milestones 1–17 完走（M1–12 = core engine→baselines、M13–17 = `fx_protocol`）。現在は月末 engine review（PR #104 `docs/engine_review_2026_05_planning.md`）で確定した P0/P1/P2 改善を Phase 1〜4 として順次実装するフェーズで、UGH v2 engine の expected_range variant 分離・state classifier sharpening・FLAT 動的 epsilon・per-variant scoreboard を target.yaml 駆動の small PR に分割しながら、並行して Milestone 18（monthly FX reporting）の spec 起草を待機させている。

## 次の発行順序

active queue — 未着手 / 進行中の Phase / Brief のみを置く。完走したら即
sweep して `## 直近 merged` へ移送する（wrap-up step 4）。

1. **Phase 1 (P0: range_hit 集計修正 + scoreboard 整理)** — `engine_review_2026_05_planning §3.2.1 + §6`。`ugh_v2_ensemble` 行追加（`forecast_batch_id` dedupe 必須）、`is_ugh_kind` 拡張、`fx_protocol.models` scope。Phase A target.yaml は §3.3 に template 済。1–2 PR 想定。
2. **Phase 2 (P0: state classifier sharpening)** — `§4`。softmax T=1.0→0.5、fire gate weighted sum、spec §5.3 改訂、`stratify_observations_by_versions` を `engine_version` 対応に拡張（Phase 3/B の bump 経路を unlock する systemic fix）。fire gate 数式は Open Question #1（着手前に spec author と議論）。
3. **Phase 3a (P1: FLAT 動的 epsilon)** — `§5`。`max(ratio * trailing, floor_bp)`、ratio sweep（0.3/0.5/0.7）を 60 サンプル replay で確認して最小値採用（Open Question #3）。
4. **Phase B (P1: range per-variant scoreboard)** — `§6 / §3.2.2`。target.yaml template 済。
5. **Phase 4 (P2: spec docstring 改訂)** — `§5.3` conviction 二重役割の spec 反映（コード変更なし）。
6. **Milestone 18 (monthly FX reporting)** — `PLANS.md` Next up。weekly report 出力を月次集計。spec を `docs/specs/` に起草してから着手。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移送
（wrap-up step 5、step 4 sweep の後に実行）。

- **PR #105** (2026-05-30) — wrap-up session memory for 2026-05-30。`.claude/memory/2026-05-30.md` + `_index.md` 追記。
- **PR #104** (2026-05-30) — `docs/engine_review_2026_05_planning.md`（870+ 行、計画書のみ・コード変更ゼロ）。Codex P2 review 13 rounds / 22 threads 全対応。本リポジトリ最多 round の base case。
