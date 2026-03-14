# PR Review Semantic Audit Engine — v1 Specification

**Milestone: `review_audit_workflow`**
**Status: Planned (pre-implementation)**
**Depends on: Milestones 1–12 (complete)**

---

## 1. 目的

`review_autofix` bot は現在、lint・import・unused などの機械的レビュー指摘に対して、
rule-based に classify し、Codex に修正タスクを渡す構造を持っている。

ただし現状は、**その修正が reviewer の意図と本当に整合していたか** を監査する層がない。

本マイルストーンの目的は、以下を満たす **PR Review Semantic Audit Engine** を追加すること。

- pure / deterministic な意味監査エンジンを追加する
- projection / state と同じく `engine → persist → replay` パターンに従う
- bot 側にはまず **shadow audit** として統合する
- v1 では **push blocking / enforcement は行わない**
- raw text は監査証跡として保持するが、**engine input にはしない**

---

## 2. 設計原則

### 2.1 三層 feature extraction

raw text をそのまま engine に渡さない。以下の3層で処理する。

```
ReviewContext  (raw GitHub event data / raw review text)
    ↓  deterministic rule-based extractor
ReviewObservation  (symbolic intermediate layer: bool / enum / counts)
    ↓  normalization rules
ReviewIntentFeatures  (bounded [0, 1] floats)
    ↓  pure engine
ReviewAuditSnapshot / ReviewAuditEngineResult
```

### 2.2 pure engine の境界

engine が受け取るのは typed / normalized / bounded なモデルのみ。

**engine 内で扱ってはいけないもの:**
- review comment 原文
- diff hunk 原文
- GitHub API payload
- live repository state
- executor output の生テキスト

**engine が扱うもの:**
- `ReviewIntentFeatures`
- `FixActionFeatures | None`
- `ReviewAuditConfig`

### 2.3 raw text の扱い

raw text は消さない。ただし用途は audit trail / extractor replay 用であり、engine input ではない。

**persistence に保持するもの:**
- `review_context_json` — 生の ReviewContext (監査証跡)
- `observation_json` — ReviewObservation (extractor replay 用)
- `intent_features_json` — ReviewIntentFeatures
- `action_features_json` — FixActionFeatures (存在する場合)
- `engine_result_json` — ReviewAuditEngineResult

### 2.4 replay を二段に分ける

| 種別 | 目的 | 入力 |
|---|---|---|
| Engine replay | engine 数式の drift 検知 | 保存済み `intent_features` + `action_features` |
| Extractor replay | extractor ルールの drift 検知 | 保存済み `review_context_json` |

---

## 3. v1 の適用範囲

### v1 に含めるもの
- spec-first で review audit math を定義
- deterministic rule-based extractor
- pure review audit engine
- persistence / workflow / query / replay
- bot への shadow integration (non-enforcing)

### v1 に含めないもの
- push blocking / verdict に基づく auto reject
- live LLM extractor / non-deterministic semantic parser
- human approval UI
- cross-PR learning
- adaptive calibration / learned thresholds

---

## 4. モデル設計

### 4.1 ReviewObservation

raw `ReviewContext` から deterministic に抽出する symbolic 中間層。
extractor replay の基準点になる。

```python
class ReviewObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    has_path_hint: bool              # context.path is not None
    has_line_anchor: bool            # context.line or context.start_line is not None
    has_diff_hunk: bool              # context.diff_hunk is not None

    priority: str                    # "P0" | "P1" | "P2" | "P3"

    mechanical_keyword_hits: int = Field(ge=0)   # _AUTO_KEYWORDS 件数
    skip_keyword_hits: int = Field(ge=0)          # _SKIP_KEYWORDS 件数

    behavior_preservation_signal: bool  # "preserve" / "behavior" / "existing" 等
    scope_limit_signal: bool            # "minimal" / "only" / "scope" 等

    ambiguity_signal_count: int = Field(ge=0)   # "should" / "consider" 等の件数
    target_file_present: bool           # context.path is not None

    review_kind: str                 # "diff_comment" | "review_body"
```

### 4.2 ReviewIntentFeatures

engine に渡す normalized features。全フィールド [0, 1]。

```python
class ReviewIntentFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_clarity: float = Field(ge=0.0, le=1.0)
    locality_strength: float = Field(ge=0.0, le=1.0)
    mechanicalness: float = Field(ge=0.0, le=1.0)
    scope_boundness: float = Field(ge=0.0, le=1.0)
    semantic_change_risk: float = Field(ge=0.0, le=1.0)
    validation_intensity: float = Field(ge=0.0, le=1.0)
```

### 4.3 FixActionFeatures

post-action audit 用。意味差分を見るため十分に構造化する。

```python
class FixActionFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    changed: bool
    validation_ok: bool

    lines_changed: int = Field(ge=0)
    files_changed: int = Field(ge=0)

    target_file_match: float = Field(ge=0.0, le=1.0)    # 指摘ファイルに実際に触れたか
    line_anchor_touched: float = Field(ge=0.0, le=1.0)  # 指摘行付近を修正したか
    diff_hunk_overlap: float = Field(ge=0.0, le=1.0)    # diff hunk との重複率
    scope_ratio: float = Field(ge=0.0, le=1.0)          # 修正規模 (0=局所, 1=広域)
    validation_scope_executed: float = Field(ge=0.0, le=1.0)  # 実行した検証の広さ
    behavior_preservation_proxy: float = Field(ge=0.0, le=1.0)  # 振る舞い変更の推定量

    execution_status: str  # "succeeded" | "no_op" | "failed" | "timeout" | "skipped"
```

### 4.4 ReviewAuditConfig

```python
class ReviewAuditConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # PoR weights (合計 ≈ 1.0 を意図する — engine は正規化しない)
    w_clarity: float = Field(default=0.30, gt=0.0)
    w_locality: float = Field(default=0.25, gt=0.0)
    w_mechanical: float = Field(default=0.20, gt=0.0)
    w_scope: float = Field(default=0.25, gt=0.0)

    extractor_version: str = "v1"
    feature_spec_version: str = "v1"
```

### 4.5 ReviewAuditSnapshot (output contract)

```python
class ReviewAuditSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    audit_id: str

    por: float = Field(ge=0.0, le=1.0)           # Probability of Relevance
    delta_e: float | None = Field(default=None, ge=0.0, le=1.0)       # Semantic divergence
    mismatch_score: float | None = Field(default=None, ge=0.0, le=1.0)

    verdict: str  # "aligned" | "marginal" | "misaligned" | "insufficient_data"
```

### 4.6 ReviewAuditEngineResult

```python
class ReviewAuditEngineResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    audit_snapshot: ReviewAuditSnapshot
    intent_features: ReviewIntentFeatures
    action_features: FixActionFeatures | None
    config: ReviewAuditConfig
```

---

## 5. Extractor 設計

### 5.1 方針

v1 は **rule-based only**。

- repo の deterministic / replay-first 思想に合致する
- `classifier.py` の既存ルールと整合する
- same input → same observation を保証できる
- extractor_version を bump することでルール変更を追跡可能にする

### 5.2 `extract_review_observation(context: ReviewContext) -> ReviewObservation`

再利用する既存コード:

| 既存 | 再利用先 |
|---|---|
| `extract_priority()` (`classifier.py`) | `priority` フィールド |
| `_AUTO_KEYWORDS` | `mechanical_keyword_hits` |
| `_SKIP_KEYWORDS` | `skip_keyword_hits` |

抽出ルール:

```
has_path_hint           = context.path is not None
has_line_anchor         = context.line is not None or context.start_line is not None
has_diff_hunk           = context.diff_hunk is not None
priority                = extract_priority(context.body)
mechanical_keyword_hits = count_keywords(_AUTO_KEYWORDS, context.body)
skip_keyword_hits       = count_keywords(_SKIP_KEYWORDS, context.body)
behavior_preservation_signal = contains_any(["preserve", "behavior", "existing", "既存"], body)
scope_limit_signal      = contains_any(["minimal", "only", "scope", "最小", "のみ"], body)
ambiguity_signal_count  = count_keywords(["should", "consider", "提案"], body)
target_file_present     = context.path is not None
review_kind             = "diff_comment" if context.diff_hunk else "review_body"
```

### 5.3 `extract_review_intent_features(obs: ReviewObservation) -> ReviewIntentFeatures`

正規化ルール (v1):

| Feature | 計算方針 |
|---|---|
| `intent_clarity` | `has_path_hint`, `has_line_anchor`, `has_diff_hunk`, `priority_score` を加重合成。`P0→1.0, P1→0.75, P2→0.5, P3→0.25` |
| `locality_strength` | `has_line_anchor` + `has_diff_hunk` を中心に合成 |
| `mechanicalness` | `min(1.0, mechanical_keyword_hits / 3.0)` を基礎に `skip_keyword_hits` で減衰 |
| `scope_boundness` | `scope_limit_signal` が強いほど高い。`semantic_change_risk` が高いほど低い |
| `semantic_change_risk` | `ambiguity_signal_count` + skip / broad-change signal で上昇 |
| `validation_intensity` | `mechanicalness` が高ければ低め (lint のみ)。`semantic_change_risk` が高ければ高め (test 必要) |

### 5.4 `extract_fix_action_features(...) -> FixActionFeatures`

入力候補:
- executor result (execution_status, changed, validation_ok)
- git diff stats (lines_changed, files_changed)
- target path / touched lines (target_file_match, line_anchor_touched)
- diff hunk (diff_hunk_overlap)
- validation result (validation_scope_executed)

重要な観点:
- review が指した対象に実際に触れたか (`target_file_match`, `line_anchor_touched`)
- 修正規模が過大か (`scope_ratio`)
- validation scope が reviewer の意図に見合っていたか (`validation_scope_executed`)

---

## 6. Pure Engine 設計

### 6.1 `compute_por(intent: ReviewIntentFeatures, config: ReviewAuditConfig) -> float`

PoR は reviewer intent の「修正可能な明瞭さ / 局所性 / 機械性 / scope 制約」をまとめた relevance 指標。

```
PoR = w_clarity   * intent_clarity
    + w_locality  * locality_strength
    + w_mechanical * mechanicalness
    + w_scope     * scope_boundness
```

出力は `[0, 1]` にクランプする。

### 6.2 `compute_delta_e(intent: ReviewIntentFeatures, action: FixActionFeatures | None, config: ReviewAuditConfig) -> float | None`

- `action is None` のとき → `None` を返す (insufficient data)
- action がある場合のみ算出 (weighted L1 distance)

```
intent_vector = [
    locality_strength,
    mechanicalness,
    scope_boundness,
    validation_intensity,
]

action_vector = [
    target_file_match,
    diff_hunk_overlap,
    1.0 - min(1.0, scope_ratio),
    validation_scope_executed,
]

delta_e = clamp(weighted_l1(intent_vector, action_vector), 0.0, 1.0)
```

### 6.3 `compute_mismatch_score(por: float, delta_e: float | None) -> float | None`

```
delta_e is None → mismatch_score = None
それ以外        → mismatch_score = 0.5 * (1 - por) + 0.5 * delta_e
```

### 6.4 `compute_verdict(por: float, delta_e: float | None, action: FixActionFeatures | None) -> str`

| 条件 | verdict |
|---|---|
| `action is None` | `"insufficient_data"` |
| `por >= 0.7 and delta_e <= 0.2` | `"aligned"` |
| `por < 0.4 or delta_e > 0.6` | `"misaligned"` |
| それ以外 | `"marginal"` |

### 6.5 `build_audit_snapshot(audit_id, por, delta_e, mismatch_score, verdict) -> ReviewAuditSnapshot`

各スカラーを `[0, 1]` にクランプしてから `ReviewAuditSnapshot` を構築する。

### 6.6 `run_review_audit_engine(audit_id, intent, action, config) -> ReviewAuditEngineResult`

エントリーポイント。呼び出し順:

```
compute_por
→ compute_delta_e
→ compute_mismatch_score
→ compute_verdict
→ build_audit_snapshot
→ ReviewAuditEngineResult
```

---

## 7. Persistence 設計

### 7.1 ReviewAuditRunRecord (ORM)

```
テーブル名: review_audit_records
```

| カラム | 型 | 用途 |
|---|---|---|
| `run_id` | `String(64)` PK | ユニーク識別子 |
| `created_at` | `DateTime(timezone=False)` | naive UTC |
| `audit_id` | `String(128)` indexed | 監査対象識別子 |
| `pr_number` | `Integer` indexed | PR番号 |
| `reviewer_login` | `String(128)` nullable | レビュアー |
| `verdict` | `String(32)` indexed | engine verdict |
| `extractor_version` | `String(32)` | feature extractor バージョン |
| `feature_spec_version` | `String(32)` | feature spec バージョン |
| `review_context_json` | `JSON` | raw audit trail |
| `observation_json` | `JSON` | extractor replay 用 |
| `intent_features_json` | `JSON` | engine replay 入力 |
| `action_features_json` | `JSON` nullable | post-action audit (存在する場合) |
| `engine_result_json` | `JSON` | engine 出力 |

### 7.2 Serializer 境界

`ReviewContext` は frozen dataclass であり、既存の `dump_model_json()` は Pydantic BaseModel を前提としているため、専用関数を追加する。

```python
dump_review_context_json(context: ReviewContext) -> dict
load_review_context_json(payload: dict) -> ReviewContext
review_audit_payload_to_models(payload: dict) -> tuple[...]
```

---

## 8. Workflow 設計

### 8.1 ReviewAuditWorkflowRequest

```python
class ReviewAuditWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    audit_id: str
    pr_number: int = Field(ge=1)
    reviewer_login: str | None = None

    review_context_json: dict           # JSON-safe (dataclass ではなく dict で渡す)
    observation: ReviewObservation
    intent_features: ReviewIntentFeatures
    action_features: FixActionFeatures | None = None

    config: ReviewAuditConfig = Field(default_factory=ReviewAuditConfig)
    run_id: str | None = None
    created_at: datetime | None = None
```

### 8.2 run_review_audit_workflow(session, request) → ReviewAuditWorkflowResult

既存 workflow パターンと同じ:

```
run_review_audit_engine(...)
→ ReviewAuditRunRepository.save_run(session, ...)  # flush only
→ ReviewAuditRunRepository.load_run(session, run_id)
→ ReviewAuditWorkflowResult(run=..., engine_result=...)
```

---

## 9. Query / Replay 設計

### 9.1 Query

追加モデル:
- `ReviewAuditRunQuery` — audit_id / pr_number / verdict / created_at_from/to / limit / offset
- `ReviewAuditRunSummary` — run_id / created_at / audit_id / pr_number / verdict
- `ReviewAuditRunBundle` — 全カラムを復元した frozen dataclass

追加 reader:
- `list_review_audit_run_summaries(session, query) -> list[ReviewAuditRunSummary]`
- `get_review_audit_run_bundle(session, run_id) -> ReviewAuditRunBundle | None`

### 9.2 Replay

**Engine replay** (`replay_review_audit_run`):
- 保存済み `intent_features` + `action_features` から engine を再実行
- `ReviewAuditReplayComparison`: `exact_match`, `por_diff`, `delta_e_diff`, `mismatch_score_diff`, `verdict_match`

**Extractor replay** (`replay_review_audit_extractor_run`):
- 保存済み `review_context_json` から extractor を再実行
- `ReviewAuditExtractorReplayComparison`: `observation_match`, `intent_features_match`, per-field diff

この二段 replay により、engine drift と extractor drift を独立して検知できる。

---

## 10. Bot Integration (Shadow Mode)

### 10.1 Insertion Point 1 — `build_review_context()` 直後

```python
# shadow audit: pre-action (intent features only)
observation = extract_review_observation(context)
intent_features = extract_review_intent_features(observation)
# detect_only / propose_only ではここまで
```

### 10.2 Insertion Point 2 — executor 完了後 / validation 集約後

```python
# shadow audit: post-action (FixActionFeatures あり)
action_features = extract_fix_action_features(codex_result, diff_stats, ...)
# run_review_audit_workflow → persist
```

### 10.3 v1 の Shadow Mode 定義

| Bot モード | 実行ポイント | 効果 |
|---|---|---|
| `detect_only` | Point 1 のみ | pre-action audit, `verdict = "insufficient_data"` |
| `propose_only` | Point 1 のみ | pre-action audit, `verdict = "insufficient_data"` |
| `apply_and_push` | Point 1 + 2 | pre + post audit, 全 verdict が出る |

**v1 のルール:**
- `verdict` は log / persistence のみに使う
- `push_head_branch()` の判定には使わない
- user-visible reply への反映は任意であり、blocking には使わない

---

## 11. 実装マイルストーン

| Milestone | 成果物 | 完了条件 |
|---|---|---|
| **M1 — Spec 固定** | `docs/specs/ugh_review_audit_v1.md` (本ファイル) | 数式と境界条件がコード前に固まっている |
| **M2 — Extractor** | `feature_extractor.py` + tests | same input → same output、各シナリオを網羅テスト |
| **M3 — Engine** | `review_audit_models.py`, `review_audit.py` + tests | bounds / frozen / action=None edge case を全テスト |
| **M4 — Persistence** | ORM + repository + serializer + migration + tests | save/load roundtrip 成功、flush-only 維持 |
| **M5 — Workflow** | workflow request/result/runner + tests | engine → persist → reload → return が成立 |
| **M6 — Query / Replay** | query models/readers + engine/extractor replay + tests | engine drift と extractor drift を分離検知可能 |
| **M7 — Bot Integration** | `bot.py` 挿入 + logging | push 判定に影響しないことを確認 |

---

## 12. 新規追加ファイル

| File | Purpose |
|---|---|
| `docs/specs/ugh_review_audit_v1.md` | 本ファイル (spec) |
| `src/ugh_quantamental/review_autofix/feature_extractor.py` | ReviewContext → ReviewObservation → ReviewIntentFeatures |
| `src/ugh_quantamental/engine/review_audit_models.py` | review audit 用 typed models |
| `src/ugh_quantamental/engine/review_audit.py` | pure audit engine |
| `alembic/versions/0005_add_review_audit_records.py` | DB migration |
| `tests/engine/test_review_audit_models.py` | model tests |
| `tests/engine/test_review_audit.py` | engine tests |
| `tests/review_autofix/test_feature_extractor.py` | extractor tests |
| `tests/persistence/test_review_audit_repositories.py` | persistence tests |
| `tests/workflows/test_review_audit_workflow.py` | workflow tests |

## 13. 既存ファイルの変更対象

| File | Change |
|---|---|
| `src/ugh_quantamental/persistence/models.py` | `ReviewAuditRunRecord` を追加 |
| `src/ugh_quantamental/persistence/repositories.py` | `ReviewAuditRun` dataclass + repository 追加 |
| `src/ugh_quantamental/persistence/serializers.py` | review audit 用 serializer 追加 |
| `src/ugh_quantamental/workflows/models.py` | workflow request/result 追加 |
| `src/ugh_quantamental/workflows/runners.py` | `run_review_audit_workflow()` 追加 |
| `src/ugh_quantamental/query/models.py` | query / summary / bundle 追加 |
| `src/ugh_quantamental/query/readers.py` | list/get reader 追加 |
| `src/ugh_quantamental/replay/models.py` | replay request/comparison/result 追加 |
| `src/ugh_quantamental/replay/runners.py` | engine replay + extractor replay 追加 |
| `src/ugh_quantamental/review_autofix/bot.py` | shadow audit 挿入 |
| `src/ugh_quantamental/engine/__init__.py` | export 追加 |

---

## 14. 守るべき Invariant

1. **Import isolation を壊さない** — `review_audit_models.py` と `workflows/models.py` は SQLAlchemy なしで import 可能
2. **Engine は pure / no I/O** — `run_review_audit_engine` は typed models のみ受け取り、typed model を返す
3. **All Pydantic models are frozen + `extra="forbid"`**
4. **Workflows は flush-only / never commit** — 呼び出し元がトランザクションを所有する
5. **Extractor は v1 で deterministic** — same `ReviewContext` → same `ReviewObservation`
6. **raw text は保存するが engine に渡さない**
7. **replay は engine replay と extractor replay に分離する**

---

## 15. 検証コマンド

```bash
ruff check .   # lint
pytest -q      # tests
```

両コマンドはすべての変更後にクリーンに通過しなければならない。

---

## 16. 既存コードの再利用ポイント

| 既存 | 場所 | 再利用先 |
|---|---|---|
| `extract_priority()` | `classifier.py` | `feature_extractor.py` |
| `_AUTO_KEYWORDS` | `classifier.py` | `feature_extractor.py` |
| `_SKIP_KEYWORDS` | `classifier.py` | `feature_extractor.py` |
| `make_run_id()` | `workflows/models.py` | audit_id / run_id 生成 |
| `_normalize_created_at()` | `repositories.py` | `ReviewAuditRunRepository` |
| `dump_model_json()` / `load_model_json()` | `serializers.py` | review audit serializer の基礎 |
| `ReviewContext` frozen dataclass | `review_autofix/models.py` | raw audit trail の保存元 |

---

## 17. v1 の本質的な位置づけ

v1 の PoR は「完璧な semantic understanding」ではない。

v1 の目標は:

1. **deterministic extractor の確立** — 同じ入力から同じ特徴が出る基盤
2. **pure audit engine の境界固定** — feature ↔ engine ↔ output の契約を決める
3. **replay 可能な監査構造の導入** — 将来の enforcement / calibration に耐える検証基盤

つまり v1 の本質は、
PR review semantic audit を「正しさの最終解」として作ることではなく、
**将来の enforcement や calibration に耐える検証基盤として成立させること**である。
