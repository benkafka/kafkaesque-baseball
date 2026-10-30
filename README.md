# Kafkaesque Baseball: Pitch Mix Tool

A pitching tool that grades every arsenal in MLB against its exact peers and flags where a pitcher's usage doesn't match his results.

Built in Python with [pybaseball](https://github.com/jldbc/pybaseball), using 2026 and 2025 Statcast data and the MLB Stats API.

**Live site:** https://benkafka.github.io/kafkaesque-baseball/

**Notebook:** [Pitch_Mix_Tool_v1.ipynb](Pitch_Mix_Tool_v1.ipynb)

## What it does

- **Grades every pitch against its exact peers.** Each pitch is compared only to the same pitch type, thrown with the same hand to the same batter side, using 716,792 regular-season pitches from 2026.
- **Measures four things per pitch:**
  - **Whiff+:** whiff rate per swing vs. league (100 = average)
  - **Run value:** Statcast `delta_run_exp`, flipped so positive helps the pitcher, per 100 pitches vs. league
  - **Contact quality:** hard-hit% (95+ mph) and xwOBAcon vs. league
  - **Location:** zone%, chase% and in-zone whiff% vs. league
  - **Location+:** grades where each pitch was thrown, using the league's average run value for that spot, pitch group, batter side and count (100 = average, 10 points = 1 standard deviation)
- **Adds shape and context:** velocity, induced vertical break, arm-side horizontal break, and splits by count (ahead, even, behind).
- **K-Stuff+ grades the pitch itself.** A gradient-boosted model, trained on every 2026 pitch, learns how velo, movement, spin, release point, extension, arm angle and the gap from the pitcher's main fastball translate into run value. It never sees location, count or results. 100 = average, 10 points = 1 standard deviation. In a first-half/second-half test, first-half K-Stuff+ predicted second-half run value better than first-half run value did (r = 0.24 vs. 0.17).
- **Pitch Lab suggests fixes for each pitcher.** It tests small, realistic changes to each pitch (1 mph, 2 inches of break, 150 rpm, 0.3 ft of extension) with the K-Stuff+ model, allowing only versions that pitchers with a similar arm slot already throw. It also builds the typical version of pitches he doesn't throw from comparable pitchers. Each suggestion comes with estimated runs saved and a real pitcher who throws a similar shape.
- **Daily Matchups** (home page). Each day's probable starters and lineups load live from the MLB Stats API. Each starter's run value by pitch group is set against the opposing offense's 2026 run value vs. that group from same-handed pitchers (ranked 1–30), with a matchup edge and per-hitter pitch-group splits.
- **2027 Watch List.** Ten starters and ten relievers who are 29 or younger, threw 600+ pitches in 2026, were average or worse and have never had a strong season since 2021 (10+ runs above average, +1.0 runs/100, or arsenal grade 60+), ranked by projected 2027 run value. The projection is a ridge regression fit on back-to-back seasons from 2021 to 2026, leaning on K-Stuff+ and Whiff+, then Location+, fastball velo change and contact quality. Forward test on 2022–2025 (each list built only from earlier seasons): reliever picks were above average the next year 28 of 40 times vs. 50% of similar relievers and broke out 9 of 40 vs. about 15%; starter picks were above average 22 of 40 vs. 38% but broke out only 6 of 40 vs. about 11%. Age sets eligibility; as a predictor it didn't consistently help, so it isn't weighted.
- **Minor Leagues.** Prospects, farm systems and a Minor League Watch List from 2026 Triple-A and Florida State League pitch tracking (1,073 pitchers graded) plus stats for every pitcher at all four levels. K-Stuff+ is scored with the model trained on MLB pitches, so a prospect's number sits on the big league scale. Farm system pages rank all 30 orgs on trends like Triple-A fastball velo, breaking ball and changeup usage, strikeout and walk rates, and age vs level. "Called up" tags link 2026 debuts to their MLB cards. Data lives in milb.json.
- **Free Agency Tracker.** Replaces Today's Matchups on the home page for the offseason. All 156 pitchers on MLB.com's 2026-27 free agent list, graded with the site's arsenal grade, K-Stuff+, run value and best pitch, with filters (available or signed, starters or relievers) and sortable columns. Signings and club option pickups update live from MLB's public transactions feed. Pitchers who barely pitched in 2026 use their most recent full season and are tagged with that year.
- **Arm Slot Changes.** Every 4°+ change in a pitcher's average arm angle from one season to the next since 2021 (335 cases, 300+ pitches both seasons), with his main fastball's ride and run change, K-Stuff+ change and run value change. Across 1,955 back-to-back seasons, each degree lower cost a fastball about 0.15" of ride and added 0.17" of arm-side run with almost no velocity change; after adjusting for the prior season, slot changes didn't reliably help or hurt results. 2021→2022 changes are measured against a league-wide ~3° tracking shift in 2022.
- **Past seasons (2021–2025).** Every pitcher page has a season switcher. Each past season is rebuilt with the same report card (Whiff+, Location+, K-Stuff+, run value with breakdown, pitch and arsenal grades, role, team, arm angle), graded against that season's league. Season data lives in `seasons/YYYY.json` and loads only when clicked. Pitchers who didn't reach 300 pitches in 2026 are still searchable by their past seasons.
- **Pitch mix optimizer** (Pitch Lab tab). Suggests how often to throw each pitch against each batter side, using each pitch's run value blended with K-Stuff+, with a diminishing-returns charge for throwing a pitch more, capped shifts (20 points) and a fastball floor. Backtest on 2025 data: pitchers who moved toward its advice held steady (+0.03 runs/100) while those who moved away declined (−0.24), but after controlling for regression to the mean the effect was small (+0.03). Given only Bryan Baker's 2025 numbers, it recommended fewer sliders and more changeups to righties, the same direction the Rays took him.
- **Backtested on real pitch changes.** For 367 pitches that changed shape from 2025 to 2026, each graded by a model that never saw that pitcher (5-fold cross-validation by pitcher), predicted whiff change matched actual whiff change: r = 0.23 (95% CI 0.11–0.34), still significant after controlling for regression to the mean. The model called the direction right 62% of the time when it expected a 2+ point swing and 68% at 5+. Year-to-year run value was too noisy to confirm (52% on 549 pitches), so runs-saved estimates are rough.
- **Grades every pitch and arsenal on the 20–80 scouting scale.** The grade blends whiff+, chase, in-zone whiffs, contact quality, ground-ball rate and Location+, each weighted by how much it predicts run value. Small samples are pulled toward 50, so a reliever needs a bigger edge than a starter to grade at the top.
- **Flags mismatches** between usage and results (rules below).
- **Writes a plain-English answer** to "what makes him nasty?" and names each pitcher's biggest strength.
- **Tracks change from 2025 to 2026:** new and dropped pitches, usage shifts, velocity, pitch shape and arm angle.
- **Ranks all 30 staffs** by pitch-weighted run value, alongside pitching payroll.

Every 2026 pitcher with 300+ pitches (563) is graded.

## Flags

A pitch can get more than one flag. Piles under 30 swings are marked **Small sample** and skipped.

| Flag | Rule |
|---|---|
| Underused weapon | whiff+ ≥ 120, run value ≥ +1.0 per 100, usage under 25% |
| Misses bats, still gets hurt | whiff+ ≥ 120, run value ≤ −1.0 per 100 |
| Below league average | run value ≤ −1.5 per 100 |
| Heavy use, below average | usage ≥ 25%, run value below 0 |
| Hit hard on contact | 20+ balls in play, xwOBAcon .040+ above league |
| Good stuff, bad spots | whiff+ ≥ 110, Location+ ≤ 90, run value below 0 |
| Gets by on location | whiff+ ≤ 90, Location+ ≥ 110, run value above 0 |

Year over year, a pitch is flagged for **New / Dropped** (under 10 thrown one season, 5%+ usage the other), **Usage up/down** (10+ points), **Velo up/down** (1.5+ mph) or **Shape change** (2.5+ inches of break). An **arm slot change** is 4+ degrees.

## Limits

- 2021 includes MLB's mid-season crackdown on sticky substances, which changed some pitchers' spin.
- Each season is graded against its own league, so a 60 in 2023 and a 60 in 2026 both mean "plus for that year," not the same raw stuff. K-Stuff+ and pitch grades are refit each season.
- Past-season Location+ uses a rebuilt version of the 2026 recipe, so small differences between seasons can come from the method, not the pitcher.
- Count splits, year-over-year changes, Pitch Lab, the mix optimizer and team pages are 2026 only.
- Small samples are flagged, not graded. Pitch and arsenal grades are pulled toward 50 on small samples.
- K-Stuff+ can't see deception, tunneling or sequencing, so pitchers who win with those can grade below their results.
- Pitch Lab can't tell whether a pitcher can physically make a change, and it treats each pitch on its own (changing a fastball also changes how his other pitches play off it).
- Grades rate pitch quality, not workload. A 200-inning starter and a one-inning reliever can grade the same.
- Run value is noisy over a few hundred pitches. Flags are prompts to look closer, not verdicts.
- Rare pitches can look good because they're rare, and the same holds for counts.
- Whiff+ inflates on pitch types with low league whiff rates, such as sinkers.
- Location+ grades the spot, not the intent. Pitchers with elite stuff often attack the zone on purpose, which can pull their Location+ down.
- Statcast sometimes reclassifies a pitch between seasons, which can look like a new and a dropped pitch.
- Arm angle is estimated from body tracking. Slot names are a rough guide.
- Teams are grouped by current roster, so a traded pitcher's full season shows on his new team.
- The tool shows where usage and results don't line up. It can't prove a new mix would work, because hitters adjust.

## Running it

Open the notebook in Google Colab and run all cells. The first run downloads each season to Google Drive, which takes a while. Later runs load it from Drive. Then grade any pitcher:

```python
report, flags = pitch_mix_report('tarik', 'skubal')
```

## Data

Statcast data via Baseball Savant and pybaseball. Player bios and transactions from the MLB Stats API. Pitching payroll from Spotrac. Inspired by Stockyard Baseball. Not affiliated with or endorsed by Major League Baseball.
