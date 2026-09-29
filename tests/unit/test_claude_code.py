"""ClaudeCodeRunner against a fake `claude` executable (tests/fixtures/fake_claude.py): never `--bare`,
never an API key (environment or settings files), JSON and usage parsing, structured output, bounded schema
retry, limit classification on the official error messages, usage kept on every failure, redaction on every
message path, timeout and crash handling. No network, no real `claude -p`.

tests/fixtures/llm/claude_cli/ holds result objects whose shape is transcribed from the `SDKResultMessage`
type of the Agent SDK reference (https://code.claude.com/docs/en/agent-sdk/typescript, consulted
2026-09-28) and whose error texts come from the error reference (https://code.claude.com/docs/en/errors).
They are not recordings of a live `claude -p` run: recording one with the pinned CLI needs the human's
consent to spend quota (see the module's open issue)."""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from studio.adapters.claude_code import (
    CLAUDE_CODE_SPEC,
    FORBIDDEN_ENV_VARS,
    PROBLEM_CHARS,
    RATE_LIMIT_PAUSE,
    ClaudeApiKeyInUse,
    ClaudeCallError,
    ClaudeCodeRunner,
    ClaudeOutputInvalid,
    ClaudeQuotaExhausted,
    ClaudeRateLimited,
    add_usage,
    assert_no_bare,
    call_usage,
    classify_failure,
    extract_structured,
    parse_reset_at,
    parse_stdout,
    parse_usage,
    redact,
    settings_files,
)
from studio.adapters.llm_base import ForbiddenAuth, LLMOutputInvalid, LLMResult, LLMRunner, LLMUsage, QuotaExhausted
from studio.core.interfaces import StudioError
from studio.core.quota import Priority, QuotaManager
from studio.domain import AdapterKind, AdapterStatus

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FAKE_CLAUDE = FIXTURES / "fake_claude.py"
CLI_OUTPUTS = FIXTURES / "llm" / "claude_cli"
T0 = dt.datetime(2026, 9, 28, 10, 0, tzinfo=dt.UTC)  # a Monday
PROMPT = "Find three outlier formats for channel A.\nAnswer in English."
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"title": {"type": "string"}, "score": {"type": "integer", "minimum": 0}},
    "required": ["title", "score"],
    "additionalProperties": False,
}
FAKE_USAGE = LLMUsage(
    input_tokens=120,
    output_tokens=55,
    cache_read_tokens=400,
    cache_creation_tokens=30,
    duration_ms=1234,
    num_turns=2,
    model="claude-sonnet-fake",
)
TWICE = add_usage(FAKE_USAGE, FAKE_USAGE)
FAKE_TOKEN = "fake-oauth-token-0123456789"
FAKE_RESET_EPOCH = 1790000000


class MockClock:
    """Fixed, settable clock (test double)."""

    def __init__(self, now: dt.datetime) -> None:
        self.now = now

    def __call__(self) -> dt.datetime:
        return self.now


class FakeClaude:
    """The fake CLI installed as an executable named `claude`, plus its call journal."""

    def __init__(self, root: Path) -> None:
        bindir = root / "bin"
        bindir.mkdir()
        self.binary = bindir / "claude"
        shim = f"#!{sys.executable}\nimport runpy\nrunpy.run_path({str(FAKE_CLAUDE)!r}, run_name='__main__')\n"
        self.binary.write_text(shim, encoding="utf-8")
        self.binary.chmod(0o755)
        self.log = root / "calls.jsonl"
        self.home = root / "home"
        self.home.mkdir()
        self.workdir = root / "work"
        self.workdir.mkdir()
        self.managed = root / "managed"  # stands for /etc/claude-code; absent until a test writes it

    def env(self, scenario: str, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        return {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.home),
            "FAKE_CLAUDE_SCENARIO": scenario,
            "FAKE_CLAUDE_LOG": str(self.log),
            **(extra or {}),
        }

    def runner(self, scenario: str, *, timeout_s: float = 30, clock: MockClock | None = None, **extra: str) -> ClaudeCodeRunner:
        return self.runner_with(scenario, extra, timeout_s=timeout_s, clock=clock)

    def runner_with(
        self,
        scenario: str,
        extra: Mapping[str, str],
        *,
        timeout_s: float = 30,
        clock: MockClock | None = None,
        cls: type[ClaudeCodeRunner] = ClaudeCodeRunner,
    ) -> ClaudeCodeRunner:
        return cls(
            binary=str(self.binary),
            timeout_s=timeout_s,
            env=self.env(scenario, extra),
            clock=clock or MockClock(T0),
            local_tz=dt.UTC,
            managed_settings_dir=self.managed,
        )

    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture
def fake(tmp_path: Path) -> FakeClaude:
    return FakeClaude(tmp_path)


def call(
    runner: ClaudeCodeRunner,
    cwd: Path,
    schema: dict[str, Any] | None = None,
    *,
    model: str = "sonnet",
    tools: Sequence[str] = ("Read", "Grep"),
    prompt: str = PROMPT,
) -> LLMResult:
    return runner.run(agent="scout", prompt=prompt, model=model, json_schema=schema, max_turns=3, allowed_tools=tools, cwd=cwd)


def option(argv: Sequence[str], flag: str) -> str:
    return argv[list(argv).index(flag) + 1]


# ------------------------------------------------------------------ never --bare, never an API key


def test_argv_matches_contract_and_never_contains_bare(fake: FakeClaude) -> None:
    result = call(fake.runner("ok_structured"), fake.workdir, SCHEMA)

    (logged,) = fake.calls()
    argv = logged["argv"]
    assert "--bare" not in argv and not any(a.startswith("--bare") for a in argv)
    assert argv == [
        "-p",
        "--output-format",
        "json",
        "--model",
        "sonnet",
        "--max-turns",
        "3",
        "--agent",
        "scout",
        "--allowedTools",
        "Read,Grep",
        "--json-schema",
        json.dumps(SCHEMA, separators=(",", ":")),
    ]
    assert json.loads(option(argv, "--json-schema")) == SCHEMA
    # the prompt travels on stdin, never on the command line
    assert logged["stdin"] == PROMPT
    assert all(PROMPT not in a for a in argv)
    assert logged["has_api_key"] is False
    assert Path(logged["cwd"]).resolve() == fake.workdir.resolve()
    assert result.output == {"title": "from structured_output", "score": 7}


def test_without_schema_or_tools_the_flags_are_absent(fake: FakeClaude) -> None:
    call(fake.runner("ok"), fake.workdir, None, tools=())

    argv = fake.calls()[0]["argv"]
    assert "--json-schema" not in argv
    assert "--allowedTools" not in argv
    assert "--bare" not in argv
    assert argv[:2] == ["-p", "--output-format"]


class MockBareRunner(ClaudeCodeRunner):
    """Test double: a regression that would sneak `--bare` into argv after it was built."""

    def build_argv(self, **kwargs: Any) -> list[str]:
        return [*super().build_argv(**kwargs), "--bare"]


def test_internal_guard_refuses_bare_before_spawning(fake: FakeClaude) -> None:
    runner = fake.runner_with("ok", {}, cls=MockBareRunner)

    with pytest.raises(ForbiddenAuth, match="--bare"):
        call(runner, fake.workdir)
    assert fake.calls() == []  # the CLI was never started


@pytest.mark.parametrize("argv", [["claude", "-p", "--bare"], ["claude", "--bare=1", "-p"]])
def test_assert_no_bare_rejects_the_flag(argv: list[str]) -> None:
    with pytest.raises(ForbiddenAuth):
        assert_no_bare(argv)


def test_assert_no_bare_ignores_other_words() -> None:
    assert_no_bare(["claude", "-p", "--model", "sonnet", "--json-schema", '{"description":"--bare"}', "--barely"])


@pytest.mark.parametrize(
    ("field", "value"),
    [("model", "--bare"), ("agent", "--bare"), ("model", ""), ("agent", "two words"), ("model", "a\nb")],
)
def test_flag_injection_through_values_is_refused(fake: FakeClaude, field: str, value: str) -> None:
    runner = fake.runner("ok")
    args: dict[str, Any] = {"agent": "scout", "model": "sonnet", "json_schema": None, "max_turns": 3, "allowed_tools": ()}
    args[field] = value

    with pytest.raises(ValueError):
        runner.build_argv(**args)
    with pytest.raises(ValueError):
        runner.run(prompt=PROMPT, cwd=fake.workdir, **args)
    assert fake.calls() == []


@pytest.mark.parametrize("tools", [("Read", ""), ("Read,Write",), ("--bare",)])
def test_invalid_tool_rules_are_refused(fake: FakeClaude, tools: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        call(fake.runner("ok"), fake.workdir, tools=tools)
    assert fake.calls() == []


@pytest.mark.parametrize("max_turns", [0, -1, True])
def test_max_turns_must_be_positive(fake: FakeClaude, max_turns: int) -> None:
    with pytest.raises(ValueError):
        fake.runner("ok").run(
            agent="scout",
            prompt=PROMPT,
            model="sonnet",
            json_schema=None,
            max_turns=max_turns,
            allowed_tools=(),
            cwd=fake.workdir,
        )


@pytest.mark.parametrize("value", ["", "sk-" + "ant-api03-not-a-real-key"])
def test_api_key_in_given_env_is_refused_even_empty(fake: FakeClaude, value: str) -> None:
    runner = fake.runner("ok", ANTHROPIC_API_KEY=value)

    with pytest.raises(ForbiddenAuth, match="ANTHROPIC_API_KEY") as caught:
        call(runner, fake.workdir)
    assert fake.calls() == []
    if value:
        assert value not in str(caught.value)


def test_api_key_in_process_env_is_refused_even_empty(fake: FakeClaude, monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in fake.env("ok").items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    runner = ClaudeCodeRunner(binary=str(fake.binary), env=None, clock=MockClock(T0), managed_settings_dir=fake.managed)

    with pytest.raises(ForbiddenAuth, match="ANTHROPIC_API_KEY"):
        call(runner, fake.workdir)
    assert fake.calls() == []


def test_process_env_is_inherited_when_no_env_is_given(fake: FakeClaude, monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in fake.env("ok").items():
        monkeypatch.setenv(name, value)
    for name in FORBIDDEN_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    runner = ClaudeCodeRunner(binary=str(fake.binary), env=None, clock=MockClock(T0), managed_settings_dir=fake.managed)

    assert call(runner, fake.workdir).output == "fake answer"
    assert fake.calls()[0]["has_api_key"] is False


@pytest.mark.parametrize("name", [n for n in FORBIDDEN_ENV_VARS if n != "ANTHROPIC_API_KEY"])
def test_other_subscription_bypasses_are_refused(fake: FakeClaude, name: str) -> None:
    with pytest.raises(ForbiddenAuth, match=name):
        call(fake.runner_with("ok", {name: "1"}), fake.workdir)
    assert fake.calls() == []


class MockUnguardedRunner(ClaudeCodeRunner):
    """Test double without the environment guard, to prove that the fake's journal sees the key."""

    def child_env(self) -> dict[str, str]:
        return dict(self._env or {})


def test_journal_reports_an_api_key_that_reaches_the_child(fake: FakeClaude) -> None:
    # Without this, `has_api_key is False` above would hold by construction (review finding).
    runner = fake.runner_with("ok", {"ANTHROPIC_API_KEY": ""}, cls=MockUnguardedRunner)

    call(runner, fake.workdir)
    assert fake.calls()[0]["has_api_key"] is True


# ------------------------------------------------------------------ settings files that set a credential


def write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("where", "settings", "found"),
    [
        ("user", {"apiKeyHelper": "~/bin/vault-key.sh"}, "apiKeyHelper"),
        ("user", {"env": {"ANTHROPIC_API_KEY": ""}}, "env.ANTHROPIC_API_KEY"),
        ("config_dir", {"apiKeyHelper": "vault read -field=key secret/anthropic"}, "apiKeyHelper"),
        ("project", {"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}, "env.CLAUDE_CODE_USE_BEDROCK"),
        ("local", {"env": {"ANTHROPIC_AUTH_TOKEN": "x"}}, "env.ANTHROPIC_AUTH_TOKEN"),
        ("git_root_local", {"apiKeyHelper": "echo key"}, "apiKeyHelper"),
        ("managed", {"apiKeyHelper": "/opt/key.sh"}, "apiKeyHelper"),
        ("managed_drop_in", {"env": {"CLAUDE_CODE_SIMPLE": "1"}}, "env.CLAUDE_CODE_SIMPLE"),
    ],
)
def test_settings_that_leave_the_subscription_are_refused(
    fake: FakeClaude, tmp_path: Path, where: str, settings: dict[str, Any], found: str
) -> None:
    extra: dict[str, str] = {}
    cwd = fake.workdir
    if where == "user":
        path = write_json(fake.home / ".claude" / "settings.json", settings)
    elif where == "config_dir":
        extra["CLAUDE_CONFIG_DIR"] = str(tmp_path / "cfg")
        path = write_json(tmp_path / "cfg" / "settings.json", settings)
    elif where == "project":
        path = write_json(fake.workdir / ".claude" / "settings.json", settings)
    elif where == "local":
        path = write_json(fake.workdir / ".claude" / "settings.local.json", settings)
    elif where == "git_root_local":
        (fake.workdir / ".git").mkdir()
        cwd = fake.workdir / "sub" / "dir"
        cwd.mkdir(parents=True)
        path = write_json(fake.workdir / ".claude" / "settings.local.json", settings)
    elif where == "managed":
        path = write_json(fake.managed / "managed-settings.json", settings)
    else:
        path = write_json(fake.managed / "managed-settings.d" / "10-policy.json", settings)

    with pytest.raises(ForbiddenAuth, match=found) as caught:
        call(fake.runner_with("ok", extra), cwd)
    assert str(path) in str(caught.value)
    assert fake.calls() == []  # refused before the CLI starts


def test_harmless_or_unreadable_settings_are_accepted(fake: FakeClaude) -> None:
    write_json(fake.home / ".claude" / "settings.json", {"model": "sonnet", "env": {"DISABLE_TELEMETRY": "1"}})
    (fake.workdir / ".claude").mkdir()
    (fake.workdir / ".claude" / "settings.json").write_text("{not json", encoding="utf-8")
    write_json(fake.managed / "managed-settings.json", ["not", "an", "object"])

    assert call(fake.runner("ok"), fake.workdir).output == "fake answer"


def test_settings_files_cover_user_project_local_and_managed(tmp_path: Path) -> None:
    home, work, managed = tmp_path / "home", tmp_path / "work", tmp_path / "managed"
    work.mkdir()
    (managed / "managed-settings.d").mkdir(parents=True)
    (managed / "managed-settings.d" / "a.json").write_text("{}", encoding="utf-8")

    files = settings_files({"HOME": str(home)}, work, managed)
    assert files == [
        home / ".claude" / "settings.json",
        work.resolve() / ".claude" / "settings.json",
        work.resolve() / ".claude" / "settings.local.json",
        managed / "managed-settings.json",
        managed / "managed-settings.d" / "a.json",
    ]


# ------------------------------------------------------------------ parsing


def test_plain_call_parses_result_usage_and_session(fake: FakeClaude) -> None:
    result = call(fake.runner("ok"), fake.workdir)

    assert result.output == "fake answer"
    assert result.usage == FAKE_USAGE
    assert result.session_id == "fake-session-0"
    assert result.raw["total_cost_usd"] == pytest.approx(0.0123)


def test_missing_fields_are_tolerated(fake: FakeClaude) -> None:
    result = call(fake.runner("minimal"), fake.workdir, model="opus")

    assert result.output == "bare minimum"
    assert result.usage == LLMUsage(model="opus")  # zero counts, requested model as fallback
    assert result.session_id == ""


def test_verbose_message_list_uses_the_result_message(fake: FakeClaude) -> None:
    result = call(fake.runner("verbose_list"), fake.workdir)

    assert result.output == "from the result message"
    assert result.usage == FAKE_USAGE


def test_message_list_without_a_result_is_a_truncated_output(fake: FakeClaude) -> None:
    # Before the fix, the last message was taken for the result: a silent success with an empty output.
    with pytest.raises(ClaudeCallError, match="without a JSON result"):
        call(fake.runner("list_no_result"), fake.workdir)
    assert parse_stdout('[{"type": "system"}, {"type": "assistant"}]') is None


def test_parse_usage_handles_malformed_values() -> None:
    usage = parse_usage(
        {"usage": {"input_tokens": "12", "output_tokens": True, "cache_read_input_tokens": 7.0}, "num_turns": None}
    )
    assert usage == LLMUsage(cache_read_tokens=7)
    assert parse_usage({"usage": "n/a", "model": "claude-opus-x"}).model == "claude-opus-x"


def test_parse_usage_counts_subagents_from_model_usage() -> None:
    # `usage` is the main loop only; `modelUsage` also counts subagents (Agent SDK reference).
    payload = {
        "usage": {"input_tokens": 100, "output_tokens": 10, "cache_read_input_tokens": 5, "cache_creation_input_tokens": 1},
        "modelUsage": {
            "claude-sonnet-x": {"inputTokens": 100, "outputTokens": 10, "cacheReadInputTokens": 5, "cacheCreationInputTokens": 1},
            "claude-haiku-x": {"inputTokens": 40, "outputTokens": 4, "cacheReadInputTokens": 2, "cacheCreationInputTokens": 3},
        },
    }
    usage = parse_usage(payload)
    assert (usage.input_tokens, usage.output_tokens, usage.cache_read_tokens, usage.cache_creation_tokens) == (140, 14, 7, 4)
    assert usage.model == "claude-sonnet-x"


def test_parse_stdout_variants() -> None:
    assert parse_stdout("") is None
    assert parse_stdout("not json") is None
    assert parse_stdout("[1, 2]") is None
    assert parse_stdout('warning: update available\n{"type":"result","result":"x"}') == {"type": "result", "result": "x"}


def test_structured_output_is_preferred_over_result(fake: FakeClaude) -> None:
    result = call(fake.runner("ok_structured"), fake.workdir, SCHEMA)

    assert result.output == {"title": "from structured_output", "score": 7}
    assert len(fake.calls()) == 1


def test_result_parsed_as_json_when_structured_output_is_absent(fake: FakeClaude) -> None:
    result = call(fake.runner("ok_result_json"), fake.workdir, SCHEMA)

    assert result.output == {"title": "from result", "score": 3}


# ------------------------------------------------------------------ documented output shapes


def cli_output(name: str) -> str:
    return (CLI_OUTPUTS / f"{name}.json").read_text(encoding="utf-8")


def test_documented_success_shape_is_parsed() -> None:
    payload = parse_stdout(cli_output("success_structured"))

    assert payload is not None and payload["type"] == "result" and payload["is_error"] is False
    assert extract_structured(payload) == ({"title": "Three outlier formats", "score": 8}, None)
    usage = parse_usage(payload)
    # main loop 1830/412 plus a haiku subagent 950/120, from modelUsage
    assert usage == LLMUsage(
        input_tokens=2780,
        output_tokens=532,
        cache_read_tokens=15360,
        cache_creation_tokens=2048,
        duration_ms=8421,
        num_turns=3,
        model="claude-sonnet-5",
    )


def test_documented_success_shape_through_the_runner(fake: FakeClaude) -> None:
    result = call(fake.runner("fixture:success_structured"), fake.workdir, SCHEMA)

    assert result.output == {"title": "Three outlier formats", "score": 8}
    assert result.session_id == "5f1c9a2e-7d4b-4e6a-8c3f-9b2d1e0a4c77"
    assert (result.usage.input_tokens, result.usage.output_tokens) == (2780, 532)


@pytest.mark.parametrize("exit_code", ["0", "1"])
@pytest.mark.parametrize(
    ("name", "expected", "reset_at"),
    [
        ("error_max_turns", ClaudeCallError, None),
        ("prompt_too_long", ClaudeCallError, None),
        ("usage_limit_result", ClaudeQuotaExhausted, dt.datetime(2026, 9, 28, 15, 45, tzinfo=dt.UTC)),
        ("usage_limit_errors", ClaudeQuotaExhausted, dt.datetime(2026, 10, 5, 0, 0, tzinfo=dt.UTC)),
        ("throttle_429", ClaudeRateLimited, T0 + RATE_LIMIT_PAUSE),
    ],
)
def test_documented_error_shapes_through_the_runner(
    fake: FakeClaude, exit_code: str, name: str, expected: type[StudioError], reset_at: dt.datetime | None
) -> None:
    with pytest.raises(expected) as caught:
        call(fake.runner(f"fixture:{name}", FAKE_CLAUDE_EXIT=exit_code), fake.workdir)

    error = caught.value
    assert type(error) is expected
    if isinstance(error, QuotaExhausted):
        assert error.reset_at == reset_at
    else:
        assert not isinstance(error, QuotaExhausted | LLMOutputInvalid)
    payload = parse_stdout(cli_output(name))
    assert payload is not None and call_usage(error) == parse_usage(payload, fallback_model="sonnet")
    assert len(fake.calls()) == 1


def test_documented_structured_retries_error_gets_one_retry(fake: FakeClaude) -> None:
    with pytest.raises(ClaudeOutputInvalid, match="error_max_structured_output_retries") as caught:
        call(fake.runner("fixture:error_max_structured_output_retries", FAKE_CLAUDE_EXIT="1"), fake.workdir, SCHEMA)
    assert len(fake.calls()) == 2
    assert caught.value.usage.output_tokens == 2 * 380


# ------------------------------------------------------------------ is_error and the exit code, each on its own


@pytest.mark.parametrize("schema", [None, SCHEMA])
@pytest.mark.parametrize("exit_code", ["0", "1"])
def test_is_error_alone_marks_a_failure(fake: FakeClaude, schema: dict[str, Any] | None, exit_code: str) -> None:
    runner = fake.runner("quota_epoch", FAKE_CLAUDE_EXIT=exit_code)
    with pytest.raises(QuotaExhausted) as caught:
        call(runner, fake.workdir, schema)
    assert caught.value.reset_at == dt.datetime.fromtimestamp(FAKE_RESET_EPOCH, dt.UTC)

    with pytest.raises(ClaudeCallError, match="error_max_turns"):
        call(fake.runner("max_turns", FAKE_CLAUDE_EXIT=exit_code), fake.workdir, schema)


@pytest.mark.parametrize("schema", [None, SCHEMA])
def test_non_zero_exit_alone_marks_a_failure(fake: FakeClaude, schema: dict[str, Any] | None) -> None:
    scenario = "ok_structured" if schema else "ok"
    with pytest.raises(ClaudeCallError, match=r"exit 1, is_error False"):
        call(fake.runner(scenario, FAKE_CLAUDE_EXIT="1"), fake.workdir, schema)
    assert len(fake.calls()) == 1


# ------------------------------------------------------------------ bounded schema retry


def test_one_corrective_retry_then_success(fake: FakeClaude) -> None:
    result = call(fake.runner("schema_fail_then_ok"), fake.workdir, SCHEMA)

    assert result.output == {"title": "from structured_output", "score": 7}
    first, second = fake.calls()
    assert first["stdin"] == PROMPT
    assert second["stdin"] != PROMPT
    assert "rejected" in second["stdin"] and second["stdin"].endswith(PROMPT)
    assert json.dumps(SCHEMA, separators=(",", ":")) in second["stdin"]
    assert "--bare" not in second["argv"]
    # both attempts are paid for
    assert result.usage.input_tokens == 2 * FAKE_USAGE.input_tokens
    assert result.usage.output_tokens == 2 * FAKE_USAGE.output_tokens
    assert result.session_id == "fake-session-1"


def test_structured_output_error_subtype_counts_as_schema_failure(fake: FakeClaude) -> None:
    result = call(fake.runner("structured_retries_then_ok"), fake.workdir, SCHEMA)

    assert result.output == {"title": "from structured_output", "score": 7}
    assert len(fake.calls()) == 2


def test_retry_is_bounded_then_llm_output_invalid(fake: FakeClaude) -> None:
    with pytest.raises(LLMOutputInvalid, match="after 2 attempts") as caught:
        call(fake.runner("schema_fail_twice"), fake.workdir, SCHEMA)

    assert len(fake.calls()) == 2  # exactly one retry
    assert isinstance(caught.value, ClaudeOutputInvalid)
    assert caught.value.usage.output_tokens == 2 * FAKE_USAGE.output_tokens
    assert "score" in str(caught.value)  # the last validation problem is reported


def test_invalid_schema_is_refused_before_any_call(fake: FakeClaude) -> None:
    with pytest.raises(ValueError, match="invalid JSON Schema"):
        call(fake.runner("ok"), fake.workdir, {"type": "no-such-type"})
    assert fake.calls() == []


# ------------------------------------------------------------------ usage kept on every failure


def test_usage_of_the_first_attempt_survives_a_quota_on_the_retry(fake: FakeClaude) -> None:
    with pytest.raises(ClaudeQuotaExhausted) as caught:
        call(fake.runner("invalid_structured,quota_epoch"), fake.workdir, SCHEMA)

    assert len(fake.calls()) == 2
    assert caught.value.usage == TWICE  # the invalid answer plus what the limit result reported
    assert call_usage(caught.value) == TWICE


def test_usage_of_the_first_attempt_survives_a_crash_on_the_retry(fake: FakeClaude) -> None:
    with pytest.raises(ClaudeCallError, match="exited with code 3") as caught:
        call(fake.runner("invalid_structured,crash"), fake.workdir, SCHEMA)

    assert len(fake.calls()) == 2
    assert caught.value.usage == FAKE_USAGE  # the crash reported nothing, the first attempt was paid


def test_usage_of_the_first_attempt_survives_a_timeout_on_the_retry(fake: FakeClaude) -> None:
    runner = fake.runner("invalid_structured,slow", timeout_s=1.5, FAKE_CLAUDE_SLEEP="60")

    with pytest.raises(ClaudeCallError, match="timed out") as caught:
        call(runner, fake.workdir, SCHEMA)
    assert caught.value.usage == FAKE_USAGE


def test_usage_of_a_failed_single_attempt_is_kept(fake: FakeClaude) -> None:
    with pytest.raises(ClaudeCallError) as caught:
        call(fake.runner("max_turns"), fake.workdir)
    assert caught.value.usage == FAKE_USAGE
    assert call_usage(ValueError("not from the runner")) is None


# ------------------------------------------------------------------ limits


def test_usage_limit_with_epoch_raises_quota_exhausted(fake: FakeClaude) -> None:
    with pytest.raises(QuotaExhausted) as caught:
        call(fake.runner("quota_epoch", FAKE_CLAUDE_RESET_EPOCH=str(FAKE_RESET_EPOCH)), fake.workdir, SCHEMA)

    assert caught.value.reset_at == dt.datetime.fromtimestamp(FAKE_RESET_EPOCH, dt.UTC)
    assert len(fake.calls()) == 1  # a quota error is never retried


def test_usage_limit_with_clock_time_uses_next_occurrence(fake: FakeClaude) -> None:
    with pytest.raises(QuotaExhausted) as caught:
        call(fake.runner("quota_text"), fake.workdir)
    assert caught.value.reset_at == dt.datetime(2026, 9, 28, 15, 45, tzinfo=dt.UTC)

    late = MockClock(dt.datetime(2026, 9, 28, 16, 0, tzinfo=dt.UTC))
    with pytest.raises(QuotaExhausted) as caught:
        call(fake.runner("quota_text", clock=late), fake.workdir)
    assert caught.value.reset_at == dt.datetime(2026, 9, 29, 15, 45, tzinfo=dt.UTC)


def test_rate_limit_on_stderr_without_json_is_a_short_pause(fake: FakeClaude) -> None:
    with pytest.raises(ClaudeRateLimited) as caught:
        call(fake.runner("quota_stderr"), fake.workdir)
    assert caught.value.reset_at == T0 + RATE_LIMIT_PAUSE


def test_limit_words_in_a_successful_answer_are_not_a_quota(fake: FakeClaude) -> None:
    result = call(fake.runner("ok_mentions_limit"), fake.workdir)
    assert "usage limit" in result.output


def test_other_errors_are_studio_errors_not_quota(fake: FakeClaude) -> None:
    with pytest.raises(StudioError, match="error_max_turns") as caught:
        call(fake.runner("max_turns"), fake.workdir, SCHEMA)
    assert not isinstance(caught.value, QuotaExhausted | LLMOutputInvalid)
    assert len(fake.calls()) == 1


# Every limit-related message of the official error reference (https://code.claude.com/docs/en/errors,
# consulted 2026-09-28), plus older CLI forms. "quota" = plan limit, "rate" = short throttle,
# "api_key" = billed to an API key, None = any other failure.
OFFICIAL_MESSAGES: list[tuple[str, str | None]] = [
    # Usage limits
    ("You've hit your session limit · resets 3:45pm", "quota"),
    ("You've hit your weekly limit · resets Mon 12:00am", "quota"),
    ("You've hit your Opus limit · resets 3:45pm", "quota"),
    ("You've hit your Sonnet limit · resets 3:45pm", "quota"),
    ("Usage limit reached · continuing automatically at 3:45pm · esc to cancel", "quota"),
    (
        "API Error: Usage credits required for 1M context · run /usage-credits to turn them on (they take effect "
        "after you restart Claude Code), or /model to switch to standard context",
        None,
    ),
    (
        "Fable limit reached · continuing on Fable 5.1 uses usage credits, and the prompt to confirm went unanswered "
        "— nothing was sent · answer it where this session is running, or /model to change",
        "quota",
    ),
    ("Fable 5 limit reached · continuing on Fable 5 uses usage credits", "quota"),
    (
        "Fable 5.1 now uses usage credits · the prompt to confirm went unanswered — nothing was sent · answer it "
        "where this session is running, or /model to change",
        None,
    ),
    ("API Error: Server is temporarily limiting requests (not your usage limit)", "rate"),
    (
        "API Error: Request rejected (429) · this may be a temporary capacity issue. If it persists, check "
        "https://status.claude.com.",
        "rate",
    ),
    ("API Error: Request rejected (429) · Too Many Requests", "rate"),
    ("Credit balance is too low", "api_key"),
    ("You've hit your monthly spend limit · raise it at claude.ai/settings/usage", "quota"),
    ("You've hit your individual spend limit · ask your admin for a higher limit", "quota"),
    ("You've hit your org's monthly spend limit · visit claude.ai/admin-settings/usage to raise it", "quota"),
    ("You've hit your team's shared budget · ask your admin to raise it at claude.ai/admin-settings/usage", "quota"),
    (
        "You've hit your channel's monthly spend limit · an org owner or channel manager can raise it in the "
        "channel's Claude settings",
        "quota",
    ),
    ("You've hit your individual usage limit · your session limit resets 3:45pm", "quota"),
    ("spend limit reached (daily; resets 2026-08-09 00:00 UTC)", "quota"),
    ("spend limit reached", "quota"),
    ("spend limit unavailable", "rate"),
    ("Could not update your spend limit: amount is below current usage", None),
    ("Could not update your spend limit. Press Enter to retry.", None),
    ("You've used 85% of your session limit · resets 3:45pm", None),
    # Request errors (the two "Context limit reached" forms were taken for a quota before the fix)
    ("Context limit reached · /compact or /clear to continue", None),
    ("Context limit reached · /clear to continue", None),
    ("Context limit reached · /compact or /clear to continue · auto-compact is off · /config to turn it on", None),
    ("Prompt is too long", None),
    ("Input is too long for requested model.", None),
    ("capability_rejected: prompt_too_long", None),
    ("Context exceeds the 200k-token limit by 94k tokens — run /compact or /clear to continue.", None),
    ("Request too large for the API's 32MB request limit", None),
    ("upstream rate limit exceeded", "rate"),
    ("API error: 429 rate limited · model not changed", "rate"),
    # Server errors
    (
        "API Error: Repeated 529 Overloaded errors. The API is at capacity — this is usually temporary. Try again "
        "in a moment. If it persists, check https://status.claude.com.",
        None,
    ),
    ("API Error: 500 Internal server error. This is a server-side issue, usually temporary — try again in a moment.", None),
    ("Opus is experiencing high load, please use /model to switch to Sonnet", None),
    ("Agent terminated early due to an API error: You've hit your session limit · resets 3:45pm", "quota"),
    ("Agent terminated early due to an API error: Request rejected (429)", "rate"),
    # Authentication
    ("Invalid API key · Fix external API key", "api_key"),
    (
        "Your apiKeyHelper script is failing · This usually means you need to re-authenticate with your provider · "
        "Run /status to see the script's error output",
        "api_key",
    ),
    ("Your organization has disabled API key authentication", "api_key"),
    ("Not logged in · Please run /login", None),
    ("OAuth token has expired", None),
    # Older CLI forms and other caps that are not the plan quota
    ("Claude AI usage limit reached|1790000000", "quota"),
    ("5-hour limit reached ∙ resets 2am", "quota"),
    ("You’ve hit your Opus limit", "quota"),
    ("API Error: 429 rate_limit_error: Rate limit reached for requests", "rate"),
    ("Output token limit reached", None),
    ("Turn limit reached", None),
    ("Budget limit reached", None),
    ("Reached maximum turns (3)", None),
    ("Invalid JSON Schema", None),
]


@pytest.mark.parametrize(("text", "kind"), OFFICIAL_MESSAGES)
def test_official_error_messages_are_classified(text: str, kind: str | None) -> None:
    assert classify_failure(text) == kind


def test_structured_signals_of_the_result() -> None:
    assert classify_failure("API Error", api_error_status=429) == "rate"
    assert classify_failure("API Error", api_error_status=529) is None
    assert classify_failure("You've hit your session limit", api_error_status=429) == "quota"
    # our own caps (--max-turns, --max-budget-usd) are never a plan limit
    for subtype in ("error_max_turns", "error_max_budget_usd", "error_max_structured_output_retries"):
        assert classify_failure("You've hit your session limit", subtype=subtype) is None


@pytest.mark.parametrize(
    ("text", "api_status", "expected", "reset_at"),
    [
        ("Context limit reached · /compact or /clear to continue", None, ClaudeCallError, None),
        (
            "API Error: Request rejected (429) · this may be a temporary capacity issue.",
            None,
            ClaudeRateLimited,
            T0 + RATE_LIMIT_PAUSE,
        ),
        (
            "API Error: Server is temporarily limiting requests (not your usage limit)",
            None,
            ClaudeRateLimited,
            T0 + RATE_LIMIT_PAUSE,
        ),
        ("API Error: overloaded", "429", ClaudeRateLimited, T0 + RATE_LIMIT_PAUSE),
        ("Credit balance is too low", None, ClaudeApiKeyInUse, None),
        (
            "You've hit your weekly limit · resets Oct 3, 9am",
            None,
            ClaudeQuotaExhausted,
            dt.datetime(2026, 10, 3, 9, tzinfo=dt.UTC),
        ),
    ],
)
def test_classification_raises_the_matching_exception(
    fake: FakeClaude, text: str, api_status: str | None, expected: type[StudioError], reset_at: dt.datetime | None
) -> None:
    extra = {"FAKE_CLAUDE_LIMIT_TEXT": text, **({"FAKE_CLAUDE_API_STATUS": api_status} if api_status else {})}
    with pytest.raises(expected) as caught:
        call(fake.runner_with("quota_text", extra), fake.workdir, SCHEMA)

    assert type(caught.value) is expected
    assert getattr(caught.value, "reset_at", None) == reset_at
    assert len(fake.calls()) == 1  # none of these is retried
    if expected is ClaudeApiKeyInUse:
        assert isinstance(caught.value, ForbiddenAuth)


def test_a_context_error_does_not_pause_the_queue(fake: FakeClaude) -> None:
    # Before the fix, "Context limit reached" matched "limit reached": a one-hour pause of every priority.
    runner = fake.runner("quota_text", FAKE_CLAUDE_LIMIT_TEXT="Context limit reached · /compact or /clear to continue")

    with pytest.raises(StudioError) as caught:
        call(runner, fake.workdir)
    assert type(caught.value) is ClaudeCallError
    assert call_usage(caught.value) == FAKE_USAGE


def test_weekly_limit_pauses_the_quota_manager_until_the_dated_reset(fake: FakeClaude) -> None:
    clock = MockClock(T0)
    quota = QuotaManager(clock)
    runner = fake.runner("quota_text", clock=clock, FAKE_CLAUDE_LIMIT_TEXT="You've hit your weekly limit · resets Oct 3, 9am")

    with pytest.raises(QuotaExhausted) as caught:
        call(runner, fake.workdir)
    assert quota.on_exhausted(caught.value) == dt.datetime(2026, 10, 3, 9, tzinfo=dt.UTC)
    clock.now = dt.datetime(2026, 10, 3, 8, 59, tzinfo=dt.UTC)
    assert not quota.can_run(Priority.COMPLIANCE_AND_SCRIPTS)
    clock.now = dt.datetime(2026, 10, 3, 9, 0, tzinfo=dt.UTC)
    assert quota.can_run(Priority.COMPLIANCE_AND_SCRIPTS)


PARIS = dt.timezone(dt.timedelta(hours=2))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Claude AI usage limit reached|1790000000", dt.datetime.fromtimestamp(1790000000, dt.UTC)),
        ("limit reached|1790000000123", dt.datetime.fromtimestamp(1790000000, dt.UTC)),
        ("resets 3pm (UTC)", dt.datetime(2026, 9, 28, 15, 0, tzinfo=dt.UTC)),
        ("resets at 9:30am (UTC)", dt.datetime(2026, 9, 29, 9, 30, tzinfo=dt.UTC)),
        ("resets 12am (UTC)", dt.datetime(2026, 9, 29, 0, 0, tzinfo=dt.UTC)),
        ("resets 12pm (UTC)", dt.datetime(2026, 9, 28, 12, 0, tzinfo=dt.UTC)),
        ("resets 15:00 (UTC)", dt.datetime(2026, 9, 28, 15, 0, tzinfo=dt.UTC)),
        ("resets 4pm (Europe/Paris)", dt.datetime(2026, 9, 28, 14, 0, tzinfo=dt.UTC)),
        ("continuing automatically at 3:45pm", dt.datetime(2026, 9, 28, 13, 45, tzinfo=dt.UTC)),  # local = +02:00
        ("resets in 2h 30m", T0 + dt.timedelta(hours=2, minutes=30)),
        ("resets in 45 minutes", T0 + dt.timedelta(minutes=45)),
        # dated resets (weekly limit): the date wins over the "next occurrence" of the time
        ("You've hit your weekly limit · resets Oct 3, 9am", dt.datetime(2026, 10, 3, 7, 0, tzinfo=dt.UTC)),
        ("You've hit your weekly limit · resets 9:00am Oct 3 (UTC)", dt.datetime(2026, 10, 3, 9, 0, tzinfo=dt.UTC)),
        ("resets 3 Oct 9am (UTC)", dt.datetime(2026, 10, 3, 9, 0, tzinfo=dt.UTC)),
        ("resets Oct. 3rd, 2027 at 10:30pm (GMT-5)", dt.datetime(2027, 10, 4, 3, 30, tzinfo=dt.UTC)),
        ("resets Oct 3", dt.datetime(2026, 10, 2, 22, 0, tzinfo=dt.UTC)),  # midnight, local
        ("resets Jan 2, 9am (UTC)", dt.datetime(2027, 1, 2, 9, 0, tzinfo=dt.UTC)),  # next year
        ("resets Sep 27, 9am (UTC)", dt.datetime(2026, 9, 27, 9, 0, tzinfo=dt.UTC)),  # just past: kept
        ("spend limit reached (daily; resets 2026-09-29 00:00 UTC)", dt.datetime(2026, 9, 29, 0, 0, tzinfo=dt.UTC)),
        # official weekday form: T0 is Monday 12:00 in Paris, so "Mon 12:00am" is next Monday
        ("You've hit your weekly limit · resets Mon 12:00am", dt.datetime(2026, 10, 4, 22, 0, tzinfo=dt.UTC)),
        ("resets Thursday 5pm (UTC)", dt.datetime(2026, 10, 1, 17, 0, tzinfo=dt.UTC)),
        ("resets tomorrow at 9am (UTC)", dt.datetime(2026, 9, 29, 9, 0, tzinfo=dt.UTC)),
        ("resets 3pm (UTC+2)", dt.datetime(2026, 9, 28, 13, 0, tzinfo=dt.UTC)),
        (
            "You've hit your individual usage limit · your session limit resets 3:45pm",
            dt.datetime(2026, 9, 28, 13, 45, tzinfo=dt.UTC),
        ),
        ("resets Feb 30, 9am", None),
        ("resets 25:00", None),
        ("resets 13pm", None),
        ("resets 3", None),
        ("You've hit your session limit", None),
    ],
)
def test_parse_reset_at(text: str, expected: dt.datetime | None) -> None:
    assert parse_reset_at(text, T0, local_tz=PARIS) == expected


# ------------------------------------------------------------------ process failures


def _alive(pid: int) -> bool:
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    state = next((line.split()[1] for line in status.splitlines() if line.startswith("State:")), "X")
    return state not in ("Z", "X")


@pytest.mark.skipif(not Path("/proc/self/status").exists(), reason="needs /proc to observe the process group")
def test_timeout_kills_the_process_group(fake: FakeClaude) -> None:
    runner = fake.runner("slow", timeout_s=1.5, FAKE_CLAUDE_SLEEP="60")

    started = time.monotonic()
    with pytest.raises(StudioError, match="timed out after 1.5s"):
        call(runner, fake.workdir)
    assert time.monotonic() - started < 15

    (logged,) = fake.calls()
    grandchild = int(logged["grandchild_pid"])
    deadline = time.monotonic() + 5
    while _alive(grandchild) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(grandchild), "a tool spawned by claude survived the timeout"


def test_crash_without_json_reports_truncated_redacted_stderr(fake: FakeClaude) -> None:
    runner = fake.runner("crash", CLAUDE_CODE_OAUTH_TOKEN=FAKE_TOKEN)

    with pytest.raises(StudioError, match="exited with code 3") as caught:
        call(runner, fake.workdir)
    message = str(caught.value)
    assert "runtime exploded" in message
    assert FAKE_TOKEN not in message
    assert "[redacted]" in message
    assert len(message) < 2300  # 5000+ chars of stderr were truncated


def test_exit_zero_without_json_is_an_error(fake: FakeClaude) -> None:
    with pytest.raises(ClaudeCallError, match="without a JSON result"):
        call(fake.runner("garbage"), fake.workdir)


def test_missing_binary_and_missing_cwd(fake: FakeClaude, tmp_path: Path) -> None:
    missing = ClaudeCodeRunner(binary=str(tmp_path / "nope" / "claude"), env=fake.env("ok"), managed_settings_dir=fake.managed)
    with pytest.raises(StudioError, match="not found"):
        call(missing, fake.workdir)
    with pytest.raises(StudioError, match="working directory"):
        call(fake.runner("ok"), tmp_path / "absent")
    assert fake.calls() == []


def test_redact_removes_secret_values_and_key_shapes() -> None:
    env: Mapping[str, str] = {"CLAUDE_CODE_OAUTH_TOKEN": FAKE_TOKEN, "PATH": "/usr/local/bin:/usr/bin"}
    text = f"token {FAKE_TOKEN} key sk-ant-api03-AbC_d-9 path /usr/local/bin:/usr/bin"
    cleaned = redact(text, env)
    assert FAKE_TOKEN not in cleaned and "sk-ant" not in cleaned
    assert "/usr/local/bin:/usr/bin" in cleaned  # not a secret name: kept


@pytest.mark.parametrize(
    ("scenario", "schema", "expected", "extra"),
    [
        ("quota_text", None, ClaudeQuotaExhausted, {}),  # plan limit
        ("quota_text", None, ClaudeRateLimited, {"FAKE_CLAUDE_LIMIT_TEXT": "API Error: Request rejected (429)"}),
        ("quota_text", None, ClaudeApiKeyInUse, {"FAKE_CLAUDE_LIMIT_TEXT": "Credit balance is too low"}),
        ("max_turns", None, ClaudeCallError, {}),  # is_error result
        ("crash", None, ClaudeCallError, {}),  # non-zero exit without JSON
        ("garbage", None, ClaudeCallError, {}),  # exit 0 without JSON
        ("schema_fail_twice", SCHEMA, ClaudeOutputInvalid, {}),  # schema problem after the retry
        ("structured_error", SCHEMA, ClaudeOutputInvalid, {}),  # the CLI's structured-output error
    ],
)
def test_no_message_path_leaks_a_secret(
    fake: FakeClaude, scenario: str, schema: dict[str, Any] | None, expected: type[StudioError], extra: dict[str, str]
) -> None:
    runner = fake.runner_with(scenario, {"CLAUDE_CODE_OAUTH_TOKEN": FAKE_TOKEN, "FAKE_CLAUDE_LEAK": "1", **extra})

    with pytest.raises(expected) as caught:
        call(runner, fake.workdir, schema)
    message = str(caught.value)
    assert type(caught.value) is expected
    assert FAKE_TOKEN not in message and "sk-ant" not in message
    assert "[redacted]" in message


@pytest.mark.parametrize(
    ("scenario", "pad"),
    [
        ("schema_fail_twice", PROBLEM_CHARS - 30),  # the token straddles the 500-char cut of the schema problem
        ("structured_error", 140),  # the token straddled the former 200-char cut of the CLI's error text
    ],
)
def test_a_secret_cut_by_truncation_is_still_redacted(fake: FakeClaude, scenario: str, pad: int) -> None:
    # Before the fix, these texts were truncated before redaction: the cut secret no longer matched its
    # value and its first characters leaked.
    extra = {"CLAUDE_CODE_OAUTH_TOKEN": FAKE_TOKEN, "FAKE_CLAUDE_LEAK": "1", "FAKE_CLAUDE_PAD": str(pad)}
    with pytest.raises(ClaudeOutputInvalid) as caught:
        call(fake.runner_with(scenario, extra), fake.workdir, SCHEMA)
    message = str(caught.value)
    assert FAKE_TOKEN[:8] not in message and "sk-ant" not in message
    assert len(message) < PROBLEM_CHARS + 200


# ------------------------------------------------------------------ contract and concurrency


def test_runner_implements_the_llm_contract() -> None:
    from studio.adapters.registry import validate_adapter

    runner = ClaudeCodeRunner()
    assert isinstance(runner, LLMRunner)
    assert validate_adapter(runner) is CLAUDE_CODE_SPEC
    assert CLAUDE_CODE_SPEC.kind is AdapterKind.LLM
    assert CLAUDE_CODE_SPEC.status is not AdapterStatus.MOCK and not CLAUDE_CODE_SPEC.is_mock
    with pytest.raises(ValueError):
        ClaudeCodeRunner(timeout_s=0)


def test_concurrent_calls_are_independent(fake: FakeClaude) -> None:
    runner = fake.runner("ok_structured")
    prompts = [f"prompt {i}" for i in range(6)]

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda p: call(runner, fake.workdir, SCHEMA, prompt=p), prompts))

    assert all(r.output == {"title": "from structured_output", "score": 7} for r in results)
    logged = fake.calls()
    assert sorted(c["stdin"] for c in logged) == sorted(prompts)
    assert all("--bare" not in c["argv"] for c in logged)
