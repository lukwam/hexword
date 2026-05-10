"""Tests for the Hexword SVG renderer."""

import pytest
from hexword.models import Hexword, Grid, ClueGroup, Clue, GridStyle, PuzzleSettings, ClueGroupSettings
from hexword.renderer import HexwordRenderer, render_svg

class TestRenderer:
    """Test suite for the HexwordRenderer."""

    def test_basic_rendering(self):
        """A simple grid should render without errors."""
        hw = Hexword(
            title="Test",
            grid=Grid(
                rows=["|H|E|L|L|O|", "|_|#|_|#|#|", "|W|O|R|L|D|"],
                columns=["|H|_|W|", "|E|#|O|", "|L|_|R|", "|L|#|L|", "|O|#|D|"]
            ),
            clue_groups=[
                ClueGroup(name="Across", clues=[
                    Clue(name="1", clue_text="Greeting", answers=["HELLO"]),
                    Clue(name="3", clue_text="Planet", answers=["WORLD"]),
                ])
            ],
            settings=PuzzleSettings(show_grid_border=True)
        )
        
        svg = render_svg(hw)
        assert "<svg" in svg
        assert "HELLO" not in svg  # Should not be in puzzle view by default
        assert "1" in svg  # Label 1
        assert "3" in svg  # Label 3
        assert 'stroke-width="4px"' in svg  # Bars/Border

    def test_solution_rendering(self):
        """A solution grid should include answers."""
        hw = Hexword(
            title="Test",
            grid=Grid(
                rows=["|H|E|L|L|O|"],
                columns=["|H|", "|E|", "|L|", "|L|", "|O|"]
            ),
            clue_groups=[
                ClueGroup(name="Across", clues=[
                    Clue(name="1", clue_text="Test", answers=["HELLO"])
                ])
            ]
        )
        
        svg = render_svg(hw, show_solution=True)
        assert "HELLO" in svg.replace("\n", "") or ">H<" in svg

    def test_styles_rendering(self):
        """Shaded squares and circles should render."""
        hw = Hexword(
            title="Styles",
            grid=Grid(
                rows=["ABC"],
                style=["#O."],
                styles={
                    "#": GridStyle(background_color="lightgrey"),
                    "O": GridStyle(shape="circle", stroke="grey"),
                    ".": GridStyle(shape="x", stroke="red")
                }
            )
        )
        
        svg = render_svg(hw)
        assert "lightgrey" in svg
        assert 'xlink:href="#svg-circle"' in svg
        assert 'stroke="red"' in svg

    def test_rebus_parsing(self):
        """Rebus entries [WORD] should be parsed as single tokens."""
        hw = Hexword(
            title="Rebus",
            grid=Grid(
                rows=["|A|[REBUS]|C|"],
                columns=["|A|", "|[REBUS]|", "|C|"]
            )
        )
        renderer = HexwordRenderer(hw)
        assert renderer.width == 3
        assert renderer.grid[0][1].row_value == "REBUS"

    def test_word_discovery_with_bars(self):
        """Words should be split by bars."""
        hw = Hexword(
            title="Bars",
            grid=Grid(
                rows=["AB|CD"],  # Two words: AB and CD, separated by a bar
                columns=["|A|", "|B|", "|C|", "|D|"]
            )
        )
        renderer = HexwordRenderer(hw)
        words = renderer._find_all_grid_words()
        across_words = [w for w in words if w.direction == "across"]
        assert len(across_words) == 2
        assert across_words[0].text == "AB"
        assert across_words[1].text == "CD"

    def test_label_offset(self):
        """label_index should affect where the label is placed."""
        hw = Hexword(
            title="Offset",
            grid=Grid(
                rows=["ABCDE"],
                columns=["|A|", "|B|", "|C|", "|D|", "|E|"]
            ),
            clue_groups=[
                ClueGroup(name="Across", clues=[
                    Clue(name="1", clue_text="Test", answers=["ABCDE"], label_index=2)
                ])
            ]
        )
        renderer = HexwordRenderer(hw)
        # Label should be on cell (2, 0)
        assert renderer.grid[0][0].label is None
        assert renderer.grid[0][2].label == "1"

    def test_clue_entry_matching(self):
        """Should match against entries if distinct from answers."""
        hw = Hexword(
            title="Entry Match",
            grid=Grid(
                rows=["AIRGUN"],
                columns=["|A|", "|I|", "|R|", "|G|", "|U|", "|N|"]
            ),
            clue_groups=[
                ClueGroup(name="Across", clues=[
                    Clue(name="1", clue_text="Weapon", answers=["AIR GUN"], entries=["AIRGUN"])
                ])
            ]
        )
        renderer = HexwordRenderer(hw)
        assert renderer.grid[0][0].label == "1"

    def test_no_labels_setting(self):
        """Should respect show_grid_labels setting."""
        hw = Hexword(
            title="No Labels",
            grid=Grid(rows=["ABC"], columns=["|A|", "|B|", "|C|"]),
            clue_groups=[
                ClueGroup(
                    name="Across", 
                    clues=[Clue(name="1", clue_text="Test", answers=["ABC"])],
                    settings=ClueGroupSettings(show_grid_labels=False)
                )
            ]
        )
        renderer = HexwordRenderer(hw)
        assert renderer.grid[0][0].label is None

    def test_non_rectangular_border(self):
        """Should render borders around blanks."""
        hw = Hexword(
            title="L-Shape",
            grid=Grid(
                rows=["AB", "A_"], # L-shaped grid
                columns=["AA", "B_"]
            ),
            settings=PuzzleSettings(show_grid_border=True)
        )
        svg = render_svg(hw)
        # Should have border lines for internal edges
        assert 'id="borders"' in svg
        # Bottom border of cell (0,1) where it meets blank (1,1)
        # x=1, y=0. Bottom edge is at y=54, x from 54 to 104.
        assert 'x1="54" y1="54" x2="104" y2="54"' in svg
