"""Test backend of the LLM contract (docs/design/phase1.md): deterministic, `mock` in its id, zero usage.

For each call:
1. a recorded answer is replayed when `<fixtures_dir>/<fixture_key(agent, prompt)>.json` exists, where
   `fixture_key = sha256((agent + prompt).encode("utf-8"))`; the file holds `{"output": ...}` and may also
   carry `agent` and `prompt`, which must then match the call;
2. otherwise, with a JSON Schema, a minimal valid instance is derived from the schema alone (required
   properties, `minItems` items, first enum value, lower numeric bound, shortest string matching
   `pattern`), then validated; without a schema, a fixed text derived from the fixture key is returned.

A replayed answer that does not validate raises LLMOutputInvalid (a stale fixture fails loudly). A schema the
generator cannot satisfy raises MockSchemaUnsupported (also an LLMOutputInvalid).

`populate_optional=True` also fills optional properties and gives every array at least one item: domain
contracts with cross-field rules that JSON Schema cannot express (a long-form Package needs a thumbnail, a
non-publishable Script needs a reason) then validate too.
"""

from __future__ import annotations

import copy
import importlib
import json
import re
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path
from typing import Any

from jsonschema import exceptions as jsonschema_exceptions
from jsonschema import validators as jsonschema_validators
from jsonschema.protocols import Validator

from studio.adapters.base import AdapterSpec
from studio.adapters.llm_base import LLMOutputInvalid, LLMResult, LLMUsage
from studio.core.interfaces import StudioError
from studio.domain import AdapterKind, AdapterStatus, LicenseClass, sha256_hex

MOCK_LLM_ID = "mock-llm"
MOCK_LLM_SPEC = AdapterSpec(
    id=MOCK_LLM_ID,
    kind=AdapterKind.LLM,
    vram_gb=None,
    gpu_seconds_per_output_second=None,
    max_width=None,
    max_height=None,
    max_duration_s=None,
    license_class=LicenseClass.ACCEPTED,
    license_url="n/a (mock)",
    status=AdapterStatus.MOCK,
)
DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "llm"
FIXTURE_KEYS = frozenset({"output", "agent", "prompt"})
MOCK_TEXT = "mock"
MAX_DEPTH = 32
POPULATE_MAX_DEPTH = 8
FORMAT_SAMPLES = {
    "date-time": "2000-01-01T00:00:00Z",
    "date": "2000-01-01",
    "time": "00:00:00Z",
    "duration": "PT0S",
    "email": "mock@example.com",
    "idn-email": "mock@example.com",
    "hostname": "mock.example.com",
    "idn-hostname": "mock.example.com",
    "ipv4": "192.0.2.1",
    "ipv6": "2001:db8::1",
    "uri": "https://example.com/mock",
    "iri": "https://example.com/mock",
    "uri-reference": "https://example.com/mock",
    "iri-reference": "https://example.com/mock",
    "url": "https://example.com/mock",
    "uuid": "00000000-0000-0000-0000-000000000000",
}


class MockSchemaUnsupported(LLMOutputInvalid):
    """The mock cannot derive a valid instance from this schema (record a fixture instead)."""


class MockFixtureInvalid(StudioError):
    """A recorded fixture file is malformed or does not belong to the call it is named after."""


def fixture_key(agent: str, prompt: str) -> str:
    """Name (without `.json`) of the fixture replayed for this call."""
    return sha256_hex(agent + prompt)


def _schema_validator(schema: dict[str, Any]) -> Validator:
    cls = jsonschema_validators.validator_for(schema)
    try:
        cls.check_schema(schema)
    except jsonschema_exceptions.SchemaError as exc:
        raise ValueError(f"invalid JSON Schema: {exc.message}") from exc
    return cls(schema)


def _problem(validator: Validator, value: Any) -> str | None:
    error = jsonschema_exceptions.best_match(validator.iter_errors(value))
    if error is None:
        return None
    path = "/".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"[:500]


class MockLLMRunner:
    """LLMRunner that never calls a model. Thread-safe; `calls` records every call (agent, model, key)."""

    def __init__(self, fixtures_dir: Path | None = None, *, populate_optional: bool = False) -> None:
        self.spec = MOCK_LLM_SPEC
        self.fixtures_dir = Path(fixtures_dir) if fixtures_dir is not None else DEFAULT_FIXTURES_DIR
        self.populate_optional = populate_optional
        self.calls: list[dict[str, str]] = []
        self._lock = threading.Lock()

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
        if not agent or not model:
            raise ValueError("agent and model are required")
        if isinstance(max_turns, bool) or not isinstance(max_turns, int) or max_turns < 1:
            raise ValueError(f"max_turns must be a positive integer, got {max_turns!r}")
        validator = _schema_validator(json_schema) if json_schema is not None else None
        key = fixture_key(agent, prompt)
        with self._lock:
            self.calls.append({"agent": agent, "model": model, "key": key})

        recorded = self._load_fixture(key, agent, prompt)
        if recorded is not None:
            output, source = recorded, "fixture"
            if validator is not None:
                problem = _problem(validator, output)
                if problem is not None:
                    raise LLMOutputInvalid(f"{MOCK_LLM_ID}: fixture {key}.json does not match the schema: {problem}")
            elif not isinstance(output, str):
                raise LLMOutputInvalid(f"{MOCK_LLM_ID}: fixture {key}.json must hold a string output when no schema is given")
        elif json_schema is not None:
            output, source = generate_instance(json_schema, populate_optional=self.populate_optional), "schema"
        else:
            output, source = f"{MOCK_TEXT} answer {key[:12]}", "text"
        return LLMResult(
            output=output,
            usage=LLMUsage(model=MOCK_LLM_ID),
            session_id=f"{MOCK_LLM_ID}-{key[:32]}",
            raw={"mock": True, "adapter": MOCK_LLM_ID, "source": source, "fixture_key": key},
        )

    def _load_fixture(self, key: str, agent: str, prompt: str) -> Any | None:
        path = self.fixtures_dir / f"{key}.json"
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MockFixtureInvalid(f"unreadable fixture {path.name}: {exc}") from exc
        if not isinstance(data, dict) or "output" not in data or set(data) - FIXTURE_KEYS:
            raise MockFixtureInvalid(f"fixture {path.name} must be an object with 'output' (and optionally 'agent', 'prompt')")
        for field, expected in (("agent", agent), ("prompt", prompt)):
            if field in data and data[field] != expected:
                raise MockFixtureInvalid(f"fixture {path.name} was recorded for another {field}")
        return data["output"]


# ------------------------------------------------------------------ instance generation


def generate_instance(schema: dict[str, Any], *, populate_optional: bool = False) -> Any:
    """A minimal instance valid against `schema`, the same for the same schema; MockSchemaUnsupported if none
    is found. Local `$ref`s (`#/...`) are followed; remote references are not."""
    validator = _schema_validator(schema)
    generator = _Generator(schema, validator, populate_optional)
    value = generator.instance(schema, variant=0, depth=0)
    problem = _problem(validator, value)
    if problem is not None:
        raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: generated instance is invalid ({problem}); record a fixture instead")
    return value


@dataclass
class _Generator:
    root: dict[str, Any]
    validator: Validator
    populate: bool

    def instance(self, schema: Any, *, variant: int, depth: int) -> Any:
        if depth > MAX_DEPTH:
            raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: schema nests deeper than {MAX_DEPTH} levels (recursive?)")
        if schema is True:
            return None
        if schema is False or not isinstance(schema, dict):
            raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: no instance satisfies schema {schema!r}")
        schema = self.flatten(schema, depth)
        if "const" in schema:
            return copy.deepcopy(schema["const"])
        if "enum" in schema:
            values = schema["enum"]
            if not values:
                raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: empty enum")
            return copy.deepcopy(values[variant % len(values)])
        for keyword in ("anyOf", "oneOf"):
            if keyword in schema:
                return self.first_branch(schema, keyword, variant, depth)
        kind = self.type_of(schema)
        if kind == "object":
            return self.object(schema, variant, depth)
        if kind == "array":
            return self.array(schema, variant, depth)
        if kind == "string":
            return self.string(schema, variant)
        if kind == "integer":
            return self.integer(schema, variant)
        if kind == "number":
            return self.number(schema, variant)
        if kind == "boolean":
            return variant % 2 == 1
        return None

    # -------------------------------------------------------------- schema plumbing

    def resolve(self, ref: str) -> Any:
        if not ref.startswith("#"):
            raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: only local $ref are supported, got {ref!r}")
        node: Any = self.root
        for token in [t for t in ref[1:].split("/") if t]:
            token = token.replace("~1", "/").replace("~0", "~")
            if isinstance(node, dict) and token in node:
                node = node[token]
            elif isinstance(node, list) and token.isdigit() and int(token) < len(node):
                node = node[int(token)]
            else:
                raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: unresolvable $ref {ref!r}")
        return node

    def flatten(self, schema: dict[str, Any], depth: int) -> dict[str, Any]:
        """Inline `$ref` and `allOf` into one schema (keywords of later parts win, properties and required merge)."""
        if "$ref" not in schema and "allOf" not in schema:
            return schema
        if depth > MAX_DEPTH:
            raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: $ref chain deeper than {MAX_DEPTH} (recursive?)")
        merged = {k: v for k, v in schema.items() if k not in ("$ref", "allOf")}
        parts: list[Any] = []
        if "$ref" in schema:
            parts.append(self.resolve(schema["$ref"]))
        parts.extend(schema.get("allOf", []))
        result: dict[str, Any] = {}
        for part in parts:
            if part is True:
                continue
            if not isinstance(part, dict):
                raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: no instance satisfies schema {part!r}")
            result = _merge(result, self.flatten(part, depth + 1))
        return _merge(result, merged)

    def first_branch(self, schema: dict[str, Any], keyword: str, variant: int, depth: int) -> Any:
        base = {k: v for k, v in schema.items() if k != keyword}
        for branch in schema[keyword]:
            if branch is False:
                continue
            merged = _merge(base, self.flatten(branch, depth + 1)) if isinstance(branch, dict) else base
            try:
                candidate = self.instance(merged, variant=variant, depth=depth + 1)
            except MockSchemaUnsupported:
                continue
            if self.validator.evolve(schema=schema).is_valid(candidate):  # evolve keeps the root's $refs
                return candidate
        raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: no {keyword} branch could be satisfied")

    @staticmethod
    def type_of(schema: dict[str, Any]) -> str:
        declared = schema.get("type")
        if isinstance(declared, list):
            concrete = [t for t in declared if t != "null"]
            return str(concrete[0] if concrete else "null")
        if isinstance(declared, str):
            return declared
        if any(k in schema for k in ("properties", "required", "additionalProperties", "minProperties")):
            return "object"
        if any(k in schema for k in ("items", "prefixItems", "minItems", "maxItems", "uniqueItems")):
            return "array"
        if any(k in schema for k in ("pattern", "minLength", "maxLength", "format")):
            return "string"
        if any(k in schema for k in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf")):
            return "number"
        return "null"

    # -------------------------------------------------------------- per type

    def object(self, schema: dict[str, Any], variant: int, depth: int) -> dict[str, Any]:
        properties: dict[str, Any] = schema.get("properties") or {}
        required: list[str] = list(schema.get("required") or [])
        extra_schema = schema.get("additionalProperties", True)
        out: dict[str, Any] = {}
        for name in [*[n for n in properties if n in required], *[n for n in required if n not in properties]]:
            out[name] = self.instance(properties.get(name, extra_schema), variant=variant, depth=depth + 1)
        optional = [n for n in properties if n not in out]
        populate = self.populate and depth < POPULATE_MAX_DEPTH
        min_properties = int(schema.get("minProperties", 0))
        for name in optional:
            if not populate and len(out) >= min_properties:
                break
            try:
                out[name] = self.instance(properties[name], variant=variant, depth=depth + 1)
            except MockSchemaUnsupported:
                if len(out) < min_properties:
                    raise
        index = 0
        while len(out) < min_properties and extra_schema is not False:
            index += 1
            out[f"{MOCK_TEXT}_{index}"] = self.instance(extra_schema, variant=variant, depth=depth + 1)
        return {name: out[name] for name in [*properties, *out] if name in out}

    def array(self, schema: dict[str, Any], variant: int, depth: int) -> list[Any]:
        items = schema.get("items", True)
        prefix: list[Any] = list(schema.get("prefixItems") or [])
        if isinstance(items, list):  # draft 4-7 tuple form
            prefix, rest = items, schema.get("additionalItems", True)
        else:
            rest = items
        count = int(schema.get("minItems", 0))
        if self.populate and depth < POPULATE_MAX_DEPTH:
            count = max(count, 1, len(prefix))
            if "maxItems" in schema:
                count = min(count, int(schema["maxItems"]))
        unique = bool(schema.get("uniqueItems"))
        out = []
        for i in range(count):
            item_schema = prefix[i] if i < len(prefix) else rest
            out.append(self.instance(item_schema, variant=i if unique else variant, depth=depth + 1))
        return out

    def string(self, schema: dict[str, Any], variant: int) -> str:
        min_length = int(schema.get("minLength", 0))
        max_length = schema.get("maxLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            return pattern_instance(pattern, min_length, None if max_length is None else int(max_length))
        sample = FORMAT_SAMPLES.get(str(schema.get("format", "")))
        if sample is not None and variant == 0 and len(sample) >= min_length:
            return sample
        text = MOCK_TEXT if variant == 0 else f"{MOCK_TEXT}{variant}"
        if len(text) < min_length:
            text = text + "-" * (min_length - len(text))
        if max_length is not None:
            text = text[: int(max_length)]
        return text

    def integer(self, schema: dict[str, Any], variant: int) -> int:
        return int(_numeric(schema, variant, integral=True))

    def number(self, schema: dict[str, Any], variant: int) -> int | float:
        value = _numeric(schema, variant, integral=False)
        return int(value) if value == value.to_integral_value() else float(value)


def _merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = dict(a)
    for key, value in b.items():
        if key == "properties" and isinstance(out.get(key), dict):
            out[key] = {**out[key], **value}
        elif key == "required" and isinstance(out.get(key), list):
            out[key] = list(dict.fromkeys([*out[key], *value]))
        else:
            out[key] = value
    return out


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None  # absent, or a draft-4 boolean exclusive bound (left to the final validation)
    return Decimal(str(value))


def _bound(schema: dict[str, Any], inclusive: str, exclusive: str, *, lower: bool) -> tuple[Decimal | None, bool]:
    """The stricter of an inclusive and an exclusive bound, and whether it is exclusive."""
    inc, exc = _decimal(schema.get(inclusive)), _decimal(schema.get(exclusive))
    if exc is None:
        return inc, False
    if inc is None or (exc >= inc if lower else exc <= inc):
        return exc, True
    return inc, False


def _snap(value: Decimal, unit: Decimal, rounding: str) -> Decimal:
    return (value / unit).to_integral_value(rounding=rounding) * unit


def _numeric(schema: dict[str, Any], variant: int, *, integral: bool) -> Decimal:
    """Smallest value within the bounds (0 when unbounded or allowed), a multiple of `multipleOf`; `variant`
    steps upwards while the bounds allow it (distinct values for `uniqueItems`)."""
    low, low_open = _bound(schema, "minimum", "exclusiveMinimum", lower=True)
    high, high_open = _bound(schema, "maximum", "exclusiveMaximum", lower=False)
    unit = _decimal(schema.get("multipleOf")) or (Decimal(1) if integral else None)
    step = unit or Decimal(1)

    def fits(v: Decimal) -> bool:
        above = low is None or (v > low if low_open else v >= low)
        below = high is None or (v < high if high_open else v <= high)
        return above and below

    if low is not None:
        base = _snap(low, unit, ROUND_CEILING) if unit is not None else low
        if low_open and base <= low:
            base += step
        if not fits(base) and unit is None and high is not None:
            base = (low + high) / 2
    elif high is not None and not fits(Decimal(0)):
        base = _snap(high, unit, ROUND_FLOOR) if unit is not None else high
        if high_open and base >= high:
            base -= step
    else:
        base = Decimal(0)
    candidate = base + variant * step
    return candidate if fits(candidate) else base


# ------------------------------------------------------------------ strings matching a pattern

# Python's own regex parser (private but stable across 3.11-3.13); JSON Schema patterns use `re.search`.
_RE_PARSER: Any = importlib.import_module("re._parser")
_RE_CONSTANTS: Any = importlib.import_module("re._constants")
_CANDIDATES = "a0Ab1B_-. xyz"
_CATEGORIES = {
    "CATEGORY_DIGIT": re.compile(r"\d"),
    "CATEGORY_NOT_DIGIT": re.compile(r"\D"),
    "CATEGORY_SPACE": re.compile(r"\s"),
    "CATEGORY_NOT_SPACE": re.compile(r"\S"),
    "CATEGORY_WORD": re.compile(r"\w"),
    "CATEGORY_NOT_WORD": re.compile(r"\W"),
}


def pattern_instance(pattern: str, min_length: int = 0, max_length: int | None = None) -> str:
    """Shortest string the regex walk yields for `pattern` (JSON Schema semantics: `re.search`), lengthened by
    repeating quantified parts until `min_length`; MockSchemaUnsupported when the result does not qualify."""
    try:
        parsed = _RE_PARSER.parse(pattern)
    except re.error as exc:
        raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: invalid pattern {pattern!r}: {exc}") from exc
    walker = _RegexWalker()
    text = walker.walk(parsed)
    if len(text) < min_length:
        walker = _RegexWalker(extra=min_length - len(text))
        text = walker.walk(parsed)
    ok = re.search(pattern, text) is not None and len(text) >= min_length
    if not ok or (max_length is not None and len(text) > max_length):
        raise MockSchemaUnsupported(
            f"{MOCK_LLM_ID}: cannot build a string for pattern {pattern!r} with length in [{min_length}, {max_length}]"
        )
    return text


class _RegexWalker:
    """Walks the parse tree of Python's `re` module and emits one matching string (first alternatives,
    minimal repeats, first member of each character class). `extra` characters are added by repeating
    quantified parts, left to right, for a `minLength`."""

    def __init__(self, extra: int = 0) -> None:
        self.extra = extra
        self.groups: dict[int, str] = {}

    def walk(self, items: Any) -> str:
        return "".join(self.node(str(op), av) for op, av in items)

    def node(self, op: str, av: Any) -> str:
        if op == "LITERAL":
            return chr(av)
        if op == "NOT_LITERAL":
            return next(c for c in _CANDIDATES if ord(c) != av)
        if op == "ANY":
            return "a"
        if op == "IN":
            return self.char_class(av)
        if op == "AT":
            return ""
        if op == "BRANCH":
            return self.walk(av[1][0])
        if op == "SUBPATTERN":
            group, _add, _del, body = av
            text = self.walk(body)
            if group is not None:
                self.groups[group] = text
            return text
        if op == "ATOMIC_GROUP":
            return self.walk(av)
        if op in ("MAX_REPEAT", "MIN_REPEAT", "POSSESSIVE_REPEAT"):
            low, high, body = av
            unbounded = high == _RE_CONSTANTS.MAXREPEAT
            parts = [self.walk(body) for _ in range(low)]
            while self.extra > 0 and (unbounded or len(parts) < high):
                piece = self.walk(body)
                if not piece:
                    break
                parts.append(piece)
                self.extra -= len(piece)
            return "".join(parts)
        if op == "GROUPREF":
            return self.groups.get(av, "")
        if op == "GROUPREF_EXISTS":
            group, yes, no = av
            return self.walk(yes) if group in self.groups else (self.walk(no) if no is not None else "")
        if op in ("ASSERT", "ASSERT_NOT"):
            return ""  # lookarounds are checked by the final re.search
        raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: unsupported regex construct {op}")

    @staticmethod
    def char_class(items: Any) -> str:
        members = [(str(op), av) for op, av in items]
        negated = bool(members) and members[0][0] == "NEGATE"
        if negated:
            members = members[1:]

        def contains(ch: str) -> bool:
            for op, av in members:
                if op == "LITERAL" and ord(ch) == av:
                    return True
                if op == "RANGE" and av[0] <= ord(ch) <= av[1]:
                    return True
                if op == "CATEGORY" and _CATEGORIES.get(str(av), re.compile(r"(?!)")).match(ch):
                    return True
            return False

        if not negated:
            op, av = members[0]
            if op == "LITERAL":
                return chr(av)
            if op == "RANGE":
                return chr(av[0])
        for ch in _CANDIDATES:
            if contains(ch) != negated:
                return ch
        raise MockSchemaUnsupported(f"{MOCK_LLM_ID}: no character found for a regex class")
