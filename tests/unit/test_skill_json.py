"""Scene JSON of the scenariste-youtube skill (v1.0) <-> Script + Package: lossless round trip, strict input."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest

from studio.core.interfaces import StudioError
from studio.domain import AvatarMode, Package, SceneLoops, SceneRole, Script, VideoFormat, canonical_json
from studio.scenario.skill_json import (
    AVATAR_FROM_SKILL,
    LAYOUT_KEY,
    MAX_DEPTH,
    ROLE_FROM_SKILL,
    ROOT_KEY,
    SkillJsonError,
    from_skill_json,
    to_skill_json,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
LONG = FIXTURES / "skill_scenes_long.json"
SHORT = FIXTURES / "skill_scenes_short.json"

Doc = dict[str, Any]


def load(path: Path) -> Doc:
    doc: Doc = json.loads(path.read_text(encoding="utf-8"))
    return doc


def round_trip(doc: Doc) -> Doc:
    return to_skill_json(*from_skill_json(doc, "idea-1"))


def assert_lossless(doc: Doc) -> None:
    out = round_trip(doc)
    assert out == doc
    # stronger than ==: 0 == 0.0 and True == 1 in Python, not in the canonical text that feeds the hashes
    assert canonical_json(out) == canonical_json(doc)


def edited(path: Path, edit: Callable[[Doc], object]) -> Doc:
    doc = load(path)
    edit(doc)
    return doc


def nested(levels: int) -> Any:
    """`levels` arrays nested in one another: nested(1) == [], nested(2) == [[]]."""
    value: Any = []
    for _ in range(levels - 1):
        value = [value]
    return value


def retimed(script: Script, index: int, duration: float) -> Script:
    """The script with one scene re-timed (as after voice synthesis) and the later scenes shifted to follow it."""
    data = script.model_dump()
    scenes = data["scenes"]
    delta = duration - scenes[index]["duration_s"]
    scenes[index]["duration_s"] = duration
    for later in scenes[index + 1 :]:
        later["start_s"] = round(later["start_s"] + delta, 3)
    return Script.model_validate(data)


def assert_reads_back(out: Doc, script: Script, package: Package) -> None:
    """What to_skill_json wrote is accepted by from_skill_json and describes the same script and package."""
    again, again_package = from_skill_json(out, script.idea_id)
    assert again.model_dump(exclude={"extras"}) == script.model_dump(exclude={"extras"})
    assert again_package == package


# ------------------------------------------------------------------ fixtures


@pytest.mark.parametrize("path", [LONG, SHORT], ids=["long", "short"])
def test_fixture_round_trip_is_lossless_down_to_the_file_text(path: Path) -> None:
    doc = load(path)
    assert_lossless(doc)
    # same key order, same number forms (0 vs 8.0), same characters: the file is reproduced byte for byte
    text = json.dumps(round_trip(doc), indent=2, ensure_ascii=False) + "\n"
    assert text == path.read_text(encoding="utf-8")


def test_long_fixture_maps_every_field() -> None:
    doc = load(LONG)
    script, package = from_skill_json(doc, "lighthouse-lens")

    assert script.idea_id == package.idea_id == "lighthouse-lens"
    assert script.format is package.format is VideoFormat.LONG
    assert script.language == "fr"
    assert script.words_per_minute == 150.0
    assert script.promise == doc["promesse"]
    assert script.titles == package.titles == tuple(doc["titres"])
    assert script.title_en == doc["titre_en"]
    assert script.next_video == doc["video_suivante"]
    assert script.first_frame == package.first_frame == doc["premiere_image"]
    assert script.disclosure.required is True
    assert script.disclosure.reason == doc["divulgation_ia"]["raison"]
    assert script.control.publishable is True
    assert script.control.blocking_reasons == ()
    assert script.control.facts_to_verify == tuple(doc["controle"]["faits_a_verifier"])
    assert script.control.idea_score == 74.0

    assert [t.id for t in package.thumbnails] == ["A", "B", "C"]
    for thumb, raw in zip(package.thumbnails, doc["miniatures"], strict=True):
        assert (thumb.concept, thumb.elements, thumb.text) == (raw["concept"], tuple(raw["elements"]), raw["texte"])

    assert len(script.scenes) >= 6
    assert [s.id for s in script.scenes] == [s["id"] for s in doc["scenes"]]
    assert [s.role for s in script.scenes] == [
        SceneRole.HOOK,
        SceneRole.SETUP,
        SceneRole.CONTENT,
        SceneRole.RELAUNCH,
        SceneRole.CONTENT,
        SceneRole.CONTENT,
        SceneRole.PAYOFF,
        SceneRole.CTA,
    ]
    assert {s.avatar for s in script.scenes} == set(AvatarMode)
    assert script.scenes[1].avatar is AvatarMode.FACING_CAMERA
    assert script.scenes[4].avatar is AvatarMode.CHARACTER_IN_SCENE
    for scene, raw in zip(script.scenes, doc["scenes"], strict=True):
        assert scene.start_s == raw["debut_s"]
        assert scene.duration_s == raw["duree_s"]
        assert scene.voice_over == raw["voix_off"]
        assert scene.tone == raw["ton"]
        assert scene.visual == raw["visuel"]
        assert scene.visual_prompt_en == raw["prompt_visuel_en"]
        assert scene.on_screen_text == raw["texte_ecran"]
        assert scene.sound == raw["son"]
        assert scene.loops.opens == tuple(raw["boucles"]["ouvre"])
        assert scene.loops.closes == tuple(raw["boucles"]["ferme"])
        assert scene.translation_note == raw["note_traduction"]
    assert script.open_loops() == set()
    assert script.duration_s == doc["duree_totale_s"]
    assert script.extras == {
        ROOT_KEY: {"version": "1.0", "duree_totale_s": 66.8},
        LAYOUT_KEY: {"float": ["scenes/S03/duree_s", "scenes/S08/debut_s"]},
    }


def test_short_fixture_carries_its_first_frame() -> None:
    doc = load(SHORT)
    script, package = from_skill_json(doc, "ancient-honey")
    assert script.format is package.format is VideoFormat.SHORT
    assert package.first_frame == script.first_frame == doc["premiere_image"] != ""
    assert package.thumbnails == ()
    assert script.scenes[-1].role is SceneRole.LOOP
    assert script.control.idea_score == 68.5
    assert script.duration_s == doc["duree_totale_s"]


# ------------------------------------------------------------------ vocabularies

ROLES = [
    ("hook", SceneRole.HOOK),
    ("cadre", SceneRole.SETUP),
    ("relance", SceneRole.RELAUNCH),
    ("contenu", SceneRole.CONTENT),
    ("payoff", SceneRole.PAYOFF),
    ("cta", SceneRole.CTA),
    ("boucle", SceneRole.LOOP),
]
AVATARS = [
    ("hors_champ", AvatarMode.OFF_SCREEN),
    ("face_camera", AvatarMode.FACING_CAMERA),
    ("personnage_dans_scene", AvatarMode.CHARACTER_IN_SCENE),
]


def test_vocabularies_cover_every_enum_member_once() -> None:
    assert dict(ROLE_FROM_SKILL) == dict(ROLES)
    assert dict(AVATAR_FROM_SKILL) == dict(AVATARS)
    assert set(ROLE_FROM_SKILL.values()) == set(SceneRole)
    assert set(AVATAR_FROM_SKILL.values()) == set(AvatarMode)


@pytest.mark.parametrize(("name", "role"), ROLES)
def test_each_role_maps_and_round_trips(name: str, role: SceneRole) -> None:
    doc = edited(LONG, lambda d: d["scenes"][2].__setitem__("role", name))
    script, _ = from_skill_json(doc, "idea-1")
    assert script.scenes[2].role is role
    assert_lossless(doc)


@pytest.mark.parametrize(("name", "avatar"), AVATARS)
def test_each_avatar_maps_and_round_trips(name: str, avatar: AvatarMode) -> None:
    doc = edited(LONG, lambda d: d["scenes"][2].__setitem__("avatar", name))
    script, _ = from_skill_json(doc, "idea-1")
    assert script.scenes[2].avatar is avatar
    assert_lossless(doc)


@pytest.mark.parametrize("value", ["intro", "setup", "Hook", ""])
def test_unknown_role_is_rejected(value: str) -> None:
    doc = edited(LONG, lambda d: d["scenes"][2].__setitem__("role", value))
    with pytest.raises(SkillJsonError, match=r"scenes\[2\] \(S03\): unknown role") as exc:
        from_skill_json(doc, "idea-1")
    assert repr(value) in str(exc.value)
    assert "cadre" in str(exc.value)  # the message lists the accepted values


@pytest.mark.parametrize("value", ["off_screen", "plein_ecran"])
def test_unknown_avatar_is_rejected(value: str) -> None:
    doc = edited(LONG, lambda d: d["scenes"][5].__setitem__("avatar", value))
    with pytest.raises(SkillJsonError, match=r"scenes\[5\] \(S06\): unknown avatar") as exc:
        from_skill_json(doc, "idea-1")
    assert repr(value) in str(exc.value)


# ------------------------------------------------------------------ total duration


@pytest.mark.parametrize("delta", [0.06, -0.06, 5.0])
def test_inconsistent_total_duration_is_rejected(delta: float) -> None:
    doc = edited(LONG, lambda d: d.__setitem__("duree_totale_s", round(d["duree_totale_s"] + delta, 2)))
    with pytest.raises(SkillJsonError, match=r"duree_totale_s: .* but the scenes last 66\.800 s"):
        from_skill_json(doc, "idea-1")


def test_total_duration_within_tolerance_is_kept_verbatim() -> None:
    doc = edited(LONG, lambda d: d.__setitem__("duree_totale_s", round(d["duree_totale_s"] + 0.04, 2)))
    script, _ = from_skill_json(doc, "idea-1")
    assert script.extras[ROOT_KEY]["duree_totale_s"] == doc["duree_totale_s"] == 66.84  # type: ignore[index]
    assert_lossless(doc)


def test_total_duration_follows_a_changed_scene() -> None:
    def lengthen(d: Doc) -> None:
        d["scenes"][-1]["duree_s"] = round(d["scenes"][-1]["duree_s"] + 1, 1)

    with pytest.raises(SkillJsonError, match="duree_totale_s"):
        from_skill_json(edited(SHORT, lengthen), "idea-1")


def one_scene(duration: float, total: float) -> Doc:
    def edit(d: Doc) -> None:
        d["scenes"] = [{**d["scenes"][0], "duree_s": duration}]
        d["duree_totale_s"] = total

    return edited(SHORT, edit)


@pytest.mark.parametrize("total", [1.05, 0.95])
def test_total_exactly_at_the_tolerance_is_accepted(total: float) -> None:
    # 1.05 - 1.0 == 0.050000000000000044 in floats: the noise must not turn "equal to the tolerance" into "beyond"
    assert abs(total - 1.0) > 0.05
    assert_lossless(one_scene(1.0, total))


@pytest.mark.parametrize("total", [1.051, 0.949])
def test_total_just_beyond_the_tolerance_is_rejected(total: float) -> None:
    with pytest.raises(SkillJsonError, match=r"duree_totale_s: .* but the scenes last 1\.000 s in total"):
        from_skill_json(one_scene(1.0, total), "idea-1")


@pytest.mark.parametrize("path", [LONG, SHORT], ids=["long", "short"])
@pytest.mark.parametrize(("delta", "accepted"), [(0.05, True), (-0.05, True), (0.051, False), (-0.051, False)])
def test_tolerance_boundary_on_the_fixtures(path: Path, delta: float, accepted: bool) -> None:
    doc = edited(path, lambda d: d.__setitem__("duree_totale_s", round(d["duree_totale_s"] + delta, 3)))
    if accepted:
        assert_lossless(doc)
    else:
        with pytest.raises(SkillJsonError, match="duree_totale_s"):
            from_skill_json(doc, "idea-1")


def drifting(d: Doc) -> None:
    """Every scene starts 0.04 s after the previous one ends: each step is within tolerance, the sum of steps is not."""
    end = 0.0
    for i, scene in enumerate(d["scenes"]):
        scene["debut_s"] = 0 if i == 0 else round(end + 0.04, 2)
        end = scene["debut_s"] + scene["duree_s"]


def test_total_must_also_match_the_end_of_the_timeline() -> None:
    doc = edited(LONG, drifting)
    assert doc["duree_totale_s"] == 66.8  # still the exact sum of the durations
    with pytest.raises(SkillJsonError, match=r"duree_totale_s: 66\.8 s but the timeline ends at 67\.080 s"):
        from_skill_json(doc, "idea-1")
    # and the end of the timeline is no escape: the sum is then off
    doc["duree_totale_s"] = 67.08
    with pytest.raises(SkillJsonError, match=r"but the scenes last 66\.800 s in total"):
        from_skill_json(doc, "idea-1")


def test_drifting_timeline_without_a_total_is_accepted() -> None:
    doc = edited(LONG, drifting)
    doc.pop("duree_totale_s")
    script, _ = from_skill_json(doc, "idea-1")
    assert script.duration_s == 67.08  # the domain accepts the drift, scene by scene
    assert_lossless(doc)


# ------------------------------------------------------------------ unknown and absent fields


def unknown_notes(d: Doc) -> None:
    """The same unknown field name at four levels of the document, each with its own value."""
    for node, value in ((d, "x"), (d["scenes"][0], "y"), (d["scenes"][0]["boucles"], "z"), (d["miniatures"][0], "w")):
        node["zz_notes"] = value


UNKNOWN_FIELDS: dict[str, Callable[[Doc], object]] = {
    "top": lambda d: d.__setitem__("chaine_cible", {"nom": "labo", "tags": [1, 2.0, None, True]}),
    "divulgation_ia": lambda d: d["divulgation_ia"].__setitem__("outil", "mock-generator"),
    "controle": lambda d: d["controle"].__setitem__("relu_par", ["qa-1"]),
    "miniature": lambda d: d["miniatures"][1].__setitem__("emotion", "surprise"),
    "scene": lambda d: d["scenes"][2].__setitem__("plan_camera", {"focale_mm": 35, "mouvement": "travelling"}),
    "boucles": lambda d: d["scenes"][4]["boucles"].__setitem__("commentaire", "fermée par le prisme"),
    "several": unknown_notes,
    "top named @layout": lambda d: d.__setitem__(LAYOUT_KEY, "note libre"),
    "top named @root": lambda d: d.__setitem__(ROOT_KEY, {"version": "9.9"}),
    "scene named @layout": lambda d: d["scenes"][1].__setitem__(LAYOUT_KEY, {"absent": ["titre_en"]}),
}


@pytest.mark.parametrize("edit", UNKNOWN_FIELDS.values(), ids=UNKNOWN_FIELDS.keys())
def test_unknown_field_is_kept_in_extras(edit: Callable[[Doc], object]) -> None:
    doc = edited(LONG, edit)
    script, _ = from_skill_json(doc, "idea-1")
    plain_script, _ = from_skill_json(load(LONG), "idea-1")
    assert script.extras != plain_script.extras
    assert script.content_hash() != plain_script.content_hash()  # the unknown field is part of the identity
    assert_lossless(doc)


def test_unknown_fields_land_under_their_parent() -> None:
    doc = load(LONG)
    for edit in UNKNOWN_FIELDS.values():
        edit(doc)
    script, _ = from_skill_json(doc, "idea-1")
    assert script.extras[ROOT_KEY] == {
        "version": "1.0",
        "duree_totale_s": 66.8,
        "chaine_cible": {"nom": "labo", "tags": [1, 2.0, None, True]},
        "zz_notes": "x",
        LAYOUT_KEY: "note libre",
        ROOT_KEY: {"version": "9.9"},
    }
    assert script.extras["divulgation_ia"] == {"outil": "mock-generator"}
    assert script.extras["controle"] == {"relu_par": ["qa-1"]}
    assert script.extras["miniatures"] == {"A": {"zz_notes": "w"}, "B": {"emotion": "surprise"}}
    scenes: Any = script.extras["scenes"]
    assert scenes["S03"] == {"plan_camera": {"focale_mm": 35, "mouvement": "travelling"}}
    assert scenes["S05"] == {"boucles": {"commentaire": "fermée par le prisme"}}
    assert scenes["S01"] == {"zz_notes": "y", "boucles": {"zz_notes": "z"}}
    assert scenes["S02"] == {LAYOUT_KEY: {"absent": ["titre_en"]}}
    assert set(script.extras) == {ROOT_KEY, LAYOUT_KEY, "divulgation_ia", "controle", "miniatures", "scenes"}
    assert_lossless(doc)


def test_fields_named_like_the_extras_metadata_are_plain_unknown_fields() -> None:
    """No document field name is reserved: a top-level "@layout" can neither be refused nor spoof the layout."""

    def spoof(d: Doc) -> None:
        d[LAYOUT_KEY] = {"absent": ["titre_en", "controle/score_idee"], "float": ["debit_mots_min"]}
        d[ROOT_KEY] = {"version": "2.0"}

    doc = edited(LONG, spoof)
    script, _ = from_skill_json(doc, "idea-1")
    assert script.extras[LAYOUT_KEY] == {"float": ["scenes/S03/duree_s", "scenes/S08/debut_s"]}
    assert script.extras[ROOT_KEY]["version"] == "1.0"  # type: ignore[index]
    out = round_trip(doc)
    assert type(out["debit_mots_min"]) is int
    assert out["titre_en"] == doc["titre_en"]
    assert_lossless(doc)


ABSENT_FIELDS: dict[str, tuple[Path, Callable[[Doc], object]]] = {
    "titre_en": (LONG, lambda d: d.pop("titre_en")),
    "video_suivante": (LONG, lambda d: d.pop("video_suivante")),
    "premiere_image (long)": (LONG, lambda d: d.pop("premiere_image")),
    "miniatures (short)": (SHORT, lambda d: d.pop("miniatures")),
    "duree_totale_s": (LONG, lambda d: d.pop("duree_totale_s")),
    "miniature texte": (LONG, lambda d: d["miniatures"][0].pop("texte")),
    "raisons_blocage": (LONG, lambda d: d["controle"].pop("raisons_blocage")),
    "faits_a_verifier": (LONG, lambda d: d["controle"].pop("faits_a_verifier")),
    "score_idee": (LONG, lambda d: d["controle"].pop("score_idee")),
    "avatar": (LONG, lambda d: d["scenes"][0].pop("avatar")),
    "voix_off": (LONG, lambda d: d["scenes"][3].pop("voix_off")),
    "texte_ecran": (SHORT, lambda d: d["scenes"][1].pop("texte_ecran")),
    "note_traduction": (LONG, lambda d: d["scenes"][1].pop("note_traduction")),
    "boucles": (LONG, lambda d: d["scenes"][1].pop("boucles")),
    "boucles.ferme": (LONG, lambda d: d["scenes"][0]["boucles"].pop("ferme")),
    "boucles emptied": (LONG, lambda d: d["scenes"][1].__setitem__("boucles", {})),
    "every optional scene field": (
        SHORT,
        lambda d: [
            d["scenes"][2].pop(k)
            for k in ("voix_off", "ton", "avatar", "visuel", "prompt_visuel_en", "texte_ecran", "son", "boucles")
        ],
    ),
}


@pytest.mark.parametrize(("path", "edit"), ABSENT_FIELDS.values(), ids=ABSENT_FIELDS.keys())
def test_omitted_optional_field_stays_omitted(path: Path, edit: Callable[[Doc], object]) -> None:
    assert_lossless(edited(path, edit))


def test_omitted_fields_take_the_contract_defaults() -> None:
    def strip(d: Doc) -> None:
        for key in ("titre_en", "video_suivante"):
            d.pop(key)
        d["controle"].pop("score_idee")
        for key in ("avatar", "note_traduction", "boucles", "ton"):
            d["scenes"][2].pop(key)

    doc = edited(LONG, strip)
    script, _ = from_skill_json(doc, "idea-1")
    assert (script.title_en, script.next_video, script.control.idea_score) == ("", "", None)
    scene = script.scenes[2]
    assert (scene.avatar, scene.translation_note, scene.tone) == (AvatarMode.OFF_SCREEN, "", "")
    assert scene.loops.opens == scene.loops.closes == ()
    assert_lossless(doc)


def test_null_score_differs_from_an_omitted_score() -> None:
    with_null = edited(LONG, lambda d: d["controle"].__setitem__("score_idee", None))
    without = edited(LONG, lambda d: d["controle"].pop("score_idee"))
    assert round_trip(with_null)["controle"]["score_idee"] is None
    assert "score_idee" not in round_trip(without)["controle"]
    assert_lossless(with_null)


def test_integer_and_float_number_forms_are_kept() -> None:
    doc = load(LONG)
    assert type(doc["scenes"][0]["debut_s"]) is int and type(doc["scenes"][2]["duree_s"]) is float
    out = round_trip(doc)
    assert type(out["scenes"][0]["debut_s"]) is int
    assert type(out["scenes"][2]["duree_s"]) is float  # 8.0 stays 8.0
    assert type(out["debit_mots_min"]) is int

    swapped = load(LONG)
    swapped["debit_mots_min"] = 150.0
    swapped["controle"]["score_idee"] = 74.0
    out = round_trip(swapped)
    assert type(out["debit_mots_min"]) is float and type(out["controle"]["score_idee"]) is float
    assert_lossless(swapped)


def test_verbatim_fields_need_no_layout_record() -> None:
    as_float_total = edited(LONG, lambda d: d.__setitem__("duree_totale_s", float(round(d["duree_totale_s"]))))
    as_float_total["scenes"][-1]["duree_s"] = round(as_float_total["scenes"][-1]["duree_s"] + 0.2, 1)
    assert as_float_total["duree_totale_s"] == 67.0
    script, _ = from_skill_json(as_float_total, "idea-1")
    assert "duree_totale_s" not in script.extras[LAYOUT_KEY]["float"]  # type: ignore[index]
    assert type(script.extras[ROOT_KEY]["duree_totale_s"]) is float  # type: ignore[index]
    assert_lossless(as_float_total)


def test_key_order_does_not_change_identity() -> None:
    def reverse(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: reverse(value[k]) for k in reversed(list(value))}
        if isinstance(value, list):
            return [reverse(v) for v in value]
        return value

    doc = load(LONG)
    doc["scenes"][3]["zz_extra"] = {"b": 1, "a": 2}
    shuffled = reverse(doc)
    assert list(shuffled) != list(doc)
    script_a, package_a = from_skill_json(doc, "idea-1")
    script_b, package_b = from_skill_json(shuffled, "idea-1")
    assert script_a.content_hash() == script_b.content_hash()
    assert package_a.content_hash() == package_b.content_hash()
    assert round_trip(shuffled) == doc


def test_scene_order_is_part_of_the_document() -> None:
    doc = load(SHORT)
    script, _ = from_skill_json(doc, "idea-1")
    assert [s["id"] for s in to_skill_json(script, from_skill_json(doc, "idea-1")[1])["scenes"]] == [
        "S01",
        "S02",
        "S03",
        "S04",
        "S05",
    ]
    swapped = copy.deepcopy(doc)
    swapped["scenes"][1], swapped["scenes"][2] = swapped["scenes"][2], swapped["scenes"][1]
    with pytest.raises(SkillJsonError, match="contiguous timeline"):
        from_skill_json(swapped, "idea-1")


# ------------------------------------------------------------------ nesting depth


def test_nesting_up_to_the_limit_round_trips() -> None:
    def deep(d: Doc) -> None:
        d["zz"] = nested(MAX_DEPTH - 1)  # document + 63 arrays
        d["scenes"][0]["zz"] = nested(MAX_DEPTH - 3)  # document, scenes, scene + 61 arrays
        d["scenes"][0]["boucles"]["zz"] = nested(MAX_DEPTH - 4)

    doc = edited(SHORT, deep)
    script, _ = from_skill_json(doc, "idea-1")
    assert script.content_hash()  # hashing walks the whole value too
    assert_lossless(doc)  # extras nest one level deeper than the document: the writer allows for it


@pytest.mark.parametrize(
    "edit",
    [
        lambda d: d.__setitem__("zz", nested(MAX_DEPTH)),
        lambda d: d["scenes"][0].__setitem__("zz", nested(MAX_DEPTH - 2)),
        lambda d: d["controle"].__setitem__("zz", [{"k": nested(MAX_DEPTH - 3)}]),
    ],
    ids=["top", "scene", "controle"],
)
def test_nesting_beyond_the_limit_is_refused(edit: Callable[[Doc], object]) -> None:
    with pytest.raises(SkillJsonError, match=f"nested deeper than {MAX_DEPTH} arrays/objects"):
        from_skill_json(edited(SHORT, edit), "idea-1")


@pytest.mark.parametrize("levels", [600, 100_000])
def test_very_deep_unknown_field_is_a_skill_json_error_not_a_recursion_error(levels: int) -> None:
    value = json.loads("[" * levels + "]" * levels) if levels < 900 else nested(levels)
    doc = edited(SHORT, lambda d: d["scenes"][1].__setitem__("zz", value))
    with pytest.raises(SkillJsonError, match=r"^scenes\[1\]\.zz(\[0\])+: nested deeper than"):
        from_skill_json(doc, "idea-1")


def test_deep_or_cyclic_extras_are_refused_on_writing() -> None:
    script, package = from_skill_json(load(SHORT), "idea-1")
    cycle: list[Any] = []
    cycle.append(cycle)
    for value in (nested(5000), cycle):
        bad = script.model_copy(update={"extras": {ROOT_KEY: {"zz": value}}})
        with pytest.raises(SkillJsonError, match="nested deeper than"):
            to_skill_json(bad, package)


# ------------------------------------------------------------------ strict input


@pytest.mark.parametrize(
    ("where", "key"),
    [
        ((), "version"),
        ((), "format"),
        ((), "langue"),
        ((), "debit_mots_min"),
        ((), "promesse"),
        ((), "titres"),
        ((), "divulgation_ia"),
        ((), "controle"),
        ((), "scenes"),
        (("divulgation_ia",), "requise"),
        (("divulgation_ia",), "raison"),
        (("controle",), "publiable"),
        (("miniatures", 0), "id"),
        (("miniatures", 0), "concept"),
        (("miniatures", 0), "elements"),
        (("scenes", 0), "id"),
        (("scenes", 0), "role"),
        (("scenes", 0), "debut_s"),
        (("scenes", 0), "duree_s"),
    ],
)
def test_missing_required_field_is_rejected(where: tuple[str | int, ...], key: str) -> None:
    doc = load(LONG)
    node: Any = doc
    for step in where:
        node = node[step]
    node.pop(key)
    with pytest.raises(SkillJsonError, match=f"missing required field '{key}'"):
        from_skill_json(doc, "idea-1")


BIG = 2**60 + 1  # an integer that a float cannot hold exactly

# name -> (edit, message the error must match)
WRONG_TYPES: dict[str, tuple[Callable[[Doc], object], str]] = {
    "number as string": (lambda d: d.__setitem__("debit_mots_min", "150"), r"^debit_mots_min: expected a number, got str"),
    "boolean as number": (lambda d: d.__setitem__("debit_mots_min", True), r"^debit_mots_min: expected a number, got bool"),
    "titles as string": (lambda d: d.__setitem__("titres", "Un titre"), r"^titres: expected an array of strings, got str"),
    "title as number": (lambda d: d["titres"].__setitem__(0, 1), r"^titres\[0\]: expected a string, got int"),
    "titles as tuple": (lambda d: d.__setitem__("titres", tuple(d["titres"])), r"^titres: tuple is not JSON data"),
    "requise as string": (
        lambda d: d["divulgation_ia"].__setitem__("requise", "oui"),
        r"^divulgation_ia\.requise: expected true or false, got str",
    ),
    "publiable as integer": (
        lambda d: d["controle"].__setitem__("publiable", 1),
        r"^controle\.publiable: expected true or false, got int",
    ),
    "score as string": (
        lambda d: d["controle"].__setitem__("score_idee", "74"),
        r"^controle\.score_idee: expected a number, got str",
    ),
    "total as string": (lambda d: d.__setitem__("duree_totale_s", "66.8"), r"^duree_totale_s: expected a number, got str"),
    "disclosure as array": (lambda d: d.__setitem__("divulgation_ia", []), r"^divulgation_ia: expected an object, got list"),
    "thumbnails as object": (lambda d: d.__setitem__("miniatures", {"A": {}}), r"^miniatures: expected an array, got dict"),
    "scenes as object": (lambda d: d.__setitem__("scenes", {"S01": d["scenes"][0]}), r"^scenes: expected a non-empty array"),
    "scenes empty": (lambda d: d.__setitem__("scenes", []), r"^scenes: expected a non-empty array"),
    "scene as string": (lambda d: d["scenes"].__setitem__(0, "S01"), r"^scenes\[0\]: expected an object, got str"),
    "voix_off null": (
        lambda d: d["scenes"][0].__setitem__("voix_off", None),
        r"^scenes\[0\]\.voix_off: expected a string, got NoneType",
    ),
    "duree_s NaN": (
        lambda d: d["scenes"][0].__setitem__("duree_s", float("nan")),
        r"^scenes\[0\]\.duree_s: expected a finite number, got nan",
    ),
    "duree_s infinite": (
        lambda d: d["scenes"][0].__setitem__("duree_s", float("inf")),
        r"^scenes\[0\]\.duree_s: expected a finite number, got inf",
    ),
    "debut_s beyond float precision": (
        lambda d: d["scenes"][0].__setitem__("debut_s", BIG),
        rf"^scenes\[0\]\.debut_s: integer {BIG} cannot be represented exactly",
    ),
    "debut_s beyond float range": (
        lambda d: d["scenes"][0].__setitem__("debut_s", 10**400),
        r"^scenes\[0\]\.debut_s: integer 1000+ cannot be represented exactly",
    ),
    # no contract invariant would catch these two if the precision guard went missing: only the guard does
    "debit_mots_min beyond float precision": (
        lambda d: d.__setitem__("debit_mots_min", BIG),
        rf"^debit_mots_min: integer {BIG} cannot be represented exactly",
    ),
    "score_idee beyond float precision": (
        lambda d: d["controle"].__setitem__("score_idee", BIG),
        rf"^controle\.score_idee: integer {BIG} cannot be represented exactly",
    ),
    "total beyond float precision": (
        lambda d: d.__setitem__("duree_totale_s", BIG),
        rf"^duree_totale_s: integer {BIG} cannot be represented exactly",
    ),
    "document with integer key": (
        lambda d: cast(dict[Any, Any], d).__setitem__(1, "x"),
        r"^document: object keys must be strings, got 1$",
    ),
    "known object with integer key": (
        lambda d: d["divulgation_ia"].__setitem__(1, "x"),
        r"^divulgation_ia: object keys must be strings, got 1$",
    ),
    "scene with integer key": (
        lambda d: d["scenes"][2].__setitem__(7, "x"),
        r"^scenes\[2\]: object keys must be strings, got 7$",
    ),
    "boucles as array": (
        lambda d: d["scenes"][0].__setitem__("boucles", ["Q1"]),
        r"^scenes\[0\]\.boucles: expected an object, got list",
    ),
    "ouvre as string": (
        lambda d: d["scenes"][0]["boucles"].__setitem__("ouvre", "Q1"),
        r"^scenes\[0\]\.boucles\.ouvre: expected an array of strings, got str",
    ),
    "elements as string": (
        lambda d: d["miniatures"][0].__setitem__("elements", "lentille"),
        r"^miniatures\[0\]\.elements: expected an array of strings, got str",
    ),
    "version as number": (lambda d: d.__setitem__("version", 1.0), r"^version: expected a string, got float"),
    "unknown field holds a set": (lambda d: d.__setitem__("zz", {1, 2}), r"^zz: set is not JSON data"),
    "unknown field holds a tuple": (lambda d: d.__setitem__("zz", (1, 2)), r"^zz: tuple is not JSON data"),
    "unknown field holds NaN": (
        lambda d: d["scenes"][0].__setitem__("zz", [float("nan")]),
        r"^scenes\[0\]\.zz\[0\]: expected a finite number, got nan",
    ),
    "unknown field with integer key": (
        lambda d: d["controle"].__setitem__("zz", {1: "a"}),
        r"^controle\.zz: object keys must be strings, got 1$",
    ),
}


@pytest.mark.parametrize(("edit", "message"), WRONG_TYPES.values(), ids=WRONG_TYPES.keys())
def test_wrong_json_type_is_rejected(edit: Callable[[Doc], object], message: str) -> None:
    with pytest.raises(SkillJsonError, match=message):
        from_skill_json(edited(LONG, edit), "idea-1")


def test_document_that_is_not_an_object_is_rejected() -> None:
    with pytest.raises(SkillJsonError, match=r"^document: expected an object, got list$"):
        from_skill_json([load(LONG)], "idea-1")  # type: ignore[arg-type]


@pytest.mark.parametrize("version", ["2.0", "0.9", "", "v1.0"])
def test_unsupported_version_is_rejected(version: str) -> None:
    doc = edited(LONG, lambda d: d.__setitem__("version", version))
    with pytest.raises(SkillJsonError, match="unsupported scene JSON version"):
        from_skill_json(doc, "idea-1")


def test_minor_version_is_accepted_and_kept() -> None:
    doc = edited(LONG, lambda d: d.__setitem__("version", "1.3"))
    assert from_skill_json(doc, "idea-1")[0].extras[ROOT_KEY]["version"] == "1.3"  # type: ignore[index]
    assert_lossless(doc)


def test_unknown_format_is_rejected() -> None:
    doc = edited(LONG, lambda d: d.__setitem__("format", "medium"))
    with pytest.raises(SkillJsonError, match="unknown format 'medium'"):
        from_skill_json(doc, "idea-1")


INVARIANTS: dict[str, tuple[Path, Callable[[Doc], object], str]] = {
    "timeline gap": (LONG, lambda d: d["scenes"][3].__setitem__("debut_s", d["scenes"][3]["debut_s"] + 1), "contiguous"),
    "timeline not starting at zero": (
        SHORT,
        lambda d: [s.__setitem__("debut_s", round(s["debut_s"] + 0.5, 1)) for s in d["scenes"]],
        "contiguous",
    ),
    "duplicate scene id": (LONG, lambda d: d["scenes"][4].__setitem__("id", "S04"), "duplicate scene id 'S04'"),
    "malformed scene id": (LONG, lambda d: d["scenes"][0].__setitem__("id", "scene-1"), "scenes.0.id"),
    "zero duration": (
        SHORT,
        lambda d: d["scenes"].append({**d["scenes"][-1], "id": "S06", "debut_s": 18.1, "duree_s": 0}),
        "duration_s",
    ),
    "duplicate thumbnail id": (LONG, lambda d: d["miniatures"][2].__setitem__("id", "A"), "duplicate thumbnail id 'A'"),
    "long without thumbnail": (LONG, lambda d: d.__setitem__("miniatures", []), "thumbnail"),
    "short without first frame": (SHORT, lambda d: d.pop("premiere_image"), "first frame"),
    "blocked without reason": (LONG, lambda d: d["controle"].__setitem__("publiable", False), "must state why"),
    "publishable with reasons": (LONG, lambda d: d["controle"].__setitem__("raisons_blocage", ["x"]), "blocking reasons"),
    "score above 100": (LONG, lambda d: d["controle"].__setitem__("score_idee", 120), "idea_score"),
    "bad language tag": (LONG, lambda d: d.__setitem__("langue", "french"), "language"),
    "no title": (LONG, lambda d: d.__setitem__("titres", []), "titles"),
    "empty promise": (LONG, lambda d: d.__setitem__("promesse", ""), "promise"),
    "zero words per minute": (LONG, lambda d: d.__setitem__("debit_mots_min", 0), "words_per_minute"),
}


@pytest.mark.parametrize(("path", "edit", "message"), INVARIANTS.values(), ids=INVARIANTS.keys())
def test_contract_invariants_surface_as_skill_json_errors(path: Path, edit: Callable[[Doc], object], message: str) -> None:
    with pytest.raises(SkillJsonError, match=message):
        from_skill_json(edited(path, edit), "idea-1")


def test_invalid_idea_id_is_rejected() -> None:
    with pytest.raises(SkillJsonError, match="idea_id"):
        from_skill_json(load(LONG), "Not A Slug")


def test_error_type_is_a_reportable_value_error() -> None:
    assert issubclass(SkillJsonError, StudioError)
    assert issubclass(SkillJsonError, ValueError)


# ------------------------------------------------------------------ writing back


def test_script_and_package_must_describe_the_same_video() -> None:
    long_script, long_package = from_skill_json(load(LONG), "idea-1")
    _, short_package = from_skill_json(load(SHORT), "idea-1")
    _, other_idea = from_skill_json(load(LONG), "idea-2")

    with pytest.raises(SkillJsonError, match="format, titles, first_frame"):
        to_skill_json(long_script, short_package)
    with pytest.raises(SkillJsonError, match="idea_id"):
        to_skill_json(long_script, other_idea)
    with pytest.raises(SkillJsonError, match="titles"):
        to_skill_json(long_script, long_package.model_copy(update={"titles": ("Autre titre",)}))
    with pytest.raises(SkillJsonError, match="on_screen_text"):
        to_skill_json(long_script, long_package.model_copy(update={"on_screen_text": "Moins de verre"}))


def test_a_value_set_after_reading_is_written_even_if_the_source_omitted_it() -> None:
    def strip(d: Doc) -> None:
        d["scenes"][1].pop("note_traduction")
        d["scenes"][1].pop("boucles")
        d.pop("titre_en")

    script, package = from_skill_json(edited(LONG, strip), "idea-1")
    scenes = list(script.scenes)
    scenes[1] = scenes[1].model_copy(update={"translation_note": "garder le nom propre", "loops": SceneLoops(opens=("Q9",))})
    changed = script.model_copy(update={"scenes": tuple(scenes), "title_en": "A new title"})

    out = to_skill_json(changed, package)
    assert out["titre_en"] == "A new title"
    assert out["scenes"][1]["note_traduction"] == "garder le nom propre"
    assert out["scenes"][1]["boucles"] == {"ouvre": ["Q9"], "ferme": []}
    assert_reads_back(out, changed, package)


def test_retimed_scene_rewrites_the_total_and_reads_back() -> None:
    script, package = from_skill_json(load(SHORT), "idea-1")
    longer = retimed(script, len(script.scenes) - 1, 6.0)  # last scene 4.0 s -> 6.0 s
    out = to_skill_json(longer, package)
    assert out["duree_totale_s"] == 20.1 and type(out["duree_totale_s"]) is float
    assert out["scenes"][-1]["duree_s"] == 6.0
    assert_reads_back(out, longer, package)


def test_retimed_middle_scene_shifts_the_timeline_and_the_total() -> None:
    script, package = from_skill_json(load(LONG), "idea-1")
    longer = retimed(script, 2, 9.5)  # S03 8.0 s -> 9.5 s, S04..S08 start 1.5 s later
    out = to_skill_json(longer, package)
    assert out["duree_totale_s"] == 68.3
    assert [s["debut_s"] for s in out["scenes"]][3:] == [31.1, 37.9, 44.7, 52.3, 61.5]
    assert_reads_back(out, longer, package)


def test_rewritten_total_keeps_its_integer_form() -> None:
    def whole(d: Doc) -> None:
        d["scenes"][-1]["duree_s"] = 3.9
        d["duree_totale_s"] = 18

    script, package = from_skill_json(edited(SHORT, whole), "idea-1")
    for duration, expected in ((4.9, 19), (4.4, 18.5)):
        out = to_skill_json(retimed(script, len(script.scenes) - 1, duration), package)
        assert out["duree_totale_s"] == expected and type(out["duree_totale_s"]) is type(expected)
    assert_reads_back(out, retimed(script, len(script.scenes) - 1, 4.4), package)


def test_rewritten_total_is_rounded_to_the_millisecond() -> None:
    script, package = from_skill_json(load(SHORT), "idea-1")
    measured = retimed(script, len(script.scenes) - 1, 4.123456)  # a duration measured on the synthesised voice
    out = to_skill_json(measured, package)
    assert out["duree_totale_s"] == 18.223
    assert out["scenes"][-1]["duree_s"] == 4.123456  # the scenes keep their full precision
    assert_reads_back(out, measured, package)


def test_total_still_within_tolerance_after_a_small_change_is_kept_verbatim() -> None:
    script, package = from_skill_json(load(LONG), "idea-1")
    nudged = retimed(script, len(script.scenes) - 1, 6.83)  # sum 66.83, declared 66.8: still consistent
    out = to_skill_json(nudged, package)
    assert out["duree_totale_s"] == 66.8
    assert_reads_back(out, nudged, package)


def test_drifting_script_with_a_kept_total_is_refused_on_writing() -> None:
    script, package = from_skill_json(load(LONG), "idea-1")
    data = script.model_dump()
    for i, scene in enumerate(data["scenes"]):
        scene["start_s"] = round(scene["start_s"] + 0.04 * i, 2)  # valid scene by scene, 0.28 s off at the end
    drifted = Script.model_validate(data)
    with pytest.raises(SkillJsonError, match=r"would be refused on reading: duree_totale_s: .* timeline ends at 67\.080 s"):
        to_skill_json(drifted, package)
    # without a declared total there is nothing to contradict
    root: Any = dict(script.extras[ROOT_KEY])  # type: ignore[call-overload]
    root.pop("duree_totale_s")
    bare = drifted.model_copy(update={"extras": {**drifted.extras, ROOT_KEY: root}})
    assert_reads_back(to_skill_json(bare, package), bare, package)


@pytest.mark.parametrize(
    ("root", "message"),
    [
        ({"version": "2.0"}, r"would be refused on reading: version: unsupported scene JSON version '2\.0'"),
        ({"version": 1}, r"would be refused on reading: version: expected a string, got int"),
        (
            {"version": "1.0", "duree_totale_s": "18.1"},
            r"would be refused on reading: duree_totale_s: expected a number, got str",
        ),
        ({"version": "1.0", "duree_totale_s": True}, r"would be refused on reading: duree_totale_s: expected a number, got bool"),
        ({"version": "1.0", "duree_totale_s": BIG}, r"would be refused on reading: duree_totale_s: integer \d+ cannot be"),
        ({"version": "1.0", "duree_totale_s": 10**400}, r"would be refused on reading: duree_totale_s: integer \d+ cannot be"),
    ],
    ids=[
        "version 2.0",
        "version as number",
        "total as text",
        "total as boolean",
        "total beyond float precision",
        "total beyond float range",
    ],
)
def test_writer_never_returns_a_document_the_reader_refuses(root: dict[str, Any], message: str) -> None:
    script, package = from_skill_json(load(SHORT), "idea-1")
    with pytest.raises(SkillJsonError, match=message):
        to_skill_json(script.model_copy(update={"extras": {**script.extras, ROOT_KEY: root}}), package)


def test_extras_of_missing_items_are_refused() -> None:
    doc = load(LONG)
    doc["scenes"][-1]["zz"] = 1
    doc["miniatures"][-1]["zz"] = 2
    script, package = from_skill_json(doc, "idea-1")

    without_last_scene = script.model_copy(update={"scenes": script.scenes[:-1]})
    with pytest.raises(SkillJsonError, match="scenes/S08"):
        to_skill_json(without_last_scene, package)
    without_last_thumb = package.model_copy(update={"thumbnails": package.thumbnails[:-1]})
    with pytest.raises(SkillJsonError, match="miniatures/C"):
        to_skill_json(script, without_last_thumb)


@pytest.mark.parametrize(
    ("extras", "message"),
    [
        ({"langue": "en"}, r"^Script\.extras: unexpected keys \['langue'\]"),
        ({"version": "1.0"}, r"^Script\.extras: unexpected keys \['version'\]"),  # top-level fields live under @root
        ({ROOT_KEY: {"langue": "en"}}, r"\['langue'\] would overwrite mapped fields"),
        ({ROOT_KEY: ["version"]}, r"expected an object of unknown fields"),
        ({"scenes": {"S01": {"role": "cta"}}}, r"\['role'\] would overwrite mapped fields"),
        ({"scenes": {"S01": {"boucles": {"ouvre": []}}}}, r"\['ouvre'\] would overwrite mapped fields"),
        ({"scenes": ["S01"]}, r"expected an object mapping ids to unknown fields"),
        ({"miniatures": {"A": "x"}}, r"expected an object mapping ids to unknown fields"),
        ({"controle": {"publiable": False}}, r"\['publiable'\] would overwrite mapped fields"),
        ({"divulgation_ia": "oui"}, r"\['divulgation_ia'\]: expected an object of unknown fields"),
        ({LAYOUT_KEY: "absent"}, r"expected an object with 'absent' and 'float' lists"),
        ({LAYOUT_KEY: {"absent": "titre_en"}}, r"'absent' and 'float' must be lists of paths"),
        ({LAYOUT_KEY: {"missing": []}}, r"expected an object with 'absent' and 'float' lists"),
        ({ROOT_KEY: {"zz": {1, 2}}}, r"^Script\.extras\.@root\.zz: set is not JSON data"),
    ],
)
def test_extras_that_cannot_be_written_back_are_refused(extras: dict[str, Any], message: str) -> None:
    script, package = from_skill_json(load(LONG), "idea-1")
    with pytest.raises(SkillJsonError, match=message):
        to_skill_json(script.model_copy(update={"extras": extras}), package)


def test_script_from_another_source_is_written_as_version_1_0() -> None:
    script, package = from_skill_json(load(SHORT), "idea-1")
    bare = script.model_copy(update={"extras": {}})
    out = to_skill_json(bare, package)
    assert out["version"] == "1.0"
    assert "duree_totale_s" not in out
    assert_reads_back(out, bare, package)


def test_documents_and_results_share_no_mutable_state() -> None:
    doc = load(LONG)
    doc["scenes"][0]["zz"] = {"items": [1]}
    doc["zz_top"] = {"k": [1]}
    script, package = from_skill_json(doc, "idea-1")
    snapshot = canonical_json(script.extras)

    doc["scenes"][0]["zz"]["items"].append(2)
    doc["zz_top"]["k"].append(2)
    doc["zz_later"] = "later"
    assert canonical_json(script.extras) == snapshot

    out = to_skill_json(script, package)
    out["scenes"][0]["zz"]["items"].append(3)
    out["zz_top"]["k"].append(3)
    out["version"] = "9.9"
    assert canonical_json(script.extras) == snapshot
    again = to_skill_json(script, package)
    assert (again["scenes"][0]["zz"], again["zz_top"], again["version"]) == ({"items": [1]}, {"k": [1]}, "1.0")
