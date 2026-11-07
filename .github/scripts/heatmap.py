"""Generate a GitHub-style contribution heatmap SVG (no external services)."""
import json, os, sys, urllib.request
from datetime import date

USER = os.environ.get("USERNAME", "Ankush0286")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/contribution-heatmap.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""

def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def mock():
    import random
    random.seed(1)
    levels = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
    weeks, total = [], 0
    for w in range(53):
        days = []
        for d in range(7):
            c = random.choice([0, 0, 0, 1, 2, 4, 7, 12])
            total += c
            days.append({"date": f"2026-01-{(d % 28) + 1:02d}", "contributionCount": c,
                         "contributionLevel": levels[0 if c == 0 else 1 if c < 3 else 2 if c < 5 else 3 if c < 9 else 4]})
        weeks.append({"contributionDays": days})
    return {"totalContributions": total, "weeks": weeks}

cal = mock() if os.environ.get("MOCK") else fetch()

COLORS = {"NONE": "#161b22", "FIRST_QUARTILE": "#0e4429", "SECOND_QUARTILE": "#006d32",
          "THIRD_QUARTILE": "#26a641", "FOURTH_QUARTILE": "#39d353"}
CELL, GAP, LEFT, TOP = 11, 3, 34, 44
STEP = CELL + GAP
weeks = cal["weeks"]
W = LEFT + len(weeks) * STEP + 16
H = TOP + 7 * STEP + 36
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
       f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117"/>',
       f'<text x="{LEFT}" y="24" font-size="13" font-weight="600" fill="#e6edf3">'
       f'{cal["totalContributions"]:,} contributions in the last year</text>']

last_month = -1
for i, wk in enumerate(weeks):
    day0 = wk["contributionDays"][0]["date"]
    m = int(day0[5:7]) - 1
    if m != last_month and (i == 0 or i + 2 < len(weeks)):
        out.append(f'<text x="{LEFT + i*STEP}" y="{TOP-8}" font-size="10" fill="#8b949e">{MONTHS[m]}</text>')
        last_month = m
for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    out.append(f'<text x="4" y="{TOP + row*STEP + 9}" font-size="9" fill="#8b949e">{label}</text>')

for i, wk in enumerate(weeks):
    for d in wk["contributionDays"]:
        # first week may be partial: row = weekday of the date
        row = date.fromisoformat(d["date"]).weekday()
        row = (row + 1) % 7  # Sunday = 0
        n = d["contributionCount"]
        tip = f'{n} contribution{"s" if n != 1 else ""} on {d["date"]}'
        out.append(f'<rect x="{LEFT + i*STEP}" y="{TOP + row*STEP}" width="{CELL}" height="{CELL}" rx="2" '
                   f'fill="{COLORS[d["contributionLevel"]]}"><title>{tip}</title></rect>')

# legend
lx = W - 16 - 5 * STEP - 60
ly = TOP + 7 * STEP + 14
out.append(f'<text x="{lx-30}" y="{ly+9}" font-size="10" fill="#8b949e">Less</text>')
for k, c in enumerate(COLORS.values()):
    out.append(f'<rect x="{lx + k*STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>')
out.append(f'<text x="{lx + 5*STEP + 4}" y="{ly+9}" font-size="10" fill="#8b949e">More</text>')
out.append("</svg>")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(out))
print("wrote", OUT)
