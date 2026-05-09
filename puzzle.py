"""Puzzle class file."""

import datetime
import json

from .clues import ClueGroups
from .grid import Grid
from .svg import SVG


class PuzzleSettings(dict):
    """Puzzle settings class."""

    def __init__(self, settings):
        """Initialize puzzle settings."""
        super().__init__(settings)


class Puzzle(dict):
    """Puzzle class."""

    # pylint: disable-next=dangerous-default-value
    def __init__(self, puzzle=None):
        """Initialize puzzle."""
        if puzzle is None:
            puzzle = {}
        super().__init__(puzzle)
        self["id"] = puzzle.get("id")
        self["date"] = puzzle.get("date")
        self["title"] = puzzle.get("title")

        self["author"] = puzzle.get("author")
        self["editor"] = puzzle.get("editor")

        # publication data
        self["issue"] = puzzle.get("issue")
        self["number"] = puzzle.get("number")
        self["publication"] = puzzle.get("publication")

        # puzzle html string data
        self["instructions"] = puzzle.get("instructions")
        self["solution"] = puzzle.get("solution")

        # puzzle objects
        self["clue_groups"] = ClueGroups(puzzle.get("clue_groups", []))
        self["grid"] = Grid(puzzle.get("grid", {}))
        self["settings"] = PuzzleSettings(puzzle.get("settings", {}))
        self["unclued"] = puzzle.get("unclued", [])

        self.errors = []

        # check for errors
        if not self["instructions"]:
            self.errors.append("Missing puzzle instructions.")
        if not self["settings"].get("status"):
            self.errors.append("Missing puzzle status.")

    @property
    def height(self):
        """Return the height of the puzzle."""
        return self["grid"].height

    @property
    def width(self):
        """Return the width of the puzzle."""
        return self["grid"].width

    def entries(self):
        """Return a dict of entries for this puzzle."""
        clue_entries = self["clue_groups"].entries()
        grid_entries = self["grid"].entries()
        data = {
            "clues": clue_entries,
            "grid": grid_entries,
        }
        return data

    def link_clues_to_grid(self):
        """Link clues to grid."""
        entries = self.entries()

        extra_clue_entries = []
        extra_grid_entries = []

        for word in entries["clues"]:
            if word == "ANS":
                self.errors.append("Answers need updating.")
            if word not in entries["grid"]:
                if word not in self["unclued"]:
                    extra_clue_entries.append(word)
                continue

            clues = entries["clues"][word]
            if len(clues) > 1:
                self.errors.append(f"Multiple clue entries match grid entry: {word}")
                print(clues)
            else:
                clue = clues[0]
                clue["grid_entry"] = entries["grid"][word][0]
                # get cells for this grid entry
                cells = []
                start_x, start_y = clue["grid_entry"]["start"]
                end_x, end_y = clue["grid_entry"]["end"]
                for y in range(start_y, end_y + 1):
                    for x in range(start_x, end_x + 1):
                        cells.append([y, x])
                if "cells" not in clue:
                    clue["cells"] = []
                clue["cells"].extend(cells)

        for word in entries["grid"]:
            if word not in entries["clues"]:
                if word not in self["unclued"]:
                    extra_grid_entries.append(word)
                continue
            e = entries["grid"][word]
            if len(e) > 1:
                self.errors.append(f"Multiple grid entries match clue entry: {word}")
                print(e)
            else:
                y, x = e[0]["start"]
                clue = entries["clues"][word][0]
                # get clue direction (across/down)
                direction = e[0]["direction"]
                # get the label index (which cell in the clue to label, usually 0)
                try:
                    label_index = clue["label_index"]
                    if direction == "across":
                        cell = self["grid"]["cells"][y][x + label_index]
                    else:
                        cell = self["grid"]["cells"][y + label_index][x]
                    if clue.clue_group["settings"].get("show_grid_labels"):
                        cell["label"] = clue.label()
                except Exception as e:
                    self.errors.append(f"Failed to label grid entry: {word}: {e}")

        if extra_clue_entries:
            self.errors.append(f"Extra Clue Entries: {extra_clue_entries}")
        if extra_grid_entries:
            self.errors.append(f"Extra Grid Entries: {extra_grid_entries}")

    def fix_firestore(self, puzzle):
        """Fix firestore data."""
        # clue groups
        clue_groups = []
        for clue_group in puzzle["clue_groups"]:
            new_group = {
                "clues": clue_group["clues"],
                "name": clue_group["name"],
                "settings": {},
            }
            for key in clue_group:
                if key in ["clues", "name"]:
                    continue
                new_group["settings"][key] = clue_group[key]
            clue_groups.append(new_group)
        puzzle["clue_groups"] = clue_groups

        # fix grid
        puzzle_style = puzzle["grid"].get("style", [])
        if puzzle_style == [""]:
            puzzle_style = []
        solution_rows = puzzle["grid"].get("solution_rows", [])
        if solution_rows in [puzzle["grid"]["rows"], [""]]:
            solution_rows = []
        solution_columns = puzzle["grid"].get("solution_columns", [])
        if solution_columns in [puzzle["grid"]["columns"], [""]]:
            solution_columns = []
        solution_style = puzzle["grid"].get("solution_style", [])
        if solution_style in [puzzle["grid"]["style"], [""]]:
            solution_style = []
        entry_rows = puzzle["grid"].get("entry_rows", [])
        if entry_rows in [puzzle["grid"]["rows"], [""]]:
            entry_rows = []
        entry_columns = puzzle["grid"].get("entry_columns", [])
        if entry_columns in [puzzle["grid"]["columns"], [""]]:
            entry_columns = []

        grid = {
            "rows": puzzle["grid"]["rows"],
            "columns": puzzle["grid"]["columns"],
            "style": puzzle_style,
            "solution_rows": solution_rows,
            "solution_columns": solution_columns,
            "solution_style": solution_style,
            "entry_rows": entry_rows,
            "entry_columns": entry_columns,
            "styles": puzzle["grid"]["styles"],
        }

        puzzle["grid"] = grid

        return puzzle

    def from_firestore(self, puzzle):
        """Load a puzzle from a firestore document."""
        return Puzzle(dict(puzzle))

    def from_request(self, request):
        """Load a puzzle from a flask form request."""
        # get puzzle data
        author = request.form.get("author")
        date = request.form.get("date")
        editor = request.form.get("editor")
        instructions = request.form.get("instructions")
        issue = request.form.get("issue")
        number = request.form.get("number")
        publication = request.form.get("publication")
        solution = request.form.get("solution")
        title = request.form.get("title")
        unclued = request.form.get("unclued").split("\r\n")

        # get clue groups
        clue_group_name = request.form.getlist("clue_group_name")
        clue_group_clues = request.form.getlist("clue_group_clues")

        # get grid data
        rows = request.form.get("rows").strip().split("\r\n")
        columns = request.form.get("columns").strip().split("\r\n")
        style = request.form.get("style").strip().split("\r\n")

        solution_rows = request.form.get("solution-rows").strip().split("\r\n")
        solution_columns = request.form.get("solution-columns").strip().split("\r\n")
        solution_style = request.form.get("solution-style").strip().split("\r\n")

        entry_rows = request.form.get("entry-rows").strip().split("\r\n")
        entry_columns = request.form.get("entry-columns").strip().split("\r\n")
        styles = request.form.get("styles").strip()

        # create clue_groups
        clue_groups = []
        for i, name in enumerate(clue_group_name):
            clues = clue_group_clues[i].split("\r\n") if clue_group_clues[i] else []

            reverse_grid_entries = request.form.get(f"clue-group-{i + 1}-reverse-grid-entries")
            show_enumerations = request.form.get(f"clue-group-{i + 1}-show-enumerations")
            show_grid_entries = request.form.get(f"clue-group-{i + 1}-show-grid-entries")
            show_grid_labels = request.form.get(f"clue-group-{i + 1}-show-grid-labels")

            group_settings = {
                "reverse_grid_entries": reverse_grid_entries == "true",
                "show_enumerations": show_enumerations,
                "show_grid_entries": show_grid_entries == "true",
                "show_grid_labels": show_grid_labels == "true",
            }
            if not name and not clues:
                continue
            if not name:
                name = "Clue Group " + str(i + 1)
            clue_groups.append(
                {
                    "name": name,
                    "clues": clues,
                    "settings": group_settings,
                }
            )

        # create grid
        grid = {
            "rows": rows if rows != [""] else [],
            "columns": columns if columns != [""] else [],
            "style": style if style != [""] else [],
            "solution_rows": solution_rows if solution_rows != [""] else [],
            "solution_columns": solution_columns if solution_columns != [""] else [],
            "solution_style": solution_style if solution_style != [""] else [],
            "entry_rows": entry_rows if entry_rows != [""] else [],
            "entry_columns": entry_columns if entry_columns != [""] else [],
            "styles": json.loads(styles) if styles else {},
        }

        settings = {
            "clue_columns": request.form.get("clue_columns"),
            "show_enumerations": request.form.get("show_enumerations") == "true",
            "show_grid_bars": request.form.get("show_grid_bars") == "true",
            "show_grid_border": request.form.get("show_grid_border") == "true",
            "show_grid_entries": request.form.get("show_grid_entries") == "true",
            "show_grid_labels": request.form.get("show_grid_labels") == "true",
            "show_grid_lines": request.form.get("show_grid_lines") == "true",
            "status": request.form.get("status"),
        }

        data = {
            "title": title,
            "author": author,
            "editor": editor,
            "date": date,
            "publication": publication,
            "issue": issue,
            "number": number,
            "instructions": instructions,
            "solution": solution,
            "clue_groups": clue_groups,
            "grid": grid,
            "settings": settings,
            "unclued": unclued,
        }

        return data

    def to_firestore(self):
        """Convert puzzle to firestore data."""
        data = dict(self)

        # convert clue groups to firestore data
        data["clue_groups"] = data["clue_groups"].to_firestore()
        data["grid"] = data["grid"].to_firestore()

        return data

    def to_svg(self, gridtype="puzzle"):
        """Convert puzzle to svg format."""
        if self["clue_groups"]:
            try:
                self.link_clues_to_grid()
            except Exception as e:
                print(e)

        svg = SVG(self, gridtype=gridtype)
        puzzle = dict(self)
        svg = {
            "size": 50,
            "width": self.width,
            "height": self.height,
            "blanks": svg.blanks(),
            "squares": svg.squares(),
            "blocks": svg.blocks(),
            "shade_squares": svg.shade_squares(),
            "shade_circles": svg.shade_circles(),
            "circles": svg.circles(),
            "xs": svg.xs(),
            "across_bars": svg.across_bars(),
            "down_bars": svg.down_bars(),
            "barjoincaps": svg.barjoincaps(),
            "borderjoincaps": svg.borderjoincaps(),
            "numbers": svg.numbers(),
            "defaults": svg.defaults(),
            "answers": svg.answers(),
            "borders": svg.borders(),
        }
        puzzle.update(svg)
        return puzzle

    def to_web(self):
        """Convert puzzle to web format."""
        puzzle = dict(self)

        # convert clue groups to firestore style
        puzzle["clue_groups"] = puzzle["clue_groups"].to_firestore()

        puzzle["date"] = datetime.datetime.strptime(puzzle["date"], "%Y-%m-%d")
        puzzle["clues"] = puzzle["clue_groups"]
        del puzzle["clue_groups"]

        puzzle["width"] = self.width
        puzzle["height"] = self.height

        return puzzle
