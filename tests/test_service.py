"""Tests for HexwordService — clue parsing, serialization, and enumeration."""

import pytest

from hexword.exceptions import ClueParseError
from hexword.service import HexwordService


@pytest.fixture()
def service() -> HexwordService:
    """Return a fresh HexwordService instance."""
    return HexwordService()


class TestParseClue:
    """Tests for parse_clue() — tilde-delimited string → Clue model."""

    def test_simple_clue(self, service: HexwordService):
        """Parse a simple numbered clue."""
        clue = service.parse_clue("1. Sort of lily branch holding up halfway ~ ARUM ~ AR(U)M")
        assert clue.name == "1"
        assert clue.clue_text == "Sort of lily branch holding up halfway"
        assert clue.answers == ["ARUM"]
        assert clue.annotations == ["AR(U)M"]
        assert clue.entries == []
        assert clue.starred is False
        assert clue.suffix is None
        assert clue.label is None
        assert clue.label_index == 0

    def test_starred_clue(self, service: HexwordService):
        """Parse a starred clue."""
        clue = service.parse_clue("*1. Clue text ~ ANS ~ SOL")
        assert clue.starred is True
        assert clue.name == "1"
        assert clue.clue_text == "Clue text"
        assert clue.answers == ["ANS"]
        assert clue.annotations == ["SOL"]

    def test_alpha_label(self, service: HexwordService):
        """Parse an alphabetic-labelled clue."""
        clue = service.parse_clue("a. Weapon shot in a rug ~ AIR GUN ~ AIR GUN (anag.)")
        assert clue.name == "a"
        assert clue.answers == ["AIR GUN"]
        assert clue.annotations == ["AIR GUN (anag.)"]

    def test_compound_label(self, service: HexwordService):
        """Parse a compound label with grid label override."""
        clue = service.parse_clue("a;16. Rose around morningtime with branches ~ RAMOSE ~ R(AM)OS E")
        assert clue.name == "a"
        assert clue.label == "16"
        assert clue.label_index == 0
        assert clue.answers == ["RAMOSE"]
        assert clue.annotations == ["R(AM)OS E"]

    def test_compound_label_with_index(self, service: HexwordService):
        """Parse a compound label with label index."""
        clue = service.parse_clue("a;16;2. Rose around ~ RAMOSE ~ R(AM)OS E")
        assert clue.name == "a"
        assert clue.label == "16"
        assert clue.label_index == 2

    def test_suffixed_label(self, service: HexwordService):
        """Parse a clue with a suffix."""
        clue = service.parse_clue("1|b. Clue text ~ ANS ~ SOL")
        assert clue.name == "1"
        assert clue.suffix == "b"
        assert clue.answers == ["ANS"]

    def test_pipe_separated_entries(self, service: HexwordService):
        """Parse a clue with pipe-separated entries."""
        clue = service.parse_clue("a. Weapon shot in a rug ~ AIR GUN|AIRGUN ~ AIR GUN (anag.)")
        assert clue.answers == ["AIR GUN"]
        assert clue.entries == ["AIRGUN"]

    def test_multi_answer_semicolons(self, service: HexwordService):
        """Parse a clue with multiple semicolon-separated answers."""
        clue = service.parse_clue("1. Double answer ~ FIRST;SECOND ~ SOL1;SOL2")
        assert clue.answers == ["FIRST", "SECOND"]
        assert clue.annotations == ["SOL1", "SOL2"]

    def test_html_in_clue_text(self, service: HexwordService):
        """Parse a clue with HTML in the clue text."""
        clue = service.parse_clue("1. A <i>sucker</i> for a tree ~ PALM ~ PALM")
        assert clue.clue_text == "A <i>sucker</i> for a tree"
        assert clue.answers == ["PALM"]

    def test_double_def_annotation(self, service: HexwordService):
        """Parse a clue with 'double def.' annotation."""
        clue = service.parse_clue("7. Acceptable behavior at parties? ~ DOS ~ DOS (double def.)")
        assert clue.name == "7"
        assert clue.answers == ["DOS"]
        assert clue.annotations == ["DOS (double def.)"]

    def test_clue_without_annotation(self, service: HexwordService):
        """Parse a clue with only two tilde parts (answer serves as annotation)."""
        clue = service.parse_clue("1. Simple clue ~ ANSWER")
        assert clue.answers == ["ANSWER"]
        assert clue.annotations == ["ANSWER"]

    def test_empty_string_raises(self, service: HexwordService):
        """Empty strings should raise ClueParseError."""
        with pytest.raises(ClueParseError):
            service.parse_clue("")

    def test_no_dot_delimiter_raises(self, service: HexwordService):
        """Strings without '. ' delimiter should raise ClueParseError."""
        with pytest.raises(ClueParseError):
            service.parse_clue("no dot delimiter here")


class TestClueToString:
    """Tests for clue_to_string() — Clue model → tilde-delimited string."""

    def test_simple_roundtrip(self, service: HexwordService):
        """A simple clue should round-trip through parse → serialize → re-parse."""
        original = "1. Sort of lily branch ~ ARUM ~ AR(U)M"
        clue = service.parse_clue(original)
        result = service.clue_to_string(clue)
        reparsed = service.parse_clue(result)
        assert reparsed.name == clue.name
        assert reparsed.clue_text == clue.clue_text
        assert reparsed.answers == clue.answers
        assert reparsed.annotations == clue.annotations

    def test_starred_roundtrip(self, service: HexwordService):
        """A starred clue should round-trip."""
        original = "*1. Clue text ~ ANS ~ SOL"
        clue = service.parse_clue(original)
        result = service.clue_to_string(clue)
        reparsed = service.parse_clue(result)
        assert reparsed.starred is True
        assert reparsed.name == "1"

    def test_compound_label_roundtrip(self, service: HexwordService):
        """A compound label clue should round-trip."""
        original = "a;16. Rose around ~ RAMOSE ~ R(AM)OS E"
        clue = service.parse_clue(original)
        result = service.clue_to_string(clue)
        reparsed = service.parse_clue(result)
        assert reparsed.name == "a"
        assert reparsed.label == "16"

    def test_entries_roundtrip(self, service: HexwordService):
        """A clue with entries should round-trip."""
        original = "a. Weapon shot ~ AIR GUN|AIRGUN ~ AIR GUN (anag.)"
        clue = service.parse_clue(original)
        result = service.clue_to_string(clue)
        reparsed = service.parse_clue(result)
        assert reparsed.answers == ["AIR GUN"]
        assert reparsed.entries == ["AIRGUN"]

    def test_suffix_roundtrip(self, service: HexwordService):
        """A suffixed clue should round-trip."""
        original = "1|b. Clue text ~ ANS ~ SOL"
        clue = service.parse_clue(original)
        result = service.clue_to_string(clue)
        reparsed = service.parse_clue(result)
        assert reparsed.name == "1"
        assert reparsed.suffix == "b"


class TestGetEnumeration:
    """Tests for get_enumeration() — answer → enumeration string."""

    def test_single_word(self):
        """Single word enumeration."""
        assert HexwordService.get_enumeration("ARUM") == "4"

    def test_two_words(self):
        """Two-word enumeration with space."""
        assert HexwordService.get_enumeration("AIR GUN") == "3,3"

    def test_three_words(self):
        """Three-word enumeration."""
        assert HexwordService.get_enumeration("FRENCH BED SET") == "6,3,3"

    def test_hyphenated(self):
        """Hyphenated word should preserve the hyphen."""
        assert HexwordService.get_enumeration("SELF-MADE") == "4-4"

    def test_empty_string(self):
        """Empty answer should produce '0'."""
        assert HexwordService.get_enumeration("") == "0"


class TestFromDict:
    """Tests for from_dict() and to_dict() dict serialization."""

    def test_from_dict_fixture(self, service: HexwordService, snow_white_dict: dict):
        """from_dict should produce a valid Hexword from the fixture."""
        hw = service.from_dict(snow_white_dict)
        assert hw.title == "Hello World!"
        assert len(hw.clue_groups) == 2
        assert hw.clue_groups[0].clues[0].name == "1"
        assert hw.clue_groups[0].clues[0].answers == ["FRENCH BED"]

    def test_to_dict_produces_aliases(self, service: HexwordService):
        """to_dict should use aliases (e.g., 'background-color')."""
        from hexword.models import GridStyle, Grid, Hexword

        hw = Hexword(
            title="Test",
            grid=Grid(
                styles={"#": GridStyle(background_color="lightgrey")},
            ),
        )
        d = service.to_dict(hw)
        assert d["grid"]["styles"]["#"]["background-color"] == "lightgrey"
        # The Python name should NOT appear in the output
        assert "background_color" not in d["grid"]["styles"]["#"]
