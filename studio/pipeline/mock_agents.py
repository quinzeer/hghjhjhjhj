"""Mock agents of the dry run (docs/design/phase1.md): they stand in for the LLM agents, the compliance
officer, the human reviewer and the procedural renderer until the real ones exist (phases 2-3).

Everything here is deterministic and says `mock` in its identifier, so a report or a manifest built from
them cannot pass for the real thing (MISSION §3.2). The invented sentences are placeholders, not content:
they make no factual claim about the world.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import jsonschema

from studio.adapters.base import AdapterSpec, MediaResult
from studio.adapters.llm_base import LLMOutputInvalid, LLMResult, LLMUsage
from studio.adapters.mock import derive_color, derive_digest, mock_spec
from studio.domain import (
    AdapterKind,
    GateDecision,
    GateName,
    PublicationCandidate,
    Scene,
    SceneRole,
    Script,
    ShotTechnique,
    Verdict,
    VideoFormat,
    sha256_hex,
)
from studio.media import ffmpeg

MOCK_LLM_ID = "mock-studio-llm"
MOCK_RENDERER_ID = "mock-procedural-renderer"
MOCK_REVIEWER_ID = "mock-reviewer"
MOCK_OFFICER_ID = "mock-compliance-officer"
WORDS_PER_MINUTE = 160.0
SCENE_TAIL_S = 0.4  # breathing room after the last word of a scene
_ROLES = {
    VideoFormat.SHORT: (
        SceneRole.HOOK,
        SceneRole.SETUP,
        SceneRole.CONTENT,
        SceneRole.RELAUNCH,
        SceneRole.PAYOFF,
        SceneRole.LOOP,
    ),
    VideoFormat.LONG: (
        SceneRole.HOOK,
        SceneRole.SETUP,
        SceneRole.CONTENT,
        SceneRole.RELAUNCH,
        SceneRole.CONTENT,
        SceneRole.CONTENT,
        SceneRole.RELAUNCH,
        SceneRole.CONTENT,
        SceneRole.CONTENT,
        SceneRole.CONTENT,
        SceneRole.PAYOFF,
        SceneRole.CTA,
    ),
}
# skill scene-JSON role names (the wire format of the scene contract)
_SKILL_ROLE = {
    SceneRole.HOOK: "hook",
    SceneRole.SETUP: "cadre",
    SceneRole.RELAUNCH: "relance",
    SceneRole.CONTENT: "contenu",
    SceneRole.PAYOFF: "payoff",
    SceneRole.CTA: "cta",
    SceneRole.LOOP: "boucle",
}

# Invented placeholder narration, one bank per topic. A bank names the channels whose concept it matches
# (ADR-005: channel A reconstructs structures, channel B explains scales); any other channel id picks one by hash.
_TOPICS: tuple[dict[str, Any], ...] = (
    {
        "channels": ("channel-a",),
        "subject": "a stone aqueduct",
        "lines": (
            "A single channel of stone once carried water across a valley.",
            "Here is how a small crew could raise it.",
            "They began by measuring the slope with simple tools.",
            "Every arch was tested on a wooden frame first.",
            "Then the hardest part waited underground.",
            "Two teams dug a tunnel toward each other from opposite hills.",
            "Small errors were corrected at every new marker.",
            "The frames came down one arch at a time.",
            "Water finally entered the channel at the highest point.",
            "It ran downhill for days before reaching the town.",
            "The two tunnels had met with only a hand of difference.",
            "Now you know how the valley got its water.",
        ),
        "visuals": (
            "a long stone aqueduct crossing a green valley at dawn",
            "a crew of tiny figures marking a slope on a hillside",
            "wooden centering frames holding a half-built stone arch",
            "a cross-section of a hill with two tunnels heading toward each other",
            "a surveyor's marker stone in a dark tunnel lit by a small lamp",
            "the finished channel with water running along its top",
        ),
        "loop": "How did they get the water across?",
    },
    {
        "channels": ("channel-b",),
        "subject": "one billion years",
        "lines": (
            "Try to imagine one billion years, all in a single day.",
            "Start the clock at midnight and watch what happens.",
            "For hours nothing seems to change on the surface.",
            "Then the first slow signs of movement appear.",
            "But the most surprising part comes near the very end.",
            "The oceans rearrange themselves across the whole map.",
            "Mountains rise and wear down like sand castles.",
            "Ice advances, waits, and leaves again.",
            "Every hour hides more time than a human life.",
            "The last second holds all of recorded history.",
            "A billion years turns out to be mostly patience.",
            "Now you can feel how long a day of deep time lasts.",
        ),
        "visuals": (
            "a clock face drawn over slowly shifting continents seen from orbit",
            "a barren planet surface at first light with a thin haze",
            "coastlines drifting apart on a glowing globe",
            "a mountain range growing and wearing down in fast time-lapse",
            "a glacier front advancing over a wide plain",
            "a single bright pixel marking the last second on a long timeline",
        ),
        "loop": "What does a billion years look like?",
    },
)


def _topic(channel_id: str) -> dict[str, Any]:
    for topic in _TOPICS:
        if channel_id in topic["channels"]:
            return topic
    return _TOPICS[int(sha256_hex(channel_id)[:8], 16) % len(_TOPICS)]


def _slug(text: str) -> str:
    return "-".join("".join(c if c.isalnum() else " " for c in text.lower()).split())[:40] or "demo"


# ------------------------------------------------------------------ builders (agent id -> output)


def build_idea(brief: Mapping[str, Any]) -> dict[str, Any]:
    channel, fmt = brief["channel"], brief["format"]
    topic = _topic(channel["id"])
    return {
        "id": f"{channel['id']}-{fmt}-{_slug(topic['subject'])}"[:64],
        "channel_id": channel["id"],
        "series_id": None,
        "promise": f"You will see how {topic['subject']} works, step by step.",
        "mechanism": "one precise question answered by a procedural reconstruction",
        "evidence": [],  # measured outliers need the YouTube API key (NEEDS_HUMAN H0)
        "score": None,
    }


def build_package(brief: Mapping[str, Any]) -> dict[str, Any]:
    idea = brief["idea"]
    subject = _topic(idea["channel_id"])["subject"]
    thumbnails = [
        {"id": "A", "concept": f"{subject} at scale", "elements": [subject, "a tiny human figure"], "text": "HOW?"},
        {"id": "B", "concept": "before and after", "elements": ["empty ground", subject], "text": "BUILT"},
        {"id": "C", "concept": "cutaway", "elements": ["cross-section", subject], "text": ""},
    ]
    return {
        "idea_id": idea["id"],
        "format": brief["format"],
        "titles": [
            f"How {subject} was made"[:50],
            f"The truth about {subject}"[:50],
            f"{subject.capitalize()}, step by step"[:50],
        ],
        "thumbnails": thumbnails if brief["format"] == VideoFormat.LONG.value else [],
        "first_frame": f"{subject} filling the frame, one line of text on top",
    }


def scene_duration(text: str, words_per_minute: float = WORDS_PER_MINUTE) -> float:
    """Length of a scene: the narration at `words_per_minute`, plus a short tail, rounded up to a tenth of a
    second (a whole number of frames at 30 fps, so scene boundaries never drift)."""
    speech = len(text.split()) * 60.0 / words_per_minute
    return math.ceil((speech + SCENE_TAIL_S) * 10 - 1e-9) / 10


def build_script_doc(brief: Mapping[str, Any], roles: Sequence[SceneRole] | None = None) -> dict[str, Any]:
    """A scene document in the skill's JSON contract (v1.0), the input the production reads.

    `roles` replaces the format's usual scene sequence (tests use a short one to keep a full run quick)."""
    idea, package = brief["idea"], brief["package"]
    fmt = VideoFormat(brief["format"])
    topic = _topic(idea["channel_id"])
    roles = tuple(roles) if roles else _ROLES[fmt]
    lines, visuals = topic["lines"], topic["visuals"]
    frame = "vertical frame" if fmt is VideoFormat.SHORT else "wide frame"
    scenes: list[dict[str, Any]] = []
    start = 0.0
    opened = 0  # loops opened so far (Q1, Q2, …)
    open_loops: list[str] = []
    for i, role in enumerate(roles):
        text = lines[i % len(lines)]
        duration = scene_duration(text)
        opens: list[str] = []
        closes: list[str] = []
        if role in (SceneRole.HOOK, SceneRole.RELAUNCH):
            opened += 1
            opens = [f"Q{opened}"]
        elif role in (SceneRole.PAYOFF, SceneRole.LOOP):
            closes = list(open_loops)
        open_loops = [q for q in open_loops if q not in closes] + opens
        scenes.append(
            {
                "id": f"S{i + 1:02d}",
                "role": _SKILL_ROLE[role],
                "debut_s": round(start, 1),
                "duree_s": duration,
                "voix_off": text,
                "ton": "calm, curious",
                "avatar": "hors_champ",
                "visuel": f"Placeholder shot {i + 1}: {visuals[i % len(visuals)]}.",
                "prompt_visuel_en": f"{visuals[i % len(visuals)]}, procedural 3D render, no people in close-up, {frame}",
                "texte_ecran": "",
                "son": "soft ambient bed",
                "boucles": {"ouvre": opens, "ferme": closes},
                "note_traduction": "",
            }
        )
        start = round(start + duration, 1)
    return {
        "version": "1.0",
        "format": fmt.value,
        "langue": brief["language"],
        "debit_mots_min": WORDS_PER_MINUTE,
        "duree_totale_s": round(start, 1),
        "promesse": idea["promise"],
        "titres": package["titles"],
        "titre_en": package["titles"][0],
        "miniatures": [
            {"id": t["id"], "concept": t["concept"], "elements": t["elements"], "texte": t["text"]} for t in package["thumbnails"]
        ],
        "premiere_image": package["first_frame"],
        "video_suivante": "",
        "divulgation_ia": {
            "requise": True,
            "raison": "photorealistic procedural reconstruction that could be taken for real footage",
        },
        "controle": {"publiable": True, "raisons_blocage": [], "faits_a_verifier": [], "score_idee": None},
        "scenes": scenes,
    }


_BUILDERS: dict[str, Callable[[Mapping[str, Any], Sequence[SceneRole] | None], dict[str, Any]]] = {
    "strategist": lambda brief, roles: build_idea(brief),
    "packaging_director": lambda brief, roles: build_package(brief),
    "head_writer": build_script_doc,
}


class MockStudioLLM:
    """`LLMRunner` that answers each studio agent from a template, deterministically and at zero cost.

    The prompt of every call is the canonical JSON of the agent's brief (channel, format, upstream outputs).
    A real backend receives a prompt built from the agent's playbook; the pipeline code around the call
    (schema, validation of the answer, cost accounting) is the same."""

    def __init__(self, *, roles: Sequence[SceneRole] | None = None) -> None:
        self.roles = tuple(roles) if roles else None
        # the id says what the mock is configured to produce: it is part of every agent step's key
        fingerprint = "" if self.roles is None else "-" + sha256_hex("|".join(r.value for r in self.roles))[:8]
        self.spec: AdapterSpec = mock_spec(f"{MOCK_LLM_ID}{fingerprint}", AdapterKind.LLM)
        self.calls: list[dict[str, str]] = []

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
        builder = _BUILDERS.get(agent)
        if builder is None:
            raise LLMOutputInvalid(f"{self.spec.id}: no template for agent {agent!r}; known: {sorted(_BUILDERS)}")
        try:
            brief = json.loads(prompt)
        except json.JSONDecodeError as exc:
            raise LLMOutputInvalid(f"{self.spec.id}: the prompt is not a JSON brief: {exc}") from exc
        output = builder(brief, self.roles)
        if json_schema is not None:
            try:
                jsonschema.validate(output, json_schema)
            except jsonschema.ValidationError as exc:
                raise LLMOutputInvalid(f"{self.spec.id}: template output does not match the schema: {exc.message}") from exc
        key = sha256_hex(agent + prompt)
        self.calls.append({"agent": agent, "model": model, "key": key})
        # Scripted usage, about four characters per token: a stand-in that lets the ledger's token accounting run
        # (its entries carry `mock`); a real backend reports the figures of Claude Code's JSON output.
        usage = LLMUsage(
            input_tokens=len(prompt) // 4, output_tokens=len(json.dumps(output)) // 4, num_turns=1, model=self.spec.id
        )
        return LLMResult(
            output=output,
            usage=usage,
            session_id=f"{self.spec.id}-{key[:24]}",
            raw={"mock": True, "adapter": self.spec.id},
        )


# ------------------------------------------------------------------ generation policy and renderer


_TECHNIQUE_CYCLE = (ShotTechnique.BLENDER, ShotTechnique.IMAGE_25D, ShotTechnique.GEN_VIDEO, ShotTechnique.MOTION)


def choose_technique(scene: Scene, index: int) -> ShotTechnique:
    """Mock `generation_engineer` policy (MISSION §6.6): live motion only where the scene needs it. Here the
    choice cycles through the grammar so that every technique is exercised by the demo."""
    return _TECHNIQUE_CYCLE[index % len(_TECHNIQUE_CYCLE)]


class MockProceduralRenderer:
    """Stands in for the scripted Blender scenes and the motion-design renderer (phase 3): a flat clip whose
    colour comes from the brief and the seed, labelled with the brief."""

    def __init__(self) -> None:
        self.spec: AdapterSpec = mock_spec(MOCK_RENDERER_ID, AdapterKind.TEXT_TO_VIDEO)

    def render(self, brief: str, *, width: int, height: int, duration_s: float, fps: int, seed: int, out: Path) -> MediaResult:
        color = derive_color(derive_digest(MOCK_RENDERER_ID, brief=brief, seed=seed))
        ffmpeg.color_clip(out, width, height, fps, duration_s, color, label=brief)
        return MediaResult(
            path=out, media_type="video/mp4", gpu_seconds=0.0, metadata={"mock": True, "color": color, "seed": seed}
        )


# ------------------------------------------------------------------ reviewers


class MockReviewer:
    """Stands in for the human at G1 and G2 (and for the agent's own opinion): approves and says so."""

    id = MOCK_REVIEWER_ID

    def decide(self, gate: GateName, subject_key: str, now: dt.datetime) -> GateDecision:
        return GateDecision(
            gate=gate,
            subject_key=subject_key,
            agent_verdict=Verdict.APPROVE,
            human_verdict=Verdict.APPROVE,
            agent_reasons=(f"{MOCK_REVIEWER_ID}: dry run",),
            human_note=f"{MOCK_REVIEWER_ID}: no human looked at this (dry run)",
            decided_at=now,
            mock=True,
        )


class MockComplianceOfficer:
    """Applies deterministic checks to what it judges: the script, the QA report and the publication candidate.

    It is a mock because the real `compliance_officer` applies the 11-point gate, the platform rules and the
    AI Act (phase 2); the mock's job is to show that a verdict is computed from the artifacts, bound to the exact
    candidate (render, title, description, disclosure, channel, run), and that a failing check blocks publication.
    The verdict is the agent's half of the decision: the human's half comes from the reviewer, and only after the
    agent approved."""

    id = MOCK_OFFICER_ID

    def review(
        self,
        script: Script,
        qa_report: Mapping[str, Any],
        candidate: PublicationCandidate,
        candidate_key: str,
        now: dt.datetime,
    ) -> GateDecision:
        problems: list[str] = []
        publication = candidate.publication
        if not script.control.publishable:
            problems.append("the script's own control block says it is not publishable")
        if script.open_loops():
            problems.append(f"loops opened and never closed: {sorted(script.open_loops())}")
        if not script.disclosure.reason.strip():
            problems.append("no reason given for the AI disclosure decision")
        if publication.contains_synthetic_media != script.disclosure.required:
            problems.append("the candidate's synthetic-media flag disagrees with the script's disclosure decision")
        if publication.title not in script.titles:
            problems.append("the candidate's title is not one of the script's titles")
        if publication.render_key != qa_report.get("render", {}).get("video_key"):
            problems.append("the candidate names a render other than the one the QA report describes")
        defects = list(qa_report.get("defects", []))
        if defects:
            problems.append(f"technical QA defects: {defects}")
        verdict = Verdict.REJECT if problems else Verdict.APPROVE
        reasons = tuple(f"{MOCK_OFFICER_ID}: {p}" for p in problems) or (f"{MOCK_OFFICER_ID}: every mock check passed",)
        return GateDecision(
            gate=GateName.COMPLIANCE,
            subject_key=candidate_key,
            agent_verdict=verdict,
            agent_reasons=reasons,
            decided_at=now,
            mock=True,
        )
