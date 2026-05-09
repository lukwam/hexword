import sys

# Ensure we can import the package
sys.path.append("/home/karlsson/src/personal/hex/packages")

from cryptic.parser import parse_to_puzzle

SAMPLE = """
Title: Test Puzzle
Author: Antigravity
Date: 2023-01-01

Grid:
|H|E|L|L|O|
|_|#|_|#|#|
|W|O|R|L|D|

Clues:
Across
1. Greeting (5) ~ HELLO
3. Planet (5) ~ WORLD
"""

try:
    puzzle = parse_to_puzzle(SAMPLE)
    print(f"Successfully parsed puzzle: {puzzle['title']}")
    print(f"Grid Dimensions: {puzzle.width}x{puzzle.height}")
    print(f"Clue Groups: {len(puzzle['clue_groups'])}")
    print(f"First Entry: {puzzle['grid']['cells'][0][0]['values']['row']}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback

    traceback.print_exc()
