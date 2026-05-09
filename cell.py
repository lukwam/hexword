"""Puzzle cell class file."""

# import json


class Cell(dict):
    """Cell class."""

    def __init__(self, cell, grid):
        """Initialize cell."""
        # super().__init__(cell)
        self.grid = grid
        self._parse_cell(cell)

    def _parse_cell(self, cell):
        """Parse the cell."""
        # get coordinates
        self["x"] = cell.get("x")
        self["y"] = cell.get("y")

        # initialize errors and warnings
        self["errors"] = []
        self["warnings"] = []

        # parse the cell values
        self["values"] = self._parse_cell_values(cell)

        # parse the cell bars
        self["bars"] = self._parse_cell_bars(cell)

        # parse the style characters
        self["styles"] = self._parse_cell_styles(cell)

    def _parse_cell_bars(self, cell):
        """Parse the cell bars for puzzle, solution and entry grids."""
        return {
            "bottom_bar": cell.get("bottom_bar") or False,
            "right_bar": cell.get("right_bar") or False,
            "solution_bottom_bar": cell.get("solution_bottom_bar") or False,
            "solution_right_bar": cell.get("solution_right_bar") or False,
            "entry_bottom_bar": cell.get("entry_bottom_bar") or False,
            "entry_right_bar": cell.get("entry_right_bar") or False,
        }

    def _parse_cell_styles(self, cell):
        """Parse the cell styles for puzzle and solution grids."""
        style_key = cell.get("style") or None
        if style_key == self.grid.BLANK:
            style_key = None

        # check for default value in the style key
        if style_key and style_key in self.grid["styles"] and "value" in self.grid["styles"][style_key]:
            self["values"]["default"] = self.grid["styles"][style_key]["value"]
        elif style_key and style_key not in self.grid["styles"] and style_key not in self.grid.STYLES:
            self["values"]["default"] = style_key

        solution_style_key = cell.get("solution_style") or None
        if solution_style_key == self.grid.BLANK:
            solution_style_key = None

        # check for default value in the style key
        if (
            solution_style_key
            and solution_style_key in self.grid["styles"]
            and "value" in self.grid["styles"][solution_style_key]
        ):
            self["values"]["solution_default"] = self.grid["styles"][solution_style_key]["value"]
        elif (
            solution_style_key
            and solution_style_key not in self.grid["styles"]
            and solution_style_key not in self.grid.STYLES
        ):
            self["values"]["solution_default"] = solution_style_key

        # get the style information for the puzzle grid
        style = {}
        if style_key in self.grid["styles"]:
            style = self.grid["styles"][style_key]
        elif style_key in self.grid.STYLES:
            style = self.grid.STYLES[style_key]

        # get the style information for the solution grid
        solution_style = {}
        if solution_style_key in self.grid["styles"]:
            solution_style = self.grid["styles"][solution_style_key]
        elif solution_style_key in self.grid.STYLES:
            solution_style = self.grid.STYLES[solution_style_key]

        return {
            "style_key": style_key,
            "style": style,
            "solution_style_key": solution_style_key,
            "solution_style": solution_style,
        }

    def _parse_cell_values(self, cell):
        """Parse the cell values (answers)."""
        row_value = cell.get("row_value")
        column_value = cell.get("column_value")

        # use the row value to decide if cell is blank/block/empty
        self["blank"] = False
        self["block"] = False
        self["empty"] = False
        if row_value == self.grid.BLANK:
            self["blank"] = True
        elif row_value == self.grid.BLOCK:
            self["block"] = True
        elif row_value == self.grid.EMPTY:
            self["empty"] = True

        # check for conflicting solution row value
        solution_row_value = cell.get("solution_row_value")
        if solution_row_value and row_value and solution_row_value != row_value:
            self["errors"].append(f"Conflicting solution row value: {solution_row_value} != {row_value}")

        # check for conflicting entry row value
        entry_row_value = cell.get("entry_row_value")
        if entry_row_value and row_value and entry_row_value != row_value:
            self["errors"].append(f"Conflicting entry row value: {entry_row_value} != {row_value}")

        # check for conflicting solution column value
        solution_column_value = cell.get("solution_column_value")
        if solution_column_value and column_value and solution_column_value != column_value:
            self["errors"].append(f"Conflicting solution column value: {solution_column_value} != {column_value}")

        # check for conflicting entry column value
        entry_column_value = cell.get("entry_column_value")
        if entry_column_value and column_value and entry_column_value != column_value:
            self["errors"].append(f"Conflicting entry column value: {entry_column_value} != {column_value}")

        # check for different row/column value
        if row_value and column_value and row_value != column_value:
            self["warnings"].append(f"Row and column values don't match: {row_value} != {column_value}")

        # return None for both values if empty
        if self.get("blank") or self.get("block") or self.get("empty"):
            return {"row": None, "column": None}

        # return the list of actual values
        if row_value in [self.grid.BLANK, self.grid.BLOCK, self.grid.EMPTY, ""]:
            row_value = None
        if column_value in [self.grid.BLANK, self.grid.BLOCK, self.grid.EMPTY, ""]:
            column_value = None

        return {
            "row": row_value,
            "column": column_value,
            "default": None,
        }
