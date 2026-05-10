"""Hexword domain exceptions."""


class HexwordError(Exception):
    """Base exception for the hexword library."""


class ClueParseError(HexwordError):
    """Raised when a clue string cannot be parsed."""
