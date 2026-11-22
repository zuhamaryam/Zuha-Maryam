"""Builds radar-chart.svg from the language mix across your public, non-fork repos.

Runs with the standard library only. Writes radar-chart.svg in the repo root.
"""
import json
import math
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "zuhamaryam")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "language-radar"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

MAX_AXES = 6
CX, CY, R = 230, 210, 140
BG, GRID, TEXT, MUTED, ACCENT, CYAN = "#0d1117", "#30363d", "#c9d1d9", "#8b949e", "#00FF41", "#00F0FF"


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def language_totals():
    repos, page = [], 1
    while True:
        batch = get_json(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        if not batch:
            break
        repos.extend(batch)
        page += 1

    totals = Counter()
    for repo in repos:
        if repo.get("fork"):
            continue
        totals.update(get_json(repo["languages_url"]))
    return totals


def build_svg(top, updated):
    n = max(len(top), 3)
    top = top + [("n/a", 0.0)] * (n - len(top))
    max_share = max(share for _, share in top) or 1.0

    def point(i, scale):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        return CX + R * scale * math.cos(angle), CY + R * scale * math.sin(angle), angle

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="440" viewBox="0 0 460 440" role="img" aria-label="Language mix radar for {USER}">',
        f'<rect width="460" height="440" rx="14" fill="{BG}"/>',
        f'<text x="30" y="40" font-family="ui-monospace,Menlo,monospace" font-size="13" letter-spacing="2" fill="{ACCENT}">LANGUAGE MIX · LIVE</text>',
    ]

    for ring in (0.25, 0.5, 0.75, 1.0):
        pts = " ".join(f"{point(i, ring)[0]:.1f},{point(i, ring)[1]:.1f}" for i in range(n))
        out.append(f'<polygon points="{pts}" fill="none" stroke="{GRID}" stroke-width="1"/>')

    for i, (name, share) in enumerate(top):
        x, y, angle = point(i, 1.0)
        out.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        lx, ly = CX + (R + 26) * math.cos(angle), CY + (R + 26) * math.sin(angle)
        anchor = "middle" if abs(math.cos(angle)) < 0.2 else ("start" if math.cos(angle) > 0 else "end")
        out.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-family="ui-monospace,Menlo,monospace" '
            f'font-size="12" fill="{TEXT}">{name} {share * 100:.1f}%</text>'
        )

    data = " ".join(f"{point(i, share / max_share)[0]:.1f},{point(i, share / max_share)[1]:.1f}" for i, (_, share) in enumerate(top))
    out.append(f'<polygon points="{data}" fill="{ACCENT}" fill-opacity="0.25" stroke="{ACCENT}" stroke-width="2"/>')
    for i, (_, share) in enumerate(top):
        x, y, _ = point(i, share / max_share)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{CYAN}"/>')

    out.append(f'<text x="30" y="420" font-family="ui-monospace,Menlo,monospace" font-size="11" fill="{MUTED}">updated {updated} UTC · public repos, forks excluded</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    totals = language_totals()
    total_bytes = sum(totals.values()) or 1
    top = [(name, size / total_bytes) for name, size in totals.most_common(MAX_AXES)]
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    with open("radar-chart.svg", "w", encoding="utf-8") as f:
        f.write(build_svg(top, updated))
    print("wrote radar-chart.svg with", len(top), "languages")


if __name__ == "__main__":
    main()
