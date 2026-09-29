"""Stand-in for the `claude` CLI used by tests/unit/test_claude_code.py. No network, no model, no secret.

The test writes an executable shim whose shebang is `sys.executable` and which runs this file. Behaviour:
- FAKE_CLAUDE_SCENARIO picks the answer (see `answer`); a comma-separated list gives one scenario per call,
  the last one repeating (e.g. `invalid_structured,quota_epoch`). `fixture:<name>` prints
  tests/fixtures/llm/claude_cli/<name>.json as is;
- FAKE_CLAUDE_EXIT overrides the exit code of every scenario that prints JSON (is_error and the exit code
  are independent in the real CLI too);
- FAKE_CLAUDE_LEAK=1 appends the value of CLAUDE_CODE_OAUTH_TOKEN and an `sk-ant-` key shape to every error
  text, after FAKE_CLAUDE_PAD filler characters, to prove the runner redacts them;
- FAKE_CLAUDE_LOG names a JSON-lines journal: one line per call with argv, stdin, cwd, the scenario played
  and whether ANTHROPIC_API_KEY was visible (its value is never written);
- like the real CLI it rejects a call without `-p --output-format json`, and it emulates bare mode
  (`--bare`: OAuth never read, so the call fails) to make a regression visible end to end.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

RESET_EPOCH = 1790000000  # 2026-09-21T14:13:20Z
VALID = {"title": "from structured_output", "score": 7}
INVALID = {"title": 5}
FAKE_KEY_SHAPE = "sk-" + "ant-api03-FAKEfake0123456789"  # built here: the secret scanners read this file too
CLI_FIXTURES = Path(__file__).resolve().parent / "llm" / "claude_cli"


def journal(entry_for: Callable[[int], dict[str, Any]]) -> int:
    """Append `entry_for(n)` to the journal, n being how many calls were logged before it; returns n."""
    path = os.environ.get("FAKE_CLAUDE_LOG")
    if not path:
        entry_for(0)
        return 0
    with open(path, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        previous = sum(1 for line in fh if line.strip())
        fh.write(json.dumps(entry_for(previous)) + "\n")
        fh.flush()
        fcntl.flock(fh, fcntl.LOCK_UN)
    return previous


def pick_scenario(call: int) -> str:
    scenarios = [s.strip() for s in os.environ.get("FAKE_CLAUDE_SCENARIO", "ok").split(",") if s.strip()] or ["ok"]
    return scenarios[min(call, len(scenarios) - 1)]


def leak() -> str:
    """Secrets appended to error texts when FAKE_CLAUDE_LEAK=1 (empty otherwise)."""
    if os.environ.get("FAKE_CLAUDE_LEAK") != "1":
        return ""
    pad = "x" * int(os.environ.get("FAKE_CLAUDE_PAD", "0"))
    return f" {pad}token {os.environ.get('CLAUDE_CODE_OAUTH_TOKEN', '')} key {FAKE_KEY_SHAPE}"


def invalid_structured() -> dict[str, Any]:
    secret = leak()
    return {"title": "ok", "score": secret} if secret else dict(INVALID)


def result(
    text: str | None,
    *,
    call: int,
    structured: Any = None,
    is_error: bool = False,
    subtype: str = "success",
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "result",
        "subtype": subtype,
        "is_error": is_error,
        "duration_ms": 1234,
        "duration_api_ms": 1000,
        "num_turns": 2,
        "session_id": f"fake-session-{call}",
        "total_cost_usd": 0.0123,
        "usage": {
            "input_tokens": 120,
            "cache_creation_input_tokens": 30,
            "cache_read_input_tokens": 400,
            "output_tokens": 55,
        },
        "modelUsage": {
            "claude-haiku-fake": {"inputTokens": 10, "outputTokens": 3},
            "claude-sonnet-fake": {"inputTokens": 110, "outputTokens": 52},
        },
    }
    if text is not None:
        payload["result"] = text
    if structured is not None:
        payload["structured_output"] = structured
    payload.update(extra)
    return payload


def emit(payload: Any, code: int = 0) -> int:
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()
    override = os.environ.get("FAKE_CLAUDE_EXIT")
    return int(override) if override is not None else code


def answer(scenario: str, call: int) -> int:
    if scenario == "ok":
        return emit(result("fake answer", call=call))
    if scenario == "minimal":
        return emit({"type": "result", "is_error": False, "result": "bare minimum"})
    if scenario == "verbose_list":
        return emit([{"type": "system", "subtype": "init"}, result("from the result message", call=call)])
    if scenario == "list_no_result":  # verbose output cut before the result message
        return emit([{"type": "system", "subtype": "init"}, {"type": "assistant", "message": {"content": []}}])
    if scenario == "ok_mentions_limit":
        return emit(result("Chapter 3: what happens when the usage limit reached its rate limit", call=call))
    if scenario == "ok_structured":
        return emit(result(json.dumps({"title": "from result", "score": 1}), call=call, structured=VALID))
    if scenario == "ok_result_json":
        fenced = "```json\n" + json.dumps({"title": "from result", "score": 3}) + "\n```"
        return emit(result(fenced, call=call))
    if scenario == "invalid_structured":
        return emit(result(None, call=call, structured=invalid_structured()))
    if scenario == "schema_fail_then_ok":
        return emit(result(None, call=call, structured=INVALID if call == 0 else VALID))
    if scenario == "schema_fail_twice":
        if call == 0:
            return emit(result("Sure! Here is the answer you asked for.", call=call))
        return emit(result(None, call=call, structured=invalid_structured()))
    if scenario == "structured_error":  # the CLI's own structured-output retries ran out
        errors = [f"structured output does not match the schema{leak()}"]
        payload = result(None, call=call, is_error=True, subtype="error_max_structured_output_retries", errors=errors)
        return emit(payload, code=1)
    if scenario == "structured_retries_then_ok":
        if call == 0:
            return emit(
                result(None, call=call, is_error=True, subtype="error_max_structured_output_retries", errors=["bad"]),
                code=1,
            )
        return emit(result(None, call=call, structured=VALID))
    if scenario == "quota_epoch":
        epoch = os.environ.get("FAKE_CLAUDE_RESET_EPOCH", str(RESET_EPOCH))
        return emit(result(f"Claude AI usage limit reached|{epoch}{leak()}", call=call, is_error=True), code=1)
    if scenario == "quota_text":  # any error text, e.g. one of the official error reference
        text = os.environ.get("FAKE_CLAUDE_LIMIT_TEXT", "You've hit your session limit · resets 3:45pm (UTC)")
        extra: dict[str, Any] = {}
        if "FAKE_CLAUDE_API_STATUS" in os.environ:
            extra["api_error_status"] = int(os.environ["FAKE_CLAUDE_API_STATUS"])
        return emit(result(text + leak(), call=call, is_error=True, **extra), code=1)
    if scenario == "quota_stderr":
        sys.stderr.write(f"API Error: 429 rate_limit_error: Rate limit reached for requests{leak()}\n")
        return 1
    if scenario == "max_turns":
        errors = [f"Reached maximum turns (3){leak()}"]
        return emit(result(None, call=call, is_error=True, subtype="error_max_turns", errors=errors), code=1)
    if scenario == "crash":
        token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
        sys.stderr.write("x" * 5000 + f"\nfatal: runtime exploded (token {token}){leak()}\n")
        return 3
    if scenario == "garbage":
        sys.stdout.write(f"this is not json{leak()}\n")
        return 0
    if scenario == "slow":
        time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "60")))
        return emit(result("too late", call=call))
    if scenario.startswith("fixture:"):
        sys.stdout.write((CLI_FIXTURES / f"{scenario.removeprefix('fixture:')}.json").read_text(encoding="utf-8"))
        sys.stdout.flush()
        return int(os.environ.get("FAKE_CLAUDE_EXIT", "0"))
    sys.stderr.write(f"unknown FAKE_CLAUDE_SCENARIO {scenario!r}\n")
    return 4


def main() -> int:
    argv = sys.argv[1:]
    prompt = sys.stdin.read()

    def entry_for(call: int) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "argv": argv,
            "stdin": prompt,
            "cwd": os.getcwd(),
            "has_api_key": "ANTHROPIC_API_KEY" in os.environ,
            "scenario": pick_scenario(call),
        }
        if entry["scenario"] == "slow":  # a tool the CLI started: the runner must kill it on timeout
            entry["grandchild_pid"] = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"]).pid
        return entry

    call = journal(entry_for)
    scenario = pick_scenario(call)

    if "--bare" in argv:
        sys.stderr.write("Not logged in: bare mode reads ANTHROPIC_API_KEY only\n")
        return 1
    fmt_at = argv.index("--output-format") + 1 if "--output-format" in argv else len(argv)
    if "-p" not in argv or argv[fmt_at : fmt_at + 1] != ["json"]:
        sys.stderr.write("error: fake claude expects -p --output-format json\n")
        return 2
    return answer(scenario, call)


if __name__ == "__main__":
    sys.exit(main())
