import json
import math
from pathlib import Path

from kumonos.cli import main
from kumonos.layout import force_directed_layout
from kumonos.sanitize import sanitize


def test_force_directed_layout_keeps_connected_nodes_closer_than_disconnected():
    nodes = ["a", "b", "c"]
    edges = [("a", "b")]
    positions = force_directed_layout(nodes, edges, width=400, height=400, iterations=150)
    assert all(0 <= x <= 400 and 0 <= y <= 400 for x, y in positions.values())
    dist_connected = math.dist(positions["a"], positions["b"])
    dist_disconnected = math.dist(positions["a"], positions["c"])
    assert dist_connected < dist_disconnected


def test_sanitize_masks_credential():
    result = sanitize("api_key=supersecretvalue123 sk-proj-abcdefghijklmnopqrstuvwxyz")
    assert "supersecretvalue123" not in result.text
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz" not in result.text
    assert result.masked_values == 2


def test_compile_is_idempotent(tmp_path: Path, monkeypatch):
    config = tmp_path / "kumonos.json"
    config.write_text(json.dumps({"input_root": "input", "output_root": "output"}), encoding="utf-8")
    source = tmp_path / "input" / "session.jsonl"
    source.parent.mkdir()
    source.write_text(json.dumps({"payload": {"role": "user", "content": "問題: 更新を見落とす"}}, ensure_ascii=False) + "\n" + json.dumps({"payload": {"role": "assistant", "content": "解決: 内容ハッシュで検出する"}}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["kumonos", "compile", "--config", str(config)])
    main()
    graph = json.loads((tmp_path / "output" / "current" / "graph.json").read_text(encoding="utf-8"))
    assert len([n for n in graph["nodes"] if n["kind"] == "knowledge"]) == 2
    main()
    graph = json.loads((tmp_path / "output" / "current" / "graph.json").read_text(encoding="utf-8"))
    assert len([n for n in graph["nodes"] if n["kind"] == "knowledge"]) == 2



def test_config_sets_existing_input_directory(tmp_path: Path, monkeypatch):
    config = tmp_path / "kumonos.json"
    input_root = tmp_path / "shared-logs"
    input_root.mkdir()
    config.write_text(json.dumps({"input_root": "input", "output_root": "output"}), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["kumonos", "config", "--config", str(config), "--input-root", str(input_root)])
    main()

    # Machine-specific absolute paths go to kumonos.local.json, never the versioned kumonos.json.
    local_config = tmp_path / "kumonos.local.json"
    settings = json.loads(local_config.read_text(encoding="utf-8"))
    assert settings["input_root"] == str(input_root.resolve())
    assert json.loads(config.read_text(encoding="utf-8"))["input_root"] == "input"



def test_compile_skips_output_inside_input_root(tmp_path: Path, monkeypatch):
    config = tmp_path / "kumonos.json"
    input_root = tmp_path
    output_root = tmp_path / "output"
    source = tmp_path / "session.jsonl"
    source.write_text(json.dumps({"payload": {"role": "user", "content": "問題: 出力フォルダを入力に混在させる"}}, ensure_ascii=False), encoding="utf-8")
    (output_root / "old.jsonl").parent.mkdir()
    (output_root / "old.jsonl").write_text("not valid JSONL", encoding="utf-8")
    config.write_text(json.dumps({"input_root": str(input_root), "output_root": "output"}), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["kumonos", "compile", "--config", str(config)])
    main()

    graph = json.loads((output_root / "current" / "graph.json").read_text(encoding="utf-8"))
    assert len([n for n in graph["nodes"] if n["kind"] == "knowledge"]) == 1



def test_config_rejects_relative_input_directory(tmp_path: Path, monkeypatch):
    config = tmp_path / "kumonos.json"
    config.write_text(json.dumps({"input_root": "input", "output_root": "output"}), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["kumonos", "config", "--config", str(config), "--input-root", "shared-logs"])
    try:
        main()
    except SystemExit as error:
        assert "absolute path" in str(error)
    else:
        raise AssertionError("relative input root should be rejected")



def test_compile_attributes_owner_from_top_level_folder_and_counts_repeats(tmp_path: Path, monkeypatch):
    # Mirrors Documents\Logs\<owner>\... : the first path segment under input_root is the owner.
    config = tmp_path / "kumonos.json"
    config.write_text(json.dumps({"input_root": "input", "output_root": "output"}), encoding="utf-8")
    same_note = json.dumps({"payload": {"role": "user", "content": "問題: 更新を見落とす"}}, ensure_ascii=False) + "\n" \
        + json.dumps({"payload": {"role": "assistant", "content": "解決: 内容ハッシュで検出する"}}, ensure_ascii=False)
    for owner in ("owner-a", "owner-b"):
        source = tmp_path / "input" / owner / "session.jsonl"
        source.parent.mkdir(parents=True)
        source.write_text(same_note, encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["kumonos", "compile", "--config", str(config)])
    main()

    graph = json.loads((tmp_path / "output" / "current" / "graph.json").read_text(encoding="utf-8"))
    solution_node = next(n for n in graph["nodes"] if n.get("type") == "solution")
    assert solution_node["owner_id"] in {"owner-a", "owner-b"}
    assert solution_node["owner_count"] == 2
    assert solution_node["occurrence_count"] == 2



def test_compile_rejects_missing_input_root(tmp_path: Path, monkeypatch):
    config = tmp_path / "kumonos.json"
    config.write_text(json.dumps({"input_root": "does-not-exist", "output_root": "output"}), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["kumonos", "compile", "--config", str(config)])
    try:
        main()
    except SystemExit as error:
        assert "does not exist" in str(error)
    else:
        raise AssertionError("missing input_root should be rejected")
