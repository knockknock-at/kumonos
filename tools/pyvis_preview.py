#!/usr/bin/env python3
"""Ad-hoc interactive preview of KUMONOS's graph.json using pyvis (vis.js physics).

Not part of KUMONOS's shipped output: index.html stays static HTML with no JS
graph library, per the project's design (see README "製品の境界"). This script
is a developer/QA convenience for inspecting clusters that a single-scale
static layout compresses too tightly to read - vis.js runs the physics live in
the browser, so dragging a node or resizing the window re-spaces its edges.

Usage: python tools/pyvis_preview.py [--graph output/current/graph.json] [--output output/current/pyvis_preview.html]
Requires: pip install pyvis
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyvis.network import Network

COLOR_KNOWLEDGE = "#2a78d6"
COLOR_PROJECT = "#eb6834"
COLOR_EDGE = "#c3c2b7"


def build_network(graph: dict) -> Network:
    net = Network(height="900px", width="100%", bgcolor="#fcfcfb", font_color="#0b0b0b", directed=False)
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120, spring_strength=0.02, damping=0.09)
    net.toggle_hide_edges_on_drag(False)

    for node in graph["nodes"]:
        if node["kind"] == "knowledge":
            size = 8 + 3 * (node["occurrence_count"] ** 0.5)
            title = f"{node['title']} (観測{node['occurrence_count']}件 / 報告者{node['owner_count']}人)"
            net.add_node(node["id"], label="", title=title, color=COLOR_KNOWLEDGE, size=size, shape="dot")
        else:
            size = 12 + 4 * (node["knowledge_count"] ** 0.5)
            title = f"{node['title']} (ナレッジ{node['knowledge_count']}件)"
            net.add_node(node["id"], label=node["title"].split("/")[-1], title=title,
                         color=COLOR_PROJECT, size=size, shape="dot")

    for edge in graph["edges"]:
        weight = edge.get("weight", 1)
        net.add_edge(edge["source"], edge["target"], color=COLOR_EDGE, value=weight,
                     title=f"観測{weight}件(同一プロジェクト内)")

    return net


def main() -> None:
    parser = argparse.ArgumentParser(description="Render KUMONOS graph.json as an interactive pyvis network")
    parser.add_argument("--graph", default=Path("output/current/graph.json"), type=Path)
    parser.add_argument("--output", default=Path("output/current/pyvis_preview.html"), type=Path)
    args = parser.parse_args()

    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    net = build_network(graph)
    net.save_graph(str(args.output))
    print(f"wrote {args.output} ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")


if __name__ == "__main__":
    main()
