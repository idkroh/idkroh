"""Generate profile assets from public GitHub data, using only the standard library."""
from collections import Counter, defaultdict
import base64
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

USER = "idkroh"
ASSETS = Path(__file__).resolve().parents[1] / "assets"
BG, PANEL, LINE = "#0d1117", "#10171f", "#29313a"
WHITE, MUTED, GREEN, GOLD = "#eef2f6", "#9aa7b5", "#39d875", "#cda66c"
FONT = "'SFMono-Regular',Consolas,'Liberation Mono',monospace"


def fetch(url, api=False):
    headers = {"User-Agent": "idkroh-profile/1.0"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        text = response.read().decode("utf-8")
    return json.loads(text) if api else text


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.tips = {}, {}
        self.current_tip = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and "data-date" in attrs:
            self.cells[attrs["id"]] = {"date": attrs["data-date"], "level": int(attrs["data-level"])}
        elif tag == "tool-tip" and attrs.get("for", "").startswith("contribution-day-"):
            self.current_tip = attrs["for"]
            self.tips[self.current_tip] = ""

    def handle_data(self, text):
        if self.current_tip is not None:
            self.tips[self.current_tip] += text

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.current_tip = None


def load_data():
    profile = fetch(f"https://api.github.com/users/{USER}", api=True)
    repos = []
    for page in range(1, 101):
        batch = fetch(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner", api=True)
        repos.extend(repo for repo in batch if not repo["private"])
        if len(batch) < 100:
            break
    else:
        raise RuntimeError("Repository pagination exceeded limit")
    calendar = CalendarParser()
    calendar.feed(fetch(f"https://github.com/users/{USER}/contributions"))
    if len(calendar.cells) < 350:
        raise RuntimeError("GitHub calendar markup changed; preserving existing assets")
    days = []
    for key, cell in calendar.cells.items():
        tip = calendar.tips.get(key, "").strip()
        match = re.match(r"([\d,]+) contribution", tip)
        if tip.startswith("No contributions"):
            count = 0
        elif match:
            count = int(match[1].replace(",", ""))
        else:
            raise RuntimeError("Unrecognized contribution tooltip; preserving existing assets")
        if not 0 <= cell["level"] <= 4:
            raise RuntimeError("Invalid contribution level")
        days.append({**cell, "count": count})
    days.sort(key=lambda day: day["date"])
    languages = Counter()
    for repo in repos:
        if not repo["fork"] and repo["name"].lower() != USER:
            languages.update(fetch(repo["languages_url"], api=True))
    return {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "public_repositories": len(repos),
        "original_public_repositories": sum(not r["fork"] for r in repos),
        "followers": profile["followers"],
        "days": days,
        "languages": dict(languages.most_common()),
    }


def txt(x, y, text, size=16, color=WHITE, weight="400", extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" {extra}>{escape(str(text))}</text>'


def rect(x, y, w, h, fill=PANEL, radius=8, stroke=LINE, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>'


def svg(w, h, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title, quote=True)}">
<title>{escape(title)}</title>
<style>text{{font-family:{FONT}}}.blink{{animation:blink 1.8s ease-in-out infinite}}.pulse{{animation:pulse 3s ease-in-out infinite}}.scan{{animation:scan 9s linear infinite}}.portrait{{animation:reveal 12s cubic-bezier(.22,.61,.36,1) infinite;will-change:clip-path,opacity}}.portrait-scan{{animation:portraitscan 12s cubic-bezier(.22,.61,.36,1) infinite;will-change:transform,opacity}}@keyframes blink{{50%{{opacity:0}}}}@keyframes pulse{{50%{{opacity:.45}}}}@keyframes scan{{0%{{transform:translateX(0);opacity:0}}10%{{opacity:.45}}90%{{opacity:.45}}100%{{transform:translateX(795px);opacity:0}}}}@keyframes reveal{{0%{{clip-path:inset(0 0 100% 0);opacity:0}}4%{{clip-path:inset(0 0 100% 0);opacity:1}}32%,94%{{clip-path:inset(0 0 0 0);opacity:1}}100%{{clip-path:inset(0 0 0 0);opacity:0}}}}@keyframes portraitscan{{0%{{transform:translateY(0);opacity:0}}4%{{transform:translateY(0);opacity:.6}}32%{{transform:translateY(329px);opacity:.6}}33%,100%{{transform:translateY(329px);opacity:0}}}}@media(prefers-reduced-motion:reduce){{.blink,.pulse,.portrait{{animation:none}}.scan,.portrait-scan{{animation:none;opacity:0}}}}</style>
{rect(1, 1, w-2, h-2, BG, 14)}{body}</svg>'''


def terminal(w, label):
    dots = ''.join(f'<circle cx="{24+i*17}" cy="23" r="4" fill="{c}"/>' for i,c in enumerate(["#ff6058", "#febc2e", "#28c840"]))
    return dots + txt(83, 28, label, 12, MUTED) + f'<path d="M1 44H{w-1}" stroke="{LINE}"/>'


def header():
    body = terminal(920, "~/rohith/profile — README.md")
    body += txt(36, 83, "idkroh@github:~ $ ./introduce.sh", 15, GREEN)
    body += txt(35, 143, "Rohith Ramesh", 54, WHITE, "700")
    body += txt(38, 180, "FULL-STACK DEVELOPMENT / AI TOOLS / WEB APPS", 14, GOLD)
    body += txt(38, 212, "Building useful things. Making them feel good to use.", 15, MUTED)
    body += f'<path d="M666 65V211" stroke="{LINE}"/>'
    for i,line in enumerate(["const rohith = {",'  focus: "AI × Web",','  mode: "building",',"  curiosity: Infinity","};"]):
        body += txt(690,83+i*25,line,12,[GREEN,GOLD,GOLD,WHITE,GREEN][i])
    body += txt(870,209,"_",17,GREEN,extra='class="blink"')
    body += f'<path d="M1 237H919" stroke="{GOLD}" stroke-opacity=".5"/>'
    return svg(920, 240, "Rohith Ramesh — full-stack development, AI tools, web apps", body)


def contributions(data):
    days = data["days"]
    start = date.fromisoformat(days[0]["date"])
    start -= timedelta(days=(start.weekday()+1)%7)
    end = date.fromisoformat(days[-1]["date"])
    cols = (end-start).days//7 + 1
    step = min(15.3, 806/cols)
    colors = ["#18251f", "#0e4429", "#166c3d", "#26a657", "#39d875"]
    body = terminal(920, "contributions.sh — rolling year")
    last_month = None
    for day in days:
        d = date.fromisoformat(day["date"])
        col, row = (d-start).days//7, (d.weekday()+1)%7
        x, y = 72+col*step, 83+row*16
        if d.month != last_month and (d.day <= 7 or last_month is None):
            if col < cols-2:
                body += txt(x, 70, d.strftime("%b"), 11, MUTED)
            last_month = d.month
        body += f'<rect x="{x:.1f}" y="{y}" width="12" height="12" rx="2" fill="{colors[day["level"]]}"><title>{day["date"]}: {day["count"]} contributions</title></rect>'
    for row, label in [(1,"Mon"),(3,"Wed"),(5,"Fri")]:
        body += txt(26, 93+row*16, label, 11, MUTED)
    body += f'<rect x="72" y="80" width="2" height="112" fill="{GREEN}" opacity="0" class="scan"/>'
    total = sum(d["count"] for d in days)
    body += txt(27, 231, f"{total:,} contributions in the past year", 15, WHITE, "600")
    body += txt(674, 231, "Less", 11, MUTED)
    for i,c in enumerate(colors):
        body += rect(711+i*18, 220, 12, 12, c, 2, c)
    body += txt(809, 231, "More", 11, MUTED)
    body += f'<circle cx="870" cy="228" r="4" fill="{GREEN}" class="pulse"/>'
    return svg(920, 255, "Public contribution calendar for the past year", body)


def dashboard(data):
    days = data["days"]
    body = terminal(610, "whoami — activity overview")
    metrics = [
        (sum(d["count"] for d in days), "CONTRIBUTIONS / YEAR", GREEN),
        (data["public_repositories"], "PUBLIC REPOSITORIES", WHITE),
        (sum(d["count"] > 0 for d in days), "ACTIVE DAYS / YEAR", WHITE),
        (max(d["count"] for d in days), "MOST IN A DAY", GOLD),
    ]
    for i,(value,label,color) in enumerate(metrics):
        x, y = 26+(i%2)*290, 64+(i//2)*96
        body += txt(x, y+18, label, 12, MUTED)
        body += txt(x, y+62, f"{value:,}", 40, color, "700")
    body += f'<path d="M26 260H584" stroke="{LINE}"/>'
    body += txt(26, 287, "MONTHLY CONTRIBUTIONS", 12, MUTED)
    months = defaultdict(int)
    for day in days:
        months[day["date"][:7]] += day["count"]
    selected = list(sorted(months.items()))[-12:]
    highest = max((n for _,n in selected), default=1) or 1
    body += f'<path d="M26 386H584" stroke="{LINE}"/>'
    for i,(month,count) in enumerate(selected):
        height = 76*count/highest
        x = 29+i*46
        body += rect(x, 386-height, 28, height if count else 2, GREEN, 3, GREEN, extra='fill-opacity=".85"')
        body += txt(x+14, 407, date.fromisoformat(month+"-01").strftime("%b"), 11, MUTED, extra='text-anchor="middle"')
    body += txt(26, 440, f"github.com/{USER}  ·  updated {data['updated']}", 11, MUTED)
    return svg(610, 458, "GitHub activity overview", body)


def identity(data):
    portrait = ASSETS / "terminal-portrait.png"
    if not portrait.exists():
        return None
    source = base64.b64encode(portrait.read_bytes()).decode("ascii")
    body = terminal(920, "whoami — Rohith Ramesh / @idkroh")
    body += rect(18,60,388,404,BG,8,LINE)
    body += txt(35,83,"01 / PORTRAIT",11,GOLD)
    body += f'<svg x="25" y="95" width="374" height="340" viewBox="0 0 374 340"><image class="portrait" href="data:image/png;base64,{source}" width="374" height="340" preserveAspectRatio="xMidYMid meet"/></svg>'
    body += f'<path d="M31 102h18M31 102v18M393 102h-18M393 102v18M31 431h18M31 431v-18M393 431h-18M393 431v-18" fill="none" stroke="{GOLD}" stroke-opacity=".65"/>'
    body += f'<rect x="40" y="102" width="340" height="1" fill="{GREEN}" opacity="0" class="portrait-scan"/>'
    body += txt(36,453,"ROHITH RAMESH",13,WHITE,"600")
    body += txt(326,453,"@idkroh",11,GOLD)
    body += txt(430,82,"02 / ACTIVITY OVERVIEW",11,GOLD)
    values = [
        (sum(d["count"] for d in data["days"]),"CONTRIBUTIONS / YEAR",GREEN),
        (data["public_repositories"],"PUBLIC REPOSITORIES",WHITE),
        (sum(d["count"]>0 for d in data["days"]),"ACTIVE DAYS / YEAR",WHITE),
        (max(d["count"] for d in data["days"]),"MOST IN A DAY",GOLD),
    ]
    for i,(value,label,color) in enumerate(values):
        x,y=430+(i%2)*240,110+(i//2)*93
        body += txt(x,y,label,11,MUTED)
        body += txt(x,y+46,f"{value:,}",40,color,"700")
    body += f'<path d="M430 275H885" stroke="{LINE}"/>'
    body += txt(430,301,"MONTHLY CONTRIBUTIONS",11,MUTED)
    months=defaultdict(int)
    for day in data["days"]:
        months[day["date"][:7]]+=day["count"]
    selected=sorted(months.items())[-12:]
    highest=max((n for _,n in selected),default=1) or 1
    for i,(month,count) in enumerate(selected):
        height=90*count/highest
        x=432+i*38
        body+=rect(x,411-height,23,height if count else 2,GREEN,2,GREEN)
        body+=txt(x+11,430,date.fromisoformat(month+"-01").strftime("%b"),10,MUTED,extra='text-anchor="middle"')
    body+=f'<path d="M430 411H886" stroke="{LINE}"/>'
    body+=txt(430,458,"PUBLIC GITHUB DATA",10,MUTED)
    body+=txt(766,458,data["updated"],10,MUTED)
    body+=f'<circle cx="887" cy="454" r="3" fill="{GREEN}" class="pulse"/>'
    return svg(920,484,"Rohith Ramesh — terminal portrait and GitHub activity",body)


def stack(data):
    body = terminal(920, "stack.json — tools I build with")
    items = [("TS","TypeScript","#72aefa"),("R","React","#67d5ef"),("PY","Python",GOLD),("API","FastAPI",GREEN),("ML","PyTorch","#ef9579"),("CV","OpenCV",GREEN),("GIT","Git",GOLD),("CI","GitHub Actions","#72aefa")]
    for i,(icon,label,c) in enumerate(items):
        x,y = 26+(i%4)*222, 64+(i//4)*65
        body += rect(x,y,202,48)
        body += rect(x+10,y+10,37,28,"#1c2732",4,"#1c2732")
        body += txt(x+28,y+29,icon,12,c,"700",'text-anchor="middle"')
        body += txt(x+59,y+30,label,15,WHITE)
    body += txt(27, 210, "PUBLIC SOURCE MIX", 11, MUTED)
    lang = list(data["languages"].items())
    total = sum(value for _,value in lang) or 1
    selected = lang[:4]
    rest = sum(value for _,value in lang[4:])
    if rest:
        selected.append(("Other",rest))
    colors = ["#72aefa",GOLD,"#ed927c","#b09bdf",MUTED]
    x = 26.0
    for i,(label,value) in enumerate(selected):
        width = 865*value/total
        body += rect(f"{x:.2f}",222,f"{width:.2f}",8,colors[i],0,colors[i])
        body += txt(26+i*174,254,f"{label} {value/total:.1%}",11,colors[i])
        x += width
    body += txt(27, 282, "Language shares by source bytes · original public repos · excludes this profile", 11, MUTED)
    return svg(920, 302, "Development stack and public repository language shares", body)


def project(title, number, lines, tags, accent):
    body = txt(25,35,number+" / PROJECT",12,accent)
    body += txt(25,76,title,22,WHITE,"700")
    for i,line in enumerate(lines):
        body += txt(25,110+i*24,line,14,MUTED)
    body += txt(25,186,tags,12,accent)
    body += txt(399,35,"↗",20,accent)
    return svg(440,210,title,body)


def generate(data):
    assets = {
        "header.svg": header(),
        "contributions.svg": contributions(data),
        "dashboard.svg": dashboard(data),
        "stack.svg": stack(data),
        "project-payments.svg": project("AI Payment Intelligence","01",["Fraud risk. Spend forecasting.","Cryptographic offline ledger checks."],"REACT / FASTAPI / PYTORCH",GREEN),
        "project-gym.svg": project("AI Gym Pose Trainer","02",["Pose tracking and personal calibration.","Rep quality and session analytics."],"PYTHON / MEDIAPIPE / OPENCV",GOLD),
        "project-codex.svg": project("Codex Multi-Model Build","03",["Isolated builds. Independent review.","Quality gates for coding agents."],"PYTHON / CODEX / DEVELOPER TOOLS",GOLD),
        "project-web.svg": project("Nascom Landscaping","04",["An independent website concept.","A focused interface for a service brand."],"TYPESCRIPT / CSS / WEB DESIGN",GREEN),
        "footer.svg": svg(920,62,"Keep building",txt(26,38,"$ keep building",14,GOLD)+txt(880,38,"_",18,GREEN,extra='class="blink"')),
    }
    identity_svg = identity(data)
    if identity_svg:
        assets["identity.svg"] = identity_svg
    # Validate every SVG before writing any asset. A failed fetch or parse retains the previous set.
    for content in assets.values():
        ET.fromstring(content)
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name,content in assets.items():
        temp = ASSETS / (name+".tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(ASSETS / name)
    (ASSETS/"activity.json").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
    print(f"Generated {len(assets)} SVGs from {len(data['days'])} public calendar days; {sum(d['count'] for d in data['days']):,} contributions.")


if __name__ == "__main__":
    generate(load_data())
