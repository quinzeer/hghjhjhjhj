"""Closed vocabularies shared by every contract. Values are the wire format (English, snake_case)."""

from __future__ import annotations

from enum import StrEnum


class VideoFormat(StrEnum):
    LONG = "long"
    SHORT = "short"


class Platform(StrEnum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"


class SceneRole(StrEnum):
    """Roles of the scenariste-youtube scene JSON (v1.0), mapped to English identifiers."""

    HOOK = "hook"
    SETUP = "setup"  # skill: "cadre"
    RELAUNCH = "relaunch"  # skill: "relance"
    CONTENT = "content"  # skill: "contenu"
    PAYOFF = "payoff"
    CTA = "cta"
    LOOP = "loop"  # skill: "boucle"


class AvatarMode(StrEnum):
    OFF_SCREEN = "off_screen"  # skill: "hors_champ"
    FACING_CAMERA = "facing_camera"  # skill: "face_camera"
    CHARACTER_IN_SCENE = "character_in_scene"  # skill: "personnage_dans_scene"


class ShotTechnique(StrEnum):
    """Shot grammar (MISSION §6.6): GPU generation only where live motion is indispensable."""

    GEN_VIDEO = "gen_video"
    BLENDER = "blender"
    IMAGE_25D = "image_25d"
    MOTION = "motion"
    ARCHIVE = "archive"


class AdapterKind(StrEnum):
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_VIDEO = "image_to_video"
    TEXT_TO_VIDEO = "text_to_video"
    LIP_SYNC = "lip_sync"
    TTS = "tts"
    MUSIC = "music"
    SFX = "sfx"
    UPSCALE = "upscale"
    INTERPOLATE = "interpolate"
    TRANSCRIBE = "transcribe"
    LLM = "llm"
    VISION_CRITIC = "vision_critic"


class LicenseClass(StrEnum):
    """ADR-002 licence policy."""

    ACCEPTED = "accepted"
    CONDITIONAL = "conditional"
    REFUSED = "refused"
    CLOSED = "closed"


class AdapterStatus(StrEnum):
    MOCK = "mock"
    CANDIDATE = "candidate"
    RETAINED = "retained"
    REJECTED = "rejected"


class GateName(StrEnum):
    G1 = "g1"  # idea + packaging
    G2 = "g2"  # final viewing + fact and compliance reports
    G3 = "g3"  # Test & Compare in YouTube Studio
    COMPLIANCE = "compliance"  # compliance_officer verdict: never bypassable, never automated away


class Verdict(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    PENDING = "pending"


class CostKind(StrEnum):
    GPU_SECONDS = "gpu_seconds"
    KWH = "kwh"
    CLAUDE_INPUT_TOKENS = "claude_input_tokens"
    CLAUDE_OUTPUT_TOKENS = "claude_output_tokens"
    CLAUDE_CALLS = "claude_calls"
    CLAUDE_SECONDS = "claude_seconds"
    HUMAN_MINUTES = "human_minutes"
    EUR = "eur"


class ResourceClass(StrEnum):
    """Queue a job needs (ADR-001): one queue per GPU card is derived from GPU at dispatch time."""

    GPU = "gpu"
    CPU = "cpu"
    LLM = "llm"
    HUMAN = "human"


class Privacy(StrEnum):
    PRIVATE = "private"
    UNLISTED = "unlisted"
    PUBLIC = "public"
