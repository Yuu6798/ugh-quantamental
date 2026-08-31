#!/usr/bin/env python3
"""FX Price Alert — independent GitHub-native price/data-gap monitor.

Watches for USDJPY moves and pipeline stalls in the hours the daily forecast
protocol does not itself look at (between snapshots, over the weekend, or
when a scheduled run silently fails to produce a forecast) and reports them
as comments on a ``fx-alert`` labeled GitHub Issue.

**Independence contract**: this module imports **stdlib only**
(``urllib`` / ``json`` / ``os`` / ``re`` / ``sys`` / ``dataclasses`` /
``datetime``). It must never import anything from ``ugh_quantamental`` /
``fx_protocol`` — this monitor exists precisely so it keeps working even
when the prediction stack is broken. See ``docs/specs/fx_price_alert_v1.md``
for the full design (state-from-issue, threshold semantics, and the
deliberate weekend-only business-day simplification).

Environment variables
----------------------
GITHUB_TOKEN         : required. Token used for the GitHub REST API (Issues).
GITHUB_REPOSITORY    : required. ``owner/repo``, set automatically in Actions.
FX_ALERT_MOVE_BP      : move-alert threshold in 1/100-yen "pips" (default 60).
FX_ALERT_LINES         : comma-separated monitored price lines (default "161.50").
FX_ALERT_DATA_DIR      : read-only checkout of the ``fx-daily-data`` branch
                       (default "fx-daily-data"); reads
                       ``csv/latest/input_snapshot.json`` (+ ``manifest.json``).
FX_ALERT_SYMBOL        : Yahoo Finance chart symbol (default "USDJPY=X").
FX_ALERT_ISSUE_LABEL   : GitHub Issue label used to find/tag the alert issue
                       (default "fx-alert").

This script performs its own decisions with pure functions
(``evaluate_alerts`` and friends below) that take already-fetched data in
and return alerts/state out — no network access is needed to unit test them.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

JST = timezone(timedelta(hours=9))

DEFAULT_MOVE_BP = 60.0
DEFAULT_LINES_RAW = "161.50"
GAP_CUTOFF_HOUR_JST = 22  # 22:00 JST — see docs/specs/fx_price_alert_v1.md
DEFAULT_ISSUE_LABEL = "fx-alert"
DEFAULT_SYMBOL = "USDJPY=X"
DEFAULT_DATA_DIR = "fx-daily-data"

GITHUB_API = "https://api.github.com"

_STATE_MARKER_PREFIX = "<!-- fx-price-alert-state:"
_STATE_MARKER_SUFFIX = "-->"
_STATE_MARKER_RE = re.compile(
    re.escape(_STATE_MARKER_PREFIX) + r"(.*?)" + re.escape(_STATE_MARKER_SUFFIX),
    re.S,
)

_SPOT_FETCH_KEY = "fetch_failure:spot"
_FORECAST_FETCH_KEY = "fetch_failure:forecast"
_MOVE_KEY = "move"
_GAP_KEY = "gap"


# --------------------------------------------------------------------------
# Pure data model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Bar:
    """One OHLC bar (daily granularity — see spec for why)."""

    ts_utc: int
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class MonitoredLine:
    """A configured alert line, keeping the exact configured token.

    Keeping the raw string (rather than only the parsed float) makes the
    per-line state key stable regardless of float formatting, and makes the
    reported line label match exactly what the operator configured.
    """

    raw: str
    value: float

    @property
    def key(self) -> str:
        return f"line:{self.raw}"


@dataclass(frozen=True)
class ForecastMeta:
    """Metadata about the most recent forecast batch, read from fx-daily-data.

    ``current_spot`` is the exact spot the engine saw when the forecast was
    generated (``input_snapshot.json``'s ``current_spot``) — never a
    reconstructed OHLC close (see AC (a) / spec).
    """

    as_of_jst: date
    current_spot: float
    forecast_batch_id: str | None = None


@dataclass(frozen=True)
class Alert:
    """One newly-fired alert."""

    key: str
    title: str
    body: str


@dataclass(frozen=True)
class EvaluationResult:
    fired: tuple[Alert, ...]
    cleared_keys: tuple[str, ...]
    state: dict[str, bool]


# --------------------------------------------------------------------------
# Pure helpers: config parsing
# --------------------------------------------------------------------------


def parse_lines_env(raw: str | None) -> tuple[MonitoredLine, ...]:
    """Parse ``FX_ALERT_LINES`` into monitored lines.

    Empty/unset falls back to the single default line ``161.50`` (the grid
    lower bound — see spec). Blank comma-separated segments are skipped.
    """
    text = raw if raw and raw.strip() else DEFAULT_LINES_RAW
    lines: list[MonitoredLine] = []
    for part in text.split(","):
        token = part.strip()
        if not token:
            continue
        lines.append(MonitoredLine(raw=token, value=float(token)))
    return tuple(lines) if lines else (MonitoredLine(raw=DEFAULT_LINES_RAW, value=161.50),)


# --------------------------------------------------------------------------
# Pure helpers: schedule-aware business-day / cutoff rules
#
# Deliberately simplified: JST weekend-only, no holiday calendar. This
# monitor trades a little precision for staying independent of
# fx_protocol.calendar (see spec).
# --------------------------------------------------------------------------


def is_business_day_jst(day: date) -> bool:
    """True for Mon-Fri; False for Sat/Sun. No holiday awareness (see spec)."""
    return day.weekday() < 5


def target_business_date_jst(now_jst: datetime) -> date:
    """The business date whose forecast should exist by now.

    On a business day this is today. On a weekend it is the most recent
    preceding business day (Friday), per AC (c).
    """
    day = now_jst.date()
    while not is_business_day_jst(day):
        day -= timedelta(days=1)
    return day


def gap_cutoff_reached(now_jst: datetime) -> bool:
    """True once the day's data-gap cutoff has passed.

    On a business day the cutoff is exactly 22:00 JST (final cron 11:00 UTC
    + 2h grace). On a weekend the relevant (Friday's) cutoff has, by
    definition, already passed.
    """
    if not is_business_day_jst(now_jst.date()):
        return True
    return (now_jst.hour, now_jst.minute, now_jst.second) >= (GAP_CUTOFF_HOUR_JST, 0, 0)


# --------------------------------------------------------------------------
# Pure helpers: per-condition evaluation
# --------------------------------------------------------------------------


def evaluate_move(live_spot: float, baseline_spot: float, threshold_bp: float) -> tuple[bool, str]:
    """Return (active, detail) for the move-vs-baseline check (AC a)."""
    diff = live_spot - baseline_spot
    diff_bp = round(abs(diff) * 100.0, 6)
    active = diff_bp >= threshold_bp
    detail = (
        f"live spot {live_spot:.3f} vs last-forecast baseline {baseline_spot:.3f} "
        f"({diff:+.3f} / {diff_bp:.1f} pips, threshold {threshold_bp:.1f} pips)"
    )
    return active, detail


def evaluate_line_cross(latest_bar: Bar, line: MonitoredLine) -> bool:
    """True while the latest bar's traded range spans the monitored line."""
    lo = min(latest_bar.low, latest_bar.high)
    hi = max(latest_bar.low, latest_bar.high)
    return lo <= line.value <= hi


def evaluate_data_gap(
    now_jst: datetime, forecast: ForecastMeta | None
) -> tuple[bool, date, bool]:
    """Return (active, target_business_date, cutoff_reached) for AC (c)."""
    target = target_business_date_jst(now_jst)
    cutoff = gap_cutoff_reached(now_jst)
    last_as_of = forecast.as_of_jst if forecast is not None else None
    active = cutoff and (last_as_of is None or last_as_of < target)
    return active, target, cutoff


# --------------------------------------------------------------------------
# Pure orchestration: combine checks + suppression/re-arm state machine
# --------------------------------------------------------------------------


def _apply(
    key: str,
    active: bool,
    title: str,
    body: str,
    *,
    prev_state: dict[str, bool],
    new_state: dict[str, bool],
    fired: list[Alert],
    cleared_keys: list[str],
) -> None:
    """Update ``new_state[key]`` and record a fire/clear transition.

    Suppression: an already-active condition (``was_active`` True) does not
    re-fire while it stays active — only the True->False->True round trip
    re-arms it. The state key never encodes bar timestamps, so a condition
    that is still true on every poll stays silent after its first report.
    """
    was_active = bool(prev_state.get(key, False))
    new_state[key] = bool(active)
    if active and not was_active:
        fired.append(Alert(key=key, title=title, body=body))
    elif not active and was_active:
        cleared_keys.append(key)


def evaluate_alerts(
    *,
    bars: tuple[Bar, ...],
    live_spot: float | None,
    forecast: ForecastMeta | None,
    lines: tuple[MonitoredLine, ...],
    move_threshold_bp: float,
    now_jst: datetime,
    prev_state: dict[str, bool],
    spot_fetch_error: str | None = None,
    forecast_fetch_error: str | None = None,
) -> EvaluationResult:
    """Pure decision function: inputs in, alerts + new state out.

    No network access. ``prev_state`` is whatever
    :func:`parse_alert_state` reconstructed from the tracking Issue's prior
    comments (or ``{}`` for a fresh start / after a manual close).

    A condition this run cannot evaluate (its inputs came from a failed
    fetch) is left untouched in the returned state — carried forward as-is
    from ``prev_state`` — rather than guessed at or force-cleared.
    """
    fired: list[Alert] = []
    cleared_keys: list[str] = []
    new_state: dict[str, bool] = dict(prev_state)

    # --- spot/bar-dependent checks: move + line-cross -------------------
    _apply(
        _SPOT_FETCH_KEY,
        spot_fetch_error is not None,
        "USDJPY spot/bar fetch failed",
        spot_fetch_error or "",
        prev_state=prev_state,
        new_state=new_state,
        fired=fired,
        cleared_keys=cleared_keys,
    )
    if spot_fetch_error is None:
        if forecast is not None and live_spot is not None:
            active, detail = evaluate_move(live_spot, forecast.current_spot, move_threshold_bp)
            _apply(
                _MOVE_KEY,
                active,
                f"USDJPY move >= {move_threshold_bp:.0f} pips vs forecast baseline",
                detail,
                prev_state=prev_state,
                new_state=new_state,
                fired=fired,
                cleared_keys=cleared_keys,
            )
        if bars:
            latest_bar = bars[-1]
            for line in lines:
                active = evaluate_line_cross(latest_bar, line)
                detail = (
                    f"latest bar range [{latest_bar.low:.3f}, {latest_bar.high:.3f}] "
                    f"spans monitored line {line.raw}"
                )
                _apply(
                    line.key,
                    active,
                    f"USDJPY crossed monitored line {line.raw}",
                    detail,
                    prev_state=prev_state,
                    new_state=new_state,
                    fired=fired,
                    cleared_keys=cleared_keys,
                )

    # --- forecast-metadata-dependent check: data gap ---------------------
    _apply(
        _FORECAST_FETCH_KEY,
        forecast_fetch_error is not None,
        "fx-daily-data forecast metadata fetch failed",
        forecast_fetch_error or "",
        prev_state=prev_state,
        new_state=new_state,
        fired=fired,
        cleared_keys=cleared_keys,
    )
    if forecast_fetch_error is None:
        active, target, cutoff = evaluate_data_gap(now_jst, forecast)
        last_as_of = forecast.as_of_jst.isoformat() if forecast is not None else "unknown"
        detail = (
            f"expected forecast business date {target.isoformat()} (JST); "
            f"cutoff reached={cutoff}; last known forecast as_of={last_as_of}"
        )
        _apply(
            _GAP_KEY,
            active,
            f"FX daily protocol appears stalled (no {target.isoformat()} forecast)",
            detail,
            prev_state=prev_state,
            new_state=new_state,
            fired=fired,
            cleared_keys=cleared_keys,
        )

    return EvaluationResult(
        fired=tuple(fired), cleared_keys=tuple(cleared_keys), state=new_state
    )


# --------------------------------------------------------------------------
# Pure helpers: state <-> Issue comment text
# --------------------------------------------------------------------------


def encode_state_marker(state: dict[str, bool]) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"))
    return f"{_STATE_MARKER_PREFIX}{payload}{_STATE_MARKER_SUFFIX}"


def parse_alert_state(comment_bodies: list[str]) -> dict[str, bool]:
    """Reconstruct the previous alert state from an Issue's comments.

    ``comment_bodies`` must be oldest-first (GitHub's default listing
    order); the most recent comment carrying a state marker wins. This is
    the *only* source of persisted state — the runner itself is stateless
    between runs (see spec).
    """
    state: dict[str, bool] = {}
    for body in comment_bodies:
        if not body:
            continue
        match = None
        for match in _STATE_MARKER_RE.finditer(body):
            pass  # last marker in this body wins (defensive; expect <= 1)
        if match is None:
            continue
        try:
            parsed = json.loads(match.group(1))
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict):
            state = {str(k): bool(v) for k, v in parsed.items()}
    return state


def render_state_comment(
    fired: tuple[Alert, ...],
    cleared_keys: tuple[str, ...],
    state: dict[str, bool],
    now_utc: datetime,
) -> str | None:
    """Build the comment body to post, or ``None`` if nothing changed.

    Writing nothing when there is genuinely nothing new keeps steady-state
    runs silent (AC: alert-free runs write nothing). The one exception is a
    clear transition with no *new* fires — that must still be recorded so
    the next poll's re-arm check sees it (AC: clear/re-arm persistence).
    """
    if not fired and not cleared_keys:
        return None

    lines_out = [f"## FX Price Alert update — {now_utc.strftime('%Y-%m-%d %H:%M UTC')}", ""]
    for alert in fired:
        lines_out.append(f"### New: {alert.title}")
        lines_out.append(alert.body)
        lines_out.append("")
    for key in cleared_keys:
        lines_out.append(f"### Cleared: {key}")
        lines_out.append("")
    lines_out.append(encode_state_marker(state))
    return "\n".join(lines_out)


# --------------------------------------------------------------------------
# I/O: Yahoo Finance chart API (stdlib urllib only)
# --------------------------------------------------------------------------


def fetch_yahoo_daily(
    symbol: str = DEFAULT_SYMBOL,
    *,
    range_: str = "10d",
    interval: str = "1d",
    timeout: int = 30,
) -> tuple[float, tuple[Bar, ...]]:
    """Fetch live spot + recent daily bars from the Yahoo Finance chart API.

    Same endpoint ``fx_protocol.data_sources.YahooFinanceFxMarketDataProvider``
    and ``fx-intraday-fetch.yml`` already use in production. Re-implemented
    here (not imported) to keep this monitor independent of the prediction
    stack. Raises on any unexpected shape/failure — callers must catch and
    surface the failure as an alert rather than silently skipping.
    """
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https URL
        payload = json.loads(resp.read().decode("utf-8"))

    result = payload["chart"]["result"][0]
    meta = result.get("meta") or {}
    raw_spot = meta.get("regularMarketPrice")
    if raw_spot is None:
        raise ValueError("Yahoo Finance response missing meta.regularMarketPrice")
    spot = float(raw_spot)

    timestamps = result.get("timestamp") or []
    quote_list = (result.get("indicators") or {}).get("quote") or [{}]
    quote = quote_list[0] if quote_list else {}
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []

    bars: list[Bar] = []
    for i, ts in enumerate(timestamps):
        if i >= len(opens) or i >= len(highs) or i >= len(lows) or i >= len(closes):
            continue
        o, h, low, c = opens[i], highs[i], lows[i], closes[i]
        if None in (o, h, low, c):
            continue
        bars.append(Bar(ts_utc=int(ts), open=float(o), high=float(h), low=float(low), close=float(c)))
    return spot, tuple(bars)


# --------------------------------------------------------------------------
# I/O: fx-daily-data forecast metadata (local read-only checkout)
# --------------------------------------------------------------------------


def read_forecast_meta(data_dir: str) -> ForecastMeta:
    """Read the last forecast's metadata from a read-only fx-daily-data checkout.

    Reads ``csv/latest/input_snapshot.json`` directly. That file is written
    once per forecast batch and, on an idempotent retry, *copied* verbatim
    from the immutable ``csv/history/<date>/<batch_id>/input_snapshot.json``
    rather than rebuilt (see ``automation.py`` step 7a and the regression
    test in ``tests/fx_protocol/test_input_snapshot_invariant.py``) — so its
    ``current_spot`` is always the forecast-time spot, never a retry-time or
    reconstructed OHLC value.
    """
    snap_path = os.path.join(data_dir, "csv", "latest", "input_snapshot.json")
    with open(snap_path, encoding="utf-8") as fh:
        data = json.load(fh)

    as_of_raw = data["as_of_jst"]
    current_spot = float(data["current_spot"])
    as_of_business_date = date.fromisoformat(str(as_of_raw)[:10])

    batch_id: str | None = None
    manifest_path = os.path.join(data_dir, "csv", "latest", "manifest.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, encoding="utf-8") as fh:
                manifest = json.load(fh)
            batch_id = manifest.get("forecast_batch_id")
        except (OSError, json.JSONDecodeError):
            batch_id = None

    return ForecastMeta(
        as_of_jst=as_of_business_date, current_spot=current_spot, forecast_batch_id=batch_id
    )


# --------------------------------------------------------------------------
# I/O: GitHub REST (Issues) via urllib + GITHUB_TOKEN
# --------------------------------------------------------------------------


def _github_request(
    method: str, url: str, token: str, body: dict[str, object] | None = None, timeout: int = 30
) -> object:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "fx-price-alert-script",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https URL
        raw = resp.read()
    return json.loads(raw) if raw else None


def find_open_alert_issue(repo: str, token: str, label: str) -> dict | None:
    url = f"{GITHUB_API}/repos/{repo}/issues?state=open&labels={label}&per_page=5"
    issues = _github_request("GET", url, token) or []
    return issues[0] if issues else None  # type: ignore[index]


def fetch_issue_comment_bodies(repo: str, token: str, issue_number: int) -> list[str]:
    """Fetch every issue-comment body oldest-first, following REST pagination."""
    bodies: list[str] = []
    page = 1
    while True:
        url = (
            f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/comments"
            f"?per_page=100&page={page}"
        )
        comments = _github_request("GET", url, token) or []
        bodies.extend(c.get("body", "") for c in comments)  # type: ignore[union-attr]
        if len(comments) < 100:  # type: ignore[arg-type]
            break
        page += 1
    return bodies


def fetch_issue_state_bodies(repo: str, token: str, issue: dict) -> list[str]:
    """Return state-bearing Issue text in chronological source order.

    The initial state marker is written into the Issue body when the tracking
    issue is first created. Comments are appended afterwards, so parsing body
    first and then all paginated comments makes the newest valid marker win.
    """
    bodies = [str(issue.get("body") or "")]
    bodies.extend(fetch_issue_comment_bodies(repo, token, int(issue["number"])))
    return bodies


def create_alert_issue(repo: str, token: str, label: str, title: str, body: str) -> dict:
    url = f"{GITHUB_API}/repos/{repo}/issues"
    return _github_request(  # type: ignore[return-value]
        "POST", url, token, {"title": title, "body": body, "labels": [label]}
    )


def comment_on_issue(repo: str, token: str, issue_number: int, body: str) -> dict:
    url = f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/comments"
    return _github_request("POST", url, token, {"body": body})  # type: ignore[return-value]


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo or not token:
        print("[ERROR] GITHUB_REPOSITORY and GITHUB_TOKEN must both be set.", file=sys.stderr)
        return 1

    move_threshold_bp = float(os.environ.get("FX_ALERT_MOVE_BP", str(DEFAULT_MOVE_BP)))
    lines = parse_lines_env(os.environ.get("FX_ALERT_LINES"))
    data_dir = os.environ.get("FX_ALERT_DATA_DIR", DEFAULT_DATA_DIR).strip() or DEFAULT_DATA_DIR
    symbol = os.environ.get("FX_ALERT_SYMBOL", DEFAULT_SYMBOL).strip() or DEFAULT_SYMBOL
    label = os.environ.get("FX_ALERT_ISSUE_LABEL", DEFAULT_ISSUE_LABEL).strip() or DEFAULT_ISSUE_LABEL

    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)

    live_spot: float | None = None
    bars: tuple[Bar, ...] = ()
    spot_fetch_error: str | None = None
    try:
        live_spot, bars = fetch_yahoo_daily(symbol)
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError, OSError) as exc:
        spot_fetch_error = f"{type(exc).__name__}: {exc}"
        print(f"[WARN] spot/bar fetch failed: {spot_fetch_error}", file=sys.stderr)

    forecast: ForecastMeta | None = None
    forecast_fetch_error: str | None = None
    try:
        forecast = read_forecast_meta(data_dir)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        forecast_fetch_error = f"{type(exc).__name__}: {exc}"
        print(f"[WARN] forecast metadata fetch failed: {forecast_fetch_error}", file=sys.stderr)

    issue = find_open_alert_issue(repo, token, label)
    prev_state_bodies = fetch_issue_state_bodies(repo, token, issue) if issue else []
    prev_state = parse_alert_state(prev_state_bodies)

    result = evaluate_alerts(
        bars=bars,
        live_spot=live_spot,
        forecast=forecast,
        lines=lines,
        move_threshold_bp=move_threshold_bp,
        now_jst=now_jst,
        prev_state=prev_state,
        spot_fetch_error=spot_fetch_error,
        forecast_fetch_error=forecast_fetch_error,
    )

    comment_body = render_state_comment(result.fired, result.cleared_keys, result.state, now_utc)
    if comment_body is None:
        print("[INFO] fx-price-alert: no change, nothing written.")
        return 0

    if issue is None:
        created = create_alert_issue(repo, token, label, "FX Price Alert", comment_body)
        print(f"[INFO] fx-price-alert: created issue #{created.get('number')}")
    else:
        comment_on_issue(repo, token, issue["number"], comment_body)
        print(f"[INFO] fx-price-alert: commented on issue #{issue['number']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
