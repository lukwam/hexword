"""Round-trip tests — dict → Hexword → dict fidelity."""

from hexword.models import Hexword
from hexword.service import HexwordService


class TestRoundTrip:
    """Verify that from_dict → to_dict produces stable output."""

    def test_fixture_round_trip(self, snow_white_dict: dict):
        """The Snow White fixture should survive a dict round-trip."""
        service = HexwordService()

        # Parse → serialize → re-parse
        hw1 = service.from_dict(snow_white_dict)
        d1 = service.to_dict(hw1)
        hw2 = service.from_dict(d1)
        d2 = service.to_dict(hw2)

        # The two serialized dicts should be identical
        assert d1 == d2

    def test_clue_objects_survive_roundtrip(self):
        """Structured Clue objects should survive dict round-trip with all fields."""
        service = HexwordService()

        data = {
            "title": "Test Puzzle",
            "clue_groups": [
                {
                    "name": "Across",
                    "clues": [
                        {
                            "name": "1",
                            "clue_text": "Test clue",
                            "answers": ["ANSWER"],
                            "annotations": ["ANNOTATION"],
                            "entries": ["ENTRY"],
                            "suffix": "b",
                            "label": "16",
                            "label_index": 2,
                            "starred": True,
                        },
                    ],
                    "settings": {
                        "show_enumerations": "answers",
                        "show_grid_entries": True,
                        "show_grid_labels": True,
                        "reverse_grid_entries": False,
                    },
                },
            ],
        }

        hw = service.from_dict(data)
        d = service.to_dict(hw)
        hw2 = service.from_dict(d)

        clue = hw2.clue_groups[0].clues[0]
        assert clue.name == "1"
        assert clue.clue_text == "Test clue"
        assert clue.answers == ["ANSWER"]
        assert clue.annotations == ["ANNOTATION"]
        assert clue.entries == ["ENTRY"]
        assert clue.suffix == "b"
        assert clue.label == "16"
        assert clue.label_index == 2
        assert clue.starred is True

    def test_grid_style_alias_roundtrip(self):
        """background-color alias should survive a round-trip."""
        service = HexwordService()

        data = {
            "title": "Style Test",
            "grid": {
                "styles": {
                    "#": {"background-color": "lightgrey"},
                    "O": {"shape": "circle", "stroke": "grey"},
                },
            },
        }

        hw = service.from_dict(data)
        d = service.to_dict(hw)

        assert d["grid"]["styles"]["#"]["background-color"] == "lightgrey"
        assert d["grid"]["styles"]["O"]["shape"] == "circle"
        assert d["grid"]["styles"]["O"]["stroke"] == "grey"

    def test_empty_lists_preserved(self):
        """Empty lists should be preserved, not dropped."""
        service = HexwordService()

        data = {
            "title": "Empty Lists",
            "clue_groups": [],
            "unclued": [],
        }

        hw = service.from_dict(data)
        d = service.to_dict(hw)

        assert d["clue_groups"] == []
        assert d["unclued"] == []

    def test_minimal_puzzle_roundtrip(self):
        """A puzzle with only a title should round-trip cleanly."""
        service = HexwordService()

        hw = Hexword(title="Minimal")
        d = service.to_dict(hw)
        hw2 = service.from_dict(d)

        assert hw2.title == "Minimal"
        assert hw2.author == ""
        assert hw2.clue_groups == []
        assert hw2.unclued == []
