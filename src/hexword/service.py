"""Hexword service — serialization, parsing, and conversion.

All business logic for working with Hexword puzzles.
Models are data-only; this service handles transformation.
"""

from __future__ import annotations

import re

from hexword.exceptions import ClueParseError
from hexword.models import Clue, ClueGroupSettings, Hexword, PuzzleSettings
from hexword.renderer import render_svg


ENUMERATION_STYLES = ("split", "total", "note")
WORD_NOTES = ("words", "numeral", "abbreviated", "none")
WORD_NOTE_POSITIONS = ("after", "before")
NUMBER_WORDS = ("", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")

# A word note at the end of clue text, in italics or not: "(two words)", "(2 wds.)", "(hyphenated)", "(hyph.)".
# Notes are data, derived from the answer (spec §4.1); one left in the clue text should be taken out.
NOTE_IN_TEXT = re.compile(
    r"\(\s*(?:<(?:i|em)>\s*)?(?:[A-Za-z0-9]+\s+(?:words|wds\.?)|hyphenated|hyph\.)\s*(?:</(?:i|em)>\s*)?\)\s*$",
    re.IGNORECASE,
)


class HexwordService:
    """Serialization, parsing, and conversion for Hexword puzzles."""

    # --- Dict serialization (Firestore round-trip) ---

    def from_dict(self, data: dict) -> Hexword:
        """Parse a well-formed dict into a Hexword model.

        Expects clean data (structured Clue objects, nested settings).
        Legacy data normalization is the consumer's responsibility.
        """
        return Hexword.model_validate(data)

    def to_dict(self, hexword: Hexword) -> dict:
        """Serialize a Hexword to a Firestore-compatible dict.

        Uses by_alias=True for fields like background-color.
        Excludes None values to match Firestore conventions.
        """
        return hexword.model_dump(
            by_alias=True,
            exclude_none=True,
        )

    # --- Rendering ---

    def render_svg(self, hexword: Hexword, show_solution: bool = False, size: int = 50) -> str:
        """Render a Hexword to an SVG string."""
        return render_svg(hexword, show_solution=show_solution, size=size)

    # --- Text format import/export (tilde-delimited clue strings) ---

    def parse_clue(
        self,
        raw: str,
        settings: ClueGroupSettings | None = None,  # noqa: ARG002 — reserved for future enumeration logic
    ) -> Clue:
        """Parse a tilde-delimited clue string into a Clue model.

        Format: '{label}. {clue_text} ~ {answer} ~ {annotation}'

        Supports:
            - Numeric labels: '1. Clue text ~ ANS ~ SOL'
            - Alpha labels: 'a. Clue text ~ ANS ~ SOL'
            - Starred clues: '*1. Clue text ~ ANS ~ SOL'
            - Compound labels: 'a;16. Clue text ~ ANS ~ SOL'
            - Suffixed labels: '1|b. Clue text ~ ANS ~ SOL'
            - Pipe-separated entries: '1. Clue ~ AIR GUN|AIRGUN ~ SOL'
            - Multi-answer with semicolons: '1. Clue ~ ANS1;ANS2 ~ SOL1;SOL2'

        Used for text/YAML import.

        Args:
            raw: The tilde-delimited clue string.
            settings: Optional clue group settings (reserved for future
                enumeration logic).

        Returns:
            A structured Clue model.

        Raises:
            ClueParseError: If the string cannot be parsed.
        """
        if not raw or not raw.strip():
            raise ClueParseError("Empty clue string.")

        # Split on '. ' to separate label from clue text.
        # The first '. ' is the label delimiter.
        dot_parts = raw.split(". ", 1)
        if len(dot_parts) < 2:
            raise ClueParseError(f"No '. ' delimiter found in clue: {raw!r}")

        raw_name = dot_parts[0]
        clue_body = dot_parts[1]

        # Parse starred clue
        starred = False
        if raw_name.startswith("*"):
            raw_name = raw_name[1:]
            starred = True

        # Parse suffix (pipe-separated: '1|b')
        suffix = None
        if "|" in raw_name:
            raw_name, suffix = raw_name.split("|", 1)

        # Parse label override (semicolon-separated: 'a;16' or 'a;16;2')
        label = None
        label_index = 0
        if ";" in raw_name:
            raw_name, label = raw_name.split(";", 1)
            if ";" in label:
                label, label_index_str = label.split(";", 1)
                label_index = int(label_index_str) if label_index_str else 0

        name = raw_name

        # Split clue body on ' ~ ' into [clue_text, answer, annotation]
        tilde_parts = clue_body.split(" ~ ")
        clue_text = tilde_parts[0].strip()
        ans_raw = tilde_parts[1] if len(tilde_parts) > 1 else ""
        sol_raw = tilde_parts[2] if len(tilde_parts) > 2 else ans_raw

        # Parse answers and entries (pipe-separated: 'AIR GUN|AIRGUN')
        answers: list[str] = []
        entries: list[str] = []
        if "|" in ans_raw:
            ans_part, ent_part = ans_raw.split("|", 1)
            answers = [a.strip() for a in ans_part.split(";") if a.strip()]
            entries = [e.strip() for e in ent_part.split(";") if e.strip()]
        elif ans_raw.strip():
            answers = [a.strip() for a in ans_raw.split(";") if a.strip()]

        # Parse annotations
        annotations: list[str] = []
        if sol_raw.strip():
            annotations = [s.strip() for s in sol_raw.split(";") if s.strip()]

        return Clue(
            name=name,
            clue_text=clue_text,
            answers=answers,
            annotations=annotations,
            entries=entries,
            suffix=suffix,
            label=label,
            label_index=label_index,
            starred=starred,
        )

    def clue_to_string(self, clue: Clue) -> str:
        """Serialize a Clue model back to a tilde-delimited string.

        Used for text/YAML export.

        The format mirrors what parse_clue() expects:
            '{label}. {clue_text} ~ {answer} ~ {annotation}'
        """
        # Build the label prefix
        text = ""
        if clue.starred:
            text += "*"
        text += clue.name
        if clue.suffix:
            text += f"|{clue.suffix}"
        if clue.label:
            text += f";{clue.label}"
            if clue.label_index:
                text += f";{clue.label_index}"

        # Add the clue text
        text += f". {clue.clue_text}"

        # Add the answers (and entries if present)
        ans = ";".join(clue.answers)
        text += f" ~ {ans}"
        if clue.entries:
            ent = ";".join(clue.entries)
            text += f"|{ent}"

        # Add the annotations
        sol = ";".join(clue.annotations)
        text += f" ~ {sol}"

        return text

    # --- Utilities ---

    @staticmethod
    def get_enumeration(answer: str) -> str:
        """Return the enumeration string for a clue answer.

        Counts alpha characters between spaces/punctuation:
            'ARUM'       → '4'
            'AIR GUN'    → '3,3'
            'FRENCH BED' → '6,3'
            'SELF-MADE'  → '4-4'

        Args:
            answer: The answer string (may contain spaces, hyphens, etc.).

        Returns:
            The enumeration string (e.g., '3,3').
        """
        num = 0
        output = ""
        for char in answer:
            if char.isalpha():
                num += 1
            elif char == " ":
                output += f"{num},"
                num = 0
            else:
                # Keep hyphens, apostrophes, etc. as-is
                output += f"{num}{char}"
                num = 0
        output += f"{num}"
        return output

    @staticmethod
    def get_total_length(answer: str) -> str:
        """Return the enumeration printed under enumeration_style 'total': every letter of the answer.

        'BETA RAY'  → '7'
        'FIVE-STAR' → '8'
        """
        return str(sum(1 for char in answer if char.isalnum()))

    @staticmethod
    def get_word_note(answer: str, form: str = "words") -> str | None:
        """Return the note printed after a total length (spec §4.1), or None if the answer needs none.

        An answer of more than one word (words are separated by spaces) gets a word count; failing that, one with a
        hyphen is 'hyphenated'. form chooses the wording:
            'words'       → 'two words' (numerals past ten), 'hyphenated'
            'numeral'     → '2 words', 'hyphenated'
            'abbreviated' → '2 wds.', 'hyph.'
            'none'        → no note
        """
        if form not in WORD_NOTES:
            form = "words"
        if form == "none":
            return None
        count = len(answer.split())
        if count > 1:
            if form == "words" and count < len(NUMBER_WORDS):
                return f"{NUMBER_WORDS[count]} words"
            return f"{count} wds." if form == "abbreviated" else f"{count} words"
        if "-" in answer:
            return "hyph." if form == "abbreviated" else "hyphenated"
        return None

    @staticmethod
    def resolve_enumeration_settings(
        clue: Clue,
        group_settings: ClueGroupSettings | None = None,
        puzzle_settings: PuzzleSettings | None = None,
    ) -> tuple[str, str, bool]:
        """Return the (enumeration_style, word_note, word_note_italic) that apply to a clue.

        The clue's own enumeration_style wins, then its group's settings, then the puzzle's; a value that isn't one
        of the allowed ones is ignored.
        """
        puzzle = puzzle_settings or PuzzleSettings()
        group = group_settings or ClueGroupSettings()
        style = next(
            (
                s
                for s in (clue.enumeration_style, group.enumeration_style, puzzle.enumeration_style)
                if s in ENUMERATION_STYLES
            ),
            "split",
        )
        note = next((n for n in (group.word_note, puzzle.word_note) if n in WORD_NOTES), "words")
        italic = group.word_note_italic if group.word_note_italic is not None else puzzle.word_note_italic
        return style, note, bool(italic)

    @staticmethod
    def resolve_word_note_position(
        group_settings: ClueGroupSettings | None = None,
        puzzle_settings: PuzzleSettings | None = None,
    ) -> str:
        """Return 'after' or 'before': where a clue's word note prints relative to its length (spec §4.1)."""
        puzzle = puzzle_settings or PuzzleSettings()
        group = group_settings or ClueGroupSettings()
        return next(
            (p for p in (group.word_note_position, puzzle.word_note_position) if p in WORD_NOTE_POSITIONS), "after"
        )

    def get_clue_enumerations(
        self,
        clue: Clue,
        group_settings: ClueGroupSettings | None = None,
        puzzle_settings: PuzzleSettings | None = None,
        measure: list[str] | None = None,
    ) -> list[tuple[str, str | None]]:
        """Return what prints after a clue, one (enumeration, word_note) pair per answer (spec §4.1).

            split: 'BETA RAY' → ('4,3', None)
            total: 'BETA RAY' → ('7', 'two words')
            note:  'BETA RAY' → ('', 'two words'): the length is withheld, so nothing prints for it

        measure gives the words to count, one per answer, when they aren't the answers: the grid entries, for a
        group whose show_enumerations is 'entries'. Word notes always come from the answers. A clue's own
        enumeration, when set, replaces the derived one, except under 'note', which prints no length.
        """
        style, form, _ = self.resolve_enumeration_settings(clue, group_settings, puzzle_settings)
        answers = clue.answers
        words = list(measure) if measure else list(answers)
        if style == "total":
            enums = [self.get_total_length(w) for w in words]
            notes = [self.get_word_note(a, form) for a in answers]
        else:
            enums = [self.get_enumeration(w) for w in words]
            notes = [None for _ in words]
        if style == "note":
            return [("", self.get_word_note(a, form)) for a in answers]
        if isinstance(clue.enumeration, list):
            enums = list(clue.enumeration)
        elif clue.enumeration:
            enums = [clue.enumeration, *enums[1:]]
        notes += [None] * (len(enums) - len(notes))
        return list(zip(enums, notes[: len(enums)], strict=True))

    @staticmethod
    def note_in_text(clue_text: str) -> bool:
        """Return whether clue text ends with a word note, such as '(two words)', that belongs in the data."""
        return bool(NOTE_IN_TEXT.search(clue_text))
