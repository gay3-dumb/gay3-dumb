"""Draws assets/activity.svg: one slim card with a contribution-mix radar, a few
stats and an equalizer of your last 30 days. Uses only the Python standard library.

Run by the GitHub Action in .github/workflows/activity.yml.
Test locally with:  python activity.py --demo
"""
import datetime as dt
import json
import os
import random
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "gay3-dumb")
OUT = os.environ.get("OUT", "assets/activity.svg")
DAYS = 30

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_days():
    token = os.environ["GITHUB_TOKEN"]
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": "bearer " + token, "User-Agent": "activity-svg"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    coll = data["data"]["user"]["contributionsCollection"]
    cal = coll["contributionCalendar"]
    kinds = {
        "commits": coll["totalCommitContributions"],
        "pull requests": coll["totalPullRequestContributions"],
        "issues": coll["totalIssueContributions"],
        "code review": coll["totalPullRequestReviewContributions"],
    }
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    return [(d["date"], d["contributionCount"]) for d in days], cal["totalContributions"], kinds


def demo_days():
    random.seed(4)
    end = dt.date(2026, 11, 6)
    out = []
    for i in range(365, -1, -1):
        d = end - dt.timedelta(days=i)
        n = random.choice([0, 0, 0, 1, 2, 3, 5, 8]) if i < 120 else 0
        out.append((d.isoformat(), n))
    kinds = {"commits": 31, "pull requests": 6, "issues": 4, "code review": 2}
    return out, sum(n for _, n in out), kinds


def streaks(days):
    counts = [n for _, n in days]
    longest = run = 0
    for n in counts:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    cur = 0
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:  # today may not have happened yet
        i -= 1
    while i >= 0 and counts[i] > 0:
        cur += 1
        i -= 1
    return cur, longest


DUCK = """
  <g id="duck">
    <rect x="15" y="0" width="20" height="5" fill="#E6D9BE"/>
    <rect x="10" y="5" width="30" height="5" fill="#E6D9BE"/>
    <rect x="5" y="10" width="10" height="5" fill="#E8943A"/>
    <rect x="15" y="10" width="5" height="5" fill="#E6D9BE"/>
    <rect x="20" y="10" width="5" height="5" fill="#1c1a19"/>
    <rect x="25" y="10" width="15" height="5" fill="#E6D9BE"/>
    <rect x="0" y="15" width="15" height="5" fill="#E8943A"/>
    <rect x="15" y="15" width="25" height="5" fill="#E6D9BE"/>
    <rect x="15" y="20" width="20" height="5" fill="#E6D9BE"/>
    <rect x="10" y="25" width="35" height="5" fill="#E6D9BE"/>
    <rect x="10" y="30" width="45" height="5" fill="#E6D9BE"/>
    <rect x="10" y="35" width="45" height="5" fill="#E6D9BE"/>
    <rect x="10" y="40" width="45" height="5" fill="#E6D9BE"/>
    <rect x="15" y="45" width="35" height="5" fill="#E6D9BE"/>
    <rect x="20" y="50" width="25" height="5" fill="#E6D9BE"/>
    <rect x="25" y="55" width="5" height="10" fill="#E8943A"/>
    <rect x="40" y="55" width="5" height="10" fill="#E8943A"/>
    <rect x="20" y="65" width="10" height="5" fill="#E8943A"/>
    <rect x="40" y="65" width="10" height="5" fill="#E8943A"/>
    <!-- headphones -->
    <rect x="15" y="-5" width="20" height="5" fill="#8a7664"/>
    <rect x="10" y="0" width="5" height="10" fill="#8a7664"/>
    <rect x="30" y="0" width="5" height="10" fill="#8a7664"/>
    <rect x="30" y="5" width="10" height="15" fill="#7A1F2B"/>
    <rect x="30" y="5" width="10" height="3" fill="#D6A756"/>
  </g>"""


def build_radar(kinds):
    import math
    W, H = 800, 300
    f = "font-family=\"'Courier New', monospace\""
    cx, cy, R = 230, 164, 72
    total = sum(kinds.values())
    pct = {k: (v / total if total else 0) for k, v in kinds.items()}
    # same layout as GitHub's own chart: review top, issues right, PRs bottom, commits left
    axes = [("code review", 0, -1), ("issues", 1, 0), ("pull requests", 0, 1), ("commits", -1, 0)]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Activity overview: share of commits, pull requests, issues and code reviews">']
    p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="#1c1a19"/>')
    p.append(f'<rect x="9" y="9" width="{W-18}" height="{H-18}" rx="6" fill="none" stroke="#BE9A5F" stroke-opacity="0.35" stroke-width="1.5" stroke-dasharray="6 6"/>')
    p.append(f'<text x="32" y="38" {f} font-size="14" fill="#BE9A5F">~/gay3 $ git shortlog --summary</text>')
    # the grid is a record: dark disc, groove rings
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{R+10}" fill="#151312"/>')
    for k in (0.25, 0.5, 0.75, 1.0):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{R*k:.1f}" fill="none" stroke="#BE9A5F" stroke-opacity="0.25" stroke-width="1" stroke-dasharray="2 4"/>')
    for name, dx, dy in axes:
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+dx*R}" y2="{cy+dy*R}" stroke="#BE9A5F" stroke-opacity="0.35" stroke-width="1"/>')
    pts = []
    for name, dx, dy in axes:
        r = R * pct[name]
        pts.append((cx + dx * r, cy + dy * r))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    p.append(f'<polygon points="{poly}" fill="#7A1F2B" fill-opacity="0.55" stroke="#D6A756" stroke-width="2" stroke-linejoin="round"/>')
    for x, y in pts:
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#E6D9BE"/>')
    # axis labels
    p.append(f'<text x="{cx}" y="{cy-R-18}" {f} font-size="12" fill="#9a8c7a" text-anchor="middle">code review</text>')
    p.append(f'<text x="{cx}" y="{cy+R+30}" {f} font-size="12" fill="#9a8c7a" text-anchor="middle">pull requests</text>')
    p.append(f'<text x="{cx-R-16}" y="{cy+4}" {f} font-size="12" fill="#9a8c7a" text-anchor="end">commits</text>')
    p.append(f'<text x="{cx+R+16}" y="{cy+4}" {f} font-size="12" fill="#9a8c7a">issues</text>')
    # legend: a tracklist of the four kinds
    p.append(f'<text x="470" y="82" {f} font-size="13" fill="#BE9A5F">in the last year</text>')
    y = 118
    for name in ("commits", "pull requests", "issues", "code review"):
        v = kinds[name]
        share = f"{round(pct[name]*100)}%"
        p.append(f'<text x="470" y="{y}" {f} font-size="15" fill="#E6D9BE">{escape(name)}</text>')
        p.append(f'<line x1="600" y1="{y-4}" x2="680" y2="{y-4}" stroke="#BE9A5F" stroke-opacity="0.35" stroke-width="1.5" stroke-dasharray="2 5"/>')
        p.append(f'<text x="770" y="{y}" {f} font-size="15" font-weight="bold" fill="#E6D9BE" text-anchor="end">{v}</text>')
        p.append(f'<text x="732" y="{y}" {f} font-size="12" fill="#9a8c7a" text-anchor="end" >{share}</text>')
        y += 34
    note = "no plays yet. press record." if total == 0 else "track mix, last 12 months."
    p.append(f'<text x="470" y="{H-26}" {f} font-size="12" fill="#9a8c7a">{note}</text>')
    p.append("</svg>")
    return "\n".join(p)


def build_compact(days, total, kinds):
    last = days[-DAYS:]
    cur, longest = streaks(days)
    month = sum(n for _, n in last)
    best = max((n for _, n in last), default=0)
    mx = max(best, 1)
    W, H = 800, 220
    f = "font-family=\"'Courier New', monospace\""
    esc = escape
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub activity: contribution mix, streaks and the last 30 days">']
    p.append(f"<defs>{DUCK}</defs>")
    p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="#1c1a19"/>')
    p.append(f'<rect x="8" y="8" width="{W-16}" height="{H-16}" rx="6" fill="none" stroke="#BE9A5F" stroke-opacity="0.35" stroke-width="1.5" stroke-dasharray="6 6"/>')
    p.append(f'<text x="26" y="32" {f} font-size="12" fill="#BE9A5F">~/gay3 $ git log --stat</text>')

    # radar (a tiny record)
    cx, cy, R = 128, 118, 50
    t = sum(kinds.values())
    pct = {k: (v / t if t else 0) for k, v in kinds.items()}
    axes = [("code review", 0, -1), ("issues", 1, 0), ("pull requests", 0, 1), ("commits", -1, 0)]
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{R+7}" fill="#151312"/>')
    for k in (0.5, 1.0):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{R*k:.1f}" fill="none" stroke="#BE9A5F" stroke-opacity="0.25" stroke-width="1" stroke-dasharray="2 4"/>')
    for name, dx, dy in axes:
        p.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+dx*R}" y2="{cy+dy*R}" stroke="#BE9A5F" stroke-opacity="0.35" stroke-width="1"/>')
    pts = [(cx + dx * R * pct[n], cy + dy * R * pct[n], n) for n, dx, dy in axes]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
    p.append(f'<polygon points="{poly}" fill="#7A1F2B" fill-opacity="0.6" stroke="#D6A756" stroke-width="1.8" stroke-linejoin="round"/>')
    for x, y, n in pts:
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#E6D9BE"><title>{esc(n)}: {kinds[n]}</title></circle>')
    lab = 'font-size="10" fill="#9a8c7a"'
    p.append(f'<text x="{cx}" y="{cy-R-12}" {f} {lab} text-anchor="middle">code review</text>')
    p.append(f'<text x="{cx}" y="{cy+R+20}" {f} {lab} text-anchor="middle">pull requests</text>')
    p.append(f'<text x="{cx-R-10}" y="{cy+3}" {f} {lab} text-anchor="end">commits</text>')
    p.append(f'<text x="{cx+R+10}" y="{cy+3}" {f} {lab}>issues</text>')

    # stats
    p.append(f'<text x="262" y="90" {f} font-size="38" font-weight="bold" fill="#E6D9BE">{total:,}</text>')
    p.append(f'<text x="262" y="110" {f} font-size="11" fill="#BE9A5F">contributions, last year</text>')
    ys = 138
    for label, val in (("streak", f"{cur}d"), ("longest", f"{longest}d"), ("30 days", str(month))):
        p.append(f'<text x="262" y="{ys}" {f} font-size="12" fill="#9a8c7a">{label}</text>')
        p.append(f'<text x="400" y="{ys}" {f} font-size="12" font-weight="bold" fill="#E6D9BE" text-anchor="end">{esc(val)}</text>')
        ys += 20

    # bars
    x0, bw, gap, base_y, max_h = 440, 8, 3.0, 172, 88
    n = len(last)
    for i, (date, c) in enumerate(last):
        x = x0 + i * (bw + gap)
        h = max(3, round(c / mx * max_h)) if c else 2
        color = "#E6D9BE" if i == n - 1 else ("#BE9A5F" if c else "#5b5148")
        b = f"{i*0.03:.2f}s"
        p.append(f'<rect x="{x:.1f}" y="{base_y}" width="{bw}" height="0" fill="{color}"><title>{esc(date)}: {c}</title>'
                 f'<animate attributeName="height" from="0" to="{h}" dur="0.6s" begin="{b}" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base_y}" to="{base_y-h}" dur="0.6s" begin="{b}" fill="freeze"/></rect>')
    end_x = x0 + n * (bw + gap)
    p.append(f'<line x1="{x0-4}" y1="{base_y+3}" x2="{end_x}" y2="{base_y+3}" stroke="#BE9A5F" stroke-opacity="0.4" stroke-width="1.2" stroke-dasharray="2 5"/>')
    p.append(f'<text x="{x0-4}" y="{base_y+18}" {f} font-size="10" fill="#9a8c7a">30 days ago</text>')
    p.append(f'<text x="{end_x-3}" y="{base_y+18}" {f} font-size="10" fill="#9a8c7a" text-anchor="end">today</text>')
    lc = last[-1][1] if last else 0
    hl = max(3, round(lc / mx * max_h)) if lc else 2
    dx = x0 + (n - 1) * (bw + gap) - 12
    dy = base_y - hl - 38
    p.append(f'<g transform="translate({dx:.1f} {dy:.1f}) scale(0.5)"><g><animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0" dur="0.9s" repeatCount="indefinite"/><use xlink:href="#duck" href="#duck"/></g></g>')
    for sym, sx, dur, bg in (("\u266a", 500, 5.0, 0), ("&lt;/&gt;", 610, 6.5, 1.5), ("\u266b", 700, 5.5, 3)):
        p.append(f'<text x="{sx}" y="80" {f} font-size="14" fill="#BE9A5F" opacity="0">{sym}'
                 f'<animate attributeName="y" values="100;45" dur="{dur}s" begin="{bg}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0.5;0" dur="{dur}s" begin="{bg}s" repeatCount="indefinite"/></text>')
    mix = f'commits {kinds["commits"]}  \u00b7  prs {kinds["pull requests"]}  \u00b7  issues {kinds["issues"]}  \u00b7  reviews {kinds["code review"]}'
    p.append(f'<text x="26" y="{H-16}" {f} font-size="11" fill="#9a8c7a">{esc(mix)}</text>')
    stamp = last[-1][0] if last else ""
    p.append(f'<text x="{W-26}" y="{H-16}" {f} font-size="10" fill="#6f6558" text-anchor="end">updated {esc(stamp)}</text>')
    p.append("</svg>")
    return "\n".join(p)


def build(days, total):
    last = days[-DAYS:]
    cur, longest = streaks(days)
    month = sum(n for _, n in last)
    best = max(n for _, n in last) if last else 0
    mx = max(best, 1)

    W, H = 800, 300
    base_y, max_h = 232, 125
    x0, bw, gap = 288, 10, 5.0
    f = "font-family=\"'Courier New', monospace\""

    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution activity for the last 30 days">')
    p.append(f"<defs>{DUCK}</defs>")
    # panel works on both light and dark GitHub themes
    p.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="#1c1a19"/>')
    p.append(f'<rect x="9" y="9" width="{W-18}" height="{H-18}" rx="6" fill="none" stroke="#BE9A5F" stroke-opacity="0.35" stroke-width="1.5" stroke-dasharray="6 6"/>')
    # prompt line
    p.append(f'<text x="32" y="38" {f} font-size="14" fill="#BE9A5F">~/gay3 $ git log --last-30-days</text>')

    # stats
    p.append(f'<text x="32" y="98" {f} font-size="44" font-weight="bold" fill="#E6D9BE">{total:,}</text>')
    p.append(f'<text x="32" y="120" {f} font-size="13" fill="#BE9A5F">contributions in the last year</text>')
    rows = [("current streak", f"{cur} day{'s' if cur != 1 else ''}"),
            ("longest streak", f"{longest} day{'s' if longest != 1 else ''}"),
            ("last 30 days", str(month)),
            ("busiest day", str(best))]
    y = 156
    for label, val in rows:
        p.append(f'<text x="32" y="{y}" {f} font-size="14" fill="#9a8c7a">{escape(label)}</text>')
        p.append(f'<text x="240" y="{y}" {f} font-size="14" font-weight="bold" fill="#E6D9BE" text-anchor="end">{escape(val)}</text>')
        y += 24

    # equalizer bars
    n = len(last)
    for i, (date, c) in enumerate(last):
        x = x0 + i * (bw + gap)
        h = max(4, round(c / mx * max_h)) if c else 3
        top = base_y - h
        color = "#BE9A5F" if c else "#5b5148"
        if i == n - 1:
            color = "#E6D9BE"
        begin = f"{i*0.035:.2f}s"
        p.append(
            f'<rect x="{x:.1f}" y="{base_y}" width="{bw}" height="0" fill="{color}">'
            f'<title>{escape(date)}: {c} contribution{"s" if c != 1 else ""}</title>'
            f'<animate attributeName="height" from="0" to="{h}" dur="0.7s" begin="{begin}" fill="freeze"/>'
            f'<animate attributeName="y" from="{base_y}" to="{top}" dur="0.7s" begin="{begin}" fill="freeze"/>'
            f'</rect>')
    # baseline + axis labels
    p.append(f'<line x1="{x0-6}" y1="{base_y+3}" x2="{x0 + n*(bw+gap)}" y2="{base_y+3}" stroke="#BE9A5F" stroke-opacity="0.4" stroke-width="1.5" stroke-dasharray="2 6"/>')
    p.append(f'<text x="{x0-6}" y="{base_y+22}" {f} font-size="11" fill="#9a8c7a">30 days ago</text>')
    p.append(f'<text x="{x0 + n*(bw+gap) - 6}" y="{base_y+22}" {f} font-size="11" fill="#9a8c7a" text-anchor="end">today</text>')

    # duck standing on today's bar, headphones on, bobbing
    last_c = last[-1][1] if last else 0
    h_last = max(4, round(last_c / mx * max_h)) if last_c else 3
    dx = x0 + (n - 1) * (bw + gap) - 12
    dy = base_y - h_last - 44
    p.append(f'<g transform="translate({dx:.1f} {dy:.1f}) scale(0.6)"><g>'
             f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" dur="0.9s" repeatCount="indefinite"/>'
             f'<use xlink:href="#duck" href="#duck"/></g></g>')

    # floating symbols
    for sym, sx, dur, bg in [("♪", 440, 5.0, 0), ("&lt;/&gt;", 580, 6.5, 1.5), ("♫", 680, 5.5, 3)]:
        p.append(f'<text x="{sx}" y="130" {f} font-size="16" fill="#BE9A5F" opacity="0">{sym}'
                 f'<animate attributeName="y" values="150;55" dur="{dur}s" begin="{bg}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0.55;0" dur="{dur}s" begin="{bg}s" repeatCount="indefinite"/></text>')

    note = "side A is quiet. first commit incoming." if month == 0 else "now playing: your commits."
    p.append(f'<text x="32" y="{H-26}" {f} font-size="12" fill="#9a8c7a">{escape(note)}</text>')
    stamp = last[-1][0] if last else ""
    p.append(f'<text x="{W-32}" y="{H-26}" {f} font-size="11" fill="#6f6558" text-anchor="end">updated {escape(stamp)}</text>')
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    if "--demo" in sys.argv:
        days, total, kinds = demo_days()
    else:
        days, total, kinds = fetch_days()
    folder = os.path.dirname(OUT) or "."
    os.makedirs(folder, exist_ok=True)
    for name, svg in (("activity.svg", build_compact(days, total, kinds)),):
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("wrote", path, len(svg), "bytes")
