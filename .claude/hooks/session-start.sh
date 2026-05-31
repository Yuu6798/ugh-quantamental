#!/bin/bash
# SessionStart hook: install the project plus the lint/test tooling so that
# ruff, pytest, and the /wrap-up discipline-test gate (pytest tests/discipline/)
# work in Claude Code on the web sessions. Synchronous so deps are guaranteed
# ready before the agent loop starts.
set -euo pipefail

# Only run in the remote (Claude Code on the web) environment; local dev
# machines manage their own virtualenv.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# SessionStart stdout is injected into the model context, so keep pip's
# progress / "Requirement already satisfied" chatter out of it: capture all
# install output and only surface it (on stderr) if the install fails.
# Idempotent: pip install -e is safe to re-run and leverages the cached
# container state.
#
# Dev tooling (ruff, pytest) is installed explicitly rather than via an
# extras group: this repo declares dev deps under PEP 735
# `[dependency-groups]`, which `pip install -e ".[dev]"` does NOT resolve.
log="$(mktemp)"
if ! python -m pip install -q -e . ruff pytest >"$log" 2>&1; then
  echo "session-start: pip install -e . + dev tooling failed:" >&2
  cat "$log" >&2
  exit 1
fi
echo "session-start: dev dependencies ready"
