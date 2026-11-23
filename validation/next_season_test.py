# Reproduces Test 1 on the "Does It Work?" page: do 2025 K-Stuff+ and Whiff+ predict 2026 results
# better than 2025 swinging-strike rate alone?
# Uses only files already in this repo (index.html and seasons/2025.json). No downloads.
# Run from the repo root:  python3 validation/next_season_test.py
import json, math, re
import numpy as np

src = open("index.html", encoding="utf-8").read()
def block(name):
    return json.loads(re.search(r'<script id="%s" type="application/json">(.*?)</script>' % name, src, re.S).group(1))

P26 = block("pitcher-data")      # 2026 pitchers: per-pitch rows
BB = block("bb-data")            # per year: [SwStr%, GB%, FB%, pulled FB%, extension]
STD = block("std-data")          # 2026 standard stats
COL = {c: i for i, c in enumerate(STD["cols"])}
STATS = {r[0]: r for r in STD["rows"]}
P25 = json.load(open("seasons/2025.json"))["P"]

# per-pitch row fields used here: [16] pitches thrown, [29] K-Stuff+, [4] Whiff+
def weighted(d, i):
    s = w = 0.0
    for r in d["r"]:
        if r[16] and r[i] is not None:
            s += r[i] * r[16]; w += r[16]
    return s / w if w else None

rows = []
for pid, d in P25.items():
    if d.get("p", 0) < 500 or P26.get(pid, {}).get("p", 0) < 500:
        continue
    b25, b26, st = BB["2025"].get(pid), BB["2026"].get(pid), STATS.get(pid)
    if not (b25 and b26 and st):
        continue
    row = dict(name=d["n"], ks=weighted(d, 29), wh=weighted(d, 4), sw25=b25[0],
               sw26=b26[0], k26=st[COL["k"]], fip26=st[COL["fip"]])
    if None not in row.values():
        rows.append(row)
print(f"{len(rows)} pitchers with 500+ pitches in both 2025 and 2026\n")

col = lambda f: np.array([r[f] for r in rows], float)
order = np.random.default_rng(0).permutation(len(rows))
def cv_r2(feats, target, k=5):
    y = col(target); X = np.column_stack([np.ones(len(y))] + [col(f) for f in feats]); pred = np.zeros(len(y))
    for f in range(k):
        test = order[f::k]; train = np.setdiff1d(order, test)
        beta = np.linalg.lstsq(X[train], y[train], rcond=None)[0]; pred[test] = X[test] @ beta
    return 1 - ((y - pred) ** 2).mean() / y.var()

names = {"sw26": "2026 swinging-strike rate", "k26": "2026 K%", "fip26": "2026 FIP"}
print(f"{'':28}{'r: 2025 SwStr%':>16}{'r: K-Stuff+':>13}{'r: Whiff+':>11}{'R2 baseline':>13}{'R2 + models':>13}")
for t, label in names.items():
    y = col(t)
    rs = [np.corrcoef(col(p), y)[0, 1] for p in ("sw25", "ks", "wh")]
    print(f"{label:28}{rs[0]:>16.2f}{rs[1]:>13.2f}{rs[2]:>11.2f}{cv_r2(['sw25'], t):>13.2f}{cv_r2(['sw25', 'ks', 'wh'], t):>13.2f}")
print("\nR2 values are 5-fold cross-validated, so no pitcher is graded by a fit that included him.")
