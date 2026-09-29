"""Test doubles for the dry-run pipeline (shared by tests/unit and tests/integration)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from studio.adapters.base import AdapterSpec
from studio.adapters.llm_base import LLMResult, LLMRunner, QuotaExhausted
from studio.adapters.mock import mock_spec
from studio.domain import AdapterKind, Channel, GateDecision, GateName, Verdict, VideoFormat
from studio.pipeline.mock_agents import MockStudioLLM


def channel(channel_id: str = "channel-a") -> Channel:
    return Channel(
        id=channel_id,
        name="Test channel",
        language="en",
        concept="how great structures of the past were built",
        formats=(VideoFormat.SHORT, VideoFormat.LONG),
        voice_id="narrator-main",
        visual_bible="knowledge/bibles/test.md",
    )


class WrappedLLM:
    """A mock LLM under another id, so that its steps get keys of their own (the id is part of a step's params)."""

    def __init__(self, suffix: str, inner: LLMRunner | None = None) -> None:
        self.inner: LLMRunner = inner or MockStudioLLM()
        self.spec: AdapterSpec = mock_spec(f"mock-studio-llm-{suffix}", AdapterKind.LLM)

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
        return self.inner.run(
            agent=agent,
            prompt=prompt,
            model=model,
            json_schema=json_schema,
            max_turns=max_turns,
            allowed_tools=allowed_tools,
            cwd=cwd,
        )


class EditedNarrationLLM(WrappedLLM):
    """The head writer's second draft: two words of one scene's narration swap places, so the scene says
    something else in as many words (same length, same duration, same picture)."""

    def __init__(self, scene_index: int, inner: LLMRunner | None = None) -> None:
        super().__init__(f"edited-s{scene_index + 1:02d}", inner)
        self.scene_index = scene_index

    def run(self, **kwargs: Any) -> LLMResult:
        result = self.inner.run(**kwargs)
        if kwargs["agent"] == "head_writer":
            scene = result.output["scenes"][self.scene_index]
            words = scene["voix_off"].split()
            words[0], words[1] = words[1], words[0]
            scene["voix_off"] = " ".join(words)
        return result


class NoDisclosureLLM(WrappedLLM):
    """The head writer's second draft switches the AI disclosure off: the render is byte for byte the approved
    one, the publication is another."""

    def __init__(self, inner: LLMRunner | None = None) -> None:
        super().__init__("no-disclosure", inner)

    def run(self, **kwargs: Any) -> LLMResult:
        result = self.inner.run(**kwargs)
        if kwargs["agent"] == "head_writer":
            result.output["divulgation_ia"]["requise"] = False
        return result


class BlockedScriptLLM(WrappedLLM):
    """The head writer's second draft leaves the render, the title and the disclosure as they were and turns the
    control block to "not publishable" (a claim the fact-checker found false): the publication looks the same."""

    def __init__(self, inner: LLMRunner | None = None) -> None:
        super().__init__("blocked-script", inner)

    def run(self, **kwargs: Any) -> LLMResult:
        result = self.inner.run(**kwargs)
        if kwargs["agent"] == "head_writer":
            control = result.output["controle"]
            control["publiable"] = False
            control["raisons_blocage"] = ["defamation risk found by the fact-checker"]
            control["faits_a_verifier"] = ["claim 3 is false"]
        return result


class QuotaAtAgentLLM(WrappedLLM):
    """Hits the subscription's usage limit when `agent` is called (a reset time in the future, or unknown)."""

    def __init__(self, agent: str, reset_at: dt.datetime | None, inner: LLMRunner | None = None) -> None:
        super().__init__(f"quota-{agent.replace('_', '-')}", inner)
        self.agent, self.reset_at = agent, reset_at
        self.exhausted = True  # set to False when the limit resets (the id stays: the same backend, healthy again)

    def run(self, **kwargs: Any) -> LLMResult:
        if self.exhausted and kwargs["agent"] == self.agent:
            raise QuotaExhausted("usage limit reached (mock)", self.reset_at)
        return self.inner.run(**kwargs)


class RejectingReviewer:
    """A human who refuses `gate`, and approves the others."""

    def __init__(self, gate: GateName) -> None:
        self.gate = gate

    def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision:
        verdict = Verdict.REJECT if gate is self.gate else Verdict.APPROVE
        return GateDecision(
            gate=gate,
            subject_key=subject_key,
            agent_verdict=Verdict.APPROVE,
            human_verdict=verdict,
            human_note="mock reviewer: refused" if verdict is Verdict.REJECT else "mock reviewer: ok",
            decided_at=now,
            mock=True,
        )
