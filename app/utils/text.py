import re

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.strip())


def cell_text(value: str | None) -> str:
    if value is None:
        return ""
    return normalize_whitespace(str(value))
