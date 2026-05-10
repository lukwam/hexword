"""Hexword service — serialization, parsing, and conversion.

All business logic for working with Hexword puzzles.
Models are data-only; this service handles transformation.
"""

from __future__ import annotations

from hexword.exceptions import ClueParseError
from hexword.models import Clue, ClueGroupSettings, Hexword


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
