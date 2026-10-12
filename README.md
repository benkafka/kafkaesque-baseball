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
- **Adds shape and context:** velocity, induced vertical break, arm-side horizontal break, and splits by count (ahead, even, behind).
- **Flags mismatches** between usage and results (rules below).
- **Writes a plain-English answer** to "what makes him nasty?" and names each pitcher's biggest strength.
- **Tracks change from 2025 to 2026:** new and dropped pitches, usage shifts, velocity, pitch shape and arm angle.
- **Finds pitch comps:** the three closest pitches in the league by velocity and movement, same hand and pitch type.
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

Year over year, a pitch is flagged for **New / Dropped** (under 10 thrown one season, 5%+ usage the other), **Usage up/down** (10+ points), **Velo up/down** (1.5+ mph) or **Shape change** (2.5+ inches of break). An **arm slot change** is 4+ degrees.

## Limits

- One season of baseline data, for now.
- Small samples are flagged, not graded.
- Run value is noisy over a few hundred pitches. Flags are prompts to look closer, not verdicts.
- Rare pitches can look good because they're rare, and the same holds for counts.
- Whiff+ inflates on pitch types with low league whiff rates, such as sinkers.
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
