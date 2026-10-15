"""Regenerate the Journey map in index.html.

Usage: python3 tools/build_journey_map.py [path/to/countries-50m.json]

Country outlines come from world-atlas (Natural Earth, public domain). Without
an argument the pinned TopoJSON file is downloaded from jsDelivr. The script
replaces everything between the journey-map markers in index.html, so edit
STOPS below and re-run it to change the path.
"""

import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"
ATLAS_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json"
START_MARKER = "<!-- journey-map:start -->"
END_MARKER = "<!-- journey-map:end -->"

# (label, note, lon, lat, label side, arc bend into this stop)
STOPS = [
    ("China", "Where it started", 103.0, 35.5, "below", 0),
    ("Oslo, Norway", "Home", 10.75, 59.91, "left", 0.3),
    ("Stockholm, Sweden", "B.Sc. at KTH", 18.07, 59.33, "right", -0.5),
    ("Beijing, China", "Research at Tsinghua", 116.40, 39.90, "right", 0.3),
    ("Zürich, Switzerland", "M.Sc. at ETH", 8.54, 47.37, "below", 0.12),
]
VISITED = {"156", "578", "752", "756"}  # China, Norway, Sweden, Switzerland

# Albers equal-area conic centred between Europe and East Asia.
LON0, LAT0, PAR1, PAR2 = 62.0, 48.0, 35.0, 62.0
WIDTH = 1000
FRAME = [(-11, 37), (-11, 55), (26, 71.5), (134, 46), (110, 17), (-8, 35)]
TOLERANCE = 0.9


def albers(lon, lat):
    p1, p2, p0 = (math.radians(v) for v in (PAR1, PAR2, LAT0))
    n = (math.sin(p1) + math.sin(p2)) / 2
    c = math.cos(p1) ** 2 + 2 * n * math.sin(p1)
    rho0 = math.sqrt(c - 2 * n * math.sin(p0)) / n
    dlon = (lon - LON0 + 180) % 360 - 180
    theta = n * math.radians(dlon)
    rho = math.sqrt(c - 2 * n * math.sin(math.radians(lat))) / n
    return rho * math.sin(theta), -(rho0 - rho * math.cos(theta))


def make_projection():
    xs, ys = zip(*(albers(*p) for p in FRAME))
    x0, y0 = min(xs), min(ys)
    scale = WIDTH / (max(xs) - x0)
    height = round((max(ys) - y0) * scale)
    return (lambda lon, lat: tuple(
        (v - o) * scale for v, o in zip(albers(lon, lat), (x0, y0))
    )), height


def decode_arcs(topo):
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        points = []
        for dx, dy in arc:
            x, y = x + dx, y + dy
            points.append((x * sx + tx, y * sy + ty))
        arcs.append(points)
    return arcs


def ring_points(ring, arcs):
    points = []
    for index in ring:
        arc = arcs[index] if index >= 0 else arcs[~index][::-1]
        points.extend(arc if not points else arc[1:])
    return points


def clip(points, width, height, margin=8):
    """Sutherland-Hodgman clip of a closed ring to the padded viewBox."""
    edges = [
        (lambda p: p[0] >= -margin, 0, -margin),
        (lambda p: p[0] <= width + margin, 0, width + margin),
        (lambda p: p[1] >= -margin, 1, -margin),
        (lambda p: p[1] <= height + margin, 1, height + margin),
    ]
    for inside, axis, bound in edges:
        if not points:
            break
        result = []
        for i, current in enumerate(points):
            previous = points[i - 1]
            if inside(current) != inside(previous):
                t = (bound - previous[axis]) / (current[axis] - previous[axis])
                result.append(tuple(a + t * (b - a) for a, b in zip(previous, current)))
            if inside(current):
                result.append(current)
        points = result
    return points


def simplify(points, tolerance):
    if len(points) < 3:
        return points
    (ax, ay), (bx, by) = points[0], points[-1]
    length = math.hypot(bx - ax, by - ay)
    worst, worst_index = 0.0, 0
    for i, (px, py) in enumerate(points[1:-1], 1):
        if length:
            d = abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / length
        else:
            d = math.hypot(px - ax, py - ay)
        if d > worst:
            worst, worst_index = d, i
    if worst <= tolerance:
        return [points[0], points[-1]]
    left = simplify(points[: worst_index + 1], tolerance)
    return left[:-1] + simplify(points[worst_index:], tolerance)


def ring_path(points):
    rounded = [(round(x), round(y)) for x, y in points]
    deduped = [p for i, p in enumerate(rounded) if i == 0 or p != rounded[i - 1]]
    if len(deduped) < 4:
        return ""
    (x, y), parts = deduped[0], [f"M{deduped[0][0]} {deduped[0][1]}"]
    for nx, ny in deduped[1:]:
        parts.append(f"{nx - x} {ny - y}")
        x, y = nx, ny
    return parts[0] + "l" + " ".join(parts[1:]) + "z"


def country_paths(topo, project, height):
    arcs = decode_arcs(topo)
    paths = {"visited": [], "other": []}
    for geometry in topo["objects"]["countries"]["geometries"]:
        polygons = geometry.get("arcs", [])
        if geometry["type"] == "Polygon":
            polygons = [polygons]
        for polygon in polygons:
            for ring in polygon:
                lonlat = ring_points(ring, arcs)
                if not any(-30 < lon < 170 and 0 < lat < 85 for lon, lat in lonlat):
                    continue
                points = clip([project(*p) for p in lonlat], WIDTH, height)
                d = ring_path(simplify(points + points[:1], TOLERANCE))
                if d:
                    group = "visited" if geometry.get("id") in VISITED else "other"
                    paths[group].append(d)
    return paths


def arc_path(start, end, bend):
    (x1, y1), (x2, y2) = start, end
    cx = (x1 + x2) / 2 + bend * (y2 - y1) / 2
    cy = (y1 + y2) / 2 - bend * (x2 - x1) / 2
    return f"M{x1:.0f} {y1:.0f}Q{cx:.0f} {cy:.0f} {x2:.0f} {y2:.0f}"


def render(topo):
    project, height = make_projection()
    paths = country_paths(topo, project, height)
    points = [project(lon, lat) for _, _, lon, lat, _, _ in STOPS]
    routes = "\n".join(
        f'          <path class="journey-route" d="{arc_path(points[i - 1], points[i], STOPS[i][5])}"/>'
        for i in range(1, len(STOPS))
    )
    pins = []
    legend = []
    for number, ((label, note, *_rest, side, _), (x, y)) in enumerate(zip(STOPS, points), 1):
        current = " current" if number == len(STOPS) else ""
        pins.append(
            f'        <span class="journey-pin journey-pin-{side}{current}" '
            f'style="left: {x / WIDTH * 100:.2f}%; top: {y / height * 100:.2f}%">'
            f'<span class="journey-pin-number">{number}</span>'
            f'<span class="journey-pin-label">{label.split(",")[0]}</span></span>'
        )
        legend.append(
            f'        <li class="journey-stop{current}"><span class="journey-stop-place">{label}</span> '
            f'<span class="journey-stop-note">{note}</span></li>'
        )
    return f"""{START_MARKER}
      <figure class="journey-figure">
      <div class="journey-map" aria-hidden="true">
        <svg viewBox="0 0 {WIDTH} {height}" focusable="false">
          <path class="journey-land" d="{''.join(paths['other'])}"/>
          <path class="journey-land journey-visited" d="{''.join(paths['visited'])}"/>
{routes}
        </svg>
{chr(10).join(pins)}
      </div>
      <figcaption class="visually-hidden">Map of the places I have lived, in order:</figcaption>
      <ol class="journey-stops">
{chr(10).join(legend)}
      </ol>
      </figure>
      {END_MARKER}"""


def main():
    if len(sys.argv) > 1:
        topo = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    else:
        with urllib.request.urlopen(ATLAS_URL) as response:
            topo = json.load(response)
    html = INDEX_HTML.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START_MARKER) + ".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(html):
        sys.exit(f"Markers not found in {INDEX_HTML}")
    INDEX_HTML.write_text(pattern.sub(lambda _: render(topo), html), encoding="utf-8")


if __name__ == "__main__":
    main()
