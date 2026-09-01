"""Local deterministic extraction for the first vertical slice.

This intentionally has no network access. A future LLM provider must receive
only SanitizedText and validate into the same candidate shape.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


MARKERS = {
    "problem": ("問題", "課題", "problem"),
    "solution": ("解決", "対応", "solution", "fix"),
    "failure": ("失敗", "エラー", "failure", "failed"),
    "playbook": ("手順", "手順書", "playbook", "手順:"),
}


@dataclass(frozen=True)
class Candidate:
    type: str
    title: str
    summary: str
    body: str
    excerpt_hash: str


def _type(text: str) -> str | None:
    lower = text.lower()
    for kind, markers in MARKERS.items():
        if any(marker.lower() in lower for marker in markers):
            return kind
    return None


def extract(text: str) -> list[Candidate]:
    """Extract explicitly-labelled reusable passages, preserving their wording."""
    candidates: list[Candidate] = []
    for passage in re.split(r"\n\s*\n", text):
        passage = " ".join(passage.split())
        kind = _type(passage)
        if not kind or len(passage) < 12:
            continue
        summary = passage[:240]
        title = re.sub(r"^(問題|課題|解決|対応|失敗|エラー|手順)\s*[:：]\s*", "", summary, flags=re.I)
        title = title[:80].rstrip("。．. ") or f"{kind} candidate"
        excerpt_hash = hashlib.sha256(passage.encode()).hexdigest()
        candidates.append(Candidate(kind, title, summary, passage, excerpt_hash))
    # Stable de-duplication within a session.
    return list({candidate.excerpt_hash: candidate for candidate in candidates}.values())
