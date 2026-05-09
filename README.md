# cryptic

A Python library for working with cryptic crossword puzzles — parsing, modeling, rendering (SVG), and storing puzzle data.

## Background

This library evolved through several iterations:

1. **`variety` repo (prototype)** — The original workspace (`lukwam/variety`) for developing cryptic crossword tools. It contained an early prototype using the `crossword` PyPI package as a base class, along with a `puzzle/` sub-package that was a more complete standalone implementation.

2. **`hex` repo (embedded)** — The puzzle modeling code was pulled into the [Hex](https://github.com/lukwam/hex) web application (a CoxRathvon cryptic crossword archive app), where it gained Firestore integration, Pydantic data models, richer SVG rendering, and a text parser.

3. **`cryptic` repo (current — this repo)** — Extracted from `hex` as a standalone library. This is the **canonical home** for all cryptic crossword library development going forward.

The `variety` repo is considered **superseded** by this repo.

## Current State

This repo contains the code as extracted from the `hex` repo. It is functional but tightly coupled to the Hex app's data layer (Firestore, Flask forms). The plan is to **rewrite the library** with a clean API that can be used independently or integrated into applications like Hex.

### Modules

| Module | Description |
|---|---|
| `puzzle.py` | Core `Puzzle` class — metadata, grid, clues, SVG export, Firestore serialization |
| `grid.py` | `Grid` class — row/column/style parsing, cell matrix construction, entry detection |
| `cell.py` | `Cell` class — value parsing, bar detection, style resolution, conflict checking |
| `clues.py` | `Clue`, `ClueGroup`, `ClueGroups` — clue parsing, enumeration, Firestore round-tripping |
| `svg.py` | `SVG` class — full puzzle rendering (bars, borders, circles, shading, numbers) |
| `schema.py` | Pydantic models for the Hex API (Book, Puzzle, Hexgrid, Grid, User, etc.) |
| `parser.py` | Text format parser — converts plain text puzzle descriptions into Puzzle objects |
| `verify.py` | Quick verification script (needs cleanup) |

## Related Projects

- **[hex](https://github.com/lukwam/hex)** — CoxRathvon cryptic crossword archive web app (consumer of this library)
- **[variety](https://github.com/lukwam/variety)** — Original prototype workspace (superseded by this repo)

## License

MIT
