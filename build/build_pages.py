# Builds one page per pitcher (p/<name>/index.html), a link-preview image for each (og/<id>.png),
# plus sitemap.xml and robots.txt, all from the data already inside index.html.
# Run from the repo root:  python3 build/build_pages.py
import html, json, os, re, shutil, sys, unicodedata, urllib.request
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

SITE = "https://kafkaesquebaseball.com"
YEAR = 2026
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT_P, OUT_OG = os.path.join(ROOT, "p"), os.path.join(ROOT, "og")
PHOTOS = "--no-photos" not in sys.argv

src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
def block(name, default=None):
    m = re.search(r'<script id="%s" type="application/json">(.*?)</script>' % name, src, re.S)
    return json.loads(m.group(1)) if m else default

P = block("pitcher-data", {})
BIO = block("bio-data", {})
SUM = block("summary-data", {})
LAB = block("lab-data", {})
MIX = block("mix-data", {})
STD = block("std-data", {"cols": [], "rows": []})
COLS = {c: i for i, c in enumerate(STD["cols"])}
STATS = {r[0]: r for r in STD["rows"]}

NAMES = {"FF": "4-Seam", "SI": "Sinker", "FC": "Cutter", "SL": "Slider", "ST": "Sweeper", "SV": "Slurve",
         "CU": "Curveball", "KC": "Knuckle Curve", "CS": "Slow Curve", "CH": "Changeup", "FS": "Splitter",
         "FO": "Forkball", "SC": "Screwball", "KN": "Knuckleball", "FA": "Fastball", "EP": "Eephus"}
COLORS = {"FF": "#d22d49", "SI": "#fe9d00", "FC": "#933f2c", "SL": "#eee716", "ST": "#ddb33a", "SV": "#93afd4",
          "CU": "#00d1ed", "KC": "#6236cd", "CS": "#0068ff", "CH": "#1dbe3a", "FS": "#3bacac", "FO": "#55ccab",
          "SC": "#60db33", "KN": "#3c44cd"}

# ---------- the same web address rule the site uses ----------
def base_slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if ord(ch) < 128).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "pitcher"
counts = {}
for pid, d in P.items():
    counts[base_slug(d["n"])] = counts.get(base_slug(d["n"]), 0) + 1
def slug(pid):
    b = base_slug(P[pid]["n"])
    return b if counts[b] == 1 else b + "-" + pid

# ---------- numbers for one pitcher ----------
def arsenal(d):
    agg, total = {}, 0
    for r in d.get("r", []):
        w = r[16] or 0
        if not w or r[14] is None or r[15] is None: continue
        a = agg.setdefault(r[0], {"t": r[0], "w": 0, "v": 0, "iv": 0, "hb": 0})
        a["w"] += w; a["v"] += (r[13] or 0) * w; a["iv"] += r[14] * w; a["hb"] += r[15] * w; total += w
    out = []
    for a in agg.values():
        out.append({"t": a["t"], "use": 100 * a["w"] / total, "v": a["v"] / a["w"], "iv": a["iv"] / a["w"], "hb": a["hb"] / a["w"]})
    return sorted(out, key=lambda x: -x["use"])

def grades(d):
    g = (d.get("g") or {}).get("p") or []
    return sorted([p for p in g if p[1] is not None], key=lambda p: -p[1])

def stat(pid, k):
    r = STATS.get(pid)
    return None if r is None or k not in COLS else r[COLS[k]]

def fmt(v, nd=2):
    return "–" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))

def ip_str(v):
    if v is None: return "–"
    w = int(v); f = round((v - w) * 3)
    if f == 3: w, f = w + 1, 0
    return f"{w}.{f}"

def grade_color(g):
    return "#2a9d6b" if g >= 55 else ("#d9622b" if g < 45 else "#7c8798")

# ---------- link-preview image (1200 x 630) ----------
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, "fonts", n), s)
def headshot(pid):
    if not PHOTOS: return None
    try:
        url = ("https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/"
               f"w_360,q_auto:best/v1/people/{pid}/headshot/67/current")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (kafkaesque-baseball)"})
        return Image.open(BytesIO(urllib.request.urlopen(req, timeout=15).read())).convert("RGB")
    except Exception:
        return None

def preview(pid, d, team):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#e9edf2"); x = ImageDraw.Draw(im)
    x.rounded_rectangle((24, 24, W - 24, 300), 22, fill="#131a23")
    # photo or initials
    px, py, ps = 56, 56, 212
    x.rounded_rectangle((px, py, px + ps, py + ps), 16, fill="#26323f")
    ph = headshot(pid)
    if ph:
        r = max(ps / ph.width, ps / ph.height); ph = ph.resize((int(ph.width * r), int(ph.height * r)))
        ph = ph.crop(((ph.width - ps) // 2, 0, (ph.width - ps) // 2 + ps, ps))
        mask = Image.new("L", (ps, ps), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, ps, ps), 16, fill=255)
        im.paste(ph, (px, py), mask)
    else:
        ini = "".join(w[0] for w in d["n"].split()[:2]).upper()
        x.text((px + ps / 2, py + ps / 2), ini, font=F("Inter-Bold.otf", 84), fill="#93a1b5", anchor="mm")
    tx = px + ps + 34
    name = d["n"].upper(); size = 66
    while x.textlength(name, font=F("Inter-BoldItalic.otf", size)) > 560 and size > 36: size -= 2
    x.text((tx, 92), name, font=F("Inter-BoldItalic.otf", size), fill="#ffffff", anchor="ls")
    g = d.get("g") or {}
    role = "Starter" if g.get("r") == "SP" else "Reliever" if g.get("r") == "RP" else "Pitcher"
    sub = " · ".join([v for v in [team, f"{YEAR} season", ("RHP" if d.get("h") == "R" else "LHP") + " " + role] if v])
    x.text((tx, 138), sub, font=F("Inter-Regular.otf", 24), fill="#c9d2de", anchor="ls")
    era, fip, ip = stat(pid, "era"), stat(pid, "fip"), stat(pid, "ip")
    line = "   ".join(s for s in [f"{ip_str(ip)} IP" if ip is not None else "", f"{fmt(era)} ERA" if era is not None else "",
                                  f"{fmt(fip)} FIP" if fip is not None else ""] if s)
    if line: x.text((tx, 184), line, font=F("Inter-SemiBold.otf", 24), fill="#e7ecf2", anchor="ls")
    # big numbers
    for i, (val, lab) in enumerate([(g.get("s"), "K-STUFF+"), (g.get("a"), "ARSENAL GRADE")]):
        cx = W - 70 - i * 210
        x.text((cx, 214), "–" if val is None else str(val), font=F("Inter-BoldItalic.otf", 92), fill="#3fc28a", anchor="rs")
        x.text((cx, 252), lab, font=F("Inter-SemiBold.otf", 17), fill="#c9d2de", anchor="rs")
    # pitch grade bars
    x.rounded_rectangle((24, 322, W - 24, 548), 22, fill="#ffffff")
    x.text((56, 362), "PITCH GRADES", font=F("Inter-SemiBold.otf", 18), fill="#5b6675", anchor="ls")
    x.text((W - 56, 362), "20 to 80 scale · 50 = average", font=F("Inter-Regular.otf", 18), fill="#7c8798", anchor="rs")
    gs = grades(d)[:4]
    cols = 2; cw = (W - 112 - 40) // cols
    for j, p in enumerate(gs):
        cx, cy = 56 + (j % cols) * (cw + 40), 400 + (j // cols) * 72
        x.ellipse((cx, cy + 4, cx + 22, cy + 26), fill=COLORS.get(p[0], "#999"))
        x.text((cx + 34, cy + 24), NAMES.get(p[0], p[0]), font=F("Inter-SemiBold.otf", 26), fill="#131a23", anchor="ls")
        bx, bw = cx + 230, cw - 230 - 70
        x.rounded_rectangle((bx, cy + 8, bx + bw, cy + 24), 8, fill="#edf0f4")
        frac = max(0.04, min(1, (p[1] - 20) / 60))
        x.rounded_rectangle((bx, cy + 8, bx + int(bw * frac), cy + 24), 8, fill=grade_color(p[1]))
        x.line((bx + bw // 2, cy + 2, bx + bw // 2, cy + 30), fill="#5b6675", width=2)
        x.text((cx + cw, cy + 28), str(p[1]), font=F("Inter-Bold.otf", 34), fill=grade_color(p[1]), anchor="rs")
    if not gs:
        x.text((56, 420), "Not enough pitches yet to grade his arsenal.", font=F("Inter-Regular.otf", 24), fill="#5b6675")
    x.rounded_rectangle((24, 568, W - 24, H - 18), 16, fill="#131a23")
    x.text((56, 606), "KAFKAESQUE BASEBALL", font=F("Inter-BoldItalic.otf", 26), fill="#ffffff", anchor="ls")
    x.text((W - 56, 606), "kafkaesquebaseball.com · Data: Statcast", font=F("Inter-Regular.otf", 20), fill="#c9d2de", anchor="rs")
    im.save(os.path.join(OUT_OG, f"{pid}.png"), optimize=True)

# ---------- the page itself ----------
CSS = """:root{--bg:#f3f5f8;--panel:#fff;--fg:#131a23;--mut:#5b6675;--line:#dfe4ea;--acc:#b86a00;--ok:#2a9d6b;--hot:#d9622b}
@media (prefers-color-scheme:dark){:root{--bg:#0e141b;--panel:#17202a;--fg:#e9eef4;--mut:#9aa6b5;--line:#2a3542;--acc:#f0a53a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--acc)}.wrap{max-width:900px;margin:0 auto;padding:0 16px}
header{background:#131a23;color:#fff}header .wrap{display:flex;justify-content:space-between;align-items:center;padding:14px 16px}
header a{color:#fff;text-decoration:none;font-weight:800;font-style:italic;letter-spacing:.02em}header nav a{font-weight:500;font-style:normal;margin-left:16px;font-size:14px;color:#c9d2de}
.hero{display:flex;gap:20px;align-items:center;margin:28px 0 8px;flex-wrap:wrap}.hero img{width:96px;height:96px;border-radius:12px;object-fit:cover;background:#26323f}
h1{margin:0;font-size:34px;line-height:1.15}.sub{color:var(--mut);margin:4px 0 0}
.nums{display:flex;gap:28px;margin-left:auto}.nums b{display:block;font-size:40px;color:var(--ok);line-height:1;font-style:italic}.nums span{font-size:12px;color:var(--mut);letter-spacing:.05em}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:16px 0}
h2{font-size:14px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);margin:0 0 10px}
table{width:100%;border-collapse:collapse;font-size:15px}th,td{text-align:right;padding:7px 6px;border-bottom:1px solid var(--line)}th:first-child,td:first-child{text-align:left}th{font-size:12px;color:var(--mut);font-weight:600}
.dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:8px;vertical-align:-1px}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.btn{background:var(--acc);color:#fff;text-decoration:none;padding:10px 16px;border-radius:8px;font-weight:600}.btn.alt{background:transparent;color:var(--acc);border:1px solid var(--acc)}
ul.fix{margin:0;padding-left:18px}ul.fix li{margin:6px 0}footer{color:var(--mut);font-size:13px;padding:24px 0 40px}
.stats{display:flex;flex-wrap:wrap;gap:8px 22px;font-size:15px}.stats b{font-weight:700}
@media (max-width:600px){.nums{margin-left:0}h1{font-size:28px}.hide-s{display:none}}"""

def esc(v): return html.escape(str(v), quote=True)

def page(pid, d, sl, team):
    g = d.get("g") or {}; n = d["n"]
    role = "starter" if g.get("r") == "SP" else "reliever" if g.get("r") == "RP" else "pitcher"
    hand = "right-handed" if d.get("h") == "R" else "left-handed"
    summ = SUM.get(pid) or {}
    best = grades(d)[:1]
    lead = summ.get("n") or (f"His best pitch is the {NAMES.get(best[0][0], best[0][0]).lower()}." if best else "")
    desc = f"{n}'s {YEAR} pitch arsenal, graded: arsenal grade {g.get('a','–')}, K-Stuff+ {g.get('s','–')}. " + lead
    desc = desc if len(desc) <= 158 else desc[:155].rsplit(" ", 1)[0] + "..."
    title = f"{n} Pitch Arsenal, Grades and Report Card ({YEAR}) | Kafkaesque Baseball"
    url = f"{SITE}/p/{sl}/"; img = f"{SITE}/og/{pid}.png"
    ars = arsenal(d); gs = grades(d)
    rows_a = "".join(
        f'<tr><td><span class="dot" style="background:{COLORS.get(a["t"],"#999")}"></span>{esc(NAMES.get(a["t"],a["t"]))}</td>'
        f'<td>{a["use"]:.1f}%</td><td>{a["v"]:.1f} mph</td><td>{a["iv"]:.1f}"</td>'
        f'<td>{abs(a["hb"]):.1f}" <span class="hide-s" style="color:var(--mut)">{"arm" if a["hb"]>0 else "glove"} side</span></td></tr>' for a in ars)
    rows_g = "".join(
        f'<tr><td><span class="dot" style="background:{COLORS.get(p[0],"#999")}"></span>{esc(NAMES.get(p[0],p[0]))}</td>'
        f'<td style="color:{grade_color(p[1])};font-weight:700">{p[1]}</td><td>{fmt(p[2],0) if p[2] is not None else "–"}</td>'
        f'<td>{fmt(p[3],0) if p[3] is not None else "–"}</td></tr>' for p in gs)
    st = [("G", "g", 0), ("GS", "gs", 0), ("IP", "ip", 1), ("ERA", "era", 2), ("FIP", "fip", 2), ("WHIP", "whip", 2),
          ("K%", "k", 1), ("BB%", "bb", 1), ("K-BB%", "kbb", 1), ("ERA+", "erap", 0)]
    stats = "".join(f"<span>{lab} <b>{ip_str(stat(pid,k)) if k == 'ip' else (fmt(stat(pid,k), nd) if not isinstance(stat(pid,k), int) else stat(pid,k))}</b></span>"
                    for lab, k, nd in st if stat(pid, k) is not None)
    fixes = LAB.get(pid) or []
    m = MIX.get(pid) or {}
    fx = "".join(f"<li><b>{esc(f[1])}:</b> {esc(f[2])} (about +{f[6]:.1f} runs a season)</li>" for f in fixes)
    mixline = f"<p>A better pitch mix is worth about <b>+{m['t']:.1f} runs a season</b>.</p>" if m.get("t") is not None and m["t"] >= 0.1 else ""
    lab_html = (f'<div class="panel"><h2>Pitch Lab</h2>{mixline}' + (f'<ul class="fix">{fx}</ul>' if fx else "") +
                f'<p style="margin:10px 0 0"><a href="/#lab-{pid}">See the full Pitch Lab breakdown →</a></p></div>') if (fx or mixline) else ""
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "name": title, "url": url,
          "mainEntity": {"@type": "Person", "name": n, "jobTitle": f"MLB {role}",
                         **({"memberOf": {"@type": "SportsTeam", "name": team}} if team else {})}}
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="profile"><meta property="og:site_name" content="Kafkaesque Baseball">
<meta property="og:title" content="{esc(n)} · {YEAR} Report Card"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(n)} · {YEAR} Report Card">
<meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{img}">
<script type="application/ld+json">{json.dumps(ld)}</script>
<style>{CSS}</style>
<script data-goatcounter="https://kafkaesque.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</head><body>
<header><div class="wrap"><a href="/">KAFKAESQUE BASEBALL</a><nav><a href="/#report">Pitchers</a><a href="/#lab">Pitch Lab</a><a href="/#about">About</a></nav></div></header>
<main class="wrap">
<div class="hero"><img src="https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_200,q_auto:best/v1/people/{pid}/headshot/67/current" alt="{esc(n)}" width="96" height="96" onerror="this.style.visibility='hidden'">
<div><h1>{esc(n)}</h1><p class="sub">{esc(team + " · " if team else "")}{YEAR} · {hand} {role}</p></div>
<div class="nums"><div><b>{g.get('a','–')}</b><span>ARSENAL GRADE</span></div><div><b>{g.get('s','–')}</b><span>K-STUFF+</span></div></div></div>
<div class="btns"><a class="btn" href="/#p{pid}">Open the full report card</a><a class="btn alt" href="/#lab-{pid}">Open in Pitch Lab</a></div>
{f'<div class="panel"><h2>{YEAR} season</h2><div class="stats">{stats}</div></div>' if stats else ''}
{f'<div class="panel"><h2>The short version</h2><p style="margin:0">{esc(summ.get("n",""))}</p>' + (f'<p style="margin:8px 0 0">{esc(summ["s"])}</p>' if summ.get("s") else "") + '</div>' if summ.get("n") or summ.get("s") else ''}
{f'<div class="panel"><h2>Pitch grades</h2><table><thead><tr><th>Pitch</th><th>Grade</th><th>vs LHH</th><th>vs RHH</th></tr></thead><tbody>{rows_g}</tbody></table><p style="color:var(--mut);font-size:13px;margin:8px 0 0">20 to 80 scale, 50 is league average.</p></div>' if rows_g else ''}
{f'<div class="panel"><h2>Arsenal</h2><table><thead><tr><th>Pitch</th><th>Usage</th><th>Velo</th><th>IVB</th><th>HB</th></tr></thead><tbody>{rows_a}</tbody></table></div>' if rows_a else ''}
{lab_html}
<p>Arsenal grade measures how well {esc(n.split()[-1])} uses the pitches he has. K-Stuff+ is our stuff model, where 100 is league average. <a href="/#glossary">Read the glossary</a>.</p>
</main>
<footer class="wrap">Kafkaesque Baseball by Ben Kafka · Data from Statcast via pybaseball and the MLB Stats API · Not affiliated with MLB.</footer>
</body></html>"""

# ---------- build everything ----------
for d_ in (OUT_P, OUT_OG):
    if os.path.isdir(d_): shutil.rmtree(d_)
    os.makedirs(d_)
urls = [f"{SITE}/"]
for i, (pid, d) in enumerate(sorted(P.items(), key=lambda kv: kv[1]["n"])):
    team = (BIO.get(pid) or {}).get("tm") or ""
    sl = slug(pid)
    os.makedirs(os.path.join(OUT_P, sl), exist_ok=True)
    open(os.path.join(OUT_P, sl, "index.html"), "w", encoding="utf-8").write(page(pid, d, sl, team))
    preview(pid, d, team)
    urls.append(f"{SITE}/p/{sl}/")
    if i % 100 == 0: print("built", i, d["n"])
with open(os.path.join(ROOT, "sitemap.xml"), "w") as fh:
    fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    fh.write("".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)); fh.write("</urlset>\n")
with open(os.path.join(ROOT, "robots.txt"), "w") as fh:
    fh.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print(f"Done: {len(urls)-1} pitcher pages")
