"""Mask credentials before content can leave the local process."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SanitizedText:
    text: str
    masked_values: int


# Deliberately conservative: false positives are safer than emitting a secret.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("bearer", re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]{12,}")),
    ("password", re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key)\s*[:=]\s*[^\s'\"`]+")),
)


def sanitize(text: str) -> SanitizedText:
    """Return safe text and the number of values masked.

    The original text is never persisted by this module. Callers must pass this
    result—not the input—to any remote provider.
    """
    count = 0

    def replacement(name: str):
        def replace(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            if name == "bearer":
                return f"{match.group(1)}[KUMONOS_MASKED]"
            if name == "password":
                return f"{match.group(1)}=[KUMONOS_MASKED]"
            return "[KUMONOS_MASKED]"
        return replace

    for name, pattern in PATTERNS:
        text = pattern.sub(replacement(name), text)
    return SanitizedText(text=text, masked_values=count)
