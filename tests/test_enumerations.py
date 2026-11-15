"""Tests for enumeration styles and word notes (hexword-format SPEC §4.1).

The cases are hexword-format's fixture 11-enumeration-styles, whose expected output both reference implementations
produce.
"""

import pytest

from hexword import Clue, ClueGroupSettings, Hexword, HexwordService, PuzzleSettings


@pytest.fixture()
def service() -> HexwordService:
    return HexwordService()


ACROSS = ClueGroupSettings(enumeration_style="total", word_note="words", word_note_italic=True)
ABBREVIATED = ClueGroupSettings(enumeration_style="total", word_note="abbreviated")
NUMERALS = ClueGroupSettings(enumeration_style="total", word_note="numeral")


@pytest.mark.parametrize(
    ("clue", "group", "expected"),
    [
        (
            Clue(name="1", clue_text="Double-cross includes a fission product", answers=["BETA RAY"]),
            ACROSS,
            [("7", "two words")],
        ),
        (
            Clue(name="3", clue_text="Match covered", answers=["FIVE-STAR"], enumeration="7"),
            ACROSS,
            [("7", "hyphenated")],
        ),
        (Clue(name="5", clue_text="City on the Mississippi", answers=["ST. LOUIS"]), ACROSS, [("7", "two words")]),
        (
            Clue(name="7", clue_text="City in Israel", answers=["TEL AVIV"], enumeration_style="split"),
            ACROSS,
            [("3,4", None)],
        ),
        (Clue(name="a", clue_text="Tycoon", answers=["SELF-MADE MAN"]), ABBREVIATED, [("11", "2 wds.")]),
        (Clue(name="b", clue_text="Fairground ride", answers=["MERRY-GO-ROUND"]), ABBREVIATED, [("12", "hyph.")]),
        (Clue(name="a", clue_text="Hamlet's question", answers=["TO BE OR NOT TO BE"]), NUMERALS, [("13", "6 words")]),
        (Clue(name="b", clue_text="Plain", answers=["SIMPLE"]), NUMERALS, [("6", None)]),
    ],
)
def test_fixture_11(service, clue, group, expected):
    assert service.get_clue_enumerations(clue, group, PuzzleSettings()) == expected


def test_split_is_the_default(service):
    clue = Clue(name="1", clue_text="x", answers=["BETA RAY"])
    assert service.get_clue_enumerations(clue) == [("4,3", None)]


def test_group_inherits_the_puzzle(service):
    clue = Clue(name="1", clue_text="x", answers=["SELF-MADE MAN"])
    puzzle = PuzzleSettings(enumeration_style="total", word_note="abbreviated", word_note_italic=True)
    assert service.get_clue_enumerations(clue, ClueGroupSettings(), puzzle) == [("11", "2 wds.")]
    assert service.resolve_enumeration_settings(clue, ClueGroupSettings(), puzzle) == ("total", "abbreviated", True)
    group = ClueGroupSettings(enumeration_style="split", word_note_italic=False)
    assert service.resolve_enumeration_settings(clue, group, puzzle) == ("split", "abbreviated", False)


def test_unknown_values_fall_back(service):
    clue = Clue(name="1", clue_text="x", answers=["BETA RAY"], enumeration_style="bogus")
    group = ClueGroupSettings(enumeration_style="total", word_note="bogus")
    assert service.get_clue_enumerations(clue, group) == [("7", "two words")]


def test_measure_counts_the_entries(service):
    """Under show_enumerations 'entries' the number counts squares; the note still comes from the answer."""
    clue = Clue(name="7", clue_text="City in Israel", answers=["TEL AVIV"], entries=["TELAV"])
    total = ClueGroupSettings(enumeration_style="total")
    assert service.get_clue_enumerations(clue, total, measure=["TELAV"]) == [("5", "two words")]
    assert service.get_clue_enumerations(clue, measure=["TELAV"]) == [("5", None)]


def test_several_answers(service):
    clue = Clue(name="1", clue_text="x", answers=["BETA RAY", "SIMPLE"], enumeration=["7", "6"])
    total = ClueGroupSettings(enumeration_style="total")
    assert service.get_clue_enumerations(clue, total) == [("7", "two words"), ("6", None)]


@pytest.mark.parametrize(
    ("answer", "form", "note"),
    [
        ("BETA RAY", "words", "two words"),
        ("BETA RAY", "numeral", "2 words"),
        ("BETA RAY", "abbreviated", "2 wds."),
        ("BETA RAY", "none", None),
        ("A B C D E F G H I J K", "words", "11 words"),
        ("FIVE-STAR", "words", "hyphenated"),
        ("FIVE-STAR", "abbreviated", "hyph."),
        ("SIMPLE", "words", None),
    ],
)
def test_word_note(answer, form, note):
    assert HexwordService.get_word_note(answer, form) == note


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("City on the Mississippi (two words)", True),
        ("Double-cross includes a fission product (<i>2 words</i>)", True),
        ("Tycoon (2 wds.)", True),
        ("Ride (<em>hyph.</em>) ", True),
        ("Fixed (hyphenated)", True),
        ("A clue (7)", False),
        ("Words (in a way) of wisdom", False),
    ],
)
def test_note_in_text(text, found):
    assert HexwordService.note_in_text(text) is found


def test_round_trip_keeps_the_settings(service):
    puzzle = Hexword.model_validate(
        {
            "title": "Word Count",
            "settings": {"enumeration_style": "total", "word_note": "abbreviated", "word_note_italic": True},
            "clue_groups": [
                {
                    "name": "Across",
                    "settings": {"enumeration_style": "split"},
                    "clues": [
                        {
                            "name": "1",
                            "clue_text": "x",
                            "answers": ["BETA RAY"],
                            "enumeration_style": "total",
                            "enumeration": "7",
                        }
                    ],
                }
            ],
        }
    )
    data = service.to_dict(puzzle)
    assert data["settings"]["enumeration_style"] == "total"
    assert data["clue_groups"][0]["settings"]["enumeration_style"] == "split"
    assert "word_note" not in data["clue_groups"][0]["settings"]  # None: inherits the puzzle's
    assert data["clue_groups"][0]["clues"][0]["enumeration"] == "7"
    assert service.from_dict(data) == puzzle
