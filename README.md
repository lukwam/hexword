# hexword

A data format library for cryptic crossword puzzles.

Pure Pydantic models for representing cryptic crossword grids, clues, and
settings — with no framework, database, or application dependencies.

## Installation

```bash
# From PyPI (coming soon)
pip install hexword

# From GitHub
pip install git+https://github.com/lukwam/cryptic.git
```

## Quick Start

```python
from hexword import Hexword, HexwordService

service = HexwordService()

# Parse a puzzle from a dict (e.g., from Firestore, YAML, or JSON)
data = {
    "title": "Shady Doings",
    "author": "Emily Cox & Henry Rathvon",
    "clue_groups": [
        {
            "name": "Across",
            "clues": [
                {
                    "name": "1",
                    "clue_text": "Sort of lily branch holding up halfway",
                    "answers": ["ARUM"],
                    "annotations": ["AR(U)M"],
                },
            ],
        },
    ],
    "grid": {
        "rows": ["ARUM|FIREANTS"],
        "columns": ["APISH|AEROBIC"],
    },
}

puzzle = service.from_dict(data)

# Access structured data
print(puzzle.title)                          # "Shady Doings"
print(puzzle.clue_groups[0].clues[0].name)   # "1"
print(puzzle.grid.rows[0])                   # "ARUM|FIREANTS"

# Serialize back to a dict (Firestore-compatible)
d = service.to_dict(puzzle)
```

## Text Format

The library supports import/export of clues in a tilde-delimited text
format, useful for YAML files and human-readable representations:

```python
from hexword import HexwordService

service = HexwordService()

# Parse a tilde-delimited clue string
clue = service.parse_clue("1. Sort of lily branch ~ ARUM ~ AR(U)M")
print(clue.name)       # "1"
print(clue.answers)    # ["ARUM"]

# Serialize back to text
text = service.clue_to_string(clue)
print(text)            # "1. Sort of lily branch ~ ARUM ~ AR(U)M"

# Compute enumerations
print(HexwordService.get_enumeration("AIR GUN"))   # "3,3"
print(HexwordService.get_enumeration("SELF-MADE"))  # "4-4"
```

## Models

| Model | Purpose |
| --- | --- |
| `Hexword` | Top-level puzzle content: title, author, clues, grid, settings |
| `Grid` | Grid structure: rows, columns, style masks, visual style definitions |
| `GridStyle` | Visual properties for a style marker (color, shape, fill, stroke) |
| `ClueGroup` | Named group of clues (Across, Down, or creative variant names) |
| `ClueGroupSettings` | Per-group display settings (enumerations, grid entries, labels) |
| `Clue` | Structured clue: label, clue text, answers, entries, annotations |
| `PuzzleSettings` | Puzzle-level display settings (columns, borders, bars, lines) |

## Architecture

```text
hexword/
├── __init__.py       # Public API with lazy imports
├── models.py         # Pydantic models (data only, no I/O)
├── service.py        # Business logic (serialization, parsing)
└── exceptions.py     # Domain exceptions
```

Following the models/services pattern:

- **Models** are data-only — validation is OK, no I/O or business logic
- **Service** handles all transformation: dict serialization, text format
  parsing, enumeration computation

## Cross-Format Support

The hexword format maps cleanly to standard crossword interchange formats:

| Field | hexword | iPuz | JPZ/XML | XD |
| --- | --- | --- | --- | --- |
| Title | `title` | `title` | `<title>` | `Title:` |
| Author | `author` | `author` | `<author>` | `Author:` |
| Editor | `editor` | `editor` | `<editor>` | `Editor:` |
| Instructions | `instructions` | `intro` | `<description>` | — |
| Solution | `solution` | `explanation` | — | — |

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest -v

# Lint
poetry run ruff check src/ tests/
```

## License

MIT

## Related

- [hex](https://github.com/lukwam/hex) — Management site for the Cox &
  Rathvon puzzle archive (consumer of this library)
- [hexgrids](https://github.com/lukwam/hexgrids) — Interactive grid editor
  for cryptic crosswords
- [iPuz](http://ipuz.org) — Open puzzle interchange format
- [XD Format](https://github.com/century-arcade/xd) — Text-based crossword format
