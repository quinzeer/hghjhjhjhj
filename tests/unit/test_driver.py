"""The dry-run driver's own rules, without a render: who answers the gates and in which mode, what is delivered
(critic B3, I-1, I-2, I-3, m-1)."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from studio.core.artifacts import LocalArtifactStore
from studio.core.db import make_engine
from studio.core.interfaces import StudioError
from studio.domain import (
    GateDecision,
    GateName,
    Platform,
    Publication,
    PublicationCandidate,
    SceneRole,
    Script,
    Verdict,
    VideoFormat,
    canonical_json,
)
from studio.pipeline.driver import _Autopilot, _clear_leftovers, _contract_message, _deliver, _waiting_for, _why
from studio.pipeline.mock_agents import MockComplianceOfficer, build_idea, build_package, build_script_doc
from studio.scenario.skill_json import from_skill_json

NOON = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.UTC)
RENDER = "c" * 64


def store_in(tmp_path: Path) -> LocalArtifactStore:
    store = LocalArtifactStore(tmp_path / "cas", make_engine(f"sqlite:///{tmp_path / 'studio.db'}"))
    store.create_schema()
    return store


def script_of(roles: tuple[SceneRole, ...] | None = None) -> Script:
    brief: dict[str, Any] = {"channel": {"id": "channel-a"}, "format": VideoFormat.SHORT.value, "language": "en", "seed": 0}
    idea = build_idea(brief)
    package = build_package({**brief, "idea": idea})
    script, _ = from_skill_json(build_script_doc({**brief, "idea": idea, "package": package}, roles), idea["id"])
    return script


class Stored:
    """A script, a QA report and the candidate that names them, in a store."""

    def __init__(self, tmp_path: Path, script: Script | None = None, defects: list[str] | None = None) -> None:
        self.store = store_in(tmp_path)
        self.script = script or script_of()
        put = self.store.put_bytes
        self.script_key = put(self.script.canonical_json().encode(), kind="json", media_type="application/json").key
        report = {"render": {"video_key": RENDER}, "defects": defects or []}
        self.qa_key = put(canonical_json(report).encode(), kind="json", media_type="application/json").key
        self.candidate = PublicationCandidate(
            run_id="run-1",
            channel_id="channel-a",
            script_key=self.script_key,
            qa_key=self.qa_key,
            publication=Publication(
                platform=Platform.YOUTUBE,
                render_key=RENDER,
                title=self.script.titles[0],
                description=self.script.promise,
                contains_synthetic_media=self.script.disclosure.required,
            ),
        )
        self.candidate_key = put(self.candidate.canonical_json().encode(), kind="json", media_type="application/json").key

    def autopilot(self, **kwargs: Any) -> _Autopilot:
        return _Autopilot(self.store, lambda: NOON, **kwargs)


class RealLookingReviewer:
    """Declares its decisions real (`mock=False`), the way a phase-2 reviewer would."""

    def __init__(self, human: Verdict = Verdict.APPROVE) -> None:
        self.human = human

    def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision:
        return GateDecision(
            gate=gate,
            subject_key=subject_key,
            agent_verdict=Verdict.APPROVE,
            human_verdict=self.human,
            decided_at=now,
            mock=False,
        )


class RealLookingOfficer:
    def review(
        self, script: Script, qa_report: Any, candidate: PublicationCandidate, candidate_key: str, now: dt.datetime
    ) -> GateDecision:
        return GateDecision(
            gate=GateName.COMPLIANCE, subject_key=candidate_key, agent_verdict=Verdict.APPROVE, decided_at=now, mock=False
        )


# ------------------------------------------------------------------ critic I-2: the autopilot answers for nobody


def test_every_decision_of_the_autopilot_says_mock_whatever_the_reviewer_and_the_officer_declare(tmp_path: Path) -> None:
    fixture = Stored(tmp_path)
    pilot = fixture.autopilot(reviewer=RealLookingReviewer(), officer=RealLookingOfficer())
    for gate, subject in (
        (GateName.G1, "a" * 64),
        (GateName.G2, fixture.candidate_key),
        (GateName.COMPLIANCE, fixture.candidate_key),
    ):
        decision = pilot.decide(gate, subject)
        assert decision.approved and decision.mock is True, gate  # an approval nobody gave is never recorded as a real one


def test_the_autopilot_puts_the_compliance_verdict_to_the_human_only_when_the_agent_did_not_reject(tmp_path: Path) -> None:
    asked: list[str] = []

    class Watching(RealLookingReviewer):
        def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision:
            asked.append(gate.value)
            return super().decide(gate, subject_key, now)

    clean = Stored(tmp_path / "clean")
    assert clean.autopilot(reviewer=Watching()).decide(GateName.COMPLIANCE, clean.candidate_key).approved and asked == [
        "compliance"
    ]

    asked.clear()
    blocked = Stored(tmp_path / "blocked", script_of((SceneRole.HOOK, SceneRole.CONTENT)))  # opens a loop, never closes it
    verdict = blocked.autopilot(reviewer=Watching()).decide(GateName.COMPLIANCE, blocked.candidate_key)
    assert verdict.rejected and verdict.mock and asked == []


# ------------------------------------------------------------------ critic B3: the officer reads what the candidate names


def test_the_officer_reads_the_script_the_candidate_names_not_the_one_the_run_holds_under_that_step_name(tmp_path: Path) -> None:
    """A script whose control block forbids publication is judged as such when the candidate names it, and a candidate
    built on the clean script is judged on the clean script: the autopilot needs no run outputs to know which."""
    clean = Stored(tmp_path / "clean")
    assert clean.autopilot().decide(GateName.COMPLIANCE, clean.candidate_key).approved

    script = clean.script
    forbidden = script.model_copy(
        update={"control": script.control.model_copy(update={"publishable": False, "blocking_reasons": ("defamation risk",)})}
    )
    other = Stored(tmp_path / "other", forbidden)
    decision = other.autopilot().decide(GateName.COMPLIANCE, other.candidate_key)
    assert decision.rejected and "control block says it is not publishable" in " ".join(decision.agent_reasons)


def test_the_officer_reads_the_qa_report_the_candidate_names(tmp_path: Path) -> None:
    flawed = Stored(tmp_path, defects=["loudness -20 LUFS"])
    decision = flawed.autopilot(officer=MockComplianceOfficer()).decide(GateName.COMPLIANCE, flawed.candidate_key)
    assert decision.rejected and "technical QA defects" in " ".join(decision.agent_reasons)


# ------------------------------------------------------------------ critic m-1: waiting is not a refusal


def test_a_decision_still_missing_a_verdict_is_waiting_not_rejected() -> None:
    def decision(agent: Verdict, human: Verdict) -> GateDecision:
        return GateDecision(gate=GateName.COMPLIANCE, subject_key="a" * 64, agent_verdict=agent, human_verdict=human, mock=True)

    pending = decision(Verdict.APPROVE, Verdict.PENDING)
    assert not pending.approved and not pending.rejected and _waiting_for(pending) == "no verdict from the human yet"
    assert _waiting_for(decision(Verdict.PENDING, Verdict.PENDING)) == "no verdict from the agent and the human yet"
    for refused in (decision(Verdict.REJECT, Verdict.PENDING), decision(Verdict.APPROVE, Verdict.REJECT)):
        assert refused.rejected and not refused.approved
    assert decision(Verdict.APPROVE, Verdict.APPROVE).approved and not decision(Verdict.APPROVE, Verdict.APPROVE).rejected


def test_why_prefers_the_words_of_the_human_then_the_agents_reasons() -> None:
    refused_by_human = GateDecision(
        gate=GateName.G2,
        subject_key="a" * 64,
        agent_verdict=Verdict.APPROVE,
        human_verdict=Verdict.REJECT,
        human_note="no thanks",
    )
    assert _why(refused_by_human) == "no thanks"
    refused_by_agent = GateDecision(
        gate=GateName.G2,
        subject_key="a" * 64,
        agent_verdict=Verdict.REJECT,
        agent_reasons=("a", "b"),
        human_verdict=Verdict.APPROVE,
    )
    assert _why(refused_by_agent) == "a; b"


# ------------------------------------------------------------------ critic I-3, m-4: what is delivered is what the store holds


def test_delivery_copies_verified_bytes_and_leaves_an_identical_file_alone(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    key = store.put_bytes(b"video bytes", kind="video", media_type="video/mp4").key
    dst = tmp_path / "out" / "render.mp4"
    _deliver(store, key, dst)
    assert dst.read_bytes() == b"video bytes" and dst.stat().st_ino != store.get(key).path.stat().st_ino
    before = dst.stat().st_mtime_ns
    _deliver(store, key, dst)
    assert dst.stat().st_mtime_ns == before  # already holding these bytes: not rewritten
    dst.write_bytes(b"edited by a tool")
    _deliver(store, key, dst)
    assert dst.read_bytes() == b"video bytes"  # a stale or edited copy is replaced by the verified bytes
    assert not list(dst.parent.glob(".*.tmp"))


def test_delivery_refuses_a_rotted_object_and_heals_the_store_so_the_next_run_recomputes_it(tmp_path: Path) -> None:
    store = store_in(tmp_path)
    key = store.put_bytes(b"good video bytes", kind="video", media_type="video/mp4").key
    path = store.get(key).path
    path.write_bytes(b"g00d video bytes")  # same size, other bytes
    dst = tmp_path / "out" / "render.mp4"
    with pytest.raises(StudioError, match="corrupt or missing.*nothing was delivered"):
        _deliver(store, key, dst)
    assert not dst.exists()
    assert not path.exists() and not store.has(key)  # removed: it reads as missing and is recomputed
    assert store.put_bytes(b"good video bytes", kind="video", media_type="video/mp4").key == key  # the recomputation rewrites it
    _deliver(store, key, dst)
    assert hashlib.sha256(dst.read_bytes()).hexdigest() == key


def test_delivery_hashes_the_copy_before_it_takes_its_place(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A copy that differs from the verified object (a disk error mid-copy) is never delivered."""
    from studio.pipeline import driver

    store = store_in(tmp_path)
    key = store.put_bytes(b"video bytes", kind="video", media_type="video/mp4").key
    monkeypatch.setattr(driver.shutil, "copy2", lambda src, dst: Path(dst).write_bytes(b"vidxx bytes"))
    dst = tmp_path / "out" / "render.mp4"
    with pytest.raises(StudioError, match="the copy of .* hashes to"):
        _deliver(store, key, dst)
    assert not dst.exists() and not list(dst.parent.glob(".*.tmp"))


def test_delivery_of_an_unknown_key_says_so(tmp_path: Path) -> None:
    with pytest.raises(StudioError, match="corrupt or missing"):
        _deliver(store_in(tmp_path), "f" * 64, tmp_path / "render.mp4")


# ------------------------------------------------------------------ what a killed predecessor leaves behind (critic N7)


def test_a_new_run_removes_the_scratch_files_and_half_written_json_of_a_killed_predecessor_and_nothing_else(
    tmp_path: Path,
) -> None:
    state, folder = tmp_path / "state", tmp_path / "channel-a" / "short"
    dead = state / "tmp" / "studio-step-dead"
    dead.mkdir(parents=True)
    (dead / "half.mp4").write_bytes(b"\x00" * 16)
    folder.mkdir(parents=True)
    for name in (".manifest.json.1a2b3c4d.tmp", ".report.json.deadbeef.tmp", ".costs.json.0badf00d.tmp"):
        (folder / name).write_text('{"half": ', encoding="utf-8")  # a JSON file killed in the middle of its write
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    (folder / "render.mp4").write_bytes(b"render")
    (folder / "notes.tmp").write_text("not a dotfile: someone else's", encoding="utf-8")

    _clear_leftovers(state, folder)

    assert not (state / "tmp").exists()
    assert sorted(f.name for f in folder.iterdir()) == ["manifest.json", "notes.tmp", "render.mp4"]


# ------------------------------------------------------------------ a document that does not fit its contract (critic R1, Q6)


def test_a_contract_error_says_where_and_why_and_never_quotes_the_document(tmp_path: Path) -> None:
    marker = "SECRET-CONTENT-OF-A-PRIVATE-DOCUMENT"
    with pytest.raises(ValidationError) as raised:
        PublicationCandidate.model_validate(
            {"run_id": "r", "channel_id": "channel-a", "publication": {}, "script_key": marker, "qa_key": marker}
        )
    assert marker in str(raised.value)  # the raw error does quote it: that is what the message must not do
    state = tmp_path / "state"
    message = _contract_message(raised.value, state)
    assert marker not in message
    assert "PublicationCandidate contract" in message and "error(s)" in message and str(state) in message
    assert "first: " in message and "another version" in message  # where it broke, why, and what can be done
