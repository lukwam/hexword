"""Puzzle grid class file."""

import re

from .cell import Cell


class Grid(dict):
    """Grid class."""

    # define special charcters for rows/columns grids
    BLANK = "_"
    BLOCK = "#"
    EMPTY = "."

    # define default styles (if otherwise undefined) for style grids
    # the "_" char can't be used, as it is used to express "no style" for a cell
    STYLES = {
        # shade square
        "#": {"background-color": "lightgrey"},
        # bullet "•"
        ".": {"background-color": "white", "fill": "black", "shape": "bullet"},
        # shade circle
        "@": {"fill": "lightgrey", "shape": "circle"},
        # circle
        "O": {"shape": "circle", "stroke": "grey"},
        # x
        "X": {"shape": "x", "stroke": "grey"},
    }

    def __init__(self, grid):
        """Initialize grid."""
        # super().__init__(grid)

        # get default grid data
        self["rows"] = grid.get("rows") or []
        self["columns"] = grid.get("columns") or []
        self["style"] = grid.get("style") or []

        # get solution grid data
        self["solution_rows"] = grid.get("solution_rows") or self["rows"]
        self["solution_columns"] = grid.get("solution_columns") or self["columns"]
        self["solution_style"] = grid.get("solution_style") or self["style"]

        # get entry grid data and style definitions
        self["entry_rows"] = grid.get("entry_rows") or self["rows"]
        self["entry_columns"] = grid.get("entry_columns") or self["columns"]
        self["styles"] = grid.get("styles") or {}

        # create cells
        cells = self._create_cells()
        self.height, self.width = self._get_dimensions(cells)

        # create empty matrix
        matrix = []
        for _ in range(self.height):
            row = []
            for _ in range(self.width):
                row.append(None)
            matrix.append(row)

        # load in cells
        for cell in cells:
            x = cell["x"]
            y = cell["y"]
            matrix[y][x] = cell

        self["cells"] = matrix

    def _clean_grid_line(self, line):
        """Clean up a single line of grid data."""
        # strip spaces and |'s at beginning/end of lines, remove spaces
        line = line.strip().strip("|").replace(" ", "")
        # fix bars next to blanks
        line = line.replace("|_", "_").replace("_|", "_")
        # fix bars next to blocks
        line = line.replace("|#", "#").replace("#|", "#")
        newline = ""
        for n, char in enumerate(line):
            if char == "|":
                # skip any bars preceded or followed by an underscore
                if "_" in [line[n - 1], line[n + 1]]:
                    continue
                newline += "|"
                continue
            newline += char
        return newline

    def _create_cells(self):
        """Create cells from grid data."""
        puzzle_cells = {}
        self._parse_grid_rows(puzzle_cells, self["rows"])
        self._parse_grid_columns(puzzle_cells, self["columns"])
        self._parse_grid_style(puzzle_cells, self["style"])

        solution_cells = {}
        self._parse_grid_rows(solution_cells, self["solution_rows"])
        self._parse_grid_columns(solution_cells, self["solution_columns"])
        self._parse_grid_style(solution_cells, self["solution_style"])

        entry_cells = {}
        self._parse_grid_rows(entry_cells, self["entry_rows"])
        self._parse_grid_columns(entry_cells, self["entry_columns"])

        merged_cells = self._merge_cells(puzzle_cells, solution_cells, entry_cells)

        cells = []
        for loc in sorted(merged_cells):
            cell = merged_cells[loc]
            cell["x"], cell["y"] = loc
            cells.append(Cell(cell, self))
        return cells

    def _create_matrix(self, lines):
        """Create a matrix from lines."""
        matrix = []
        for line in lines:
            line = self._clean_grid_line(line)
            items = self._parse_rebus_line(line)
            matrix.append(items)
        return matrix

    def _get_dimensions(self, cells):
        """Return the dimensions of the grid."""
        height = 0
        width = 0
        for cell in cells:
            height = max(height, cell["y"] + 1)
            width = max(width, cell["x"] + 1)
        return height, width

    def _merge_cells(self, puzzle_cells, solution_cells, entry_cells):
        """Merge cells."""
        cells = {}

        coordinates = list(set(list(puzzle_cells) + list(solution_cells) + list(entry_cells)))
        for loc in coordinates:
            puz = puzzle_cells.get(loc) or {}
            sol = solution_cells.get(loc) or {}
            ent = entry_cells.get(loc) or {}

            cell = {
                # puzzle data
                "row_value": puz.get("row_value") or False,
                "column_value": puz.get("column_value") or False,
                "right_bar": puz.get("right_bar") or False,
                "bottom_bar": puz.get("bottom_bar") or False,
                "style": puz.get("style") or None,
                # solution data
                "solution_row_value": sol.get("row_value") or False,
                "solution_column_value": sol.get("column_value") or False,
                "solution_right_bar": sol.get("right_bar") or False,
                "solution_bottom_bar": sol.get("bottom_bar") or False,
                "solution_style": sol.get("style") or None,
                # entry data
                "entry_row_value": ent.get("row_value") or False,
                "entry_column_value": ent.get("column_value") or False,
                "entry_right_bar": ent.get("right_bar") or False,
                "entry_bottom_bar": ent.get("bottom_bar") or False,
            }
            cells[loc] = cell

        return cells

    def _parse_grid_columns(self, cells, columns):
        """Parse the columns into cells."""
        columns_matrix = self._create_matrix(columns)
        x = 0
        for col in columns_matrix:
            y = 0
            for item in col:
                if item == "|":
                    loc = (x, y - 1)
                    if loc in cells:
                        cells[loc]["bottom_bar"] = True
                    else:
                        cells[loc] = {"bottom_bar": True}
                else:
                    loc = (x, y)
                    if loc in cells:
                        cells[loc]["column_value"] = item
                    else:
                        cells[loc] = {"column_value": item}
                    y += 1
            x += 1
        return cells

    def _parse_grid_rows(self, cells, rows):
        """Parse the rows into cells."""
        rows_matrix = self._create_matrix(rows)
        y = 0
        for row in rows_matrix:
            x = 0
            for item in row:
                if item == "|":
                    loc = (x - 1, y)
                    if loc in cells:
                        cells[loc]["right_bar"] = True
                    else:
                        cells[loc] = {"right_bar": True}
                else:
                    loc = (x, y)
                    if loc in cells:
                        cells[loc]["row_value"] = item
                    else:
                        cells[loc] = {"row_value": item}
                    x += 1
            y += 1
        return cells

    def _parse_grid_style(self, cells, style):
        """Parse the style into cells."""
        style_matrix = self._create_matrix(style)
        for y, row in enumerate(style_matrix):
            for x, item in enumerate(row):
                loc = (x, y)
                if loc in cells:
                    cells[loc]["style"] = item
                else:
                    cells[loc] = {"style": item}
        return cells

    def _parse_rebus_line(self, line):
        """Handle rebus entries, shown between brackets."""
        data = {}
        matches = re.findall(r"\[(.*?)\]", line)
        for match in matches:
            search = f"[{match}]"
            n = line.find(search)
            data[n] = match
            line = line.replace(search, " ", 1)
        for n, char in enumerate(line):
            if char == " ":
                continue
            data[n] = char
        items = []
        length = max(data.keys()) + 1
        for n in range(length):
            items.append(data.get(n, ""))
        return items

    def _line_words(self, line):
        """Return a list of words in the line."""
        line = re.sub(r"[\._#]", "|", line)
        words = []
        for word in line.split("|"):
            if len(word) > 1:
                words.append(word)
        return words

    def _line_word_location(self, line, word):
        """Return the location of the word in the line."""
        line = line.replace("|", "")
        n = line.find(f"{word}")
        return (n, n + len(word) - 1)

    def entries(self):
        """Return a dict of grid entries."""
        data = self.to_firestore()
        rows = data["entry_rows"] or data["rows"]
        columns = data["entry_columns"] or data["columns"]
        output = {}

        # parse rows
        for y, line in enumerate(rows):
            words = self._line_words(line)
            for word in words:
                x1, x2 = self._line_word_location(line, word)
                start = (y, x1)
                end = (y, x2)
                if word not in output:
                    output[word] = []
                output[word].append(
                    {
                        "direction": "across",
                        "start": start,
                        "end": end,
                        "entry": word,
                    }
                )

        # parse columns
        for x, line in enumerate(columns):
            words = self._line_words(line)
            for word in words:
                y1, y2 = self._line_word_location(line, word)
                start = (y1, x)
                end = (y2, x)
                if word not in output:
                    output[word] = []
                output[word].append(
                    {
                        "direction": "down",
                        "start": start,
                        "end": end,
                        "entry": word,
                    }
                )

        return output

    #
    # convert grid to firestore format
    #
    # def _convert_columnssolution

    def _create_firestore_columns(self, gridtype="puzzle"):
        """Return the columns in the string array format used by firestore."""
        columns = []
        if gridtype not in ["puzzle", "solution", "entry"]:
            return columns

        for x in range(self.width):
            items = []
            for y in range(self.height):
                cell = self["cells"][y][x]
                if not cell:
                    continue
                # add value
                if cell["blank"]:
                    item = "_"
                elif cell["block"]:
                    item = "#"
                elif cell["empty"]:
                    item = "."
                else:
                    item = cell["values"]["column"] or cell["values"]["row"] or "_"
                if len(item) > 1:
                    items.append(f"[{item}]")
                else:
                    items.append(item)
                # add bars
                if gridtype == "puzzle":
                    if cell["bars"]["bottom_bar"]:
                        items.append("|")
                elif gridtype == "solution":
                    if cell["bars"]["solution_bottom_bar"]:
                        items.append("|")
                elif gridtype == "entry":
                    if cell["bars"]["entry_bottom_bar"]:
                        items.append("|")
            columns.append("".join(items))
        return columns

    def _create_firestore_rows(self, gridtype="puzzle"):
        """Return the rows in the string array format used by firestore."""
        rows = []
        if gridtype not in ["puzzle", "solution", "entry"]:
            return rows

        for row in self["cells"]:
            items = []
            for cell in row:
                if not cell:
                    continue
                # add value
                if cell["blank"]:
                    item = "_"
                elif cell["block"]:
                    item = "#"
                elif cell["empty"]:
                    item = "."
                else:
                    item = cell["values"]["row"] or "_"
                if len(item) > 1:
                    items.append(f"[{item}]")
                else:
                    items.append(item)
                # add bars
                if gridtype == "puzzle":
                    if cell["bars"]["right_bar"]:
                        items.append("|")
                elif gridtype == "solution":
                    if cell["bars"]["solution_right_bar"]:
                        items.append("|")
                elif gridtype == "entry":
                    if cell["bars"]["entry_right_bar"]:
                        items.append("|")
            rows.append("".join(items))
        return rows

    def _create_firestore_style(self, gridtype="puzzle"):
        """Return the style in the string array format used by firestore."""
        style = []
        if gridtype not in ["puzzle", "solution"]:
            return style

        for row in self["cells"]:
            items = []
            for cell in row:
                if not cell:
                    continue
                if gridtype == "puzzle":
                    item = cell["styles"]["style_key"] or "_"
                elif gridtype == "solution":
                    item = cell["styles"]["solution_style_key"] or "_"
                if len(item) > 1:
                    item = f"[{item}]"
                items.append(item)
            style.append("".join(items))
        return style

    def to_firestore(self):
        """Convert grid to firestore data."""
        rows = self._create_firestore_rows()
        columns = self._create_firestore_columns()
        style = self._create_firestore_style()

        solution_rows = self._create_firestore_rows(gridtype="solution")
        solution_columns = self._create_firestore_columns(gridtype="solution")
        solution_style = self._create_firestore_style(gridtype="solution")

        entry_rows = self._create_firestore_rows(gridtype="entry")
        entry_columns = self._create_firestore_columns(gridtype="entry")

        # remove any style definitions that are unused
        styles = {}
        for style_key in self["styles"]:
            if style_key not in "\n".join(style) and style_key not in "\n".join(solution_style):
                continue
            styles[style_key] = self["styles"][style_key]

        puzzle = {
            "rows": rows,
            "columns": columns,
            "style": style,
            "solution_rows": solution_rows if solution_rows != rows else [],
            "solution_columns": solution_columns if solution_columns != columns else [],
            "solution_style": solution_style if solution_style != style else [],
            "entry_rows": entry_rows if entry_rows != rows else [],
            "entry_columns": entry_columns if entry_columns != columns else [],
            "styles": styles,
        }
        return puzzle
