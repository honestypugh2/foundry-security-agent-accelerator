"""Render the editable six-plane Draw.io source into offline SVG and interactive HTML."""

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets" / "architecture"
SOURCE = ASSETS / "six-plane-reference.drawio"

CSS = """
svg { display:block; width:100%; height:auto; background:#fff; font-family:Arial,sans-serif }
text { fill:#172b4d }
.edge { fill:none; stroke-linejoin:round }
.flow-line { stroke-dasharray:9 7; animation:travel 1.4s linear infinite }
.card { transition:stroke-width .15s }
.step-card { animation:signal 18s linear infinite; animation-delay:var(--delay) }
.interactive .step-card { animation:none }
.interactive [data-node] { cursor:pointer; outline:none }
.interactive [data-node]:focus-visible .card,
.interactive [data-node].selected .card { stroke:#075985; stroke-width:5 }
.interactive [data-node].selected text { fill:#0c4a6e }
.paused .flow-line { animation-play-state:paused }
@keyframes travel { to { stroke-dashoffset:-32 } }
@keyframes signal { 0%,8% { stroke-width:5 } 12%,100% { stroke-width:2 } }
@media(prefers-reduced-motion:reduce) {
  .flow-line,.step-card { animation:none }
  .card { transition:none }
}
"""

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Foundry + Agent 365: one flow, six planes</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f1f5f9;color:#172b4d;font:17px/1.5 system-ui,sans-serif}
main{max-width:1640px;margin:auto;padding:20px}a{color:#075985}button{font:inherit;cursor:pointer}
header,.controls,.details{
  background:#fff;border:1px solid #cbd5e1;border-radius:14px;padding:16px 20px}
header p{margin:0}.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:14px 0}
button{border:2px solid #0369a1;border-radius:8px;background:#eff6ff;
  color:#0c4a6e;padding:8px 18px;min-height:44px}
button:focus-visible,a:focus-visible{outline:3px solid #7e22ce;outline-offset:3px}
.diagram{overflow-x:auto;border:1px solid #cbd5e1;border-radius:14px;background:white}
.diagram svg{min-width:1050px}.details{margin-top:14px;min-height:140px}
.details h1{font-size:24px;margin:0 0 8px}
.details p{margin:0}#phase{font-weight:700;color:#075985}#status{margin-left:auto}
nav{display:flex;gap:20px;flex-wrap:wrap;margin-top:12px}noscript{display:block;padding:16px}
@media print{.controls{display:none}.diagram{overflow:visible}
  .diagram svg{min-width:0}body{background:white}}
__SVG_CSS__
</style></head><body><main>
<header><p><strong>Interactive workshop architecture</strong> &mdash; conceptual animation only.
No Azure calls, live signals, customer data, or production-readiness claim.</p>
<nav aria-label="Architecture resources">
<a href="six-plane-reference.drawio" download>Edit Draw.io source</a>
<a href="six-plane-reference.svg">Animated SVG preview</a>
<a href="../../architecture/overview.md">Implementation and evidence boundaries</a></nav></header>
<div class="controls" aria-label="Animation controls">
<button id="play" type="button" aria-pressed="false">Play</button>
<button id="next" type="button">Next step</button>
<button id="restart" type="button">Restart</button>
<span id="phase"></span><span id="status" role="status" aria-live="off"></span></div>
<p>Click a card, or Tab to it and press Enter/Space. Six surrounding planes:
Entra, Agent 365, Purview, Defender, Monitor, and GitHub. Foundry is the central AI flow.</p>
<div class="diagram" aria-label="Scrollable architecture diagram">__SVG__</div>
<section class="details" aria-labelledby="detail-title">
<h1 id="detail-title">Select a flow step or control plane</h1>
<p id="detail-text">Native governance relationships require independent evidence.</p></section>
<noscript>The diagram remains readable without JavaScript. Open the SVG for a motion-reduced
or animated preview; interaction requires JavaScript. All depicted writes remain DRY_RUN.</noscript>
</main><script>
"use strict";
const nodes = __NODES__;
const sequence = nodes.filter(node => node.step).sort((a,b) => a.step-b.step);
const cards = Array.from(document.querySelectorAll("[data-node]"));
const svg = document.querySelector("svg");
const play = document.getElementById("play");
const status = document.getElementById("status");
const reduced = matchMedia("(prefers-reduced-motion: reduce)");
let index = 0;
let timer = null;
svg.classList.add("interactive", "paused");
svg.setAttribute("role", "group");
function select(node, announce) {
  cards.forEach(card => {
    const active = card.dataset.node === node.id;
    card.classList.toggle("selected", active);
    card.setAttribute("aria-pressed", String(active));
  });
  status.setAttribute("aria-live", announce ? "polite" : "off");
  status.textContent = node.step ? "Step " + node.step + " of " + sequence.length : "Control plane";
  document.getElementById("phase").textContent = node.phase;
  document.getElementById("detail-title").textContent = node.title;
  document.getElementById("detail-text").textContent = node.details;
}
function setPlaying(playing) {
  clearInterval(timer);
  timer = null;
  play.textContent = playing ? "Pause" : "Play";
  play.setAttribute("aria-pressed", String(playing));
  svg.classList.toggle("paused", !playing);
  if (playing) {
    select(sequence[index], false);
    timer = setInterval(() => {
      index = (index + 1) % sequence.length;
      select(sequence[index], false);
    }, 2200);
  }
}
cards.forEach(card => {
  card.setAttribute("role", "button");
  card.setAttribute("tabindex", "0");
  const activate = () => {
    setPlaying(false);
    const node = nodes.find(item => item.id === card.dataset.node);
    if (node.step) index = sequence.indexOf(node);
    select(node, true);
  };
  card.addEventListener("click", activate);
  card.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activate();
    }
  });
});
play.addEventListener("click", () => setPlaying(timer === null));
document.getElementById("next").addEventListener("click", () => {
  setPlaying(false);
  index = (index + 1) % sequence.length;
  select(sequence[index], true);
});
document.getElementById("restart").addEventListener("click", () => {
  setPlaying(false);
  index = 0;
  select(sequence[index], true);
});
document.addEventListener("visibilitychange", () => {
  if (document.hidden) setPlaying(false);
});
reduced.addEventListener("change", () => { if (reduced.matches) setPlaying(false); });
select(sequence[index], false);
setPlaying(!reduced.matches && !document.hidden);
</script></body></html>
"""


def style(cell: ET.Element) -> dict[str, str]:
    return dict(entry.split("=", 1) for entry in cell.get("style", "").split(";") if "=" in entry)


def geometry(cell: ET.Element) -> tuple[float, float, float, float]:
    box = cell.find("mxGeometry")
    if box is None:
        raise ValueError("Diagram vertex is missing geometry")
    return (
        float(box.get("x", "0")),
        float(box.get("y", "0")),
        float(box.get("width", "0")),
        float(box.get("height", "0")),
    )


def lines(label: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]*>", "", line)) for line in re.split(r"<br\s*/?>", label)]


def render() -> dict[Path, str]:
    root = ET.parse(SOURCE).getroot()
    objects = root.findall("./root/object")
    cells = {obj.attrib["id"]: obj.find("mxCell") for obj in objects}
    nodes: list[dict[str, str | int]] = []
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" '
        'role="img" aria-labelledby="diagram-title diagram-description">',
        '<title id="diagram-title">Foundry + Agent 365: one flow, six planes</title>',
        '<desc id="diagram-description">Central caller-side Python and Azure Foundry flow, '
        "surrounded by Entra, Agent 365, Purview, Defender, Monitor, and GitHub. "
        "Dashed native relationships require separate verification. All writes are DRY_RUN.</desc>",
        f"<style>{CSS}</style>",
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#0369a1"/></marker></defs>',
        '<rect width="1600" height="1080" fill="#fff"/>',
    ]
    for cell in root.findall("./root/mxCell[@vertex='1']"):
        x, y, width, height = geometry(cell)
        settings = style(cell)
        label = html.escape(cell.attrib["value"])
        if cell.attrib["id"] == "azure":
            parts.append(
                f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="16" '
                'fill="#f8fafc" stroke="#2563eb" stroke-width="2" stroke-dasharray="7 6"/>'
            )
        parts.append(
            f'<text x="{x + 8}" y="{y + float(settings["fontSize"])}" '
            f'font-size="{settings["fontSize"]}" '
            f'font-weight="{"700" if settings.get("fontStyle") == "1" else "400"}">'
            f"{label}</text>"
        )
    for edge in root.findall("./root/mxCell[@edge='1']"):
        settings = style(edge)
        source, target = cells[edge.attrib["source"]], cells[edge.attrib["target"]]
        if source is None or target is None:
            raise ValueError("Diagram edge references an absent vertex")
        sx, sy, sw, sh = geometry(source)
        tx, ty, tw, th = geometry(target)
        start = (sx + sw * float(settings["exitX"]), sy + sh * float(settings["exitY"]))
        end = (tx + tw * float(settings["entryX"]), ty + th * float(settings["entryY"]))
        points = edge.findall("./mxGeometry/Array/mxPoint")
        path = f"M {start[0]} {start[1]} "
        if points:
            path += " ".join(f"L {point.attrib['x']} {point.attrib['y']}" for point in points)
            path += f" L {end[0]} {end[1]}"
        else:
            middle = (start[0] + end[0]) / 2
            path += f"C {middle} {start[1]} {middle} {end[1]} {end[0]} {end[1]}"
        dashed = settings.get("dashed") == "1"
        parts.append(
            f'<path id="{edge.attrib["id"]}" d="{path}" '
            f'class="edge{"" if dashed else " flow-line"}" '
            f'stroke="{settings["strokeColor"]}" stroke-width="{settings["strokeWidth"]}" '
            + ('stroke-dasharray="7 7"/>' if dashed else 'marker-end="url(#arrow)"/>')
        )
    for obj in objects:
        cell = cells[obj.attrib["id"]]
        if cell is None:
            raise ValueError("Diagram object is missing its cell")
        x, y, width, height = geometry(cell)
        settings = style(cell)
        text = lines(obj.attrib["label"])
        title_index = 1 if obj.attrib["kind"] == "plane" else 0
        step = int(obj.get("step", "0"))
        node = {
            "id": obj.attrib["id"],
            "kind": obj.attrib["kind"],
            "step": step,
            "phase": obj.attrib["phase"],
            "title": text[title_index],
            "details": obj.attrib["tooltip"],
        }
        nodes.append(node)
        parts.append(
            f'<g data-node="{obj.attrib["id"]}" data-kind="{obj.attrib["kind"]}" '
            f'aria-label="{html.escape(text[title_index], quote=True)}">'
            f"<title>{html.escape(obj.attrib['tooltip'])}</title>"
            f'<rect class="card{" step-card" if step else ""}" '
            f'style="--delay:{max(step - 1, 0) * 2}s" '
            f'x="{x}" y="{y}" width="{width}" height="{height}" rx="18" '
            f'fill="{settings["fillColor"]}" stroke="{settings["strokeColor"]}" stroke-width="2"'
            + (' stroke-dasharray="7 5"/>' if settings.get("dashed") == "1" else "/>")
        )
        for number, line in enumerate(text):
            eyebrow = obj.attrib["kind"] == "plane" and number == 0
            baseline = 28 + number * 32 if obj.attrib["kind"] == "plane" else 26 + number * 28
            parts.append(
                f'<text x="{x + 20}" y="{y + baseline}" '
                f'font-size="{16 if eyebrow else 23}" '
                f'font-weight="{700 if number == title_index else 400}">'
                f"{html.escape(line)}</text>"
            )
        parts.append("</g>")
    parts.append("</svg>\n")
    svg = "\n".join(parts)
    page = (
        HTML.replace("__SVG_CSS__", CSS)
        .replace("__SVG__", svg)
        .replace("__NODES__", json.dumps(nodes).replace("</", "<\\/"))
    )
    return {
        ASSETS / "six-plane-reference.svg": svg,
        ASSETS / "six-plane-reference.html": page,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Reject stale generated previews")
    args = parser.parse_args()
    for path, content in render().items():
        if args.check:
            if not path.is_file() or path.read_text() != content:
                raise SystemExit(f"Stale architecture preview: {path.name}")
        else:
            path.write_text(content)
        print(f"PASS: {path.name}")


if __name__ == "__main__":
    main()
