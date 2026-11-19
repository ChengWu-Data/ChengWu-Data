#!/usr/bin/env python3
"""Refresh the "live from SponsorScope" block in README.md.

Reads the public feed my daily job scan publishes
(chengwu-data.github.io, branch sponsorscope-scan), draws assets/scan.svg and
rewrites the section between the two markers. If the feed can't be read the
script exits with an error and leaves the README as it was.
"""
import json
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

FEED = ("https://raw.githubusercontent.com/ChengWu-Data/"
        "chengwu-data.github.io/sponsorscope-scan/latest.json")
START, END = "<!-- SS:START -->", "<!-- SS:END -->"

# direction id -> label (same names the SponsorScope page uses), tier-1 first
LABELS = {
    "pricing": "Pricing & monetization",
    "gtm": "GTM & revenue operations",
    "ai": "AI deployment & automation",
    "product": "Product operations & strategy",
    "customer": "Customer strategy & commercial ops",
    "solutions": "Solutions & value consulting",
    "stratops": "Strategy & business operations",
    "analytics": "Product, growth & customer analytics",
}


def load():
    req = urllib.request.Request(FEED, headers={"User-Agent": "profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    for key in ("generated", "counts", "boards", "jobs"):
        if key not in data:
            raise SystemExit("feed is missing " + key)
    return data


def svg(counts):
    rows = [("Last 24 hours", counts["day"]), ("Last 7 days", counts["week"])]
    width, left, bar_w = 640, 110, 500
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="130" '
        f'viewBox="0 0 {width} 130" role="img" aria-label="Verdicts for roles my scan found">',
        "<style>",
        "text{font:13px -apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:#24292f}",
        ".m{fill:#57606a;font-size:12px}.w{fill:#fff;font-weight:600}",
        ".a{fill:#1a7f4b}.k{fill:#b7791f}.s{fill:#c0392b}",
        "@media (prefers-color-scheme:dark){text{fill:#e6edf3}.m{fill:#8b949e}"
        ".a{fill:#2ea66a}.k{fill:#d29a3a}.s{fill:#e0584a}}",
        "</style>",
    ]
    y = 20
    for label, c in rows:
        total = max(c["all"], 1)
        out.append(f'<text x="0" y="{y + 17}">{label}</text>')
        x = left
        for key, cls, name in (("apply", "a", "Apply"), ("ask", "k", "Ask first"),
                               ("skip", "s", "Skip")):
            w = bar_w * c[key] / total
            out.append(f'<rect class="{cls}" x="{x:.1f}" y="{y}" width="{w:.1f}" height="26" rx="3"/>')
            if w > 34:
                out.append(f'<text class="w" x="{x + w / 2:.1f}" y="{y + 18}" '
                           f'text-anchor="middle">{c[key]}</text>')
            x += w
        y += 44
    lx = left
    for cls, name in (("a", "Apply: nothing rules me out"),
                      ("k", "Ask first"), ("s", "Skip: rules me out")):
        out.append(f'<rect class="{cls}" x="{lx}" y="{y + 4}" width="10" height="10" rx="2"/>')
        out.append(f'<text class="m" x="{lx + 15}" y="{y + 14}">{name}</text>')
        lx += 190 if cls == "a" else 110
    out.append("</svg>")
    return "\n".join(out)


def block(data):
    c = data["counts"]
    when = datetime.fromisoformat(data["generated"].replace("Z", "+00:00")).astimezone(
        ZoneInfo("America/New_York"))
    stamp = when.strftime("%b %-d, %Y, %-I:%M %p ET")
    boards, rows = data["boards"]["total"], data["boards"].get("rows", 0)

    week = Counter(j["dir"] for j in data["jobs"] if j["verdict"] == "apply")
    lines = [
        f'<p align="center"><img src="assets/scan.svg?v={int(when.timestamp())}" '
        f'alt="Apply, Ask first and Skip counts for the last 24 hours and 7 days" width="640"></p>',
        "",
        f"My scan read **{boards} company job boards ({rows:,} open roles)** and found "
        f"**{c['day']['all']} new roles in the last 24 hours**, of which **{c['day']['apply']}** "
        f"clear my limits. Roles with an Apply verdict in the last 7 days, by direction:",
        "",
        "| Direction | Apply roles |",
        "|---|---:|",
    ]
    for key in sorted(LABELS, key=lambda k: -week.get(k, 0)):
        if week.get(key):
            lines.append(f"| {LABELS[key]} | {week[key]} |")
    lines += ["", f"<sub>Updated {stamp} by a GitHub Action in this repo.</sub>"]
    return "\n".join(lines)


def main():
    data = load()
    open("assets/scan.svg", "w").write(svg(data["counts"]))
    text = open("README.md").read()
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pat.search(text):
        raise SystemExit("markers not found in README.md")
    new = pat.sub(lambda m: START + "\n" + block(data) + "\n" + END, text)
    open("README.md", "w").write(new)
    print("updated")


if __name__ == "__main__":
    sys.exit(main())
