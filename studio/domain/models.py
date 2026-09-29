"""Domain contracts (MISSION §9 phase 1): Channel, Series, Idea, Package, Script, Scene, Shot, Asset,
Render, Publication, Metric, Experiment, CostEntry, plus GateDecision and RunManifest.

Rules that belong to the private playbooks (word budgets, scene length limits, title length…) are NOT
encoded here: they live in knowledge/ and are checked by the editorial controls (phase 2). These models
only enforce structural invariants that hold for every channel.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from studio.domain.base import StudioModel
from studio.domain.enums import (
    AvatarMode,
    CostKind,
    GateName,
    Platform,
    Privacy,
    SceneRole,
    ShotTechnique,
    Verdict,
    VideoFormat,
)

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Slug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")]
LanguageTag = Annotated[str, Field(pattern=r"^[a-z]{2}(-[A-Z]{2})?$")]
TIMELINE_TOLERANCE_S = 0.05


# ------------------------------------------------------------------ channel


class Channel(StudioModel):
    id: Slug
    name: str = Field(min_length=1)
    language: LanguageTag
    concept: str = Field(min_length=1)
    formats: tuple[VideoFormat, ...] = (VideoFormat.LONG, VideoFormat.SHORT)
    voice_id: str = Field(min_length=1)
    visual_bible: str = Field(min_length=1, description="path or id of the channel's visual bible")
    watchlist: tuple[str, ...] = Field(default=(), description="competitor channels (@handle or UC… id) for scout")
    platforms: tuple[Platform, ...] = (Platform.YOUTUBE,)


class Series(StudioModel):
    id: Slug
    channel_id: Slug
    title: str = Field(min_length=1)
    premise: str = Field(min_length=1)
    season: int = Field(default=1, ge=1)


# ------------------------------------------------------------------ idea and packaging


class OutlierEvidence(StudioModel):
    """One measured outlier backing an idea (ADR-004: measured through the official API only)."""

    video_id: str = Field(pattern=r"^[\w-]{6,20}$")
    ratio: float = Field(gt=0)
    baseline_n: int = Field(ge=1)
    measured_at: dt.datetime
    method: str = Field(min_length=1)


class IdeaScore(StudioModel):
    """Score on the channel's grid. Criteria and weights come from knowledge/ (private), not from code."""

    criteria: dict[str, float] = Field(description="criterion id -> points awarded")
    total: float = Field(ge=0, le=100)
    eliminatory_failed: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _total_matches(self) -> IdeaScore:
        if self.criteria and abs(sum(self.criteria.values()) - self.total) > 0.01:
            raise ValueError("total must equal the sum of criteria points")
        return self


class Idea(StudioModel):
    id: Slug
    channel_id: Slug
    series_id: Slug | None = None
    promise: str = Field(min_length=1)
    mechanism: str = Field(min_length=1, description="proven format mechanism transferred to a new subject")
    evidence: tuple[OutlierEvidence, ...] = ()
    score: IdeaScore | None = None


class ThumbnailConcept(StudioModel):
    id: str = Field(pattern=r"^[A-Z]$")
    concept: str = Field(min_length=1)
    elements: tuple[str, ...] = Field(min_length=1)
    text: str = ""


class Package(StudioModel):
    idea_id: Slug
    format: VideoFormat
    titles: tuple[str, ...] = Field(min_length=1)
    thumbnails: tuple[ThumbnailConcept, ...] = ()
    first_frame: str = ""
    on_screen_text: str = ""

    @field_validator("thumbnails")
    @classmethod
    def _unique_ids(cls, v: tuple[ThumbnailConcept, ...]) -> tuple[ThumbnailConcept, ...]:
        ids = [t.id for t in v]
        if len(ids) != len(set(ids)):
            raise ValueError("thumbnail ids must be unique")
        return v

    @model_validator(mode="after")
    def _long_needs_thumbnail(self) -> Package:
        if self.format is VideoFormat.LONG and not self.thumbnails:
            raise ValueError("a long-form package needs at least one thumbnail concept")
        if self.format is VideoFormat.SHORT and not self.first_frame:
            raise ValueError("a Short package needs its first frame (it plays the thumbnail's role)")
        return self


# ------------------------------------------------------------------ script


class SceneLoops(StudioModel):
    opens: tuple[str, ...] = ()
    closes: tuple[str, ...] = ()


class Scene(StudioModel):
    id: str = Field(pattern=r"^S\d{2,3}$")
    role: SceneRole
    start_s: float = Field(ge=0)
    duration_s: float = Field(gt=0)
    voice_over: str = ""
    tone: str = ""
    avatar: AvatarMode = AvatarMode.OFF_SCREEN
    visual: str = ""
    visual_prompt_en: str = ""
    on_screen_text: str = ""
    sound: str = ""
    loops: SceneLoops = SceneLoops()
    translation_note: str = ""


class AIDisclosure(StudioModel):
    required: bool
    reason: str = Field(min_length=1)


class ControlBlock(StudioModel):
    publishable: bool
    blocking_reasons: tuple[str, ...] = ()
    facts_to_verify: tuple[str, ...] = ()
    idea_score: float | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def _blocked_needs_reason(self) -> ControlBlock:
        if not self.publishable and not self.blocking_reasons:
            raise ValueError("a non-publishable script must state why")
        if self.publishable and self.blocking_reasons:
            raise ValueError("a publishable script cannot carry blocking reasons")
        return self


class Script(StudioModel):
    idea_id: Slug
    format: VideoFormat
    language: LanguageTag
    words_per_minute: float = Field(gt=0)
    promise: str = Field(min_length=1)
    titles: tuple[str, ...] = Field(min_length=1)
    title_en: str = ""
    next_video: str = ""
    first_frame: str = ""
    disclosure: AIDisclosure
    control: ControlBlock
    scenes: tuple[Scene, ...] = Field(min_length=1)
    extras: dict[str, object] = Field(default_factory=dict, description="source fields kept verbatim for lossless mapping")

    @model_validator(mode="after")
    def _timeline(self) -> Script:
        ids = [s.id for s in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError("scene ids must be unique")
        t = 0.0
        for s in self.scenes:
            if round(abs(s.start_s - t), 6) > TIMELINE_TOLERANCE_S:  # rounded: 1.05 - 1.0 is 0.05000000000000004
                raise ValueError(f"scene {s.id} starts at {s.start_s}s, expected {t:.2f}s (contiguous timeline)")
            t = s.start_s + s.duration_s
        return self

    @property
    def duration_s(self) -> float:
        last = self.scenes[-1]
        return round(last.start_s + last.duration_s, 3)

    def open_loops(self) -> set[str]:
        """Loops opened and never closed (the editorial control rejects a script with any)."""
        opened: set[str] = set()
        for s in self.scenes:
            opened |= set(s.loops.opens)
            opened -= set(s.loops.closes)
        return opened


# ------------------------------------------------------------------ production


class Shot(StudioModel):
    id: str = Field(pattern=r"^S\d{2,3}-\d{2}$")
    scene_id: str = Field(pattern=r"^S\d{2,3}$")
    technique: ShotTechnique
    prompt: str = ""
    duration_s: float = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: int = Field(gt=0, le=120)
    seed: int = Field(ge=0)
    draft: bool = True
    model_id: str = Field(min_length=1)


class Asset(StudioModel):
    key: Sha256
    kind: str = Field(pattern=r"^(image|video|audio|subtitle|json|text)$")
    media_type: str = Field(min_length=3)
    size_bytes: int = Field(ge=0)
    producer_step: str = Field(min_length=1)


class Render(StudioModel):
    format: VideoFormat
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: float = Field(gt=0)
    duration_s: float = Field(gt=0)
    video_key: Sha256
    has_audio: bool
    integrated_lufs: float | None = None
    true_peak_dbtp: float | None = None


class Publication(StudioModel):
    platform: Platform
    render_key: Sha256
    title: str = Field(min_length=1)
    description: str = ""
    privacy: Privacy = Privacy.PRIVATE
    publish_at: dt.datetime | None = None
    contains_synthetic_media: bool
    is_aigc: bool | None = Field(default=None, description="TikTok AIGC flag; None on YouTube")
    localizations: dict[str, dict[str, str]] = Field(default_factory=dict)
    external_id: str | None = None


class Metric(StudioModel):
    publication_external_id: str = Field(min_length=1)
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    value: float
    window: str = Field(pattern=r"^(48h|7d|28d|lifetime)$")
    measured_at: dt.datetime
    source: str = Field(min_length=1)


class Experiment(StudioModel):
    id: Slug
    hypothesis: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    variants: tuple[str, ...] = Field(min_length=2)
    min_sample: int = Field(ge=1)
    preregistered_at: dt.datetime
    status: str = Field(default="planned", pattern=r"^(planned|running|stopped|analysed)$")


class CostEntry(StudioModel):
    run_id: str = Field(min_length=1)
    step_key: Sha256
    kind: CostKind
    quantity: float = Field(ge=0)
    estimated: bool = False
    at: dt.datetime


# ------------------------------------------------------------------ gates and manifest


class GateDecision(StudioModel):
    """A gate validates one exact artifact (ADR-001 decision 8): a new hash needs a new decision."""

    gate: GateName
    subject_key: Sha256
    agent_verdict: Verdict
    human_verdict: Verdict = Verdict.PENDING
    agent_reasons: tuple[str, ...] = ()
    human_note: str = ""
    decided_at: dt.datetime | None = None

    @property
    def approved(self) -> bool:
        if self.gate is GateName.COMPLIANCE:
            # the compliance verdict is the agent's, and a human cannot override a block (MISSION §7, §11)
            return self.agent_verdict is Verdict.APPROVE and self.human_verdict is not Verdict.REJECT
        return self.agent_verdict is not Verdict.REJECT and self.human_verdict is Verdict.APPROVE


class RunManifest(StudioModel):
    run_id: str = Field(min_length=1)
    channel_id: Slug
    format: VideoFormat
    dry_run: bool
    locked: dict[str, Sha256] = Field(default_factory=dict, description="step name -> locked output key")
    step_keys: dict[str, Sha256] = Field(default_factory=dict, description="step name -> step key")
    costs: tuple[CostEntry, ...] = ()
    versions: dict[str, str] = Field(default_factory=dict)
    mock: bool = Field(description="True when any adapter used is a mock (MISSION §3.2)")
