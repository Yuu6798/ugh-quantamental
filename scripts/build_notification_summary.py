"""Generate a short Japanese Markdown TL;DR of the latest FX daily run.

Reads ``forecast.csv``, ``scoreboard.csv``, ``run_summary.json``, and
``daily_report.md`` from the directory passed as the first argument
(default: ``csv/latest``), feeds them to Claude, and prints the model's
summary to stdout. Used by the email-notification step in the
``fx-daily-protocol`` workflow.

The underlying CSV/JSON inputs are deterministic; the natural-language
interpretation is delegated to the model. On missing ``ANTHROPIC_API_KEY``
or any API/import failure, the script prints nothing and exits 0 so the
notification still goes out with the raw ``daily_report.md`` body.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

SYSTEM_PROMPT = """\
あなたは定量的なFX予測パイプライン (USDJPY) の出力を、日次運用者向けに
簡潔な日本語Markdownで要約するアシスタントです。

出力フォーマット:
## TL;DR

- 5〜8項目の bullet list

要件:
- 入力に出現した数値・ラベルのみを使う。値を捏造しない。
- カバーすべき観点: UGH v2 モデル群の方向コンセンサス／不一致、期待変化の大きさ、
  dominant_state の分布、ベースラインとの比較、直近の方向的中率、前windowの outcome 状況。
- 売買推奨や方向の助言はしない。
- 具体的・定量的に。曖昧表現を避ける。
- 出力は ## TL;DR セクションのみ。前置き・後書き・コードフェンスは付けない。
"""


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else "(missing)"


def _build_user_message(base: Path) -> str:
    return (
        f"## forecast.csv\n{_read(base / 'forecast.csv')}\n\n"
        f"## scoreboard.csv\n{_read(base / 'scoreboard.csv')}\n\n"
        f"## run_summary.json\n{_read(base / 'run_summary.json')}\n\n"
        f"## daily_report.md\n{_read(base / 'daily_report.md')}\n"
    )


def main(argv: list[str]) -> int:
    base = Path(argv[1]) if len(argv) > 1 else Path("csv/latest")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return 0

    try:
        import anthropic
    except ImportError as exc:
        print(f"(LLM summary unavailable: {exc})", file=sys.stderr)
        return 0

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_message(base)}],
        )
    except anthropic.APIError as exc:
        print(f"(LLM summary unavailable: {exc})", file=sys.stderr)
        return 0

    text = "".join(block.text for block in response.content if block.type == "text")
    print(text.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
