"""Redact obvious personal identifiers before agent I/O is stored or shown in the monitor."""
import re

_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN]"),
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAAR]"),
    (re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)"), "[PHONE]"),
]


def redact(text: str) -> str:
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text


def summarize(value, limit: int = 300):
    """Compact, redacted summary of arbitrary agent input/output for the monitor."""
    if isinstance(value, str):
        return redact(value[:limit])
    if isinstance(value, (list, tuple)):
        return f"{len(value)} items"
    if isinstance(value, dict):
        return {k: summarize(v, limit) for k, v in list(value.items())[:12]}
    return value
