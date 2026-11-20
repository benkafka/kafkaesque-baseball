# Finds the 4 pitchers people looked up most on Kafkaesque Baseball in the last 7 days
# (from GoatCounter) and saves them to trending.json for the "Trending" buttons on Pitcher Search.
# Needs the GOATCOUNTER_KEY secret. Run from the repo root:  python3 build/trending.py
import datetime, json, os, re, sys, unicodedata, urllib.parse, urllib.request

CODE = "kafkaesque"
DAYS = 7
TOP = 4
KEY = os.environ.get("GOATCOUNTER_KEY", "").strip()
if not KEY:
    print("No GOATCOUNTER_KEY secret set, leaving trending.json alone"); sys.exit(0)

src = open("index.html", encoding="utf-8").read()
P = json.loads(re.search(r'<script id="pitcher-data" type="application/json">(.*?)</script>', src, re.S).group(1))

# the same web address rule as the pitcher pages (p/<name>/)
def base_slug(name):
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if ord(ch) < 128).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "pitcher"
counts = {}
for d in P.values():
    counts[base_slug(d["n"])] = counts.get(base_slug(d["n"]), 0) + 1
SLUG = {}
for pid, d in P.items():
    b = base_slug(d["n"])
    SLUG[b if counts[b] == 1 else b + "-" + pid] = pid

def pid_of(path):
    m = re.search(r"#(?:p|lab-)(\d+)(?:-\d{4})?$", path)
    if m:
        return m.group(1)
    m = re.match(r"^/p/([a-z0-9-]+)/?$", path)
    if m:
        return SLUG.get(m.group(1))
    return None

now = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
start = (now - datetime.timedelta(days=DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
end = now.strftime("%Y-%m-%dT%H:%M:%SZ")
views, seen = {}, []
for page in range(10):
    q = {"start": start, "end": end, "limit": 100}
    url = f"https://{CODE}.goatcounter.com/api/v0/stats/hits?" + urllib.parse.urlencode(q)
    for pid_ in seen:
        url += "&exclude_paths=" + str(pid_)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except Exception as e:
        print("GoatCounter request failed, leaving trending.json alone:", e); sys.exit(0)
    for h in r.get("hits", []):
        seen.append(h["path_id"])
        if h.get("event"):
            continue
        pid = pid_of(h.get("path", ""))
        if pid and pid in P:
            views[pid] = views.get(pid, 0) + int(h.get("count") or 0)
    if not r.get("more"):
        break

top = sorted(views.items(), key=lambda kv: (-kv[1], P[kv[0]]["n"]))[:TOP]
out = {"updated": now.strftime("%Y-%m-%dT%H:%MZ"), "days": DAYS,
       "top": [{"id": pid, "n": P[pid]["n"], "views": v} for pid, v in top if v > 0]}
old = None
if os.path.exists("trending.json"):
    try:
        old = json.load(open("trending.json"))
    except Exception:
        pass
if old and old.get("top") == out["top"]:
    print("Same top pitchers as before:", [t["n"] for t in out["top"]]); sys.exit(0)
json.dump(out, open("trending.json", "w"), indent=1)
print("Trending:", [(t["n"], t["views"]) for t in out["top"]])
