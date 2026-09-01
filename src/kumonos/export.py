"""Rebuild portable output artifacts from SQLite."""

from __future__ import annotations

import html
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape

from .layout import force_directed_layout
from .store import SCHEMA_VERSION, all_knowledge, occurrences

TYPE_LABELS = {"problem": "問題", "solution": "解決", "failure": "失敗", "playbook": "手順"}

# Validated categorical pair (node scripts/validate_palette.js "#2a78d6,#eb6834" --mode light --pairs all -> ALL PASS).
COLOR_KNOWLEDGE = "#2a78d6"
COLOR_PROJECT = "#eb6834"
COLOR_SURFACE = "#fcfcfb"
COLOR_EDGE = "#c3c2b7"
COLOR_TEXT_PRIMARY = "#0b0b0b"
COLOR_TEXT_SECONDARY = "#52514e"
COLOR_TEXT_MUTED = "#898781"


def _project_key(source_path: str) -> str:
    """Group session files by project so the network shows projects, not individual files."""
    parts = source_path.split("/")
    if "projects" in parts:
        index = parts.index("projects")
        if index + 1 < len(parts):
            return "/".join(parts[: index + 2])
    return "/".join(parts[:-1]) or source_path


def _project_label(source_path: str, owner_id: str) -> str:
    parts = source_path.split("/")
    folder = parts[-2] if len(parts) >= 2 else parts[-1]
    return f"{owner_id}/{folder}"


def _build_graph(items: list[dict], occ: list[dict]) -> tuple[list[dict], list[dict]]:
    project_knowledge: dict[str, set[str]] = {}
    project_label: dict[str, str] = {}
    # weight = how many source files in that project reported this knowledge - repeated
    # occurrences within one project used to collapse into a single, unweighted edge.
    edge_weight: dict[tuple[str, str], int] = {}
    for row in occ:
        project_id = "PRJ:" + _project_key(row["source_path"])
        project_knowledge.setdefault(project_id, set()).add(row["knowledge_id"])
        project_label.setdefault(project_id, _project_label(row["source_path"], row["owner_id"]))
        key = (row["knowledge_id"], project_id)
        edge_weight[key] = edge_weight.get(key, 0) + 1

    nodes = [{"id": item["id"], "kind": "knowledge", "type": item["type"], "title": item["title"],
              "summary": item["summary"], "confidence": item["confidence"], "owner_count": item["owner_count"],
              "occurrence_count": item["occurrence_count"], "note_path": f"notes/{item['id']}.md",
              "source_path": item["source_path"], "owner_id": item["owner_id"]} for item in items]
    nodes += [{"id": project_id, "kind": "project", "title": project_label[project_id],
               "knowledge_count": len(knowledge_ids)}
              for project_id, knowledge_ids in sorted(project_knowledge.items())]
    edges = [{"source": source, "target": target, "relation": "extracted_from", "weight": weight}
              for (source, target), weight in sorted(edge_weight.items())]
    return nodes, edges


def _network_svg(nodes: list[dict], edges: list[dict], width: int = 1000, height: int = 700) -> str:
    node_ids = [n["id"] for n in nodes]
    edge_pairs = [(e["source"], e["target"]) for e in edges]
    positions = force_directed_layout(node_ids, edge_pairs, width=width, height=height)

    def radius(node: dict) -> float:
        magnitude = node["occurrence_count"] if node["kind"] == "knowledge" else node["knowledge_count"]
        return 4 + 3 * math.sqrt(max(magnitude, 1))

    lines = [f'<line x1="{positions[e["source"]][0]:.1f}" y1="{positions[e["source"]][1]:.1f}" '
             f'x2="{positions[e["target"]][0]:.1f}" y2="{positions[e["target"]][1]:.1f}" '
             f'stroke="{COLOR_EDGE}" stroke-width="{min(1 + (e["weight"] - 1) * 0.8, 6):.1f}" stroke-opacity="0.5">'
             f'<title>観測{e["weight"]}件</title></line>' for e in edges]

    # Direct-label only the highest-degree project nodes; the rest rely on the hover tooltip + table below.
    project_nodes = sorted((n for n in nodes if n["kind"] == "project"), key=lambda n: -n["knowledge_count"])
    labelled_ids = {n["id"] for n in project_nodes[:8]}

    circles = []
    for node in nodes:
        x, y = positions[node["id"]]
        r = radius(node)
        color = COLOR_KNOWLEDGE if node["kind"] == "knowledge" else COLOR_PROJECT
        tooltip = (f"{TYPE_LABELS.get(node.get('type'), '')} / {node['title']}"
                   f" (観測{node['occurrence_count']}件・報告者{node['owner_count']}人)") if node["kind"] == "knowledge" \
            else f"{node['title']}(ナレッジ{node['knowledge_count']}件)"
        circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" '
                        f'stroke="{COLOR_SURFACE}" stroke-width="2"><title>{escape(tooltip)}</title></circle>')
        if node["id"] in labelled_ids:
            # Long encoded paths share a common prefix (owner/root); the distinguishing part is at
            # the end, so truncate from the front rather than clipping off the meaningful suffix.
            title = node["title"]
            label = title if len(title) <= 34 else "…" + title[-33:]
            circles.append(f'<text x="{x:.1f}" y="{y - r - 4:.1f}" font-size="10" text-anchor="middle" '
                            f'fill="{COLOR_TEXT_SECONDARY}">{escape(label)}</text>')

    legend = (
        f'<g transform="translate(16,16)">'
        f'<circle cx="6" cy="0" r="6" fill="{COLOR_KNOWLEDGE}"/>'
        f'<text x="18" y="4" font-size="12" fill="{COLOR_TEXT_PRIMARY}">ナレッジ(円の大きさ=観測件数)</text>'
        f'<circle cx="6" cy="20" r="6" fill="{COLOR_PROJECT}"/>'
        f'<text x="18" y="24" font-size="12" fill="{COLOR_TEXT_PRIMARY}">プロジェクト(出典、円の大きさ=ナレッジ件数)</text>'
        f'<line x1="0" y1="40" x2="12" y2="40" stroke="{COLOR_EDGE}" stroke-width="3"/>'
        f'<text x="18" y="44" font-size="12" fill="{COLOR_TEXT_PRIMARY}">線の太さ=同一プロジェクト内での観測回数</text>'
        f'</g>')

    return (f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img" '
            f'aria-label="ナレッジとプロジェクトの関係ネットワーク図">'
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="{COLOR_SURFACE}"/>'
            f'{"".join(lines)}{"".join(circles)}{legend}</svg>')


def _knowledge_table(items: list[dict]) -> str:
    rows = []
    for item in sorted(items, key=lambda i: (i["type"], -i["occurrence_count"])):
        rows.append(
            f'<tr><td>{html.escape(TYPE_LABELS.get(item["type"], item["type"]))}</td>'
            f'<td><a href="{html.escape(item["id"])}.md">{html.escape(item["title"])}</a></td>'
            f'<td>{item["confidence"]:.2f}</td><td>{item["occurrence_count"]}</td><td>{item["owner_count"]}</td></tr>')
    return (
        '<table><thead><tr><th>種別</th><th>タイトル</th><th>信頼度</th>'
        '<th>観測件数</th><th>報告者数</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>')


def export_all(connection, output: Path) -> None:
    notes = output / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    items = all_knowledge(connection)
    occ = occurrences(connection)

    for item in items:
        (notes / f"{item['id']}.md").write_text(
            f"---\nid: {item['id']}\ntype: {item['type']}\nlifecycle: draft\nconfidence: {item['confidence']:.2f}\n---\n\n"
            f"# {item['title']}\n\n## 要点\n\n{item['summary']}\n\n## 根拠\n\n"
            f"- `{item['source_path']}`(報告者: {item['owner_id']})\n"
            f"- 観測件数: {item['occurrence_count']}件 / 報告者数: {item['owner_count']}人\n",
            encoding="utf-8")

    nodes, edges = _build_graph(items, occ)
    graph = {"schema_version": SCHEMA_VERSION, "generated_at": datetime.now(UTC).isoformat(),
             "nodes": nodes, "edges": edges}
    (output / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "decisions.json").write_text(json.dumps({"schema_version": SCHEMA_VERSION, "decisions": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    graphml_keys = ('<key id="title" for="node" attr.name="title" attr.type="string"/>'
                     '<key id="kind" for="node" attr.name="kind" attr.type="string"/>'
                     '<key id="weight" for="edge" attr.name="weight" attr.type="double"/>')
    graphml_nodes = "".join(
        f'<node id="{escape(n["id"])}"><data key="title">{escape(n["title"])}</data>'
        f'<data key="kind">{escape(n["kind"])}</data></node>' for n in nodes)
    graphml_edges = "".join(
        f'<edge source="{escape(e["source"])}" target="{escape(e["target"])}">'
        f'<data key="weight">{e["weight"]}</data></edge>' for e in edges)
    (output / "graph.graphml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><graphml>{graphml_keys}'
        f'<graph id="kumonos" edgedefault="directed">{graphml_nodes}{graphml_edges}</graph></graphml>',
        encoding="utf-8")

    svg = _network_svg(nodes, edges)
    table = _knowledge_table(items)
    (output / "index.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>KUMONOS</title>"
        "<style>"
        f"body{{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:{COLOR_TEXT_PRIMARY};"
        f"background:#f9f9f7;margin:0;padding:24px}}"
        f"h1{{font-size:20px}} h2{{font-size:15px;color:{COLOR_TEXT_SECONDARY}}}"
        f"table{{border-collapse:collapse;width:100%;font-size:13px}}"
        f"th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #e1e0d9}}"
        f"th{{color:{COLOR_TEXT_MUTED};font-weight:600}}"
        f"svg{{background:{COLOR_SURFACE};border:1px solid #e1e0d9;border-radius:8px}}"
        "</style>"
        f"<h1>KUMONOS 知識一覧</h1><p>{len(items)}件の候補</p>"
        f"<h2>ネットワーク図(ナレッジ ↔ プロジェクト)</h2>{svg}"
        f"<h2>一覧(種別ごと)</h2>{table}",
        encoding="utf-8")
