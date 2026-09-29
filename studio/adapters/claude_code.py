"""`claude -p` backend of the LLM contract (ADR-001 decision 7; docs/research/apis.md [S25] [S26] [S28] [S29] [S35]).

Guarantees, each covered by tests/unit/test_claude_code.py:
- Credential sources that outrank the subscription (apis.md finding 41) are refused with ForbiddenAuth before
  the CLI starts. Checked: the child environment (`ANTHROPIC_API_KEY` even empty, `ANTHROPIC_AUTH_TOKEN`, a
  cloud-provider switch, `CLAUDE_CODE_SIMPLE` which `--bare` sets) and the settings files the CLI reads
  (user: `$CLAUDE_CONFIG_DIR/settings.json` or `$HOME/.claude/settings.json`; project and local:
  `<cwd>/.claude/settings.json`, `<cwd>/.claude/settings.local.json`, the local file at the git root; managed:
  `/etc/claude-code/managed-settings.json` and `managed-settings.d/*.json`) for `apiKeyHelper` or one of those
  variables in their `env` block. Not checked: server-managed settings and a Console key saved by an earlier
  login. A failed call whose error shows API-key billing ("Credit balance is too low", "Invalid API key", an
  apiKeyHelper error) also raises ForbiddenAuth.
- Never `--bare`: bare mode never reads OAuth credentials. The final argv is checked before every spawn.
- No shell. The prompt goes through stdin: it never shows in `ps`, and the variadic `--allowedTools` flag
  cannot swallow it.
- Structured output: `--json-schema` is passed, `structured_output` is preferred, `result` parsed as JSON is
  the fallback; the value is validated with `jsonschema`. One bounded retry with a corrective prompt, then
  LLMOutputInvalid.
- A call fails when `is_error` is true or the exit code is not 0, each on its own.
- Limit detection on failed calls only (see `classify_failure`): a plan limit raises QuotaExhausted with the
  reset time when the message gives one; a short server throttle (429) raises ClaudeRateLimited, a
  QuotaExhausted whose `reset_at` is a few minutes ahead. No structured reset field is documented for `-p`
  (apis.md findings 48-49): the patterns follow the official error reference [S35] and are a best estimate.
- Every exception raised once the CLI has started carries `usage`, the sum over all attempts of the call.
- Timeout kills the whole process group; messages are redacted before truncation and never carry a secret.

The CLI version is pinned on the execution machine; a CLI upgrade must pass the contract test (ADR-001):
`--bare` is announced as the future default of `-p`, which this runner cannot detect from the outside.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pwd
import re
import signal
import subprocess
import zoneinfo
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from jsonschema import exceptions as jsonschema_exceptions
from jsonschema import validators as jsonschema_validators
from jsonschema.protocols import Validator

from studio.adapters.base import AdapterSpec
from studio.adapters.llm_base import ForbiddenAuth, LLMCallError, LLMOutputInvalid, LLMResult, LLMUsage, QuotaExhausted
from studio.core.interfaces import StudioError
from studio.domain import AdapterKind, AdapterStatus, LicenseClass

CLAUDE_CODE_SPEC = AdapterSpec(
    id="claude-code",
    kind=AdapterKind.LLM,
    vram_gb=None,
    gpu_seconds_per_output_second=None,
    max_width=None,
    max_height=None,
    max_duration_s=None,
    # A remote service used under the subscription terms (the only remote creative service, MISSION §5).
    license_class=LicenseClass.CONDITIONAL,
    license_url="https://code.claude.com/docs/en/legal-and-compliance",
    # Becomes `retained` once the contract test passes on the execution machine with the pinned CLI.
    status=AdapterStatus.CANDIDATE,
)

BARE_FLAG = "--bare"
# Each of these makes Claude Code bill or authenticate outside the subscription (apis.md [S29]).
FORBIDDEN_ENV_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_SIMPLE",
)
MANAGED_SETTINGS_DIR = Path("/etc/claude-code")  # Linux location of file-based managed settings
SCHEMA_RETRIES = 1
STDERR_TAIL_CHARS = 2000
PROBLEM_CHARS = 500
SNIPPET_CHARS = 200
KILL_GRACE_S = 5.0
# Claude Code already retried a throttle with backoff before failing the call ([S35] "Automatic retries").
RATE_LIMIT_PAUSE = dt.timedelta(minutes=5)
# A dated reset without a year that lies further back than this is read as next year's date.
YEAR_ROLLOVER = dt.timedelta(days=180)
# Local caps set by our own flags: never a subscription limit, whatever their text says.
LOCAL_CAP_SUBTYPES = frozenset({"error_max_turns", "error_max_budget_usd", "error_max_structured_output_retries"})

FailureKind = Literal["quota", "rate", "api_key"]

# ------------------------------------------------------------------ failure patterns (best estimate, [S35])

# The call was billed, or about to be billed, to an API key instead of the subscription.
_API_KEY_PATTERNS = (
    re.compile(r"\bcredit balance is too low\b", re.IGNORECASE),
    re.compile(r"\binvalid api key\b", re.IGNORECASE),
    re.compile(r"\bapiKeyHelper\b", re.IGNORECASE),
    re.compile(r"\bdisabled api key authentication\b", re.IGNORECASE),
)
# Short server-side throttles that the reference says are not the plan quota; checked before plan limits
# because "(not your usage limit)" contains the words "usage limit".
_THROTTLE_PATTERNS = (
    re.compile(r"\btemporarily limiting requests\b", re.IGNORECASE),
    re.compile(r"\bnot your usage limit\b", re.IGNORECASE),
    re.compile(r"\bspend limit unavailable\b", re.IGNORECASE),
)
_RATE_PATTERNS = (
    re.compile(r"\brate[ _-]?limit", re.IGNORECASE),
    re.compile(r"\btoo many requests\b", re.IGNORECASE),
    re.compile(r"\(429\)"),
    re.compile(r"\b(?:api error|error|status|http)\W{0,3}429\b", re.IGNORECASE),
)
# A plan limit names what ran out: "You've hit your session limit", "... your org's monthly spend limit",
# "... your team's shared budget", "Usage limit reached", "5-hour limit reached", "Fable 5 limit reached".
_QUOTA_QUALIFIER_RE = re.compile(
    r"\b(?:session|weekly|week|daily|monthly|5[- ]?hours?|five[- ]hours?|opus|sonnet|haiku|fable|spend|usage|plan|"
    r"subscription)\b",
    re.IGNORECASE,
)
# What never is a plan limit: "Context limit reached", "Output token limit reached", "Turn limit reached",
# "Budget limit reached" (--max-budget-usd), "rate limit" (a throttle).
_NOT_QUOTA_RE = re.compile(
    r"\b(?:context|tokens?|turns?|output|input|images?|requests?|rate|budget|compaction|size|files?|pdf)\b",
    re.IGNORECASE,
)
_HIT_YOUR_RE = re.compile(
    r"\b(?:hit|reached|exceeded|exhausted)\s+your\s+(?P<what>(?:[\w'’.\-]+\s+){0,4}?)"
    r"(?P<noun>limit|budget|allowance|quota)\b",
    re.IGNORECASE,
)
_LIMIT_REACHED_RE = re.compile(
    r"(?<![\w'’.\-])(?P<what>[\w'’.\-]+)(?:\s+[\d.]+)?\s+limit\s+(?:reached|exceeded)\b", re.IGNORECASE
)

# ------------------------------------------------------------------ reset-time patterns

_EPOCH_RE = re.compile(r"\|\s*(\d{10,13})\b")
_RELATIVE_RE = re.compile(
    r"\bresets?\s+in\s+(?:(?P<hours>\d{1,3})\s*h(?:ours?|rs?)?)?\s*(?:(?P<minutes>\d{1,4})\s*m(?:in(?:ute)?s?)?)?",
    re.IGNORECASE,
)
_ANCHOR_RE = re.compile(
    r"\b(?:resets?|continuing\s+automatically\s+at|try\s+again\s+(?:at|after)|available\s+again\s+(?:at|on))\b",
    re.IGNORECASE,
)
_SEGMENT_END_RE = re.compile(r"[·∙•|;\n]")
_MONTH_NAMES = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?"
)
_MONTHS = {
    name: number
    for number, name in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)
}
_WEEKDAYS = {name: number for number, name in enumerate(("mon", "tue", "wed", "thu", "fri", "sat", "sun"))}
_ISO_DATE_RE = re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\b")
_MONTH_DAY_RE = re.compile(
    rf"\b(?P<month>{_MONTH_NAMES})\b\.?\s+(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\b(?:,?\s+(?P<year>\d{{4}})\b)?", re.IGNORECASE
)
_DAY_MONTH_RE = re.compile(
    rf"\b(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<month>{_MONTH_NAMES})\b\.?(?:,?\s+(?P<year>\d{{4}})\b)?", re.IGNORECASE
)
_WEEKDAY_RE = re.compile(
    r"\b(?P<weekday>mon(?:day)?|tue(?:s(?:day)?)?|wed(?:nesday)?|thu(?:r(?:s(?:day)?)?)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b\.?",
    re.IGNORECASE,
)
_TOMORROW_RE = re.compile(r"\btomorrow\b", re.IGNORECASE)
_TIME_RE = re.compile(r"(?<![\d:])(?P<hour>\d{1,2})(?!\d)(?::(?P<minute>\d{2}))?\s*(?P<ampm>[ap]\.?m\b\.?)?", re.IGNORECASE)
_TZ_PAREN_RE = re.compile(r"\((?P<tz>[A-Za-z][A-Za-z0-9_+\-/:]{0,63})\)")
_TZ_BARE_RE = re.compile(r"\b(?P<tz>(?:UTC|GMT)(?:\s*[+-]\s*\d{1,2}(?::?\d{2})?)?)(?![\w/])", re.IGNORECASE)
_TZ_OFFSET_RE = re.compile(r"^(?:UTC|GMT)\s*(?P<sign>[+-])\s*(?P<hours>\d{1,2})(?::?(?P<minutes>\d{2}))?$", re.IGNORECASE)

_SECRET_NAME_RE = re.compile(r"TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL", re.IGNORECASE)
_SECRET_VALUE_RE = re.compile(r"sk-ant-[A-Za-z0-9_\-]+")
_FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\s*\n(?P<body>.*)\n```\s*$", re.DOTALL)


# ------------------------------------------------------------------ errors that carry the call's usage


class ClaudeCallError(LLMCallError):
    """`claude -p` failed (crash, timeout, error result). `usage` sums every attempt, so the waste is logged."""


class ClaudeOutputInvalid(LLMOutputInvalid):
    """LLMOutputInvalid that keeps the usage of every attempt, so the cost ledger can log the waste."""


class ClaudeQuotaExhausted(QuotaExhausted):
    """A plan limit was hit; `usage` sums the attempts made before (e.g. a first answer that failed its schema)."""


class ClaudeRateLimited(ClaudeQuotaExhausted):
    """A short server-side throttle (429) that outlived the CLI's own retries: `reset_at` is a short pause."""

    def __init__(self, message: str, reset_at: dt.datetime | None = None, *, usage: LLMUsage | None = None) -> None:
        super().__init__(message, reset_at, usage=usage, kind="rate")


class ClaudeApiKeyInUse(ForbiddenAuth):
    """The failed call shows that an API key, not the subscription, authenticated it."""


def call_usage(exc: BaseException) -> LLMUsage | None:
    """Usage carried by an exception raised by ClaudeCodeRunner.run (None when it carries none)."""
    usage = getattr(exc, "usage", None)
    return usage if isinstance(usage, LLMUsage) else None


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


# ------------------------------------------------------------------ guards


def check_env(env: Mapping[str, str]) -> None:
    """Raise ForbiddenAuth when `env` would make `claude` leave the subscription. Names only, never values."""
    present = [name for name in FORBIDDEN_ENV_VARS if name in env]
    if present:
        raise ForbiddenAuth(
            f"refusing to run claude: {', '.join(present)} is set in the child environment "
            "(it would bypass the subscription's OAuth credentials); unset it, even if empty"
        )


def _home(env: Mapping[str, str]) -> Path | None:
    if env.get("HOME"):
        return Path(env["HOME"])
    try:
        return Path(pwd.getpwuid(os.getuid()).pw_dir)
    except KeyError:
        return None


def _git_root(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def settings_files(env: Mapping[str, str], cwd: Path, managed_dir: Path | None = MANAGED_SETTINGS_DIR) -> list[Path]:
    """Settings files the CLI would read for a session started in `cwd` with `env` (existing or not)."""
    files: list[Path] = []
    if env.get("CLAUDE_CONFIG_DIR"):
        files.append(Path(env["CLAUDE_CONFIG_DIR"]) / "settings.json")
    else:
        home = _home(env)
        if home is not None:
            files.append(home / ".claude" / "settings.json")
    cwd = cwd.resolve()
    files += [cwd / ".claude" / "settings.json", cwd / ".claude" / "settings.local.json"]
    root = _git_root(cwd)
    if root is not None and root != cwd:  # the local file lives at the repository root
        files.append(root / ".claude" / "settings.local.json")
    if managed_dir is not None:
        files.append(managed_dir / "managed-settings.json")
        drop_ins = managed_dir / "managed-settings.d"
        if drop_ins.is_dir():
            files += sorted(drop_ins.glob("*.json"))
    return files


def _read_settings(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None  # absent or unusable: it cannot configure a credential either
    return data if isinstance(data, dict) else None


def check_settings(files: Sequence[Path]) -> None:
    """Raise ForbiddenAuth when a settings file sets `apiKeyHelper` or a forbidden variable in `env`."""
    for path in files:
        data = _read_settings(path)
        if data is None:
            continue
        found = ["apiKeyHelper"] if data.get("apiKeyHelper") is not None else []
        env_block = data.get("env")
        if isinstance(env_block, dict):
            found += [f"env.{name}" for name in FORBIDDEN_ENV_VARS if name in env_block]
        if found:
            raise ForbiddenAuth(
                f"refusing to run claude: {path} sets {', '.join(found)} "
                "(it would bypass the subscription's OAuth credentials); remove it"
            )


def assert_no_bare(argv: Sequence[str]) -> None:
    """Raise ForbiddenAuth if `--bare` appears anywhere in argv (bare mode never reads OAuth credentials)."""
    for arg in argv:
        if arg == BARE_FLAG or arg.startswith(BARE_FLAG + "="):
            raise ForbiddenAuth("refusing to run claude with --bare: bare mode never uses the subscription")


def _check_word(name: str, value: str) -> None:
    if not value or value.startswith("-") or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError(f"invalid {name} {value!r}: non-empty, no whitespace, must not start with '-'")


def schema_validator(schema: dict[str, Any]) -> Validator:
    """Validator for `schema` (draft from `$schema`, 2020-12 by default); ValueError if the schema is invalid."""
    cls = jsonschema_validators.validator_for(schema)
    try:
        cls.check_schema(schema)
    except jsonschema_exceptions.SchemaError as exc:
        raise ValueError(f"invalid JSON Schema: {exc.message}") from exc
    return cls(schema)


def validation_problem(validator: Validator, value: Any) -> str | None:
    """Most relevant validation error as `path: message` (untruncated), or None when `value` is valid."""
    error = jsonschema_exceptions.best_match(validator.iter_errors(value))
    if error is None:
        return None
    path = "/".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"


# ------------------------------------------------------------------ output parsing


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _tail(text: str, limit: int) -> str:
    return text if len(text) <= limit else "…" + text[-(limit - 1) :]


def redact(text: str, env: Mapping[str, str]) -> str:
    """Remove secret-looking env values and Anthropic key shapes. Always redact before truncating: a cut
    secret no longer matches its value."""
    for name, value in env.items():
        if len(value) >= 8 and _SECRET_NAME_RE.search(name):
            text = text.replace(value, "[redacted]")
    return _SECRET_VALUE_RE.sub("[redacted]", text)


def _as_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0
    return int(value)


def parse_stdout(stdout: str) -> dict[str, Any] | None:
    """The result object printed by `--output-format json`, or None when stdout holds no result.

    Accepts a single object, a list of messages (verbose mode: the last message of type `result`; a list
    without one is a truncated output, hence None) and, as a fallback, a JSON value on the last non-empty
    line (a warning printed before it)."""
    text = stdout.strip()
    if not text:
        return None
    candidates = [text]
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        candidates.append(lines[-1])
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            results = [m for m in data if isinstance(m, dict) and m.get("type") == "result"]
            if results:
                return results[-1]
    return None


def _main_model(payload: Mapping[str, Any]) -> str:
    model = payload.get("model")
    if isinstance(model, str) and model:
        return model
    per_model = payload.get("modelUsage")
    if isinstance(per_model, dict) and per_model:
        # side calls (e.g. a small model for titles) also appear: the main model wrote the most tokens
        def output_tokens(name: str) -> int:
            stats = per_model[name]
            return _as_int(stats.get("outputTokens")) if isinstance(stats, dict) else 0

        return str(max(per_model, key=output_tokens))
    return ""


def _model_usage_totals(payload: Mapping[str, Any]) -> tuple[int, int, int, int]:
    per_model = payload.get("modelUsage")
    totals = [0, 0, 0, 0]
    if isinstance(per_model, dict):
        for stats in per_model.values():
            if isinstance(stats, dict):
                for i, key in enumerate(("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")):
                    totals[i] += _as_int(stats.get(key))
    return totals[0], totals[1], totals[2], totals[3]


def parse_usage(payload: Mapping[str, Any], fallback_model: str = "") -> LLMUsage:
    """Usage of one call; absent or malformed fields count as zero.

    `usage` covers the main agent loop only, while `modelUsage` adds subagents and compaction (SDKResultMessage
    in the Agent SDK reference, which advises `modelUsage` for accounting): each count is the larger of the two."""
    usage = payload.get("usage")
    u: Mapping[str, Any] = usage if isinstance(usage, dict) else {}
    model_in, model_out, model_read, model_creation = _model_usage_totals(payload)
    return LLMUsage(
        input_tokens=max(_as_int(u.get("input_tokens")), model_in),
        output_tokens=max(_as_int(u.get("output_tokens")), model_out),
        cache_read_tokens=max(_as_int(u.get("cache_read_input_tokens")), model_read),
        cache_creation_tokens=max(_as_int(u.get("cache_creation_input_tokens")), model_creation),
        duration_ms=_as_int(payload.get("duration_ms")),
        num_turns=_as_int(payload.get("num_turns")),
        model=_main_model(payload) or fallback_model,
    )


def add_usage(a: LLMUsage, b: LLMUsage) -> LLMUsage:
    return LLMUsage(
        input_tokens=a.input_tokens + b.input_tokens,
        output_tokens=a.output_tokens + b.output_tokens,
        cache_read_tokens=a.cache_read_tokens + b.cache_read_tokens,
        cache_creation_tokens=a.cache_creation_tokens + b.cache_creation_tokens,
        duration_ms=a.duration_ms + b.duration_ms,
        num_turns=a.num_turns + b.num_turns,
        model=b.model or a.model,
    )


def extract_structured(payload: Mapping[str, Any]) -> tuple[Any, str | None]:
    """(value, None) from `structured_output`, else from `result` parsed as JSON; (None, problem) otherwise."""
    structured = payload.get("structured_output")
    if structured is not None:
        return structured, None
    result = payload.get("result")
    if not isinstance(result, str) or not result.strip():
        return None, "no structured_output and an empty result"
    text = result.strip()
    fenced = _FENCE_RE.match(text)
    if fenced:
        text = fenced.group("body").strip()
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, f"the answer is not JSON ({exc.msg} at char {exc.pos})"


def error_text(payload: Mapping[str, Any]) -> str:
    """The human-readable error of a result: `result` (success arm) and `errors` (error arms)."""
    parts: list[str] = []
    for key in ("result", "error", "message"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            parts.append(value)
    errors = payload.get("errors")
    if isinstance(errors, list):
        parts.extend(str(e) for e in errors if e)
    return " | ".join(parts)


# ------------------------------------------------------------------ failure classification


def _is_plan_limit(text: str) -> bool:
    for match in _HIT_YOUR_RE.finditer(text):
        what = match.group("what")
        if _NOT_QUOTA_RE.search(what):
            continue
        if not what.strip() or match.group("noun").lower() != "limit" or _QUOTA_QUALIFIER_RE.search(what):
            return True
    for match in _LIMIT_REACHED_RE.finditer(text):
        what = match.group("what")
        if _QUOTA_QUALIFIER_RE.fullmatch(what) and not _NOT_QUOTA_RE.fullmatch(what):
            return True
    return False


def classify_failure(text: str, *, api_error_status: Any = None, subtype: str = "") -> FailureKind | None:
    """Kind of a FAILED call from its error text: "api_key" (billed to an API key), "rate" (short throttle),
    "quota" (a plan limit that holds until its reset), or None (any other failure).

    Best estimate built on the official error reference ([S35], consulted 2026-09-28); `-p` documents no
    structured field for it besides `api_error_status` (429 counts as a throttle when no plan limit is named)."""
    if subtype in LOCAL_CAP_SUBTYPES:
        return None
    if any(p.search(text) for p in _API_KEY_PATTERNS):
        return "api_key"
    if any(p.search(text) for p in _THROTTLE_PATTERNS):
        return "rate"
    if _is_plan_limit(text):
        return "quota"
    if any(p.search(text) for p in _RATE_PATTERNS) or (_as_int(api_error_status) == 429):
        return "rate"
    return None


# ------------------------------------------------------------------ reset time


def _zone(name: str | None, default: dt.tzinfo) -> dt.tzinfo:
    if not name:
        return default
    name = name.strip()
    if name.upper() in ("UTC", "GMT", "Z"):
        return dt.UTC
    offset = _TZ_OFFSET_RE.match(name)
    if offset:
        delta = dt.timedelta(hours=int(offset.group("hours")), minutes=int(offset.group("minutes") or 0))
        if delta >= dt.timedelta(hours=24):
            return default
        return dt.timezone(-delta if offset.group("sign") == "-" else delta)
    try:
        return zoneinfo.ZoneInfo(name)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        return default


def _cut(segment: str, match: re.Match[str]) -> str:
    return segment[: match.start()] + " " + segment[match.end() :]


_INVALID_TIME = (-1, -1)


def _clock_time(segment: str) -> tuple[int, int] | None:
    """(hour, minute) of the first time in `segment`, `_INVALID_TIME` when it is out of range, None when there
    is none; a bare number (no minutes, no am/pm) is not a time."""
    for match in _TIME_RE.finditer(segment):
        if match.group("minute") is None and not match.group("ampm"):
            continue
        hour, minute = int(match.group("hour")), int(match.group("minute") or 0)
        ampm = (match.group("ampm") or "").replace(".", "").lower()
        if ampm:
            if not 1 <= hour <= 12:
                return _INVALID_TIME
            hour = hour % 12 + (12 if ampm == "pm" else 0)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return _INVALID_TIME
        return hour, minute
    return None


def _dated(year: int, month: int, day: int, at: tuple[int, int], tz: dt.tzinfo) -> dt.datetime | None:
    try:
        return dt.datetime(year, month, day, at[0], at[1], tzinfo=tz)
    except ValueError:
        return None


def parse_reset_at(text: str, now: dt.datetime, local_tz: dt.tzinfo | None = None) -> dt.datetime | None:
    """Best-effort reset time in a limit message; None when nothing parses.

    Understood after "resets", "continuing automatically at", "try again at": `|<epoch seconds or ms>`,
    "in 2h 30m", a time ("3pm", "3:45pm", "15:00"), a date and a time in either order ("Oct 3, 9am",
    "9:00am Oct 3", "3 Oct 9am", "2026-08-09 00:00"), a weekday ("Mon 12:00am"), "tomorrow at 9am". The zone
    is the one named in parentheses or as "UTC"/"GMT±h", else `local_tz`, else the machine's zone. A time
    alone is its next occurrence after `now`; a weekday is its next occurrence; a date without a year is this
    year's, or next year's when it lies more than 180 days back. A bare hour without minutes or am/pm is ignored."""
    epoch = _EPOCH_RE.search(text)
    if epoch:
        seconds = int(epoch.group(1))
        if seconds > 10**11:
            seconds //= 1000
        return dt.datetime.fromtimestamp(seconds, dt.UTC)
    relative = _RELATIVE_RE.search(text)
    if relative and (relative.group("hours") or relative.group("minutes")):
        return now + dt.timedelta(hours=int(relative.group("hours") or 0), minutes=int(relative.group("minutes") or 0))
    anchor = _ANCHOR_RE.search(text)
    if not anchor:
        return None
    segment = text[anchor.end() : anchor.end() + 80]
    end = _SEGMENT_END_RE.search(segment)
    if end:
        segment = segment[: end.start()]

    tz_name: str | None = None
    tz_match = _TZ_PAREN_RE.search(segment) or _TZ_BARE_RE.search(segment)
    if tz_match:
        tz_name = tz_match.group("tz")
        segment = _cut(segment, tz_match)
    default_tz = local_tz or now.astimezone().tzinfo or dt.UTC
    tz = _zone(tz_name, default_tz)
    local_now = now.astimezone(tz)

    date: tuple[int | None, int, int] | None = None
    date_match = _ISO_DATE_RE.search(segment)
    if date_match:
        date = (int(date_match.group("year")), int(date_match.group("month")), int(date_match.group("day")))
    else:
        date_match = _MONTH_DAY_RE.search(segment) or _DAY_MONTH_RE.search(segment)
        if date_match:
            year = date_match.group("year")
            month = _MONTHS[date_match.group("month")[:3].lower()]
            date = (int(year) if year else None, month, int(date_match.group("day")))
    weekday_match = None if date_match else _WEEKDAY_RE.search(segment)
    tomorrow_match = None if date_match or weekday_match else _TOMORROW_RE.search(segment)
    for used in (date_match, weekday_match, tomorrow_match):
        if used:
            segment = _cut(segment, used)

    clock = _clock_time(segment)
    if clock == _INVALID_TIME:
        return None
    if clock is None and not (date_match or weekday_match or tomorrow_match):
        return None
    at = clock or (0, 0)

    if date is not None:
        year, month, day = date
        candidate = _dated(year if year is not None else local_now.year, month, day, at, tz)
        if candidate is not None and year is None and candidate < local_now - YEAR_ROLLOVER:
            candidate = _dated(local_now.year + 1, month, day, at, tz)
    elif weekday_match or tomorrow_match:
        if weekday_match:
            ahead = (_WEEKDAYS[weekday_match.group("weekday")[:3].lower()] - local_now.weekday()) % 7
        else:
            ahead = 1
        day_ = local_now.date() + dt.timedelta(days=ahead)
        candidate = _dated(day_.year, day_.month, day_.day, at, tz)
        if candidate is not None and weekday_match and candidate <= local_now:
            candidate += dt.timedelta(days=7)
    else:
        candidate = local_now.replace(hour=at[0], minute=at[1], second=0, microsecond=0)
        if candidate <= local_now:
            candidate = (local_now + dt.timedelta(days=1)).replace(hour=at[0], minute=at[1], second=0, microsecond=0)
    return candidate.astimezone(dt.UTC) if candidate is not None else None


# ------------------------------------------------------------------ runner


class ClaudeCodeRunner:
    """LLMRunner that shells out (without a shell) to `claude -p` on the subscription.

    `env=None` passes a snapshot of this process's environment at each call; a mapping is passed as the
    child's whole environment (it must then carry PATH and HOME for the CLI to find its credentials).
    `managed_settings_dir` is where file-based managed settings live (None skips them)."""

    def __init__(
        self,
        binary: str = "claude",
        timeout_s: float = 900,
        env: Mapping[str, str] | None = None,
        *,
        clock: Callable[[], dt.datetime] = _utc_now,
        local_tz: dt.tzinfo | None = None,
        managed_settings_dir: Path | None = MANAGED_SETTINGS_DIR,
    ) -> None:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        self.spec = CLAUDE_CODE_SPEC
        self.binary = binary
        self.timeout_s = timeout_s
        self._env = dict(env) if env is not None else None
        self._clock = clock
        self._local_tz = local_tz
        self.managed_settings_dir = managed_settings_dir

    def child_env(self) -> dict[str, str]:
        env = dict(os.environ) if self._env is None else dict(self._env)
        check_env(env)
        return env

    def check_credentials(self, env: Mapping[str, str], cwd: Path) -> None:
        """Refuse settings files that would authenticate the child with an API key."""
        check_settings(settings_files(env, cwd, self.managed_settings_dir))

    def build_argv(
        self,
        *,
        agent: str,
        model: str,
        json_schema: Mapping[str, Any] | None,
        max_turns: int,
        allowed_tools: Sequence[str],
    ) -> list[str]:
        _check_word("agent", agent)
        _check_word("model", model)
        if isinstance(max_turns, bool) or not isinstance(max_turns, int) or max_turns < 1:
            raise ValueError(f"max_turns must be a positive integer, got {max_turns!r}")
        if isinstance(allowed_tools, str):
            raise ValueError("allowed_tools must be a sequence of tool rules, not a string")
        for tool in allowed_tools:
            if not tool or tool.startswith("-") or "," in tool:
                raise ValueError(f"invalid tool rule {tool!r}: non-empty, no ',', must not start with '-'")
        argv = [
            self.binary,
            "-p",
            "--output-format",
            "json",
            "--model",
            model,
            "--max-turns",
            str(max_turns),
            "--agent",
            agent,
        ]
        if allowed_tools:  # an empty value would be an empty rule: no tool is pre-approved either way
            argv += ["--allowedTools", ",".join(allowed_tools)]
        if json_schema is not None:
            argv += ["--json-schema", json.dumps(json_schema, separators=(",", ":"))]
        assert_no_bare(argv)
        return argv

    def run(
        self,
        *,
        agent: str,
        prompt: str,
        model: str,
        json_schema: dict[str, Any] | None,
        max_turns: int,
        allowed_tools: Sequence[str],
        cwd: Path,
    ) -> LLMResult:
        env = self.child_env()
        validator = schema_validator(json_schema) if json_schema is not None else None
        argv = self.build_argv(
            agent=agent, model=model, json_schema=json_schema, max_turns=max_turns, allowed_tools=allowed_tools
        )
        cwd = Path(cwd)
        if not cwd.is_dir():
            raise ClaudeCallError(f"claude working directory does not exist: {cwd}")
        self.check_credentials(env, cwd)

        total = LLMUsage()
        current_prompt = prompt
        problem = ""
        for attempt_no in range(1 + SCHEMA_RETRIES):
            payload, total = self._attempt(argv, current_prompt, cwd, env, model, prior=total, schema_mode=validator is not None)
            session_id = str(payload.get("session_id") or "")
            if validator is None:
                result = payload.get("result")
                output = result if isinstance(result, str) else ""
                return LLMResult(output=output, usage=total, session_id=session_id, raw=payload)
            value, found = self._structured(payload)
            found = found or validation_problem(validator, value)
            if found is None:
                return LLMResult(output=value, usage=total, session_id=session_id, raw=payload)
            problem = _truncate(redact(found, env), PROBLEM_CHARS)
            if attempt_no < SCHEMA_RETRIES:
                current_prompt = corrective_prompt(prompt, problem, json_schema or {})
        raise ClaudeOutputInvalid(
            f"agent {agent}: output does not match the JSON Schema after {1 + SCHEMA_RETRIES} attempts: {problem}",
            usage=total,
        )

    # -------------------------------------------------------------- internals

    @staticmethod
    def _structured(payload: Mapping[str, Any]) -> tuple[Any, str | None]:
        if payload.get("is_error"):
            return None, f"structured output failed ({payload.get('subtype')}): {error_text(payload)}"
        return extract_structured(payload)

    def _attempt(
        self,
        argv: list[str],
        prompt: str,
        cwd: Path,
        env: Mapping[str, str],
        model: str,
        *,
        prior: LLMUsage,
        schema_mode: bool,
    ) -> tuple[dict[str, Any], LLMUsage]:
        """One spawn: (payload, usage so far) on success, else an exception that carries the usage so far."""
        assert_no_bare(argv)
        returncode, stdout, stderr = self._spawn(argv, prompt, cwd, env, prior)
        payload = parse_stdout(stdout)
        if payload is None:
            self._raise_for_limit(f"{stdout}\n{stderr}", env, prior)
            if returncode != 0:
                raise ClaudeCallError(
                    f"claude -p exited with code {returncode} without a JSON result; stderr: "
                    f"{_tail(redact(stderr.strip(), env), STDERR_TAIL_CHARS) or '(empty)'}",
                    prior,
                )
            raise ClaudeCallError(
                f"claude -p exited with code 0 without a JSON result (truncated output?): "
                f"{_truncate(redact(stdout.strip(), env), SNIPPET_CHARS) or '(empty)'}",
                prior,
            )
        total = add_usage(prior, parse_usage(payload, fallback_model=model))
        if not payload.get("is_error") and returncode == 0:
            return payload, total
        subtype = str(payload.get("subtype") or "")
        message = error_text(payload)
        self._raise_for_limit(
            f"{message}\n{stderr}", env, total, api_error_status=payload.get("api_error_status"), subtype=subtype
        )
        if schema_mode and "structured_output" in subtype:
            return {**payload, "is_error": True}, total  # handled as a schema failure (bounded retry)
        detail = message or stderr.strip()
        raise ClaudeCallError(
            f"claude -p failed (exit {returncode}, is_error {bool(payload.get('is_error'))}, subtype {subtype or 'n/a'}): "
            f"{_truncate(redact(detail, env), STDERR_TAIL_CHARS) or '(no message)'}",
            total,
        )

    def _raise_for_limit(
        self, text: str, env: Mapping[str, str], usage: LLMUsage, *, api_error_status: Any = None, subtype: str = ""
    ) -> None:
        kind = classify_failure(text, api_error_status=api_error_status, subtype=subtype)
        if kind is None:
            return
        snippet = _truncate(" ".join(redact(text, env).split()), SNIPPET_CHARS)
        if kind == "api_key":
            raise ClaudeApiKeyInUse(
                f"claude -p was authenticated by an API key, not the subscription (check apiKeyHelper, "
                f"ANTHROPIC_API_KEY and `claude /status`): {snippet}",
                usage,
            )
        now = self._clock()
        reset_at = parse_reset_at(text, now, self._local_tz)
        if kind == "rate":
            retry_at = reset_at if reset_at is not None and reset_at > now else now + RATE_LIMIT_PAUSE
            raise ClaudeRateLimited(f"Claude API throttled (retry at {retry_at.isoformat()}): {snippet}", retry_at, usage=usage)
        when = reset_at.isoformat() if reset_at else "unknown"
        raise ClaudeQuotaExhausted(f"Claude usage limit reached (reset at {when}): {snippet}", reset_at, usage=usage)

    def _spawn(self, argv: list[str], prompt: str, cwd: Path, env: Mapping[str, str], usage: LLMUsage) -> tuple[int, str, str]:
        try:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=dict(env),
                text=True,
                encoding="utf-8",
                errors="replace",
                start_new_session=True,  # own process group: a timeout kills the tools it spawned too
            )
        except FileNotFoundError as exc:
            raise ClaudeCallError(f"claude binary not found: {self.binary}", usage) from exc
        except OSError as exc:
            raise ClaudeCallError(f"cannot start {self.binary}: {exc.strerror}", usage) from exc
        try:
            stdout, stderr = proc.communicate(prompt, timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            _kill_group(proc)
            raise ClaudeCallError(f"claude -p timed out after {self.timeout_s:g}s; its process group was killed", usage) from None
        except BaseException:
            _kill_group(proc)
            raise
        return proc.returncode, stdout, stderr


def _kill_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.communicate(timeout=KILL_GRACE_S)
    except subprocess.TimeoutExpired:  # a descendant left the group and holds the pipes
        proc.kill()
        proc.wait()


def corrective_prompt(prompt: str, problem: str, schema: Mapping[str, Any]) -> str:
    return (
        f"Your previous answer was rejected: {problem}\n"
        "Reply again with a single JSON value that validates against this JSON Schema, and nothing else:\n"
        f"{json.dumps(schema, separators=(',', ':'))}\n\n"
        f"The original task follows.\n\n{prompt}"
    )
