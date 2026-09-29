"""Adapter registry: kind → adapters by id (MISSION §6.3). Steps ask for `get(kind, adapter_id)` and never
import a concrete adapter, so a mock and a local model are swapped by configuration.

Registration enforces the contracts that must hold whatever the adapter:
- it satisfies the protocol of its kind (runtime check of `studio/adapters/base.py`, `llm_base.py`), and
  its methods accept the protocol's parameters: `isinstance` alone only checks names, so it cannot tell
  a text-to-image adapter from a text-to-video one (both expose `generate`);
- a mock says so: `status is MOCK` if and only if `mock` is in its id (reports then show it);
- ADR-002 licence policy: an adapter whose licence class is `refused` or `closed` cannot be registered.
"""

from __future__ import annotations

import inspect
import threading
from collections.abc import Mapping

from studio.adapters.base import (
    AdapterSpec,
    ImageToVideo,
    Interpolator,
    LipSync,
    MusicGenerator,
    SoundEffects,
    TextToImage,
    TextToSpeech,
    TextToVideo,
    Transcriber,
    Upscaler,
    VisionCritic,
)
from studio.adapters.llm_base import LLMRunner
from studio.adapters.mock import MOCK_CLASSES
from studio.adapters.mock_llm import MockLLMRunner
from studio.core.interfaces import StudioError
from studio.domain import AdapterKind, AdapterStatus, LicenseClass

PROTOCOLS: Mapping[AdapterKind, type] = {
    AdapterKind.TEXT_TO_IMAGE: TextToImage,
    AdapterKind.IMAGE_TO_VIDEO: ImageToVideo,
    AdapterKind.TEXT_TO_VIDEO: TextToVideo,
    AdapterKind.LIP_SYNC: LipSync,
    AdapterKind.TTS: TextToSpeech,
    AdapterKind.MUSIC: MusicGenerator,
    AdapterKind.SFX: SoundEffects,
    AdapterKind.UPSCALE: Upscaler,
    AdapterKind.INTERPOLATE: Interpolator,
    AdapterKind.TRANSCRIBE: Transcriber,
    AdapterKind.LLM: LLMRunner,
    AdapterKind.VISION_CRITIC: VisionCritic,
}
FORBIDDEN_LICENSES = frozenset({LicenseClass.REFUSED, LicenseClass.CLOSED})


class AdapterNotFound(StudioError):
    pass


class AdapterRejected(StudioError):
    """The adapter breaks a registration rule (protocol, mock naming, licence policy)."""


def _signature_mismatch(adapter: object, protocol: type) -> str | None:
    """Why `adapter`'s methods cannot be called as `protocol` declares them (None when they can)."""
    for name, member in vars(protocol).items():
        if name.startswith("_") or not callable(member):
            continue
        expected = list(inspect.signature(member).parameters.values())[1:]  # drop `self`
        actual = list(inspect.signature(getattr(adapter, name)).parameters.values())  # bound method
        if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in actual) and any(
            p.kind is inspect.Parameter.VAR_POSITIONAL for p in actual
        ):
            continue
        positional = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        want_pos = [p.name for p in expected if p.kind in positional]
        have_pos = [p.name for p in actual if p.kind in positional]
        if have_pos[: len(want_pos)] != want_pos:
            return f"{name}() positional parameters {have_pos}, expected {want_pos}"
        by_name = {p.name: p for p in actual}
        takes_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in actual)
        for p in expected:
            if p.kind is inspect.Parameter.KEYWORD_ONLY and p.name not in by_name and not takes_kwargs:
                return f"{name}() lacks keyword parameter {p.name!r}"
        wanted = {p.name for p in expected}
        for p in actual:
            if p.name not in wanted and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                if p.default is inspect.Parameter.empty:
                    return f"{name}() requires unexpected parameter {p.name!r}"
    return None


def validate_adapter(adapter: object) -> AdapterSpec:
    """Return the adapter's spec, or raise AdapterRejected with the rule it breaks."""
    spec = getattr(adapter, "spec", None)
    if not isinstance(spec, AdapterSpec):
        raise AdapterRejected(f"{adapter!r} has no AdapterSpec `spec`")
    protocol = PROTOCOLS.get(spec.kind)
    if protocol is None or not isinstance(adapter, protocol):
        raise AdapterRejected(f"{spec.id}: does not implement the {spec.kind.value} protocol")
    mismatch = _signature_mismatch(adapter, protocol)
    if mismatch is not None:
        raise AdapterRejected(f"{spec.id}: signature does not match the {spec.kind.value} protocol: {mismatch}")
    if (spec.status is AdapterStatus.MOCK) != ("mock" in spec.id):
        raise AdapterRejected(f"{spec.id}: a mock must have status 'mock' and 'mock' in its id, and only a mock")
    if spec.license_class in FORBIDDEN_LICENSES:
        raise AdapterRejected(f"{spec.id}: licence class {spec.license_class.value} is excluded by ADR-002")
    return spec


class AdapterRegistry:
    """Thread-safe map kind → {adapter id → adapter}."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._adapters: dict[AdapterKind, dict[str, object]] = {}

    def register(self, adapter: object, *, replace: bool = False) -> None:
        spec = validate_adapter(adapter)
        with self._lock:
            by_id = self._adapters.setdefault(spec.kind, {})
            if spec.id in by_id and not replace:
                raise AdapterRejected(f"{spec.kind.value} adapter {spec.id!r} is already registered")
            by_id[spec.id] = adapter

    def get(self, kind: AdapterKind, adapter_id: str) -> object:
        with self._lock:
            adapter = self._adapters.get(kind, {}).get(adapter_id)
        if adapter is None:
            known = ", ".join(self.ids(kind)) or "none"
            raise AdapterNotFound(f"no {kind.value} adapter {adapter_id!r} (registered: {known})")
        return adapter

    def ids(self, kind: AdapterKind) -> list[str]:
        with self._lock:
            return sorted(self._adapters.get(kind, {}))

    def kinds(self) -> list[AdapterKind]:
        with self._lock:
            return sorted(k for k, v in self._adapters.items() if v)


def default_mocks() -> dict[AdapterKind, object]:
    """A fresh mock for every media kind (`MOCK_CLASSES`). The LLM mock is not a media mock:
    `default_registry()` adds it."""
    mocks: dict[AdapterKind, object] = {}
    for cls in MOCK_CLASSES:
        adapter = cls()
        mocks[adapter.spec.kind] = adapter
    return mocks


def default_registry() -> AdapterRegistry:
    """Every default mock, one per kind: the eleven media mocks and `MockLLMRunner` (`mock-llm`, which
    replays recorded answers or derives valid ones from the schema). A step gets its adapter from the
    registry by kind and id, so no step imports a concrete adapter, whatever the kind."""
    registry = AdapterRegistry()
    for adapter in default_mocks().values():
        registry.register(adapter)
    registry.register(MockLLMRunner())
    return registry


_default: AdapterRegistry | None = None
_default_lock = threading.Lock()


def _registry() -> AdapterRegistry:
    global _default
    with _default_lock:
        if _default is None:
            _default = default_registry()
        return _default


def register(adapter: object, *, replace: bool = False) -> None:
    """Add an adapter to the process-wide registry (pre-filled with `default_registry()`)."""
    _registry().register(adapter, replace=replace)


def get(kind: AdapterKind, adapter_id: str) -> object:
    """Adapter `adapter_id` of `kind` from the process-wide registry; AdapterNotFound otherwise."""
    return _registry().get(kind, adapter_id)
