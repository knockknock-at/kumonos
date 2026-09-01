from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from .codex import read_jsonl
from .export import export_all
from .extract import extract
from .sanitize import sanitize
from .store import all_knowledge, changed, open_store, replace_source


def _local_config_path(path: Path) -> Path:
    """Path to the machine-specific override file (gitignored, holds absolute paths)."""
    return path.with_name(f"{path.stem}.local{path.suffix}")


def _config(path: Path) -> dict:
    """Merge the versioned config with this machine's local override, if present."""
    config = json.loads(path.read_text(encoding="utf-8"))
    local_path = _local_config_path(path)
    if local_path.exists():
        config.update(json.loads(local_path.read_text(encoding="utf-8")))
    return config


def _write_config(path: Path, config: dict) -> None:
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _input_root_value(value: str) -> str:
    """Validate an administrator-provided absolute input directory."""
    input_root = Path(value).expanduser()
    if not input_root.is_absolute():
        raise SystemExit(f"input_root must be an absolute path: {value}")
    input_root = input_root.resolve()
    if not input_root.is_dir():
        raise SystemExit(f"input_root is not an existing directory: {input_root}")
    return str(input_root)


def _paths(config: dict, config_path: Path) -> tuple[Path, Path]:
    base = config_path.parent
    return (base / config["input_root"]).resolve(), (base / config["output_root"]).resolve()


def init(args: argparse.Namespace) -> int:
    path = Path(args.config)
    if path.exists():
        raise SystemExit(f"config already exists: {path}")
    (path.parent / "input").mkdir(exist_ok=True)
    _write_config(path, {"input_root": "input", "output_root": "output", "include": ["*.jsonl"]})
    print(f"created {path}")
    return 0


def config(args: argparse.Namespace) -> int:
    path = Path(args.config)
    if not path.exists():
        raise SystemExit(f"config does not exist: {path}")
    local_path = _local_config_path(path)
    settings = json.loads(local_path.read_text(encoding="utf-8")) if local_path.exists() else {}
    settings["input_root"] = _input_root_value(args.input_root)
    _write_config(local_path, settings)
    print(f"updated {local_path}")
    return 0


def compile_(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    config = _config(config_path)
    input_root, output_root = _paths(config, config_path)
    if not input_root.is_dir():
        raise SystemExit(f"input_root does not exist: {input_root}")
    if output_root == input_root or output_root in input_root.parents:
        raise SystemExit("output_root must not contain input_root")
    store = open_store(output_root / ".kumonos" / "store.sqlite3")
    processed = skipped = masked = 0
    for pattern in config.get("include", ["*.jsonl"]):
        for source in sorted(input_root.rglob(pattern)):
            if not source.is_file() or output_root in source.parents:
                continue
            relative = source.relative_to(input_root).as_posix()
            owner_id = relative.split("/", 1)[0]
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if not changed(store, relative, digest):
                skipped += 1
                continue
            turns = read_jsonl(source)
            safe = sanitize("\n\n".join(f"{turn.role}: {turn.text}" for turn in turns))
            masked += safe.masked_values
            now = datetime.now(UTC).isoformat()
            candidates = []
            for candidate in extract(safe.text):
                knowledge_id = "KNO-" + hashlib.sha256((candidate.type + candidate.title).encode()).hexdigest()[:12]
                candidates.append({"id": knowledge_id, "source_path": relative, "owner_id": owner_id, "source_hash": digest,
                    "type": candidate.type, "title": candidate.title, "summary": candidate.summary, "body": candidate.body,
                    "confidence": 0.60, "observed_at": now, "excerpt_hash": candidate.excerpt_hash})
            replace_source(store, relative, owner_id, digest, now, candidates)
            processed += 1
    export_all(store, output_root / "current")
    print(json.dumps({"processed": processed, "skipped": skipped, "masked_values": masked, "knowledge": len(all_knowledge(store))}, ensure_ascii=False))
    return 0


def status(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    _, output_root = _paths(_config(config_path), config_path)
    store = open_store(output_root / ".kumonos" / "store.sqlite3")
    print(json.dumps({"knowledge": len(all_knowledge(store))}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="kumonos")
    sub = parser.add_subparsers(required=True)
    for name, func in (("init", init), ("compile", compile_), ("status", status)):
        command = sub.add_parser(name)
        command.add_argument("--config", default="kumonos.json")
        command.set_defaults(func=func)
    command = sub.add_parser("config", help="update the existing KUMONOS configuration")
    command.add_argument("--config", default="kumonos.json")
    command.add_argument("--input-root", required=True, help="existing directory to recursively scan for JSONL logs")
    command.set_defaults(func=config)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
