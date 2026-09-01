"""SQLite storage for manifests and extracted knowledge candidates."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"


def open_store(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS manifest (
          source_path TEXT PRIMARY KEY, owner_id TEXT NOT NULL, content_hash TEXT NOT NULL,
          processed_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS knowledge (
          id TEXT PRIMARY KEY, source_path TEXT NOT NULL, owner_id TEXT NOT NULL, source_hash TEXT NOT NULL,
          type TEXT NOT NULL, title TEXT NOT NULL, summary TEXT NOT NULL,
          body TEXT NOT NULL, confidence REAL NOT NULL, observed_at TEXT NOT NULL,
          excerpt_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS knowledge_occurrence (
          knowledge_id TEXT NOT NULL REFERENCES knowledge(id),
          source_path TEXT NOT NULL, owner_id TEXT NOT NULL, source_hash TEXT NOT NULL,
          observed_at TEXT NOT NULL, excerpt_hash TEXT NOT NULL,
          PRIMARY KEY (knowledge_id, source_path)
        );
    """)
    return connection


def changed(connection: sqlite3.Connection, source_path: str, digest: str) -> bool:
    row = connection.execute("SELECT content_hash FROM manifest WHERE source_path = ?", (source_path,)).fetchone()
    return row is None or row["content_hash"] != digest


def replace_source(connection: sqlite3.Connection, source_path: str, owner_id: str, digest: str, processed_at: str,
                   candidates: list[dict[str, Any]]) -> None:
    with connection:
        connection.execute("DELETE FROM knowledge_occurrence WHERE source_path = ?", (source_path,))
        connection.execute("""INSERT INTO manifest(source_path, owner_id, content_hash, processed_at, active)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(source_path) DO UPDATE SET owner_id=excluded.owner_id, content_hash=excluded.content_hash,
            processed_at=excluded.processed_at, active=1""", (source_path, owner_id, digest, processed_at))
        connection.executemany("""INSERT INTO knowledge
            (id, source_path, owner_id, source_hash, type, title, summary, body, confidence, observed_at, excerpt_hash)
            VALUES (:id, :source_path, :owner_id, :source_hash, :type, :title, :summary, :body, :confidence, :observed_at, :excerpt_hash)
            ON CONFLICT(id) DO UPDATE SET source_path=excluded.source_path, owner_id=excluded.owner_id,
            source_hash=excluded.source_hash, type=excluded.type, title=excluded.title, summary=excluded.summary,
            body=excluded.body, confidence=excluded.confidence, observed_at=excluded.observed_at,
            excerpt_hash=excluded.excerpt_hash, active=1""", candidates)
        connection.executemany("""INSERT INTO knowledge_occurrence
            (knowledge_id, source_path, owner_id, source_hash, observed_at, excerpt_hash)
            VALUES (:id, :source_path, :owner_id, :source_hash, :observed_at, :excerpt_hash)
            ON CONFLICT(knowledge_id, source_path) DO UPDATE SET owner_id=excluded.owner_id,
            source_hash=excluded.source_hash, observed_at=excluded.observed_at,
            excerpt_hash=excluded.excerpt_hash""", candidates)


def occurrences(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("""
        SELECT o.knowledge_id, o.source_path, o.owner_id
        FROM knowledge_occurrence o JOIN knowledge k ON k.id = o.knowledge_id
        WHERE k.active = 1
    """)
    return [dict(row) for row in rows]


def all_knowledge(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("""
        SELECT k.*,
               (SELECT COUNT(DISTINCT owner_id) FROM knowledge_occurrence WHERE knowledge_id = k.id) AS owner_count,
               (SELECT COUNT(*) FROM knowledge_occurrence WHERE knowledge_id = k.id) AS occurrence_count
        FROM knowledge k WHERE k.active = 1 ORDER BY k.id
    """)
    return [dict(row) for row in rows]
