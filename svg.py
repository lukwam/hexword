"""Puzzle SVG class file."""


class SVG(dict):
    """SVG class."""

    def __init__(self, puzzle, gridtype="puzzle"):
        """Initialize SVG."""
        super().__init__(puzzle)
        self.gridtype = gridtype

    def answers(self):
        """Return a list of answer cells."""
        answers = []
        if self.gridtype == "puzzle":
            return answers
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                values = []
                # skip answer if we have a default in the solution grid
                if cell["values"].get("solution_default"):
                    continue
                row = cell["values"]["row"]
                column = cell["values"]["column"]
                if row:
                    values.append(row)
                if column and column not in values:
                    values.append(column)
                if len(values) > 1:
                    cell["values"] = values
                else:
                    cell["value"] = row
                answers.append(cell)
        return answers

    def blanks(self):
        """Return a list of blank cells."""
        blanks = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if cell["blank"]:
                    blanks.append(cell)
        return blanks

    def blocks(self):
        """Return a list of block cells."""
        blocks = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if cell["block"]:
                    blocks.append(cell)
        return blocks

    def across_bars(self):
        """Return a list of grid across_bars."""
        across_bars = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if self.gridtype == "puzzle":
                    if cell["bars"].get("right_bar"):
                        across_bars.append(cell)
                else:
                    if cell["bars"].get("solution_right_bar"):
                        across_bars.append(cell)
        return across_bars

    def barjoincaps(self):
        """Return a list of bar join caps."""
        barjoincaps = {}
        rows = self["grid"]["cells"]
        for y, row in enumerate(rows):
            for x, cell in enumerate(row):
                if not cell:
                    continue
                if cell["blank"]:
                    continue
                if cell["block"]:
                    continue

                left = None if x < 1 else row[x - 1]
                top = None if y < 1 else rows[y - 1][x]

                top_bar = False if not top else top["bars"].get("bottom_bar")
                right_bar = cell["bars"].get("right_bar", False)
                bottom_bar = cell["bars"].get("bottom_bar", False)
                left_bar = False if not left else left["bars"].get("right_bar")

                if top_bar and left_bar:
                    loc = (y, x)
                    if loc not in barjoincaps:
                        barjoincaps[loc] = {"x": x, "y": y}
                if top_bar and right_bar:
                    loc = (y, x + 1)
                    if loc not in barjoincaps:
                        barjoincaps[loc] = {"x": x + 1, "y": y}
                if bottom_bar and left_bar:
                    loc = (y + 1, x)
                    if loc not in barjoincaps:
                        barjoincaps[loc] = {"x": x, "y": y + 1}
                if bottom_bar and right_bar:
                    loc = (y + 1, x + 1)
                    if loc not in barjoincaps:
                        barjoincaps[loc] = {"x": x + 1, "y": y + 1}

        output = []
        for loc in sorted(barjoincaps):
            output.append(barjoincaps[loc])
        return output

    def borderjoincaps(self):
        """Return a list of border join caps."""
        borderjoincaps = {}
        cells = self.borders()
        for cell in cells:
            if not cell:
                continue
            if cell["blank"]:
                continue
            if cell["block"]:
                continue
            x = cell["x"]
            y = cell["y"]
            if cell["top_border"] and cell["left_border"]:
                loc = (y, x)
                if loc not in borderjoincaps:
                    borderjoincaps[loc] = {"x": x, "y": y}
            if cell["top_border"] and cell["right_border"]:
                loc = (y, x + 1)
                if loc not in borderjoincaps:
                    borderjoincaps[loc] = {"x": x + 1, "y": y, "right": True}
            if cell["bottom_border"] and cell["left_border"]:
                loc = (y + 1, x)
                if loc not in borderjoincaps:
                    borderjoincaps[loc] = {"x": x, "y": y + 1, "bottom": True}
            if cell["bottom_border"] and cell["right_border"]:
                loc = (y + 1, x + 1)
                if loc not in borderjoincaps:
                    borderjoincaps[loc] = {
                        "x": x + 1,
                        "y": y + 1,
                        "right": True,
                        "bottom": True,
                    }
        return borderjoincaps.values()

    def borders(self):
        """Return a list of borders."""
        borders = []
        if not self["settings"].get("show_grid_border"):
            return borders
        rows = self["grid"]["cells"]
        for y, row in enumerate(rows):
            for x, cell in enumerate(row):
                left = None if x < 1 else row[x - 1]
                right = None if x >= len(row) - 1 else row[x + 1]
                top = None if y < 1 else rows[y - 1][x]
                bottom = None if y >= len(rows) - 1 else rows[y + 1][x]

                left_border = False
                right_border = False
                top_border = False
                bottom_border = False

                if not cell:
                    continue
                if cell["blank"]:
                    continue

                if not left or left["blank"]:
                    left_border = True
                if not right or right["blank"]:
                    right_border = True
                if not top or top["blank"]:
                    top_border = True
                if not bottom or bottom["blank"]:
                    bottom_border = True

                cell["left_border"] = left_border
                cell["right_border"] = right_border
                cell["top_border"] = top_border
                cell["bottom_border"] = bottom_border
                borders.append(cell)

        return borders

    def circles(self):
        """Return a list of circles."""
        circles = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if self.gridtype == "puzzle":
                    style = cell["styles"]["style"]
                else:
                    style = cell["styles"]["solution_style"]
                if style.get("shape") == "circle" and style.get("stroke"):
                    cell["circle"] = style.get("stroke")
                    circles.append(cell)
        return circles

    def defaults(self):
        """Return a list of grid defaults."""
        defaults = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if self.gridtype == "puzzle":
                    if cell["values"].get("default"):
                        cell["default"] = cell["values"]["default"]
                        defaults.append(cell)
                else:
                    if cell["values"].get("solution_default"):
                        cell["default"] = cell["values"]["solution_default"]
                        defaults.append(cell)
        return defaults

    def down_bars(self):
        """Return a list of grid down_bars."""
        down_bars = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if self.gridtype == "puzzle":
                    if cell["bars"].get("bottom_bar"):
                        down_bars.append(cell)
                else:
                    if cell["bars"].get("solution_bottom_bar"):
                        down_bars.append(cell)
        return down_bars

    def numbers(self):
        """Return a list of grid numbers."""
        numbers = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if cell.get("label"):
                    numbers.append(cell)
        return numbers

    def shade_circles(self):
        """Return a list of share circles."""
        shade_circles = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if self.gridtype == "puzzle":
                    style = cell["styles"]["style"]
                else:
                    style = cell["styles"]["solution_style"]
                if style.get("shape") == "circle" and style.get("fill"):
                    cell["shade_circle"] = style["fill"]
                    shade_circles.append(cell)
        return shade_circles

    def shade_squares(self):
        """Return a list of share squares."""
        shade_squares = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if self.gridtype == "puzzle":
                    style = cell["styles"]["style"]
                else:
                    style = cell["styles"]["solution_style"]
                if "background-color" in style:
                    cell["background_color"] = style["background-color"]
                    shade_squares.append(cell)
        return shade_squares

    def squares(self):
        """Return a list of grid squares."""
        squares = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if not cell["blank"]:
                    squares.append(cell)
        return squares

    def xs(self):
        """Return a list of Xs."""
        xs = []
        for row in self["grid"]["cells"]:
            for cell in row:
                if not cell:
                    continue
                if self.gridtype == "puzzle":
                    style = cell["styles"]["style"]
                else:
                    style = cell["styles"]["solution_style"]
                if style.get("shape") == "x":
                    cell["shade_x"] = style.get("stroke", "grey")
                    xs.append(cell)
        return xs
