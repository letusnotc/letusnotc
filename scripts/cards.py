#!/usr/bin/env python3
"""Fetch letusnotc's public contribution calendar and render the README cards into cards/.

Every card is a standalone animated SVG shown through <img>: CSS animations, SMIL and fonts
embedded as data URIs only (GitHub allows no JS or external requests there).
Standard library only. Run with STATIC=1 to render every animation at its end state.
Run with OFFLINE=1 to reuse data/contributions.json instead of fetching.
"""
import base64
import datetime as dt
import json
import os
import re
import urllib.request
from html import escape, unescape

USER = "letusnotc"
SITE = "arnav-pandey.vercel.app"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT, FONTS, DATA = (os.path.join(ROOT, p) for p in ("cards", "fonts", "data/contributions.json"))
STATIC = bool(os.environ.get("STATIC"))

# ---- your content -----------------------------------------------------------------------
KICKER = "AI & ML ENGINEER  ·  IIIT NAYA RAIPUR"
FIRST, LAST = "Arnav", "Pandey"
TAGLINE = ["I build AI systems that solve real problems,", "from health monitoring to voice payments."]
TERMINAL = [
    ("$ whoami", "cmd"),
    ("B.Tech Data Science & AI", "out"),
    ("competitive programmer", "out"),
    ("$ cat stack.txt", "cmd"),
    ("python  c++  pytorch  tensorflow", "out"),
    ("opencv  huggingface  langchain  fastapi", "out"),
    ("$ learning --now", "cmd"),
    ("vision, multimodal AI, LLM agents", "out"),
]
TILES = [  # file, label, colour, text colour, number, word, blurb
    ("build", "BUILD", "forest", "#ffffff", "3", "AI products",
     "SwasthyaAI, Vachan Pay and SentinelAI: health, voice payments and sentiment."),
    ("win", "HACKATHONS", "olive", "#111111", "4", "podiums",
     "1st at a national hackathon and at Lazarus Mission, Codeutsava 9.0 winner, 2nd at Think Plus."),
    ("rank", "KAGGLE", "amber", "#111111", "9", "of 4000+",
     "Best Playground Series rank. Also 38 of 2500+, and 4th at NIT Kurukshetra."),
]
REPOS = [  # repo (None = no public repo), title, description, language, colour
    ("bp-proba-api", "SwasthyaAI", "BP prediction with ARIMA forecasts and Gemini insights. 23% better early risk detection.", "Next.js · MongoDB", "forest"),
    ("vachan-pay", "Vachan Pay", "Voice UPI payments in English and Hindi. 95%+ command accuracy across accents.", "TypeScript", "olive"),
    ("SENTINEL.AI", "SentinelAI", "YouTube sentiment analytics with RoBERTa and emoji heatmaps, 5000+ comments.", "TypeScript", "amber"),
]
STACK = [
    ("LANGUAGES", "Python, C++, MySQL"),
    ("MACHINE LEARNING", "scikit-learn, XGBoost, LightGBM, CatBoost, AutoGluon, PyTorch, TensorFlow, Optuna"),
    ("COMPUTER VISION", "OpenCV, Swin V2, ResNet, SupCon, MediaPipe, Albumentations"),
    ("NLP & GENAI", "HuggingFace, LangChain, Gemini API, Ollama, sentence embeddings, Stable Diffusion"),
    ("BACKEND & TOOLS", "Flask, FastAPI, Docker, Git, Streamlit, RAPIDS, Pandas, NumPy"),
]
WINS = [
    ("HACKATHONS", ["1st, national-level hackathon (Alzheimer's assistance AI)",
                    "Problem statement winner, Codeutsava 9.0 (SwasthyaAI)",
                    "2nd, Think Plus national hackathon"]),
    ("ML COMPETITIONS", ["1st, Lazarus Mission ML hackathon (NIT Karnataka)",
                         "4th, ML competition (NIT Kurukshetra)",
                         "Kaggle Playground: 9 of 4000+, 38 of 2500+"]),
]

# ---- look ---------------------------------------------------------------------------------
PAPER, PAPER_DEEP, INK, INK_SOFT, MUTED, RULE = "#f3f3f1", "#e2e2de", "#111111", "#3a3a3c", "#6e6e73", "#dcdcd7"
COLOR = {"forest": "#587529", "olive": "#71951E", "amber": "#F4BE38", "sun": "#EDDA5E"}
RAMP = [PAPER_DEEP, COLOR["sun"], COLOR["amber"], COLOR["olive"], COLOR["forest"], "#3d5219"]
W, GAP = 880, 12
THIRD = W / 3 - 8  # three cards plus two 12px gaps fill the column
SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, Menlo, monospace"
FONT_FILES = {"serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
              "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
              "sans": ("Geist", "normal", 400, "geist-400.woff"),
              "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
              "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff")}
ANIM = ".up,.in,.bar,.dot,.blink,.drop"
CSS = """
@keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes in{from{opacity:0}to{opacity:1}}
@keyframes bar{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes dot{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
@keyframes drop{0%{opacity:0;transform:translateY(70px) scale(.7) rotate(-6deg)}60%{opacity:1;transform:translateY(-6px) scale(1.03) rotate(1deg)}100%{opacity:1;transform:none}}
.up{opacity:0;animation:up .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.in{opacity:0;animation:in .8s ease-out both}
.bar{transform-box:fill-box;transform-origin:bottom;animation:bar .8s cubic-bezier(.2,.7,.2,1) both}
.dot{opacity:0;transform-box:fill-box;transform-origin:center;animation:dot .4s ease-out both}
.blink{animation:blink 1.6s ease-in-out infinite}
.drop{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:drop 1s cubic-bezier(.2,.8,.2,1) both}
"""
STILL = f"{ANIM}{{animation:none!important;opacity:1!important;transform:none!important}}"
CSS += f"@media (prefers-reduced-motion:reduce){{{STILL}}}"


def fonts(keys):
    out = ""
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), "rb").read()).decode()
        out += f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};src:url(data:font/woff;base64,{b64}) format('woff')}}"
    return out


def save(name, w, h, body, label, keys, left=0, right=0, bottom=GAP):
    """Write one card; left/right/bottom pad it so cards tile with even gaps inside the README."""
    w2, h2 = w + left + right, h + bottom
    css = fonts(keys) + CSS + (STILL if STATIC else "")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w2:.3f}" height="{h2}" viewBox="0 0 {w2:.3f} {h2}" '
           f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><style>{css}</style>'
           f'<g transform="translate({left:.3f} 0)">{body}</g></svg>')
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote cards/{name} ({len(svg) // 1024} KB)")


def at(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def lines_svg(x, y, lines, lh, attrs):
    return "".join(f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(t)}</text>' for i, t in enumerate(lines))


# ---- data ---------------------------------------------------------------------------------
def parse_calendar(html):
    """GitHub's contributions page -> [{date, count}] sorted by date."""
    dates = dict(re.findall(r'data-date="([\d-]+)" id="(contribution-day-component-[\d-]+)"', html))
    dates = {v: k for k, v in dates.items()}
    counts = {}
    for cid, tip in re.findall(r'<tool-tip[^>]*for="(contribution-day-component-[\d-]+)"[^>]*>([^<]*)', html):
        m = re.match(r"\s*(\d+) contribution", unescape(tip))
        counts[cid] = int(m.group(1)) if m else 0
    return sorted(({"date": dates[c], "count": counts.get(c, 0)} for c in dates), key=lambda d: d["date"])


def summarise(days):
    counts = [d["count"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    tail = counts[:-1] if counts and counts[-1] == 0 else counts  # today may not have a commit yet
    current = 0
    for c in reversed(tail):
        if not c:
            break
        current += 1
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    best = max(days, key=lambda d: d["count"])
    return {"days": days, "total": sum(counts), "active": sum(1 for c in counts if c),
            "current": current, "longest": longest, "best_day": best,
            "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())]}


def load():
    if os.environ.get("OFFLINE"):
        return json.load(open(DATA))
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions", headers={"User-Agent": "profile-cards"})
    days = parse_calendar(urllib.request.urlopen(req, timeout=30).read().decode())
    if len(days) < 300:
        raise SystemExit(f"calendar parse looks wrong: only {len(days)} days")  # keep yesterday's cards
    data = summarise(days)
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    json.dump(data, open(DATA, "w"), indent=1)
    return data


def repo_meta():
    """Stars per repo from the public API; empty if offline or rate-limited."""
    stars = {}
    for repo, *_ in REPOS:
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{USER}/{repo}", headers={"User-Agent": "profile-cards"})
            stars[repo] = json.load(urllib.request.urlopen(req, timeout=10)).get("stargazers_count", 0)
        except Exception as e:
            print(f"stars for {repo} unavailable: {e}")
    return stars


# ---- cards --------------------------------------------------------------------------------
def hero():
    h = 400
    term = []
    for i, (t, kind) in enumerate(TERMINAL):
        fill = COLOR["forest"] if kind == "cmd" else INK_SOFT
        gap = 10 if kind == "cmd" and i else 0
        term.append((t, fill, gap))
    y, rows = 96, []
    for i, (t, fill, gap) in enumerate(term):
        y += gap
        rows.append(f'<text class="in" {at(0.9 + i * 0.22)} x="540" y="{y}" font-family="{MONO}" font-size="12.5" fill="{fill}">{escape(t)}</text>')
        y += 24
    cursor_y = y - 24 + 6
    body = f"""
<defs><linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
  <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/><stop offset=".5" stop-color="{COLOR['amber']}"/>
  <stop offset=".58" stop-color="{INK}"/><stop offset="1" stop-color="{INK}"/>
  {"" if STATIC else '<animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0" keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>'}
</linearGradient></defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="in" {at(0)}>
  <rect class="blink" x="48" y="49" width="8" height="8" rx="2" fill="{COLOR['forest']}"/>
  <text x="66" y="57" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">{escape(KICKER)}</text>
</g>
<text class="up" {at(0.15)} x="44" y="180" font-family="{SERIF}" font-size="112" letter-spacing="-2.5" fill="{INK}">{FIRST}</text>
<text class="up" {at(0.3)} x="44" y="278" font-family="{SERIF}" font-style="italic" font-size="112" letter-spacing="-2.5" fill="url(#shine)">{LAST}</text>
<g class="up" {at(0.55)}>{lines_svg(48, 318, TAGLINE, 27, f'font-family="{SANS}" font-size="18" fill="{INK_SOFT}"')}</g>
<g class="in" {at(0.8)}>
  <text x="48" y="376" font-family="{MONO}" font-size="13" fill="{INK}">{SITE}</text>
  <text x="{48 + 7.8 * len(SITE) + 8:.0f}" y="376" font-family="{MONO}" font-size="13" fill="{COLOR['forest']}">&#8599;</text>
</g>
<rect class="in" {at(0.7)} x="516" y="60" width="330" height="{cursor_y - 60 + 30}" rx="10" fill="#ffffff" stroke="{RULE}"/>
{''.join(rows)}
<rect class="blink" x="540" y="{cursor_y + 4}" width="8" height="14" fill="{INK}"/>
"""
    save("hero.svg", W, h, body, f"{FIRST} {LAST}. {KICKER}. {' '.join(TAGLINE)}", ["serif", "serif-i", "sans", "mono"])


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    """Number counts up from 0 using SMIL <set> frames, which work inside <img>."""
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
    if STATIC:
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'
    val, out = int(num), []
    for i in range(frames + 1):
        shown = num if i == frames else str(round(val * (1 - (1 - i / frames) ** 3)))
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" {attrs} opacity="0">{shown}{tail}'
                   f'<set attributeName="opacity" to="1" begin="{begin + dur * i / frames:.3f}s"/>{off}</text>')
    return "".join(out)


def tile(pos, name, label, colour, on, num, word, blurb):
    delay = 2.9 + pos * 0.25
    h = 210
    text = "".join(f'<text x="24" y="{148 + i * 20}" font-family="{SANS}" font-size="14" fill="{on}" opacity=".92">{escape(t)}</text>'
                   for i, t in enumerate(wrap(blurb, 36)[:3]))
    body = f"""
<g class="drop" {at(delay)}>
  <rect width="{THIRD}" height="{h}" rx="14" fill="{COLOR[colour]}"/>
  <text x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{on}">{label}</text>
  <text x="{THIRD - 34:.0f}" y="38" font-family="{MONO}" font-size="14" fill="{on}">&#8594;</text>
  {count_up(num, word, 22, 108, f'font-family="{SERIF}" font-size="44" fill="{on}"', delay + 0.4)}
  {text}
</g>"""
    save(f"{name}.svg", THIRD, h, body, f"{label}: {num} {word}. {blurb}", ["serif", "serif-i", "sans", "mono"],
         left=4 * pos, right=8 - 4 * pos)


def heatmap(data):
    days = data["days"]
    lead = (dt.date.fromisoformat(days[0]["date"]).weekday() + 1) % 7  # Sunday is row 0
    step, gx, gy = 15, 44, 96
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        col, row = divmod(i + lead, 7)
        date = dt.date.fromisoformat(day["date"])
        if row == 0 and date.day <= 7 and date.month not in seen:
            seen.add(date.month)
            months.append((col, date.strftime("%b")))
        c = day["count"]
        level = 0 if c == 0 else 1 if c <= 3 else 2 if c <= 8 else 3 if c <= 15 else 4 if c <= 30 else 5
        cells.append(f'<rect class="dot" {at(1.0 + col * 0.03 + row * 0.02)} x="{gx + col * step}" y="{gy + row * step}" '
                     f'width="12" height="12" rx="3" fill="{RAMP[level]}"><title>{day["date"]}: {c}</title></rect>')
    right = gx + ((len(days) + lead + 6) // 7) * step - 3
    ly = gy + 7 * step + 16
    labels = "".join(f'<text x="{gx + c * step}" y="{ly}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
                     for c, m in months if gx + c * step < right - 150)
    lx = right - len(RAMP) * 14
    legend = "".join(f'<rect x="{lx + i * 14}" y="{ly - 10}" width="11" height="11" rx="2.5" fill="{c}"/>' for i, c in enumerate(RAMP))
    h = gy + 7 * step + 44
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="up" {at(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{COLOR['forest']}">in green</tspan></text>
<text class="in" {at(0.8)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>
{''.join(cells)}
<g class="in" {at(2.4)}>{labels}
<text x="{lx - 8}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>{legend}
<text x="{lx + len(RAMP) * 14 + 2}" y="{ly}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>"""
    save("heatmap.svg", W, h, body, f"Contribution graph: {data['total']:,} contributions in the last year", ["serif", "serif-i", "mono"])


def activity(data):
    h = 340
    monthly = data["monthly"][-12:]
    best = max(monthly[:-1] or monthly, key=lambda m: m["total"])
    top = max(best["total"], 1)
    x0, x1, base, maxh, gap = 40, 600, 292, 140, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, m in enumerate(monthly):
        bh = max(4, round(min(m["total"], top) / top * maxh))
        x = x0 + i * (bw + gap)
        fill = COLOR["forest"] if m is best else ("#c9c9c4" if i == len(monthly) - 1 else INK)
        label = dt.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(f'<rect class="bar" {at(2.0 + i * 0.07)} x="{x:.1f}" y="{base - bh}" width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}">'
                    f'<title>{label}: {m["total"]:,}</title></rect>'
                    f'<text class="in" {at(2.0 + i * 0.07)} x="{x + bw / 2:.1f}" y="{base + 22}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>')
        if m is best:
            bars.append(f'<text class="dot" {at(3.0)} x="{x + bw / 2:.1f}" y="{base - bh - 10}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{COLOR["forest"]}">{m["total"]:,}</text>')
    cur, lng = data["current"], data["longest"]
    stats = [(f'{cur} <tspan font-style="italic">{"day" if cur == 1 else "days"}</tspan>',
              "current streak, and the longest" if cur >= lng else f"current streak, longest {lng}"),
             (f'{data["active"]}<tspan fill="#8e8e93"> / {len(data["days"])}</tspan>', "days with a commit"),
             (str(data["best_day"]["count"]), "on the busiest day")]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(f'<g class="up" {at(2.4 + i * 0.15)}><text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text>'
                    f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>')
        if i < 2:
            side.append(f'<rect class="in" {at(2.4)} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="in" {at(1.8)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="up" {at(1.9)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{data['total']:,} <tspan font-style="italic">contributions</tspan></text>
{''.join(bars)}{''.join(side)}"""
    save("activity.svg", W, h, body, f"{data['total']:,} contributions in the last year, {cur}-day streak", ["serif", "serif-i", "sans", "mono"])


def title(name, text, italic):
    for theme, fg in (("light", INK), ("dark", "#e6edf3")):
        body = f'<text class="up" {at(0.3)} x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}">{escape(text)} <tspan font-style="italic">{escape(italic)}</tspan></text>'
        save(f"title-{name}-{theme}.svg", W, 64, body, f"{text} {italic}", ["serif", "serif-i"], bottom=0)


def repo_card(pos, repo, name, desc, lang, colour, stars):
    h = 176
    meta = lang + (f"  ·  ★ {stars}" if stars else "")
    body = f"""
<rect width="{THIRD}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="up" {at(0.5 + pos * 0.12)}>
  <rect x="24" y="30" width="8" height="8" rx="2" fill="{COLOR[colour]}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{INK}">{escape(name)}</text>
  {lines_svg(24, 72, wrap(desc, 36)[:3], 21, f'font-family="{SANS}" font-size="14" fill="{INK_SOFT}"')}
  <text x="24" y="{h - 24}" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape(meta)}</text>
</g>"""
    save(f"repo-{repo}.svg", THIRD, h, body, f"{name}: {desc}", ["sans", "sans-b", "mono"], left=4 * pos, right=8 - 4 * pos)


def stack():
    rows, y = [], 112
    for i, (label, tools) in enumerate(STACK):
        lines = wrap(tools, 62)
        rows.append(f'<g class="up" {at(0.4 + i * 0.1)}><text x="40" y="{y}" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{COLOR["forest"]}">{escape(label)}</text>'
                    + lines_svg(250, y, lines, 22, f'font-family="{SANS}" font-size="15" fill="{INK_SOFT}"') + "</g>")
        y += 22 * len(lines) + 12
        if i < len(STACK) - 1:
            rows.append(f'<rect class="in" {at(0.4)} x="40" y="{y - 16}" width="{W - 80}" height="1" fill="{RULE}"/>')
            y += 12
    h = y + 14
    body = f"""<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="up" {at(0.2)} x="40" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">The <tspan font-style="italic">stack</tspan></text>
{''.join(rows)}"""
    save("stack.svg", W, h, body, "Tech stack. " + ". ".join(f"{a}: {b}" for a, b in STACK), ["serif", "serif-i", "sans", "mono"])


def wins():
    cols = []
    for c, (label, items) in enumerate(WINS):
        x = 40 + c * 410
        out = f'<text x="{x}" y="112" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{COLOR["forest"]}">{label}</text>'
        y = 144
        for item in items:
            ls = wrap(item, 46)
            out += f'<rect x="{x}" y="{y - 9}" width="6" height="6" rx="1.5" fill="{INK}"/>' + lines_svg(x + 16, y, ls, 20, f'font-family="{SANS}" font-size="14.5" fill="{INK_SOFT}"')
            y += 20 * len(ls) + 12
        cols.append((f'<g class="up" {at(0.4 + c * 0.15)}>{out}</g>', y))
    h = max(y for _, y in cols) + 16
    body = f"""<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="up" {at(0.2)} x="40" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Wins, <tspan font-style="italic" fill="{COLOR['olive']}">so far</tspan></text>
{''.join(c for c, _ in cols)}"""
    save("wins.svg", W, h, body, "Achievements. " + " ".join(f"{a}: {'; '.join(b)}." for a, b in WINS), ["serif", "serif-i", "sans", "mono"])


def selftest():
    sample = ('<td data-date="2025-01-01" id="contribution-day-component-3-0" data-level="0">'
              '<td data-date="2025-01-02" id="contribution-day-component-4-0" data-level="2">'
              '<td data-date="2025-01-03" id="contribution-day-component-5-0" data-level="1">'
              '<tool-tip for="contribution-day-component-3-0">No contributions on January 1st.</tool-tip>'
              '<tool-tip for="contribution-day-component-4-0">12 contributions on January 2nd.</tool-tip>'
              '<tool-tip for="contribution-day-component-5-0">1 contribution on January 3rd.</tool-tip>')
    days = parse_calendar(sample)
    assert [d["count"] for d in days] == [0, 12, 1], days
    s = summarise(days)
    assert (s["total"], s["current"], s["longest"], s["active"]) == (13, 2, 2, 2), s
    assert summarise(days + [{"date": "2025-01-04", "count": 0}])["current"] == 2  # today empty keeps streak


if __name__ == "__main__":
    selftest()
    data = load()
    hero()
    heatmap(data)
    activity(data)
    for pos, t in enumerate(TILES):
        tile(pos, *t)
    stack()
    title("building", "What I'm", "building")
    stars = repo_meta()
    for pos, r in enumerate(REPOS):
        repo_card(pos, *r, stars.get(r[0]))
    wins()
