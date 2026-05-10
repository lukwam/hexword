"""Tests for hexword Pydantic models."""

import pytest
from pydantic import ValidationError

from hexword.models import (
    Clue,
    ClueGroup,
    ClueGroupSettings,
    Grid,
    GridStyle,
    Hexword,
    PuzzleSettings,
)


class TestHexword:
    """Hexword top-level model tests."""

    def test_minimal_construction(self):
        """A Hexword with just a title should work."""
        hw = Hexword(title="Test Puzzle")
        assert hw.title == "Test Puzzle"
        assert hw.author == ""
        assert hw.editor is None
        assert hw.instructions is None
        assert hw.solution is None
        assert hw.clue_groups == []
        assert hw.grid == Grid()
        assert hw.settings == PuzzleSettings()
        assert hw.unclued == []

    def test_full_construction(self, snow_white_dict: dict):
        """A Hexword from the Snow White fixture should parse completely."""
        hw = Hexword.model_validate(snow_white_dict)
        assert hw.title == "Hello World!"
        assert hw.author == "Tweedle Dee and Tweedle Dum"
        assert hw.editor == "Barney McFly"
        assert hw.instructions is not None
        assert "BOLD" in hw.instructions
        assert hw.solution is not None
        assert len(hw.clue_groups) == 2
        assert hw.clue_groups[0].name == "Across"
        assert hw.clue_groups[1].name == "Down"
        assert len(hw.clue_groups[0].clues) == 15
        assert len(hw.clue_groups[1].clues) == 20
        assert len(hw.unclued) == 9
        assert "BASHFUL" in hw.unclued
        assert "SNOW" in hw.unclued

    def test_ignores_unknown_fields(self):
        """Hexword should silently ignore unknown fields (forward-compat)."""
        hw = Hexword(title="Test", future_field="whatever")
        assert hw.title == "Test"
        assert not hasattr(hw, "future_field")


class TestGrid:
    """Grid model tests."""

    def test_empty_grid(self):
        """An empty Grid should have all-empty defaults."""
        g = Grid()
        assert g.rows == []
        assert g.columns == []
        assert g.style == []
        assert g.styles == {}
        assert g.solution_rows == []
        assert g.entry_rows == []

    def test_grid_from_fixture(self, snow_white_dict: dict):
        """Grid from Snow White should have 12 rows and 12 columns."""
        g = Grid.model_validate(snow_white_dict["grid"])
        assert len(g.rows) == 12
        assert len(g.columns) == 12
        assert g.rows[0] == "FRENCHBED|DOS"
        assert g.columns[0] == "FLABBY|GROUND"

    def test_grid_rejects_unknown_fields(self):
        """Grid should reject unknown fields (strict)."""
        with pytest.raises(ValidationError):
            Grid(rows=[], bogus_field="nope")


class TestGridStyle:
    """GridStyle model tests."""

    def test_background_color_alias(self):
        """GridStyle should accept 'background-color' as alias."""
        gs = GridStyle.model_validate({"background-color": "lightgrey"})
        assert gs.background_color == "lightgrey"

    def test_background_color_python_name(self):
        """GridStyle should also accept 'background_color' directly."""
        gs = GridStyle(background_color="lightgrey")
        assert gs.background_color == "lightgrey"

    def test_shape_literals(self):
        """GridStyle shape must be one of the allowed literals."""
        gs = GridStyle(shape="circle")
        assert gs.shape == "circle"

        gs = GridStyle(shape="shadesquare")
        assert gs.shape == "shadesquare"

        gs = GridStyle(shape="x")
        assert gs.shape == "x"

    def test_shape_rejects_invalid(self):
        """GridStyle rejects unknown shape values."""
        with pytest.raises(ValidationError):
            GridStyle(shape="triangle")

    def test_rejects_unknown_fields(self):
        """GridStyle should reject unknown fields (strict)."""
        with pytest.raises(ValidationError):
            GridStyle(background_color="grey", opacity=0.5)

    def test_all_observed_production_styles(self):
        """All observed production style dicts should parse successfully."""
        production_styles = [
            {"background-color": "lightgrey"},
            {"background-color": "lightgreen"},
            {"background-color": "lightgreen", "shape": "shadesquare"},
            {"background-color": "lightblue"},
            {"background-color": "#DCCDE1"},
            {"fill": "lightblue", "shape": "circle"},
            {"shape": "circle"},
            {"shape": "circle", "stroke": "grey"},
            {"background-color": "#D9EEFA"},
            {"shape": "x", "stroke": "grey"},
        ]
        for style_dict in production_styles:
            gs = GridStyle.model_validate(style_dict)
            assert gs is not None


class TestClueGroupSettings:
    """ClueGroupSettings model tests."""

    def test_defaults(self):
        """Default settings should be sensible."""
        s = ClueGroupSettings()
        assert s.reverse_grid_entries is False
        assert s.show_enumerations == ""
        assert s.show_grid_entries is True
        assert s.show_grid_labels is True

    def test_enumeration_modes(self):
        """Various enumeration modes should be accepted."""
        s = ClueGroupSettings(show_enumerations="answers")
        assert s.show_enumerations == "answers"

        s = ClueGroupSettings(show_enumerations="entries")
        assert s.show_enumerations == "entries"


class TestClue:
    """Clue model tests."""

    def test_simple_clue(self):
        """A simple structured clue should work."""
        c = Clue(
            name="1",
            clue_text="Sort of lily branch holding up halfway",
            answers=["ARUM"],
            annotations=["AR(U)M"],
        )
        assert c.name == "1"
        assert c.clue_text == "Sort of lily branch holding up halfway"
        assert c.answers == ["ARUM"]
        assert c.annotations == ["AR(U)M"]
        assert c.entries == []
        assert c.suffix is None
        assert c.label is None
        assert c.starred is False

    def test_clue_with_entries(self):
        """A clue with entries distinct from answers."""
        c = Clue(
            name="a",
            clue_text="Weapon shot in a rug",
            answers=["AIR GUN"],
            entries=["AIRGUN"],
            annotations=["AIR GUN (anag.)"],
        )
        assert c.answers == ["AIR GUN"]
        assert c.entries == ["AIRGUN"]

    def test_starred_clue(self):
        """A starred/thematic clue."""
        c = Clue(name="1", clue_text="Test", starred=True)
        assert c.starred is True

    def test_clue_rejects_unknown_fields(self):
        """Clue should reject unknown fields (strict)."""
        with pytest.raises(ValidationError):
            Clue(name="1", clue_text="Test", bogus="nope")


class TestClueGroup:
    """ClueGroup model tests."""

    def test_with_structured_clues(self):
        """A ClueGroup with structured Clue objects."""
        group = ClueGroup(
            name="Across",
            clues=[
                Clue(name="1", clue_text="Test clue", answers=["ANS"], annotations=["SOL"]),
            ],
        )
        assert group.name == "Across"
        assert len(group.clues) == 1
        assert group.clues[0].name == "1"
        assert group.settings == ClueGroupSettings()

    def test_all_observed_group_names(self):
        """All 17 observed production group names should work."""
        names = [
            "Across",
            "Down",
            "Clues",
            "Grades",
            "Marginal",
            "Misprints",
            "O's",
            "Outsiders",
            "Pairs",
            "Projectors",
            "Sixes and Sevens",
            "Students",
            "Word Square",
            "Wrapped & Unwrapped",
            "X's",
        ]
        for name in names:
            group = ClueGroup(name=name)
            assert group.name == name


class TestPuzzleSettings:
    """PuzzleSettings model tests."""

    def test_defaults(self):
        """Default settings should match spec."""
        s = PuzzleSettings()
        assert s.status == ""
        assert s.clue_columns == 2
        assert s.show_grid_border is True
        assert s.show_grid_lines is True
        assert s.show_starred_entries_in_grid is False

    def test_published_status(self):
        """Status 'published' should be accepted."""
        s = PuzzleSettings(status="published")
        assert s.status == "published"
