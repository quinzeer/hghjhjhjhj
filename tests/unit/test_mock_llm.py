"""MockLLMRunner: `mock` in its id, deterministic, zero usage, replays recorded fixtures, and derives from a
JSON Schema a minimal instance that validates against it (checked with jsonschema, and with Pydantic for the
domain contracts)."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator, Draft202012Validator, validators
from pydantic import BaseModel

from studio.adapters.llm_base import LLMOutputInvalid, LLMRunner, LLMUsage
from studio.adapters.mock_llm import (
    DEFAULT_FIXTURES_DIR,
    MOCK_LLM_ID,
    MockFixtureInvalid,
    MockLLMRunner,
    MockSchemaUnsupported,
    fixture_key,
    generate_instance,
    pattern_instance,
)
from studio.domain import (
    CONTRACTS,
    AdapterKind,
    AdapterStatus,
    Channel,
    CostEntry,
    Experiment,
    GateDecision,
    Idea,
    Metric,
    Package,
    Publication,
    Render,
    RunManifest,
    Scene,
    Script,
    Series,
    Shot,
    VideoFormat,
)
from studio.domain.models import Asset

RICH_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$defs": {
        "Level": {"enum": ["low", "mid", "high"]},
        "Tag": {"type": "string", "pattern": "^#[a-z]{3,8}$"},
        "Point": {
            "type": "object",
            "properties": {"x": {"type": "integer", "minimum": 5}, "y": {"type": "integer", "maximum": -3}},
            "required": ["x", "y"],
        },
    },
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 12, "maxLength": 40},
        "code": {"type": "string", "pattern": r"^[A-Z]{2}-\d{4}$"},
        "slug": {"type": "string", "pattern": r"^[a-z0-9][a-z0-9_-]{0,63}$", "minLength": 5},
        "when": {"type": "string", "format": "date-time"},
        "count": {"type": "integer", "exclusiveMinimum": 0, "maximum": 10},
        "ratio": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1},
        "even": {"type": "integer", "minimum": 3, "multipleOf": 2},
        "score": {"type": "number", "minimum": 2.5, "maximum": 3},
        "level": {"$ref": "#/$defs/Level"},
        "kind": {"const": "demo"},
        "flag": {"type": "boolean"},
        "tags": {"type": "array", "items": {"$ref": "#/$defs/Tag"}, "minItems": 2},
        "unique": {"type": "array", "items": {"type": "string"}, "minItems": 3, "uniqueItems": True},
        "unique_ints": {"type": "array", "items": {"type": "integer", "minimum": 1}, "minItems": 3, "uniqueItems": True},
        "pair": {"type": "array", "prefixItems": [{"type": "integer"}, {"type": "string"}], "minItems": 2},
        "maybe": {"anyOf": [{"$ref": "#/$defs/Point"}, {"type": "null"}]},
        "choice": {"oneOf": [{"type": "string", "maxLength": 2}, {"type": "integer", "minimum": 100}]},
        "merged": {"allOf": [{"$ref": "#/$defs/Point"}, {"properties": {"label": {"type": "string"}}, "required": ["label"]}]},
        "scores": {"type": "object", "additionalProperties": {"type": "number"}, "minProperties": 2},
        "optional_note": {"type": "string"},
    },
    "required": [
        "title",
        "code",
        "slug",
        "when",
        "count",
        "ratio",
        "even",
        "score",
        "level",
        "kind",
        "flag",
        "tags",
        "unique",
        "unique_ints",
        "pair",
        "maybe",
        "choice",
        "merged",
        "scores",
    ],
    "additionalProperties": False,
}


def run(runner: MockLLMRunner, schema: dict[str, Any] | None, *, agent: str = "scout", prompt: str = "p") -> Any:
    return runner.run(
        agent=agent, prompt=prompt, model="opus", json_schema=schema, max_turns=2, allowed_tools=("Read",), cwd=Path(".")
    )


@pytest.fixture
def runner(tmp_path: Path) -> MockLLMRunner:
    return MockLLMRunner(fixtures_dir=tmp_path)


# ------------------------------------------------------------------ identity and contract


def test_mock_identity_and_contract() -> None:
    from studio.adapters.registry import validate_adapter

    mock = MockLLMRunner()
    assert isinstance(mock, LLMRunner)
    assert mock.spec.id == MOCK_LLM_ID == "mock-llm"
    assert mock.spec.kind is AdapterKind.LLM
    assert mock.spec.status is AdapterStatus.MOCK and mock.spec.is_mock
    assert validate_adapter(mock) is mock.spec


def test_usage_is_zero_and_raw_says_mock(runner: MockLLMRunner) -> None:
    result = run(runner, RICH_SCHEMA)

    assert result.usage == LLMUsage(model=MOCK_LLM_ID)
    assert (result.usage.input_tokens, result.usage.output_tokens, result.usage.num_turns) == (0, 0, 0)
    assert result.raw["mock"] is True and result.raw["source"] == "schema"
    assert "mock" in result.session_id


# ------------------------------------------------------------------ schema-derived output


def test_schema_output_is_valid_and_minimal(runner: MockLLMRunner) -> None:
    out = run(runner, RICH_SCHEMA).output

    Draft202012Validator(RICH_SCHEMA).validate(out)
    assert "optional_note" not in out  # minimal: optional properties are left out
    assert len(out["tags"]) == 2 and len(out["unique"]) == 3
    assert out["level"] == "low"  # first enum value
    assert out["kind"] == "demo"
    assert out["count"] == 1 and out["even"] == 4 and out["score"] == 2.5
    assert 0 < out["ratio"] < 1
    assert out["merged"]["x"] >= 5 and out["merged"]["y"] <= -3 and "label" in out["merged"]
    assert len(set(out["unique"])) == 3 and len(set(out["unique_ints"])) == 3
    assert len(out["title"]) >= 12 and out["title"].startswith("mock")


def test_schema_output_is_deterministic(tmp_path: Path) -> None:
    first = run(MockLLMRunner(fixtures_dir=tmp_path), RICH_SCHEMA).output
    second = run(MockLLMRunner(fixtures_dir=tmp_path), RICH_SCHEMA, prompt="another prompt").output
    again = run(MockLLMRunner(fixtures_dir=tmp_path), json.loads(json.dumps(RICH_SCHEMA))).output

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True) == json.dumps(again, sort_keys=True)


def test_different_schemas_give_different_outputs(runner: MockLLMRunner) -> None:
    a = run(runner, {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}).output
    b = run(runner, {"type": "object", "properties": {"b": {"type": "integer", "minimum": 3}}, "required": ["b"]}).output
    assert a == {"a": "mock"} and b == {"b": 3}


def test_draft7_schema_with_tuple_items(runner: MockLLMRunner) -> None:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "array",
        "items": [{"type": "string", "format": "email"}, {"type": "number", "exclusiveMaximum": 0}],
        "minItems": 2,
    }
    out = run(runner, schema).output
    Draft7Validator(schema).validate(out)
    assert out[0] == "mock@example.com" and out[1] < 0


@pytest.mark.parametrize("model", CONTRACTS, ids=lambda m: m.__name__)
@pytest.mark.parametrize("populate", [False, True], ids=["minimal", "populated"])
def test_every_domain_contract_schema_is_satisfied(model: type[BaseModel], populate: bool, tmp_path: Path) -> None:
    schema = model.model_json_schema()
    out = run(MockLLMRunner(fixtures_dir=tmp_path, populate_optional=populate), schema).output

    validators.validator_for(schema)(schema).validate(out)


@pytest.mark.parametrize(
    "model",
    [Channel, Series, Idea, Scene, Shot, Asset, Render, Publication, Metric, Experiment, CostEntry, GateDecision, RunManifest],
    ids=lambda m: m.__name__,
)
def test_minimal_output_builds_contracts_without_cross_field_rules(model: type[BaseModel], runner: MockLLMRunner) -> None:
    model.model_validate(run(runner, model.model_json_schema()).output)


@pytest.mark.parametrize("model", [Package, Script], ids=lambda m: m.__name__)
def test_populated_output_satisfies_cross_field_rules(model: type[BaseModel], tmp_path: Path) -> None:
    schema = model.model_json_schema()
    minimal = run(MockLLMRunner(fixtures_dir=tmp_path), schema).output
    with pytest.raises(ValueError):  # JSON Schema cannot express these rules: the minimal instance breaks them
        model.model_validate(minimal)

    populated = run(MockLLMRunner(fixtures_dir=tmp_path, populate_optional=True), schema).output
    built = model.model_validate(populated)
    assert built.model_dump()["format"] is VideoFormat.LONG


@pytest.mark.parametrize(
    ("pattern", "min_length", "expected"),
    [
        (r"^[\w-]{6,20}$", 0, "aaaaaa"),
        (r"^(48h|7d|28d|lifetime)$", 0, "48h"),
        (r"^S\d{2,3}-\d{2}$", 0, "S00-00"),
        (r"^[^abc]+$", 0, "0"),
        (r"^(ab)\1$", 0, "abab"),
        (r"^(?=x)x+?$", 0, "x"),
        (r"^[a-z0-9][a-z0-9_-]{0,63}$", 10, "aaaaaaaaaa"),
        (r"id-\d", 0, "id-0"),
    ],
)
def test_pattern_instance(pattern: str, min_length: int, expected: str) -> None:
    assert pattern_instance(pattern, min_length) == expected


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "string", "pattern": "^a{2}$", "minLength": 3},  # contradictory
        {"type": "string", "pattern": "^(?!x)x$"},  # lookahead makes it impossible
        {"type": "object", "properties": {"a": False}, "required": ["a"]},
        {"type": "object", "properties": {"n": {"$ref": "#"}}, "required": ["n"]},  # infinitely recursive
        {"$ref": "https://example.com/remote.json"},
        {"type": "integer", "minimum": 5, "maximum": 4},
        {"type": "array", "items": {"enum": ["only"]}, "minItems": 2, "uniqueItems": True},
    ],
)
def test_unsatisfiable_schemas_raise_instead_of_returning_invalid_output(schema: dict[str, Any], runner: MockLLMRunner) -> None:
    with pytest.raises(MockSchemaUnsupported) as caught:
        run(runner, schema)
    assert isinstance(caught.value, LLMOutputInvalid)


def test_recursive_schema_through_optional_property_terminates(tmp_path: Path) -> None:
    schema = {
        "$defs": {"Node": {"type": "object", "properties": {"child": {"$ref": "#/$defs/Node"}, "v": {"type": "integer"}}}},
        "$ref": "#/$defs/Node",
    }
    populated = generate_instance(schema, populate_optional=True)
    depth = 0
    node = populated
    while "child" in node:
        node, depth = node["child"], depth + 1
    assert 0 < depth <= 10
    assert generate_instance(schema) == {}


def test_invalid_schema_and_arguments_are_refused(runner: MockLLMRunner) -> None:
    with pytest.raises(ValueError, match="invalid JSON Schema"):
        run(runner, {"type": 12})
    with pytest.raises(ValueError):
        runner.run(agent="", prompt="p", model="opus", json_schema=None, max_turns=1, allowed_tools=(), cwd=Path("."))
    with pytest.raises(ValueError):
        runner.run(agent="a", prompt="p", model="opus", json_schema=None, max_turns=0, allowed_tools=(), cwd=Path("."))


def test_text_output_without_schema_is_deterministic_per_prompt(runner: MockLLMRunner) -> None:
    a1 = run(runner, None, prompt="one").output
    a2 = run(runner, None, prompt="one").output
    b = run(runner, None, prompt="two").output

    assert isinstance(a1, str) and "mock" in a1
    assert a1 == a2 != b


# ------------------------------------------------------------------ recorded fixtures


def write_fixture(directory: Path, agent: str, prompt: str, payload: Any) -> Path:
    path = directory / f"{fixture_key(agent, prompt)}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_fixture_key_is_sha256_of_agent_and_prompt() -> None:
    import hashlib

    assert fixture_key("scout", "hello") == hashlib.sha256(b"scouthello").hexdigest()


def test_recorded_fixture_is_replayed(tmp_path: Path) -> None:
    schema = {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}
    write_fixture(tmp_path, "scout", "p", {"output": {"title": "recorded"}})
    runner = MockLLMRunner(fixtures_dir=tmp_path)

    result = run(runner, schema)
    assert result.output == {"title": "recorded"}
    assert result.raw["source"] == "fixture"
    assert run(runner, schema, agent="other").raw["source"] == "schema"  # another agent: another key


def test_committed_fixtures_are_replayed_from_the_default_directory() -> None:
    runner = MockLLMRunner()
    assert runner.fixtures_dir == DEFAULT_FIXTURES_DIR

    text = run(runner, None, agent="mock-demo", prompt="Say hello in one sentence.")
    assert text.output == "Hello from a recorded mock fixture." and text.raw["source"] == "fixture"

    schema = {"type": "object", "properties": {"title": {"type": "string"}, "score": {"type": "integer"}}, "required": ["title"]}
    structured = run(runner, schema, agent="mock-demo", prompt="Give the demo package title as JSON.")
    assert structured.output == {"title": "A recorded mock title", "score": 42}


def test_committed_fixtures_are_well_formed() -> None:
    files = sorted(DEFAULT_FIXTURES_DIR.glob("*.json"))
    assert files
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert set(data) <= {"output", "agent", "prompt"} and "output" in data
        if "agent" in data and "prompt" in data:
            assert path.stem == fixture_key(data["agent"], data["prompt"])


def test_stale_fixture_that_breaks_the_schema_fails_loudly(tmp_path: Path) -> None:
    schema = {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}
    write_fixture(tmp_path, "scout", "p", {"output": {"name": "old field"}})

    with pytest.raises(LLMOutputInvalid, match="does not match the schema"):
        run(MockLLMRunner(fixtures_dir=tmp_path), schema)


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "no output key"},
        {"output": "x", "unexpected": 1},
        {"output": "x", "agent": "someone-else"},
        {"output": "x", "prompt": "another prompt"},
    ],
)
def test_malformed_or_misnamed_fixture_is_refused(tmp_path: Path, payload: dict[str, Any]) -> None:
    write_fixture(tmp_path, "scout", "p", payload)
    with pytest.raises(MockFixtureInvalid):
        run(MockLLMRunner(fixtures_dir=tmp_path), None)


def test_unreadable_fixture_and_non_text_output_are_refused(tmp_path: Path) -> None:
    path = write_fixture(tmp_path, "scout", "p", {})
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(MockFixtureInvalid):
        run(MockLLMRunner(fixtures_dir=tmp_path), None)

    write_fixture(tmp_path, "scout", "p", {"output": {"a": 1}})
    with pytest.raises(LLMOutputInvalid, match="string output"):
        run(MockLLMRunner(fixtures_dir=tmp_path), None)


# ------------------------------------------------------------------ concurrency


def test_concurrent_calls_are_deterministic_and_all_recorded(runner: MockLLMRunner) -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        outputs = list(pool.map(lambda i: json.dumps(run(runner, RICH_SCHEMA, prompt=f"p{i}").output), range(64)))

    assert len(set(outputs)) == 1
    assert len(runner.calls) == 64
    assert {c["key"] for c in runner.calls} == {fixture_key("scout", f"p{i}") for i in range(64)}
