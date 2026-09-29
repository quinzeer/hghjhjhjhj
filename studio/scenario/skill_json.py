"""Production input contract: the scene JSON of the `scenariste-youtube` skill (v1.0) <-> `Script` + `Package`.

Only the skill's field names appear here; its editorial rules stay private (knowledge/, phase 2).

Field mapping (skill -> contract):
  langue -> Script.language            debit_mots_min -> words_per_minute   promesse -> promise
  titres -> titles (Script, Package)    titre_en -> title_en                 video_suivante -> next_video
  premiere_image -> first_frame (Script, Package)
  divulgation_ia{requise, raison} -> disclosure{required, reason}
  controle{publiable, raisons_blocage, faits_a_verifier, score_idee}
      -> control{publishable, blocking_reasons, facts_to_verify, idea_score}
  miniatures[{id, concept, elements, texte}] -> Package.thumbnails[{id, concept, elements, text}]
  scenes[{id, role, debut_s, duree_s, voix_off, ton, avatar, visuel, prompt_visuel_en, texte_ecran, son,
          boucles{ouvre, ferme}, note_traduction}] -> Script.scenes

Lossless round trip: `to_skill_json(*from_skill_json(doc, idea_id)) == doc` for every valid document, and
both canonical JSON texts are equal too (an integer stays an integer, 4.0 stays 4.0). What the contracts
cannot hold is kept in `Script.extras`, under a closed set of keys:
  - `@root`: the top-level fields without a contract field (`version`, `duree_totale_s`, unknown fields), verbatim;
  - `divulgation_ia`, `controle`: their unknown sub-fields; `miniatures`, `scenes`: unknown sub-fields by item
    id (a scene's unknown `boucles` sub-fields under `boucles`);
  - `@layout`: `absent` lists the optional fields the document omitted, `float` the integral numbers it
    wrote as floats, as paths such as "scenes/S03/duree_s".
A document field never becomes a key of `extras` itself, so no field name is reserved (not even "@layout").
Object key order carries no meaning in JSON and is not kept, so reordering keys never changes a Script's
hash; `to_skill_json` writes the skill's field order, then unknown fields.

Input must be plain JSON data (objects with string keys, arrays, strings, finite numbers, booleans, null)
nested at most MAX_DEPTH arrays/objects deep. Required: version (1.x), format, langue, debit_mots_min,
promesse, titres, divulgation_ia{requise, raison}, controle{publiable}, scenes[{id, role, debut_s, duree_s}],
miniatures[{id, concept, elements}]; every other known field is optional and takes the contract default.
Types are checked strictly (no "150" for 150, no 1 for true). `duree_totale_s`, when present, must match both
the sum of scene durations and the end of the timeline within TIMELINE_TOLERANCE_S (a gap of exactly the
tolerance is accepted: gaps are compared at the microsecond).

`to_skill_json` refuses a Script/Package pair that disagrees (idea, format, titles, first frame) or holds
something v1.0 cannot carry (`Package.on_screen_text`, extras that clash with mapped fields or name missing
scenes or thumbnails), instead of dropping it. `duree_totale_s` is derived from the scenes: it is written
verbatim while it still matches them and recomputed (same number form) once a scene changed. Every document
it returns is read back by `from_skill_json`; one that would be refused is never returned.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from pydantic import ValidationError

from studio.core.interfaces import StudioError
from studio.domain import AvatarMode, Package, Scene, SceneRole, Script, VideoFormat
from studio.domain.models import TIMELINE_TOLERANCE_S

SUPPORTED_MAJOR: Final = "1"
DEFAULT_VERSION: Final = "1.0"
MAX_DEPTH: Final = 64
ROOT_KEY: Final = "@root"
LAYOUT_KEY: Final = "@layout"

ROLE_FROM_SKILL: Final[Mapping[str, SceneRole]] = {
    "hook": SceneRole.HOOK,
    "cadre": SceneRole.SETUP,
    "relance": SceneRole.RELAUNCH,
    "contenu": SceneRole.CONTENT,
    "payoff": SceneRole.PAYOFF,
    "cta": SceneRole.CTA,
    "boucle": SceneRole.LOOP,
}
ROLE_TO_SKILL: Final[Mapping[SceneRole, str]] = {v: k for k, v in ROLE_FROM_SKILL.items()}

AVATAR_FROM_SKILL: Final[Mapping[str, AvatarMode]] = {
    "hors_champ": AvatarMode.OFF_SCREEN,
    "face_camera": AvatarMode.FACING_CAMERA,
    "personnage_dans_scene": AvatarMode.CHARACTER_IN_SCENE,
}
AVATAR_TO_SKILL: Final[Mapping[AvatarMode, str]] = {v: k for k, v in AVATAR_FROM_SKILL.items()}

# Skill field order, used when writing a document back.
_TOP_ORDER: Final = (
    "version",
    "format",
    "langue",
    "debit_mots_min",
    "duree_totale_s",
    "promesse",
    "titres",
    "titre_en",
    "miniatures",
    "premiere_image",
    "video_suivante",
    "divulgation_ia",
    "controle",
    "scenes",
)
# Top-level fields held by the contracts (`version` and `duree_totale_s` are checked, then kept under `@root`).
_TOP_MAPPED: Final = frozenset(_TOP_ORDER) - {"version", "duree_totale_s"}
_EXTRAS_KEYS: Final = frozenset({ROOT_KEY, LAYOUT_KEY, "divulgation_ia", "controle", "miniatures", "scenes"})
_DISCLOSURE_FIELDS: Final = frozenset({"requise", "raison"})
_CONTROL_FIELDS: Final = frozenset({"publiable", "raisons_blocage", "faits_a_verifier", "score_idee"})
_THUMBNAIL_FIELDS: Final = frozenset({"id", "concept", "elements", "texte"})
_LOOP_FIELDS: Final = frozenset({"ouvre", "ferme"})
_SCENE_TEXTS: Final = (
    ("voix_off", "voice_over"),
    ("ton", "tone"),
    ("visuel", "visual"),
    ("prompt_visuel_en", "visual_prompt_en"),
    ("texte_ecran", "on_screen_text"),
    ("son", "sound"),
)
_SCENE_FIELDS: Final = frozenset(
    {"id", "role", "debut_s", "duree_s", "avatar", "boucles", "note_traduction"} | {k for k, _ in _SCENE_TEXTS}
)


class SkillJsonError(StudioError, ValueError):
    """Invalid v1.0 scene JSON, or a Script/Package pair that cannot be written back without loss."""


class _Missing:
    pass


_MISSING: Final = _Missing()


# ------------------------------------------------------------------ plain JSON data


def _check_json_value(value: Any, where: str, limit: int = MAX_DEPTH, depth: int = 0) -> None:
    """Accept only what json.loads returns, nested at most `limit` arrays/objects deep.

    Runs before anything copies or hashes the data, so a deep or cyclic value is refused here with its location
    instead of blowing the stack later. `depth` is the nesting level of `value` (0 for the outermost container).
    """
    if value is None or isinstance(value, str | bool | int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SkillJsonError(f"{where}: expected a finite number, got {value!r}")
        return
    if not isinstance(value, list | dict):
        raise SkillJsonError(f"{where}: {type(value).__name__} is not JSON data")
    if depth >= limit:
        raise SkillJsonError(f"{where}: nested deeper than {limit} arrays/objects")
    if isinstance(value, list):
        for i, item in enumerate(value):
            _check_json_value(item, f"{where}[{i}]", limit, depth + 1)
        return
    for key, item in value.items():
        if not isinstance(key, str):
            raise SkillJsonError(f"{where}: object keys must be strings, got {key!r}")
        _check_json_value(item, f"{where}.{key}", limit, depth + 1)


def _check_document(doc: Any) -> Mapping[str, Any]:
    if not isinstance(doc, Mapping):
        raise SkillJsonError(f"document: expected an object, got {type(doc).__name__}")
    for key, value in doc.items():
        if not isinstance(key, str):
            raise SkillJsonError(f"document: object keys must be strings, got {key!r}")
        _check_json_value(value, key, depth=1)
    return doc


def _beyond_tolerance(a: float, b: float) -> bool:
    # Rounded to the microsecond so that float noise never decides a gap of exactly the tolerance.
    return round(abs(a - b), 6) > TIMELINE_TOLERANCE_S


def _total_fault(total: float, scenes: Sequence[Scene]) -> str | None:
    """Why a declared total duration disagrees with the scenes, or None when it matches them."""
    summed = math.fsum(s.duration_s for s in scenes)
    end = scenes[-1].start_s + scenes[-1].duration_s
    for value, fact in ((summed, "the scenes last {:.3f} s in total"), (end, "the timeline ends at {:.3f} s")):
        if _beyond_tolerance(value, total):
            return f"{total} s but {fact.format(value)} (tolerance {TIMELINE_TOLERANCE_S} s)"
    return None


# ------------------------------------------------------------------ reading


class _Reader:
    """Strict type checks with located errors; records omitted optional fields and integral floats.

    It reads a document that `_check_document` accepted: plain JSON data, string keys, finite numbers.
    """

    def __init__(self) -> None:
        self.absent: list[str] = []
        self.floats: list[str] = []

    @staticmethod
    def obj(value: Any, where: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise SkillJsonError(f"{where}: expected an object, got {type(value).__name__}")
        return value

    @staticmethod
    def required(node: Mapping[str, Any], key: str, where: str) -> Any:
        if key not in node:
            raise SkillJsonError(f"{where}: missing required field {key!r}")
        return node[key]

    def optional(self, node: Mapping[str, Any], key: str, layout_path: str) -> Any:
        if key not in node:
            self.absent.append(layout_path)
            return _MISSING
        return node[key]

    @staticmethod
    def text(value: Any, where: str) -> str:
        if not isinstance(value, str):
            raise SkillJsonError(f"{where}: expected a string, got {type(value).__name__}")
        return value

    @staticmethod
    def boolean(value: Any, where: str) -> bool:
        if not isinstance(value, bool):
            raise SkillJsonError(f"{where}: expected true or false, got {type(value).__name__}")
        return value

    def number(self, value: Any, where: str, layout_path: str | None) -> float:
        """`layout_path` None: the value is kept verbatim elsewhere, its number form needs no record."""
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise SkillJsonError(f"{where}: expected a number, got {type(value).__name__}")
        if isinstance(value, float):
            if value.is_integer() and layout_path is not None:
                self.floats.append(layout_path)
            return value
        try:
            as_float = float(value)
        except OverflowError:
            as_float = math.inf
        if as_float != value:
            raise SkillJsonError(f"{where}: integer {value} cannot be represented exactly")
        return as_float

    def texts(self, value: Any, where: str) -> tuple[str, ...]:
        if not isinstance(value, list):
            raise SkillJsonError(f"{where}: expected an array of strings, got {type(value).__name__}")
        return tuple(self.text(item, f"{where}[{i}]") for i, item in enumerate(value))

    def opt_text(self, node: Mapping[str, Any], key: str, where: str, layout_path: str) -> str:
        value = self.optional(node, key, layout_path)
        return "" if value is _MISSING else self.text(value, f"{where}.{key}")

    def opt_texts(self, node: Mapping[str, Any], key: str, where: str, layout_path: str) -> tuple[str, ...]:
        value = self.optional(node, key, layout_path)
        return () if value is _MISSING else self.texts(value, f"{where}.{key}")


def _residual(node: Mapping[str, Any], known: Iterable[str]) -> dict[str, Any]:
    known_set = frozenset(known)
    return {k: copy.deepcopy(v) for k, v in node.items() if k not in known_set}


def _choices(names: Iterable[str]) -> str:
    return ", ".join(names)


def _read_thumbnails(r: _Reader, doc: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = r.optional(doc, "miniatures", "miniatures")
    if raw is _MISSING:
        return [], {}
    if not isinstance(raw, list):
        raise SkillJsonError(f"miniatures: expected an array, got {type(raw).__name__}")
    thumbnails: list[dict[str, Any]] = []
    residuals: dict[str, Any] = {}
    for i, item in enumerate(raw):
        where = f"miniatures[{i}]"
        node = r.obj(item, where)
        tid = r.text(r.required(node, "id", where), f"{where}.id")
        if any(t["id"] == tid for t in thumbnails):
            raise SkillJsonError(f"{where}: duplicate thumbnail id {tid!r}")
        thumbnails.append(
            {
                "id": tid,
                "concept": r.text(r.required(node, "concept", where), f"{where}.concept"),
                "elements": r.texts(r.required(node, "elements", where), f"{where}.elements"),
                "text": r.opt_text(node, "texte", where, f"miniatures/{tid}/texte"),
            }
        )
        extra = _residual(node, _THUMBNAIL_FIELDS)
        if extra:
            residuals[tid] = extra
    return thumbnails, residuals


def _read_scene(r: _Reader, item: Any, i: int) -> tuple[dict[str, Any], dict[str, Any]]:
    where = f"scenes[{i}]"
    node = r.obj(item, where)
    sid = r.text(r.required(node, "id", where), f"{where}.id")
    lp = f"scenes/{sid}"
    role_name = r.text(r.required(node, "role", where), f"{where}.role")
    if role_name not in ROLE_FROM_SKILL:
        raise SkillJsonError(f"{where} ({sid}): unknown role {role_name!r}; expected one of: {_choices(ROLE_FROM_SKILL)}")
    avatar = AvatarMode.OFF_SCREEN
    avatar_raw = r.optional(node, "avatar", f"{lp}/avatar")
    if avatar_raw is not _MISSING:
        avatar_name = r.text(avatar_raw, f"{where}.avatar")
        if avatar_name not in AVATAR_FROM_SKILL:
            raise SkillJsonError(
                f"{where} ({sid}): unknown avatar {avatar_name!r}; expected one of: {_choices(AVATAR_FROM_SKILL)}"
            )
        avatar = AVATAR_FROM_SKILL[avatar_name]
    scene: dict[str, Any] = {
        "id": sid,
        "role": ROLE_FROM_SKILL[role_name],
        "start_s": r.number(r.required(node, "debut_s", where), f"{where}.debut_s", f"{lp}/debut_s"),
        "duration_s": r.number(r.required(node, "duree_s", where), f"{where}.duree_s", f"{lp}/duree_s"),
        "avatar": avatar,
    }
    for skill_key, field in _SCENE_TEXTS:
        scene[field] = r.opt_text(node, skill_key, where, f"{lp}/{skill_key}")
    residual = _residual(node, _SCENE_FIELDS)
    loops_raw = r.optional(node, "boucles", f"{lp}/boucles")
    scene["loops"] = {"opens": (), "closes": ()}
    if loops_raw is not _MISSING:
        lwhere = f"{where}.boucles"
        loops = r.obj(loops_raw, lwhere)
        scene["loops"] = {
            "opens": r.opt_texts(loops, "ouvre", lwhere, f"{lp}/boucles/ouvre"),
            "closes": r.opt_texts(loops, "ferme", lwhere, f"{lp}/boucles/ferme"),
        }
        loop_extra = _residual(loops, _LOOP_FIELDS)
        if loop_extra:
            residual["boucles"] = loop_extra
    scene["translation_note"] = r.opt_text(node, "note_traduction", where, f"{lp}/note_traduction")
    return scene, residual


def _read_scenes(r: _Reader, doc: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = r.required(doc, "scenes", "document")
    if not isinstance(raw, list) or not raw:
        raise SkillJsonError("scenes: expected a non-empty array")
    scenes: list[dict[str, Any]] = []
    residuals: dict[str, Any] = {}
    for i, item in enumerate(raw):
        scene, residual = _read_scene(r, item, i)
        if any(s["id"] == scene["id"] for s in scenes):
            raise SkillJsonError(f"scenes[{i}]: duplicate scene id {scene['id']!r}")
        scenes.append(scene)
        if residual:
            residuals[scene["id"]] = residual
    return scenes, residuals


def _describe(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors(include_url=False):
        loc = ".".join(str(p) for p in err["loc"]) or "(model)"
        parts.append(f"{loc}: {err['msg']}")
    return f"{exc.title}: " + "; ".join(parts)


def from_skill_json(doc: Mapping[str, Any], idea_id: str) -> tuple[Script, Package]:
    """Map a v1.0 scene JSON onto the contracts. Raises SkillJsonError with the location of the first fault."""
    root = _check_document(doc)
    r = _Reader()

    def req(key: str) -> Any:
        return r.required(root, key, "document")

    version = r.text(req("version"), "version")
    if version.split(".")[0] != SUPPORTED_MAJOR:
        raise SkillJsonError(f"version: unsupported scene JSON version {version!r} (supported: {SUPPORTED_MAJOR}.x)")
    format_name = r.text(req("format"), "format")
    try:
        video_format = VideoFormat(format_name)
    except ValueError:
        choices = _choices(f.value for f in VideoFormat)
        raise SkillJsonError(f"format: unknown format {format_name!r}; expected one of: {choices}") from None
    language = r.text(req("langue"), "langue")
    words_per_minute = r.number(req("debit_mots_min"), "debit_mots_min", "debit_mots_min")
    promise = r.text(req("promesse"), "promesse")
    titles = r.texts(req("titres"), "titres")
    title_en = r.opt_text(root, "titre_en", "document", "titre_en")
    thumbnails, thumbnail_extras = _read_thumbnails(r, root)
    first_frame = r.opt_text(root, "premiere_image", "document", "premiere_image")
    next_video = r.opt_text(root, "video_suivante", "document", "video_suivante")

    disclosure_node = r.obj(req("divulgation_ia"), "divulgation_ia")
    disclosure = {
        "required": r.boolean(r.required(disclosure_node, "requise", "divulgation_ia"), "divulgation_ia.requise"),
        "reason": r.text(r.required(disclosure_node, "raison", "divulgation_ia"), "divulgation_ia.raison"),
    }

    control_node = r.obj(req("controle"), "controle")
    publishable = r.boolean(r.required(control_node, "publiable", "controle"), "controle.publiable")
    blocking = r.opt_texts(control_node, "raisons_blocage", "controle", "controle/raisons_blocage")
    facts = r.opt_texts(control_node, "faits_a_verifier", "controle", "controle/faits_a_verifier")
    score_raw = r.optional(control_node, "score_idee", "controle/score_idee")
    score = (
        None if score_raw is _MISSING or score_raw is None else r.number(score_raw, "controle.score_idee", "controle/score_idee")
    )
    control = {"publishable": publishable, "blocking_reasons": blocking, "facts_to_verify": facts, "idea_score": score}

    scenes, scene_extras = _read_scenes(r, root)
    total = None if "duree_totale_s" not in root else r.number(root["duree_totale_s"], "duree_totale_s", None)

    # Every field has been read: the residuals and the layout are complete.
    residuals = {
        ROOT_KEY: _residual(root, _TOP_MAPPED),
        "divulgation_ia": _residual(disclosure_node, _DISCLOSURE_FIELDS),
        "controle": _residual(control_node, _CONTROL_FIELDS),
        "miniatures": thumbnail_extras,
        "scenes": scene_extras,
    }
    extras: dict[str, Any] = {k: v for k, v in residuals.items() if v}
    layout = {k: list(v) for k, v in (("absent", r.absent), ("float", r.floats)) if v}
    if layout:
        extras[LAYOUT_KEY] = layout

    script_data = {
        "idea_id": idea_id,
        "format": video_format,
        "language": language,
        "words_per_minute": words_per_minute,
        "promise": promise,
        "titles": titles,
        "title_en": title_en,
        "next_video": next_video,
        "first_frame": first_frame,
        "disclosure": disclosure,
        "control": control,
        "scenes": scenes,
        "extras": extras,
    }
    package_data = {
        "idea_id": idea_id,
        "format": video_format,
        "titles": titles,
        "thumbnails": thumbnails,
        "first_frame": first_frame,
    }
    try:
        script, package = Script.model_validate(script_data), Package.model_validate(package_data)
    except ValidationError as exc:
        raise SkillJsonError(f"document breaks a contract invariant: {_describe(exc)}") from exc
    # Checked on the validated timeline, so a broken timeline is reported as such first.
    fault = None if total is None else _total_fault(total, script.scenes)
    if fault is not None:
        raise SkillJsonError(f"duree_totale_s: {fault}")
    return script, package


# ------------------------------------------------------------------ writing


class _Writer:
    def __init__(self, layout: Any) -> None:
        if layout is None:
            layout = {}
        if not isinstance(layout, Mapping) or not set(layout) <= {"absent", "float"}:
            raise SkillJsonError(f"Script.extras[{LAYOUT_KEY!r}]: expected an object with 'absent' and 'float' lists")
        absent, floats = layout.get("absent", []), layout.get("float", [])
        if not all(isinstance(x, list) and all(isinstance(p, str) for p in x) for x in (absent, floats)):
            raise SkillJsonError(f"Script.extras[{LAYOUT_KEY!r}]: 'absent' and 'float' must be lists of paths")
        self.absent = frozenset(absent)
        self.floats = frozenset(floats)

    def number(self, value: float, path: str) -> int | float:
        if path in self.floats:
            return value
        return int(value) if value.is_integer() else value

    def put(self, target: dict[str, Any], key: str, value: Any, default: Any, path: str) -> None:
        """Write an optional field, unless the source omitted it and it still holds its default."""
        if path in self.absent and value == default:
            return
        target[key] = value


def _merge(target: dict[str, Any], residual: Any, where: str) -> dict[str, Any]:
    if not isinstance(residual, Mapping):
        raise SkillJsonError(f"Script.extras{where}: expected an object of unknown fields")
    clash = sorted(set(target) & set(residual))
    if clash:
        raise SkillJsonError(f"Script.extras{where}: {clash} would overwrite mapped fields")
    target.update(residual)
    return target


def _by_id(extras: dict[str, Any], name: str) -> dict[str, Any]:
    value = extras.pop(name, {})
    if not isinstance(value, dict) or not all(isinstance(v, Mapping) for v in value.values()):
        raise SkillJsonError(f"Script.extras[{name!r}]: expected an object mapping ids to unknown fields")
    return value


def _check_pair(script: Script, package: Package) -> None:
    mismatches = [
        name
        for name, a, b in (
            ("idea_id", script.idea_id, package.idea_id),
            ("format", script.format, package.format),
            ("titles", script.titles, package.titles),
            ("first_frame", script.first_frame, package.first_frame),
        )
        if a != b
    ]
    if mismatches:
        raise SkillJsonError(f"script and package disagree on {', '.join(mismatches)}")
    if package.on_screen_text:
        raise SkillJsonError("package.on_screen_text has no field in scene JSON v1.0 and would be lost")


def _write_scenes(w: _Writer, script: Script, residuals: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for scene in script.scenes:
        lp = f"scenes/{scene.id}"
        residual = dict(residuals.pop(scene.id, {}))
        loop_residual = residual.pop("boucles", {})
        item: dict[str, Any] = {
            "id": scene.id,
            "role": ROLE_TO_SKILL[scene.role],
            "debut_s": w.number(scene.start_s, f"{lp}/debut_s"),
            "duree_s": w.number(scene.duration_s, f"{lp}/duree_s"),
        }
        for skill_key, field in _SCENE_TEXTS[:2]:
            w.put(item, skill_key, getattr(scene, field), "", f"{lp}/{skill_key}")
        w.put(item, "avatar", AVATAR_TO_SKILL[scene.avatar], AVATAR_TO_SKILL[AvatarMode.OFF_SCREEN], f"{lp}/avatar")
        for skill_key, field in _SCENE_TEXTS[2:]:
            w.put(item, skill_key, getattr(scene, field), "", f"{lp}/{skill_key}")
        loops: dict[str, Any] = {}
        w.put(loops, "ouvre", list(scene.loops.opens), [], f"{lp}/boucles/ouvre")
        w.put(loops, "ferme", list(scene.loops.closes), [], f"{lp}/boucles/ferme")
        _merge(loops, loop_residual, f"['scenes'][{scene.id!r}]['boucles']")
        no_loops = not (scene.loops.opens or scene.loops.closes or loop_residual)
        if not (f"{lp}/boucles" in w.absent and no_loops):
            item["boucles"] = loops
        w.put(item, "note_traduction", scene.translation_note, "", f"{lp}/note_traduction")
        out.append(_merge(item, residual, f"['scenes'][{scene.id!r}]"))
    return out


def _refresh_total(root: dict[str, Any], scenes: Sequence[Scene]) -> None:
    """Recompute a kept `duree_totale_s` that no longer matches the scenes, keeping its number form."""
    total = root.get("duree_totale_s")
    if isinstance(total, bool) or not isinstance(total, int | float):
        return  # absent, or not a number: the read-back check reports the latter
    try:
        as_float = float(total)  # finite: extras went through _check_json_value
    except OverflowError:
        return  # an integer no float can hold: the read-back check reports it
    if as_float != total or _total_fault(as_float, scenes) is None:
        return
    fresh = round(math.fsum(s.duration_s for s in scenes), 3)
    root["duree_totale_s"] = int(fresh) if isinstance(total, int) and fresh.is_integer() else fresh


def to_skill_json(script: Script, package: Package) -> dict[str, Any]:
    """Write the pair back as a v1.0 scene JSON. Refuses any content the format could not carry."""
    _check_pair(script, package)
    # `@root` wraps the top-level fields: extras nest one level deeper than the document they describe.
    _check_json_value(script.extras, "Script.extras", limit=MAX_DEPTH + 1)
    extras = copy.deepcopy(script.extras)
    unexpected = sorted(set(extras) - _EXTRAS_KEYS)
    if unexpected:
        raise SkillJsonError(f"Script.extras: unexpected keys {unexpected}; expected some of {sorted(_EXTRAS_KEYS)}")
    w = _Writer(extras.get(LAYOUT_KEY))
    root = _merge({}, extras.get(ROOT_KEY, {}), f"[{ROOT_KEY!r}]")
    clash = sorted(set(root) & _TOP_MAPPED)
    if clash:
        raise SkillJsonError(f"Script.extras[{ROOT_KEY!r}]: {clash} would overwrite mapped fields")
    root.setdefault("version", DEFAULT_VERSION)
    _refresh_total(root, script.scenes)
    thumbnail_extras = _by_id(extras, "miniatures")
    scene_extras = _by_id(extras, "scenes")

    mapped: dict[str, Any] = {
        "format": script.format.value,
        "langue": script.language,
        "debit_mots_min": w.number(script.words_per_minute, "debit_mots_min"),
        "promesse": script.promise,
        "titres": list(script.titles),
    }
    w.put(mapped, "titre_en", script.title_en, "", "titre_en")
    thumbnails = []
    for t in package.thumbnails:
        item: dict[str, Any] = {"id": t.id, "concept": t.concept, "elements": list(t.elements)}
        w.put(item, "texte", t.text, "", f"miniatures/{t.id}/texte")
        thumbnails.append(_merge(item, thumbnail_extras.pop(t.id, {}), f"['miniatures'][{t.id!r}]"))
    w.put(mapped, "miniatures", thumbnails, [], "miniatures")
    w.put(mapped, "premiere_image", script.first_frame, "", "premiere_image")
    w.put(mapped, "video_suivante", script.next_video, "", "video_suivante")
    mapped["divulgation_ia"] = _merge(
        {"requise": script.disclosure.required, "raison": script.disclosure.reason},
        extras.get("divulgation_ia", {}),
        "['divulgation_ia']",
    )
    control: dict[str, Any] = {"publiable": script.control.publishable}
    w.put(control, "raisons_blocage", list(script.control.blocking_reasons), [], "controle/raisons_blocage")
    w.put(control, "faits_a_verifier", list(script.control.facts_to_verify), [], "controle/faits_a_verifier")
    score = script.control.idea_score
    w.put(control, "score_idee", None if score is None else w.number(score, "controle/score_idee"), None, "controle/score_idee")
    mapped["controle"] = _merge(control, extras.get("controle", {}), "['controle']")
    mapped["scenes"] = _write_scenes(w, script, scene_extras)

    orphans = [f"miniatures/{k}" for k in thumbnail_extras] + [f"scenes/{k}" for k in scene_extras]
    if orphans:
        raise SkillJsonError(f"Script.extras holds unknown fields of missing items: {orphans}")

    out: dict[str, Any] = {}
    for key in _TOP_ORDER:
        if key in mapped:
            out[key] = mapped[key]
        elif key in root:
            out[key] = root.pop(key)
    out.update(root)
    try:
        from_skill_json(out, script.idea_id)
    except SkillJsonError as exc:
        raise SkillJsonError(f"the written document would be refused on reading: {exc}") from exc
    return out
