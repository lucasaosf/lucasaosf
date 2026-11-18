import os
import math
import urllib.request
import json
from collections import defaultdict
from datetime import date

login = os.environ.get("GH_LOGIN", "lucasaosf")
token = os.environ.get("GITHUB_TOKEN")

def get_headers():
    h = {"User-Agent": "Mozilla/5.0 (compatible; GitHubStatusHUD/1.0)"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


# 1. User & Repos Info
req = urllib.request.Request(f"https://api.github.com/users/{login}", headers=get_headers())
with urllib.request.urlopen(req) as resp:
    user_info = json.loads(resp.read().decode())

req_repos = urllib.request.Request(f"https://api.github.com/users/{login}/repos?per_page=100", headers=get_headers())
with urllib.request.urlopen(req_repos) as resp:
    repos = json.loads(resp.read().decode())

stars = sum(r['stargazers_count'] for r in repos)
public_repos = user_info['public_repos']
followers = user_info['followers']

# 2. Languages
langs = defaultdict(int)
for r in repos:
    try:
        req_l = urllib.request.Request(r['languages_url'], headers=get_headers())
        with urllib.request.urlopen(req_l) as resp:
            l_data = json.loads(resp.read().decode())
            for lang, bytes_cnt in l_data.items():
                langs[lang] += bytes_cnt
    except Exception:
        pass

# 3. Contributions & Streaks
url_contrib = f"https://github-contributions-api.jogruber.de/v4/{login}"
req_c = urllib.request.Request(url_contrib, headers=get_headers())
with urllib.request.urlopen(req_c) as resp:
    c_data = json.loads(resp.read().decode())

days = c_data.get('contributions', [])
days.sort(key=lambda d: d['date'])

today_str = date.today().isoformat()
total_contribs = 0
longest_streak = 0
current_streak = 0

for d in days:
    dt = d['date']
    if dt > today_str:
        break
    c = d['count']
    total_contribs += c
    if c > 0:
        current_streak += 1
        if current_streak > longest_streak:
            longest_streak = current_streak
    elif dt != today_str:
        current_streak = 0

commits_last_12m = c_data.get('total', {}).get('2026', 0)

# Level calculations
level = math.floor(math.sqrt(total_contribs))
lo = level ** 2
hi = (level + 1) ** 2
xp = (total_contribs - lo) / (hi - lo) if hi > lo else 0

# Language percentages
total_lang_bytes = sum(langs.values()) or 1
sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]
top_langs = [(name, (cnt / total_lang_bytes) * 100) for name, cnt in sorted_langs]

# Color Palette: BioKuri Green Theme
BG = "#07140B"
LINE = "#1B3B24"
LINE_SUBTLE = "#132D1B"
GREEN_NEON = "#38E54D"
EMERALD = "#4ECCA3"
CREME = "#F2EBDD"
SAGE = "#B2C2A5"
DIM = "#6E846A"
GOLD = "#C5A059"
BLUE = "#38A3A5"

W = 880
H = 330
mono = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
sans = "'Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif"

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def fmt(n):
    return f"{n:,}".replace(",", ".")

big = [
    ("CONTRIBUTIONS", fmt(total_contribs), "since start"),
    ("CURRENT STREAK", fmt(current_streak), "days in a row" if current_streak != 1 else "day in a row"),
    ("LONGEST STREAK", fmt(longest_streak), "days" if longest_streak != 1 else "day")
]

big_svg = []
for i, (l, v, sub) in enumerate(big):
    x = 40 + i * 176
    sep = f'<path d="M-20 -6 V78" stroke="{LINE}"/>' if i else ""
    val_color = EMERALD if i == 1 else CREME
    big_svg.append(f"""<g transform="translate({x} 112)">{sep}
<text font-family="{mono}" font-size="10.5" letter-spacing="2" fill="{DIM}">{l}</text>
<text y="50" font-family="{sans}" font-size="46" font-weight="700" fill="{val_color}">{v}</text>
<text y="72" font-family="{mono}" font-size="10.5" fill="{DIM}">{sub}</text></g>""")
big_svg_str = "".join(big_svg)

rows = [
    ("COMMITS (12 MOS)", commits_last_12m),
    ("PULL REQUESTS", 0),
    ("ISSUES", 0),
    ("STARS", stars),
    ("PUBLIC REPOS", public_repos),
    ("FOLLOWERS", followers)
]

row_svg = []
for i, (l, v) in enumerate(rows):
    x = 40 + (i % 3) * 176
    y = 232 + (i // 3) * 44
    row_svg.append(f"""<g transform="translate({x} {y})">
<text font-family="{mono}" font-size="9.5" letter-spacing="1.5" fill="{DIM}">{l}</text>
<text y="22" font-family="{mono}" font-size="17" font-weight="600" fill="{CREME}">{fmt(v)}</text></g>""")
row_svg_str = "".join(row_svg)

bx = 598
bw = 242
lang_colors = [EMERALD, GREEN_NEON, BLUE, GOLD, SAGE]

lang_svg = []
for i, (n, p) in enumerate(top_langs):
    y = 110 + i * 40
    w = max(3.0, (p / 100.0) * bw)
    color = lang_colors[i % len(lang_colors)]
    lang_svg.append(f"""<g transform="translate({bx} {y})">
<text font-family="{mono}" font-size="11.5" fill="{SAGE}">{esc(n)}</text>
<text x="{bw}" text-anchor="end" font-family="{mono}" font-size="11.5" fill="{DIM}">{p:.1f}%</text>
<rect y="9" width="{bw}" height="7" rx="2" fill="{LINE_SUBTLE}"/>
<rect class="bar" style="animation-delay:{i*0.12:.2f}s" y="9" width="{w:.1f}" height="7" rx="2" fill="{color}"/>
</g>""")
lang_svg_str = "".join(lang_svg)

svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub Status Lucas Aøsf: {fmt(total_contribs)} contributions, current streak {current_streak}, longest streak {longest_streak}">
<defs>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="#4ECCA3" opacity=".03"/>
  </pattern>
  <linearGradient id="xpGrad" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="{GREEN_NEON}"/>
    <stop offset="100%" stop-color="{EMERALD}"/>
  </linearGradient>
</defs>
<style>
  .bar {{ transform-origin: 0 0; animation: g 1.1s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes g {{ from {{ transform: scaleX(0); }} }}
  .xp {{ transform-origin: 40px 0; animation: g 1.4s cubic-bezier(.2,.8,.2,1) both; }}
  .dot {{ animation: b 1.6s steps(1) infinite; }}
  @keyframes b {{ 50% {{ opacity: .15; }} }}
  @media (prefers-reduced-motion: reduce) {{ .bar, .xp, .dot {{ animation: none; }} }}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>
<rect width="{W}" height="{H}" rx="14" fill="url(#scan)"/>

<g fill="none" stroke="{EMERALD}" stroke-width="1.5" opacity="0.85">
  <path d="M14 34 V14 H34"/>
  <path d="M{W - 34} 14 H{W - 14} V34"/>
  <path d="M14 {H - 34} V{H - 14} H34"/>
  <path d="M{W - 34} {H - 14} H{W - 14} V{H - 34}"/>
</g>

<text x="40" y="50" font-family="{mono}" font-size="12" letter-spacing="3" fill="{SAGE}">STATUS <tspan fill="{DIM}">// @{esc(login)}</tspan></text>
<text x="40" y="74" font-family="{mono}" font-size="12" font-weight="700" fill="{EMERALD}">LV {level}</text>

<rect x="100" y="66" width="390" height="7" rx="2" fill="{LINE_SUBTLE}"/>
<g transform="translate(60 0)">
  <rect class="xp" x="40" y="66" width="{(xp * 390):.1f}" height="7" rx="2" fill="url(#xpGrad)"/>
</g>
<text x="528" y="74" text-anchor="end" font-family="{mono}" font-size="9.5" fill="{DIM}">XP</text>

<circle class="dot" cx="{W - 44}" cy="46" r="4.5" fill="{GREEN_NEON}"/>
<text x="{W - 56}" y="50" text-anchor="end" font-family="{mono}" font-size="10.5" letter-spacing="2" fill="{DIM}">LIVE</text>

{big_svg_str}

<path d="M40 206 H528" stroke="{LINE}"/>

{row_svg_str}

<path d="M563 40 V{H - 40}" stroke="{LINE}"/>

<text x="{bx}" y="74" font-family="{mono}" font-size="10.5" letter-spacing="2" fill="{DIM}">TOP LANGUAGES</text>
{lang_svg_str}
</svg>"""

out_path = os.environ.get("HUD_OUT", "assets/hud.svg")
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.write(svg_content)
print(f"HUD generated at {out_path}")
