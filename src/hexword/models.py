"""Hexword Pydantic models.

Pure data models for the cryptic crossword puzzle format.
No I/O, no business logic — validation only.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GridStyle(BaseModel):
    """Visual properties for a style marker character.

    Maps a single-character marker in the grid's style mask
    (e.g., '#', 'O', 'X') to visual rendering properties.

    Examples from production:
        {"#": {"background-color": "lightgrey"}}
        {"O": {"shape": "circle", "stroke": "grey"}}
    """

    background_color: str | None = Field(
        default=None,
        alias="background-color",
        description="CSS background color (e.g., 'lightgrey', '#DCCDE1').",
    )
    fill: str | None = Field(
        default=None,
        description="SVG fill color (e.g., 'lightblue').",
    )
    shape: Literal["circle", "shadesquare", "x"] | None = Field(
        default=None,
        description="Cell shape overlay.",
    )
    stroke: str | None = Field(
        default=None,
        description="SVG stroke color (e.g., 'grey').",
    )

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )


class Grid(BaseModel):
    """The puzzle grid structure.

    Rows and columns are lists of strings, one per row/column.
    Each string contains pipe-delimited answer words:
        "ARUM|FIREANTS"       → Two words in this row
        "PATOIS|O|AVAIL"      → Three entries (incl. single letter)

    The total character count (excluding pipes) equals the grid
    width (for rows) or height (for columns).
    """

    # Core grid data
    rows: list[str] = Field(
        default_factory=list,
        description="Pipe-delimited answer strings, one per row.",
    )
    columns: list[str] = Field(
        default_factory=list,
        description="Pipe-delimited answer strings, one per column.",
    )
    style: list[str] = Field(
        default_factory=list,
        description="Style mask strings, one per row. Characters map to 'styles' dict.",
    )

    # Solution overlay (rarely used)
    solution_rows: list[str] = Field(default_factory=list)
    solution_columns: list[str] = Field(default_factory=list)
    solution_style: list[str] = Field(default_factory=list)

    # Entry overlay (for special puzzle types)
    entry_rows: list[str] = Field(default_factory=list)
    entry_columns: list[str] = Field(default_factory=list)

    # Style definitions — maps style mask characters to visual properties
    styles: dict[str, GridStyle] = Field(
        default_factory=dict,
        description="Map of style marker characters to their visual properties.",
    )

    model_config = ConfigDict(extra="ignore")


class ClueGroupSettings(BaseModel):
    """Per-group display settings.

    Controls how clues in this group are rendered and
    how their entries interact with the grid.
    """

    reverse_grid_entries: bool = Field(
        default=False,
        description="Whether grid entries for this group read backwards.",
    )
    show_enumerations: str = Field(
        default="",
        description="Enumeration source: 'answers', 'entries', or '' for none.",
    )
    show_grid_entries: bool = Field(
        default=True,
        description="Whether clues in this group map to grid entries.",
    )
    show_grid_labels: bool = Field(
        default=True,
        description="Whether to number the starting cell in the grid.",
    )

    model_config = ConfigDict(extra="ignore")


class Clue(BaseModel):
    """A single crossword clue with structured fields.

    Stored as a structured object in Firestore. Can be serialized
    to/from the tilde-delimited text format via HexwordService.

    Text format example:
        "1. Sort of lily branch holding up halfway ~ ARUM ~ AR(U)M"
    """

    name: str = Field(
        description="Clue label/number (e.g., '1', 'a', '12').",
    )
    clue_text: str = Field(
        description="The clue text presented to the solver.",
    )
    answers: list[str] = Field(
        default_factory=list,
        description="Answer word(s) (e.g., ['ARUM'], ['AIR GUN']).",
    )
    annotations: list[str] = Field(
        default_factory=list,
        description="Solution annotations/explanations (e.g., ['AR(U)M']).",
    )
    entries: list[str] = Field(
        default_factory=list,
        description="Grid entries if different from answers (e.g., ['AIRGUN'] for answer 'AIR GUN').",
    )
    suffix: str | None = Field(
        default=None,
        description="Clue name suffix for sub-clues (e.g., 'b' from '1|b.').",
    )
    label: str | None = Field(
        default=None,
        description="Grid label override (e.g., '16' from 'a;16.').",
    )
    label_index: int = Field(
        default=0,
        description="Which cell in the entry to label (usually 0).",
    )
    starred: bool = Field(
        default=False,
        description="Whether this is a starred/thematic clue.",
    )

    model_config = ConfigDict(extra="ignore")


class ClueGroup(BaseModel):
    """A named group of clues (e.g., Across, Down, or a custom group).

    Group names are NOT limited to 'Across'/'Down' — variety
    puzzles use creative names like 'Marginal', 'Projectors',
    'Sixes and Sevens', etc.

    Observed group names from production:
        Across, Down, Clues, Grades, Marginal, Misprints,
        O's, Outsiders, Pairs, Projectors, Sixes and Sevens,
        Students, Word Square, Wrapped & Unwrapped, X's
    """

    name: str = Field(description="Group heading name.")
    clues: list[Clue] = Field(
        default_factory=list,
        description="Structured clue objects.",
    )
    settings: ClueGroupSettings = Field(
        default_factory=ClueGroupSettings,
        description="Display settings for this clue group.",
    )

    model_config = ConfigDict(extra="ignore")


class PuzzleSettings(BaseModel):
    """Puzzle-level display and rendering settings."""

    status: str = Field(
        default="",
        description="Publication status: 'published', 'draft', or ''.",
    )
    clue_columns: int = Field(
        default=2,
        description="Number of columns for clue layout (2 or 3).",
    )
    show_enumerations: str = Field(
        default="",
        description="Global enumeration display: 'answers' or ''.",
    )
    show_grid_bars: str = Field(
        default="",
        description="Bar display: 'all', 'solution', or ''.",
    )
    show_grid_border: bool = Field(
        default=True,
        description="Whether to show the outer grid border.",
    )
    show_grid_entries: bool = Field(
        default=True,
        description="Whether to show entry letters in the grid.",
    )
    show_grid_labels: bool = Field(
        default=True,
        description="Whether to show clue numbers in the grid.",
    )
    show_grid_lines: bool = Field(
        default=True,
        description="Whether to show internal grid lines.",
    )
    show_starred_entries_in_grid: bool = Field(
        default=False,
        description="Whether starred clue entries are highlighted in the grid.",
    )

    model_config = ConfigDict(extra="ignore")


class Hexword(BaseModel):
    """A complete cryptic crossword puzzle — the portable content model.

    This is the core data format for representing cryptic crossword
    puzzles. It captures the puzzle content (grid, clues, instructions)
    independent of any specific application or database.

    Hex-specific catalog metadata (id, date, publication, issue, books,
    links, files) lives in the consuming application's model, not here.
    """

    title: str = Field(description="Puzzle title (e.g., 'Shady Doings').")
    author: str = Field(
        default="",
        description="Puzzle constructor(s) (e.g., 'Emily Cox & Henry Rathvon').",
    )
    editor: str | None = Field(
        default=None,
        description="Puzzle editor, if any. Standard field across iPuz, JPZ, and XD formats.",
    )
    instructions: str | None = Field(
        default=None,
        description="Puzzle instructions for the solver. May contain HTML.",
    )
    solution: str | None = Field(
        default=None,
        description="Solution description text.",
    )
    clue_groups: list[ClueGroup] = Field(
        default_factory=list,
        description="Ordered list of clue groups (usually 2+: Across/Down or creative names).",
    )
    grid: Grid = Field(
        default_factory=Grid,
        description="Grid structure, cell data, and style definitions.",
    )
    settings: PuzzleSettings = Field(
        default_factory=PuzzleSettings,
        description="Puzzle-level display and rendering settings.",
    )
    unclued: list[str] = Field(
        default_factory=list,
        description="Unclued grid entries (e.g., thematic words the solver must discover).",
    )

    model_config = ConfigDict(extra="ignore")
