"""SVG Renderer for Hexword puzzles.

This module provides the defacto implementation for converting a Hexword
puzzle model into a high-quality SVG string. It handles grid parsing,
clue-to-grid linking, and visual rendering of all variety puzzle features.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from hexword.models import Clue, ClueGroup, GridStyle, Hexword


@dataclass
class RenderCell:
    """A single cell in the grid prepared for rendering."""

    x: int
    y: int
    row_value: str = ""
    col_value: str = ""
    solution_row_value: str = ""
    solution_col_value: str = ""

    # State
    is_block: bool = False
    is_blank: bool = False
    is_empty: bool = False

    # Bars (Puzzle)
    right_bar: bool = False
    bottom_bar: bool = False

    # Bars (Solution)
    solution_right_bar: bool = False
    solution_bottom_bar: bool = False

    # Visuals
    label: str | None = None
    style: GridStyle | None = None
    solution_style: GridStyle | None = None

    @property
    def is_playable(self) -> bool:
        """True if the cell is part of the playable grid (not a block or blank)."""
        return not (self.is_block or self.is_blank)


@dataclass
class RenderWord:
    """A word entry in the grid (Across or Down)."""

    text: str
    direction: Literal["across", "down"]
    start_x: int
    start_y: int
    length: int
    cells: list[RenderCell] = field(default_factory=list)


class HexwordRenderer:
    """Renderer for Hexword puzzles to SVG."""

    def __init__(
        self,
        hexword: Hexword,
        size: int = 50,
        show_solution: bool = False,
    ):
        self.hw = hexword
        self.size = size
        self.show_solution = show_solution
        self.grid: list[list[RenderCell]] = []
        self.width = 0
        self.height = 0

        # Constants from legacy renderer for visual consistency
        self.BAR_WIDTH = 4
        self.BORDER_WIDTH = 4
        self.LINE_WIDTH = 0.5
        self.FONT_SIZE = 24
        self.LABEL_FONT_SIZE = 12

        self._initialize_grid()
        self._link_clues()

    def _initialize_grid(self):
        """Parse the Hexword grid into a matrix of RenderCell objects."""
        raw_rows = self.hw.grid.rows
        raw_cols = self.hw.grid.columns

        # Determine dimensions
        # Width is the max number of non-bar tokens in any row
        self.width = 0
        for line in raw_rows:
            self.width = max(self.width, sum(1 for t in self._tokenize_line(line) if t != "|"))
        if not self.width:
            self.width = len(raw_cols)

        # Height is the max number of non-bar tokens in any column
        self.height = 0
        for line in raw_cols:
            self.height = max(self.height, sum(1 for t in self._tokenize_line(line) if t != "|"))
        if not self.height:
            self.height = len(raw_rows)

        # Initialize matrix with calculated dimensions
        self.grid = [[RenderCell(x=x, y=y) for x in range(self.width)] for y in range(self.height)]

        # Parse Puzzle Grid (Rows)
        self._apply_grid_data(raw_rows, "across", "puzzle")
        # Parse Puzzle Grid (Cols)
        self._apply_grid_data(raw_cols, "down", "puzzle")

        # Parse Solution Grid (Rows)
        self._apply_grid_data(self.hw.grid.solution_rows or raw_rows, "across", "solution")
        # Parse Solution Grid (Cols)
        self._apply_grid_data(self.hw.grid.solution_columns or raw_cols, "down", "solution")

        # Apply Styles
        self._apply_styles(self.hw.grid.style, "puzzle")
        self._apply_styles(self.hw.grid.solution_style or self.hw.grid.style, "solution")

    def _tokenize_line(self, line: str) -> list[str]:
        """Tokenize a grid line into characters and rebus entries [WORD]."""
        # Clean line first (remove whitespace, handle bars near underscores/blocks)
        line = line.strip().replace(" ", "")

        tokens = []
        rebus_matches = list(re.finditer(r"\[(.*?)\]", line))
        
        # Simple character-by-character scan, respecting [rebus]
        i = 0
        while i < len(line):
            if line[i] == "[":
                end = line.find("]", i)
                if end != -1:
                    tokens.append(line[i + 1 : end])
                    i = end + 1
                    continue
            tokens.append(line[i])
            i += 1
        return tokens

    def _apply_grid_data(self, lines: list[str], direction: Literal["across", "down"], mode: Literal["puzzle", "solution"]):
        """Apply raw grid strings to the cell matrix."""
        for i, line in enumerate(lines):
            tokens = self._tokenize_line(line)
            
            coord = 0
            for token in tokens:
                if token == "|":
                    # Bar applies to the previous cell
                    if coord > 0:
                        prev_x = coord - 1 if direction == "across" else i
                        prev_y = i if direction == "across" else coord - 1
                        if prev_y < self.height and prev_x < self.width:
                            cell = self.grid[prev_y][prev_x]
                            if mode == "puzzle":
                                if direction == "across": cell.right_bar = True
                                else: cell.bottom_bar = True
                            else:
                                if direction == "across": cell.solution_right_bar = True
                                else: cell.solution_bottom_bar = True
                    continue
                
                # Update cell value
                x = coord if direction == "across" else i
                y = i if direction == "across" else coord
                
                if y < self.height and x < self.width:
                    cell = self.grid[y][x]
                    
                    # Special markers
                    if token == "#": cell.is_block = True
                    elif token == "_": cell.is_blank = True
                    elif token == ".": cell.is_empty = True
                    
                    # Values
                    if mode == "puzzle":
                        if direction == "across": cell.row_value = token
                        else: cell.col_value = token
                    else:
                        if direction == "across": cell.solution_row_value = token
                        else: cell.solution_col_value = token
                
                coord += 1

    def _apply_styles(self, style_lines: list[str], mode: Literal["puzzle", "solution"]):
        """Apply style masks to the cell matrix."""
        for y, line in enumerate(style_lines):
            if y >= self.height: break
            tokens = self._tokenize_line(line)
            for x, char in enumerate(tokens):
                if x >= self.width: break
                if char in self.hw.grid.styles:
                    style_obj = self.hw.grid.styles[char]
                    if mode == "puzzle":
                        self.grid[y][x].style = style_obj
                    else:
                        self.grid[y][x].solution_style = style_obj

    def _link_clues(self):
        """Find grid entries and link them to clue groups for labeling."""
        grid_words = self._find_all_grid_words()
        
        # Build lookup: text -> list of words
        word_lookup: dict[str, list[RenderWord]] = {}
        for w in grid_words:
            if w.text not in word_lookup: word_lookup[w.text] = []
            word_lookup[w.text].append(w)

        # Match clues to words
        for group in self.hw.clue_groups:
            for clue in group.clues:
                # Determine the lookup key (entry if present, else answer)
                # Note: Answers/entries can be pipe-separated
                search_words = clue.entries if clue.entries else clue.answers
                
                for search_word in search_words:
                    if search_word in word_lookup:
                        # Find the matching word in the grid
                        # (Simple matching for now, variety puzzles might need better logic)
                        for grid_word in word_lookup[search_word]:
                            # Apply label to the starting cell (or offset by label_index)
                            label_cell = grid_word.cells[min(clue.label_index, len(grid_word.cells)-1)]
                            
                            # Use label override if present, else clue name
                            label_text = clue.label if clue.label else clue.name
                            if group.settings.show_grid_labels:
                                label_cell.label = label_text

    def _find_all_grid_words(self) -> list[RenderWord]:
        """Discover all playable words in the grid based on bars, blocks, and blanks."""
        words = []
        
        # Across
        for y in range(self.height):
            current_word: list[RenderCell] = []
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell.is_playable:
                    current_word.append(cell)
                    # Word ends if there's a bar or it's the edge
                    if cell.right_bar or x == self.width - 1:
                        if len(current_word) > 1:
                            words.append(RenderWord(
                                text="".join(c.row_value for c in current_word),
                                direction="across",
                                start_x=current_word[0].x,
                                start_y=y,
                                length=len(current_word),
                                cells=list(current_word)
                            ))
                        current_word = []
                else:
                    if len(current_word) > 1:
                        words.append(RenderWord(
                            text="".join(c.row_value for c in current_word),
                            direction="across",
                            start_x=current_word[0].x,
                            start_y=y,
                            length=len(current_word),
                            cells=list(current_word)
                        ))
                    current_word = []

        # Down
        for x in range(self.width):
            current_word = []
            for y in range(self.height):
                cell = self.grid[y][x]
                if cell.is_playable:
                    current_word.append(cell)
                    if cell.bottom_bar or y == self.height - 1:
                        if len(current_word) > 1:
                            words.append(RenderWord(
                                text="".join(c.col_value for c in current_word),
                                direction="down",
                                start_x=x,
                                start_y=current_word[0].y,
                                length=len(current_word),
                                cells=list(current_word)
                            ))
                        current_word = []
                else:
                    if len(current_word) > 1:
                        words.append(RenderWord(
                            text="".join(c.col_value for c in current_word),
                            direction="down",
                            start_x=x,
                            start_y=current_word[0].y,
                            length=len(current_word),
                            cells=list(current_word)
                        ))
                    current_word = []
        return words

    def render(self) -> str:
        """Render the puzzle to an SVG string."""
        view_w = self.width * self.size + (self.BORDER_WIDTH * 2)
        view_h = self.height * self.size + (self.BORDER_WIDTH * 2)

        svg_parts = [
            '<?xml version="1.0" standalone="no"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" id="grid" '
            f'width="100%" height="100%" '
            f'viewBox="0 0 {view_w} {view_h}" fill="white">',
            f'  <title>{self.hw.title}</title>',
            '  <defs>',
            f'    <rect id="svg-block" width="{self.size}" height="{self.size}" fill="black" stroke="black" stroke-width="1px" />',
            f'    <rect id="svg-square" width="{self.size}" height="{self.size}" fill="transparent" '
            f'stroke="black" stroke-width="{self.LINE_WIDTH}px" />',
            '    <circle id="svg-circle" r="21" fill="transparent" stroke-width="4px" />',
            '    <circle id="svg-shadecircle" r="23" />',
            f'    <rect id="svg-barjoincap" width="{self.BAR_WIDTH}" height="{self.BAR_WIDTH}" fill="black" />',
            '  </defs>'
        ]

        # 1. Background / Blocks / Blanks
        svg_parts.append('  <g id="cells">')
        for row in self.grid:
            for cell in row:
                x = cell.x * self.size + self.BORDER_WIDTH
                y = cell.y * self.size + self.BORDER_WIDTH
                
                style = cell.solution_style if self.show_solution and cell.solution_style else cell.style
                
                if cell.is_blank:
                    if style and style.background_color:
                        svg_parts.append(f'    <rect x="{x}" y="{y}" width="{self.size}" height="{self.size}" fill="{style.background_color}" '
                                       f'stroke="black" stroke-width="{self.LINE_WIDTH}px" />')
                    else:
                        continue
                elif cell.is_block:
                    if style and style.background_color:
                        svg_parts.append(f'    <rect x="{x}" y="{y}" width="{self.size}" height="{self.size}" fill="{style.background_color}" '
                                       f'stroke="black" stroke-width="{self.LINE_WIDTH}px" />')
                    else:
                        svg_parts.append(f'    <use xlink:href="#svg-block" x="{x}" y="{y}" />')
                else:
                    # Squares (Shaded or White)
                    fill = "white"
                    if style and style.background_color:
                        fill = style.background_color
                    
                    svg_parts.append(f'    <rect x="{x}" y="{y}" width="{self.size}" height="{self.size}" fill="{fill}" '
                                   f'stroke="black" stroke-width="{self.LINE_WIDTH}px" />')
                    
                    # Shapes (Circles, X)
                    if style:
                        if style.shape == "circle":
                            cx, cy = x + self.size/2, y + self.size/2
                            if style.fill:
                                svg_parts.append(f'    <use xlink:href="#svg-shadecircle" fill="{style.fill}" x="{cx}" y="{cy}" />')
                            if style.stroke:
                                svg_parts.append(f'    <use xlink:href="#svg-circle" stroke="{style.stroke}" x="{cx}" y="{cy}" />')
                        elif style.shape == "x":
                            stroke = style.stroke or "grey"
                            svg_parts.append(f'    <line x1="{x+8}" y1="{y+8}" x2="{x+self.size-8}" y2="{y+self.size-8}" stroke="{stroke}" stroke-width="4px" />')
                            svg_parts.append(f'    <line x1="{x+self.size-8}" y1="{y+8}" x2="{x+8}" y2="{y+self.size-8}" stroke="{stroke}" stroke-width="4px" />')
        svg_parts.append('  </g>')

        # 2. Bars
        svg_parts.append(f'  <g id="bars" stroke="black" stroke-width="{self.BAR_WIDTH}px">')
        for row in self.grid:
            for cell in row:
                x = cell.x * self.size + self.BORDER_WIDTH
                y = cell.y * self.size + self.BORDER_WIDTH
                
                right = cell.solution_right_bar if self.show_solution else cell.right_bar
                bottom = cell.solution_bottom_bar if self.show_solution else cell.bottom_bar
                
                if right:
                    svg_parts.append(f'    <line x1="{x+self.size}" y1="{y}" x2="{x+self.size}" y2="{y+self.size}" />')
                if bottom:
                    svg_parts.append(f'    <line x1="{x}" y1="{y+self.size}" x2="{x+self.size}" y2="{y+self.size}" />')
        svg_parts.append('  </g>')

        # 3. Bar Join Caps
        svg_parts.append('  <g id="barjoincaps">')
        for cap in self._get_barjoincaps():
            cx = cap["x"] * self.size + self.BORDER_WIDTH - self.BAR_WIDTH / 2
            cy = cap["y"] * self.size + self.BORDER_WIDTH - self.BAR_WIDTH / 2
            svg_parts.append(f'    <use xlink:href="#svg-barjoincap" x="{cx}" y="{cy}" />')
        svg_parts.append('  </g>')

        # 4. Labels
        svg_parts.append(f'  <g id="labels" fill="black" font-family="Helvetica, Arial, sans-serif" font-size="{self.LABEL_FONT_SIZE}px">')
        for row in self.grid:
            for cell in row:
                if cell.label:
                    lx = cell.x * self.size + self.BORDER_WIDTH + (self.BAR_WIDTH/2) + 2
                    ly = cell.y * self.size + self.BORDER_WIDTH + self.LABEL_FONT_SIZE
                    svg_parts.append(f'    <text x="{lx}" y="{ly}" style="user-select: none;">{cell.label}</text>')
        svg_parts.append('  </g>')

        # 5. Values (Answers)
        if self.show_solution:
            svg_parts.append(f'  <g id="answers" fill="black" font-family="Helvetica, Arial, sans-serif" font-size="{self.FONT_SIZE}px" text-anchor="middle">')
            for row in self.grid:
                for cell in row:
                    val = cell.solution_row_value or cell.solution_col_value
                    if val and val not in ["#", "_", "."]:
                        vx = cell.x * self.size + self.BORDER_WIDTH + self.size/2
                        vy = cell.y * self.size + self.BORDER_WIDTH + self.size/2 + (self.FONT_SIZE/3)
                        
                        # Handle long values (rebus)
                        fs = self.FONT_SIZE
                        if len(val) > 1: fs = max(12, fs - (len(val) * 2))
                        
                        svg_parts.append(f'    <text x="{vx}" y="{vy}" font-size="{fs}px">{val}</text>')
            svg_parts.append('  </g>')

        # 6. Borders
        if self.hw.settings.show_grid_border:
            svg_parts.append(f'  <g id="borders" stroke="black" stroke-width="{self.BORDER_WIDTH}px">')
            for row in self.grid:
                for cell in row:
                    if not cell.is_playable:
                        continue
                    
                    x = cell.x * self.size + self.BORDER_WIDTH
                    y = cell.y * self.size + self.BORDER_WIDTH
                    
                    # Check neighbors for border lines
                    left = self.grid[cell.y][cell.x-1] if cell.x > 0 else None
                    right = self.grid[cell.y][cell.x+1] if cell.x < self.width - 1 else None
                    top = self.grid[cell.y-1][cell.x] if cell.y > 0 else None
                    bottom = self.grid[cell.y+1][cell.x] if cell.y < self.height - 1 else None
                    
                    if not top or not top.is_playable:
                        svg_parts.append(f'    <line x1="{x}" y1="{y}" x2="{x+self.size}" y2="{y}" />')
                    if not bottom or not bottom.is_playable:
                        svg_parts.append(f'    <line x1="{x}" y1="{y+self.size}" x2="{x+self.size}" y2="{y+self.size}" />')
                    if not left or not left.is_playable:
                        svg_parts.append(f'    <line x1="{x}" y1="{y}" x2="{x}" y2="{y+self.size}" />')
                    if not right or not right.is_playable:
                        svg_parts.append(f'    <line x1="{x+self.size}" y1="{y}" x2="{x+self.size}" y2="{y+self.size}" />')
            svg_parts.append('  </g>')

        # 7. Border Join Caps
        if self.hw.settings.show_grid_border:
            svg_parts.append('  <g id="borderjoincaps">')
            # Same logic as barjoincaps but for borders
            caps = {}
            for y in range(self.height):
                for x in range(self.width):
                    cell = self.grid[y][x]
                    if not cell.is_playable: continue
                    
                    # Top-Left corner
                    left = self.grid[y][x-1] if x > 0 else None
                    top = self.grid[y-1][x] if y > 0 else None
                    if (not left or not left.is_playable) and (not top or not top.is_playable):
                        caps[(y, x)] = (x, y)
                    # Top-Right
                    right = self.grid[y][x+1] if x < self.width-1 else None
                    if (not right or not right.is_playable) and (not top or not top.is_playable):
                        caps[(y, x+1)] = (x+1, y)
                    # Bottom-Left
                    bottom = self.grid[y+1][x] if y < self.height-1 else None
                    if (not left or not left.is_playable) and (not bottom or not bottom.is_playable):
                        caps[(y+1, x)] = (x, y+1)
                    # Bottom-Right
                    if (not right or not right.is_playable) and (not bottom or not bottom.is_playable):
                        caps[(y+1, x+1)] = (x+1, y+1)

            for cx, cy in caps.values():
                px = cx * self.size + self.BORDER_WIDTH - self.BORDER_WIDTH/2
                py = cy * self.size + self.BORDER_WIDTH - self.BORDER_WIDTH/2
                svg_parts.append(f'    <rect width="{self.BORDER_WIDTH}" height="{self.BORDER_WIDTH}" fill="black" x="{px}" y="{py}" />')
            svg_parts.append('  </g>')

        svg_parts.append('</svg>')
        return "\n".join(svg_parts)

    def _get_barjoincaps(self) -> list[dict[str, int]]:
        """Calculate coordinates for bar join caps (corners where bars meet)."""
        caps = {}
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if not cell.is_playable:
                    continue

                # Check neighbors
                left = self.grid[y][x - 1] if x > 0 else None
                top = self.grid[y - 1][x] if y > 0 else None

                # Bar state
                top_bar = top.bottom_bar if top else False
                right_bar = cell.right_bar
                bottom_bar = cell.bottom_bar
                left_bar = left.right_bar if left else False

                # Check corners
                if top_bar and left_bar:
                    caps[(y, x)] = {"x": x, "y": y}
                if top_bar and right_bar:
                    caps[(y, x + 1)] = {"x": x + 1, "y": y}
                if bottom_bar and left_bar:
                    caps[(y + 1, x)] = {"x": x, "y": y + 1}
                if bottom_bar and right_bar:
                    caps[(y + 1, x + 1)] = {"x": x + 1, "y": y + 1}

        return [caps[loc] for loc in sorted(caps)]


def render_svg(hexword: Hexword, show_solution: bool = False, size: int = 50) -> str:
    """Convenience function to render a Hexword to an SVG string."""
    renderer = HexwordRenderer(hexword, size=size, show_solution=show_solution)
    return renderer.render()
