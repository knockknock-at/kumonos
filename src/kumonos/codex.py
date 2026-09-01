"""Tolerant reader for Codex session/rollout JSONL exports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Turn:
    role: str
    text: str
    line: int


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [part for item in value for part in _strings(item)]
    if isinstance(value, dict):
        preferred = [value[key] for key in ("text", "message", "content") if key in value]
        return [part for item in preferred for part in _strings(item)]
    return []


def _find_role(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    role = value.get("role")
    if role in {"user", "assistant"}:
        return role
    for key in ("payload", "item", "message"):
        result = _find_role(value.get(key))
        if result:
            return result
    return None


def read_jsonl(path: Path) -> list[Turn]:
    """Read user/assistant turns without interpreting log content as commands."""
    turns: list[Turn] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(f"INVALID_JSONL line {line_number}: {error.msg}") from error
        role = _find_role(item)
        if not role:
            continue
        texts = _strings(item.get("payload", item))
        text = "\n".join(dict.fromkeys(part.strip() for part in texts if part.strip()))
        if text:
            turns.append(Turn(role=role, text=text, line=line_number))
    return turns
