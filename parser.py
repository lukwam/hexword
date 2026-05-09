"""Text parser for cryptic puzzles."""

from .puzzle import Puzzle


def transpose_grid(rows):
    """Transpose a list of row strings into column strings.

    Assumes row strings are in the format |A|B|C|.
    Cells are bracketed by bars or implicit boundaries.
    This simple parser assumes strict |X|Y| format for now.
    """
    # Remove leading/trailing pipes for splitting, but handle empty strings
    # This is a simplified logic that assumes visual alignment or | delimiter

    # First, tokenize each row
    matrix = []
    for row in rows:
        # Strip potential leading/trailing whitespace
        row = row.strip()
        # If strict pipe format: |A|B| -> ['', 'A', 'B', ''] -> ['A', 'B']
        if row.startswith("|") and row.endswith("|"):
            row = row[1:-1]

        # Split by pipe
        # Note: This doesn't handle complex valid cases like "A B" (no bars) well unless we enforce pipes.
        # For this implementation, we enforce | delimiters for simplicity in "Text" format.
        cells = row.split("|")
        matrix.append(cells)

    if not matrix:
        return []

    # Transpose
    max_len = max(len(row) for row in matrix)
    transposed = []
    for i in range(max_len):
        col_cells = []
        for row in matrix:
            if i < len(row):
                col_cells.append(row[i])
            else:
                col_cells.append("_")  # filler
        # Reconstruct string
        transposed.append("|" + "|".join(col_cells) + "|")

    return transposed


def parse_text(content: str) -> dict:
    """Parse a text-formatted puzzle into a dictionary."""
    lines = content.split("\n")

    data = {
        "title": "Untitled",
        "author": "Unknown",
        "date": "2023-01-01",
        "settings": {"status": "draft"},
        "clue_groups": [],
        "grid": {},
        "instructions": "",
    }

    mode = "HEADER"
    grid_rows = []
    current_clue_group = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.lower() == "grid:":
            mode = "GRID"
            continue
        elif line.lower() == "clues:":
            mode = "CLUES"
            continue
        elif line.lower() == "instructions:":
            mode = "INSTRUCTIONS"
            continue

        if mode == "HEADER":
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.lower().strip()] = value.strip()

        elif mode == "GRID":
            if line.startswith("|") or (len(line) > 0 and line[0].isalnum()):
                grid_rows.append(line)

        elif mode == "INSTRUCTIONS":
            data["instructions"] += line + "\n"

        elif mode == "CLUES":
            # Detect group headers (Across/Down)
            if line.lower() in ["across", "down"] or line.endswith(":"):
                group_name = line.replace(":", "")
                current_clue_group = {"name": group_name, "clues": [], "settings": {}}
                data["clue_groups"].append(current_clue_group)
            else:
                # Parse clue: "1. Clue text (5)"
                # This basic parser just appends the raw string for Clues class to parse later
                # The Clues class (ported from hexgrids) handle strings like "1. Clue text ~ ANSWER"
                if current_clue_group:
                    current_clue_group["clues"].append(line)

    # Process grid
    if grid_rows:
        data["grid"]["rows"] = grid_rows
        # Auto-generate columns for full validation
        data["grid"]["columns"] = transpose_grid(grid_rows)

    return data


def parse_to_puzzle(content: str) -> Puzzle:
    """Parse text to Puzzle object."""
    data = parse_text(content)
    # Ensure instructions are present if missing (Puzzle validation requirement)
    if not data.get("instructions"):
        data["instructions"] = "Solve the puzzle."
    return Puzzle(data)
