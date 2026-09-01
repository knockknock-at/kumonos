"""Dependency-free force-directed layout for small-to-medium graphs.

Runs entirely at export time so the published output stays static HTML/SVG
with no JavaScript graph library and no network fetch at view time.
"""

from __future__ import annotations

import math
import random


def force_directed_layout(node_ids: list[str], edges: list[tuple[str, str]], width: float = 1000,
                           height: float = 700, iterations: int = 300, seed: int = 42,
                           center_strength: float = 0.02, margin: float = 0.06) -> dict[str, tuple[float, float]]:
    """Fruchterman-Reingold style layout. O(n^2) per iteration; fine for a few hundred nodes.

    The simulation runs unconstrained (no per-step boundary clamp): clamping mid-simulation
    pins nodes pushed outward by repulsion (a big hub, or a small disconnected component) to
    the wall, where they stack up instead of settling into their own space. Positions are
    rescaled into [0, width] x [0, height] once, after the simulation settles.
    """
    rng = random.Random(seed)
    positions = {node: [rng.uniform(-width / 2, width / 2), rng.uniform(-height / 2, height / 2)]
                 for node in node_ids}
    if len(node_ids) <= 1:
        return {node: (width / 2, height / 2) for node in node_ids}

    ideal_distance = math.sqrt((width * height) / len(node_ids))
    adjacency = [(a, b) for a, b in edges if a in positions and b in positions and a != b]
    temperature = width / 10

    for step in range(iterations):
        forces = {node: [0.0, 0.0] for node in node_ids}
        for i, a in enumerate(node_ids):
            ax, ay = positions[a]
            for b in node_ids[i + 1:]:
                bx, by = positions[b]
                dx, dy = ax - bx, ay - by
                distance = math.hypot(dx, dy) or 0.01
                repulsion = (ideal_distance * ideal_distance) / distance
                fx, fy = dx / distance * repulsion, dy / distance * repulsion
                forces[a][0] += fx
                forces[a][1] += fy
                forces[b][0] -= fx
                forces[b][1] -= fy
        for a, b in adjacency:
            ax, ay = positions[a]
            bx, by = positions[b]
            dx, dy = ax - bx, ay - by
            distance = math.hypot(dx, dy) or 0.01
            attraction = (distance * distance) / ideal_distance
            fx, fy = dx / distance * attraction, dy / distance * attraction
            forces[a][0] -= fx
            forces[a][1] -= fy
            forces[b][0] += fx
            forces[b][1] += fy

        # Weak pull toward the origin: keeps the whole layout compact and numerically
        # stable without fighting local repulsion the way a hard boundary clamp would.
        for node in node_ids:
            x, y = positions[node]
            forces[node][0] -= x * center_strength
            forces[node][1] -= y * center_strength

        cooling = temperature * (1 - step / iterations)
        for node in node_ids:
            fx, fy = forces[node]
            displacement = math.hypot(fx, fy) or 0.01
            move = min(displacement, cooling)
            x, y = positions[node]
            positions[node] = [x + fx / displacement * move, y + fy / displacement * move]

    xs = [pos[0] for pos in positions.values()]
    ys = [pos[1] for pos in positions.values()]
    span_x = (max(xs) - min(xs)) or 1.0
    span_y = (max(ys) - min(ys)) or 1.0
    min_x, min_y = min(xs), min(ys)
    inner_width = width * (1 - 2 * margin)
    inner_height = height * (1 - 2 * margin)
    return {
        node: (width * margin + (x - min_x) / span_x * inner_width,
               height * margin + (y - min_y) / span_y * inner_height)
        for node, (x, y) in positions.items()
    }
