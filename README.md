# Nasdaq Internet-boom vs AI-boom — auto-updating chart

Compares the dot-com era and the AI era on the same axes: **% change from each
boom's start** vs **trading days from start**.

- **Blue — Internet boom:** Nasdaq Composite `1995-01-03 → 2000-04-07` (0% → ~+579% peak).
- **Red — AI boom:** Nasdaq Composite from `2022-12-01` to **today** (re-fetched live each run).

Both lines are pulled from real data (FRED `NASDAQCOM`), so dates and values are exact.
A one-off pixel-traced copy of the original (`blue_internet_line.csv`) is kept only as
an offline fallback.

## One-time setup
```bash
cd ~/Projects/dot-com/nasdaq_recreate
python3 -m venv venv
source venv/bin/activate
pip install numpy matplotlib          # optional fallback source: pip install yfinance
```
(If you skip the venv and hit `externally-managed-environment`, add
`--break-system-packages` to the pip command.)

## Static chart (PNG)
```bash
source venv/bin/activate
python3 update_chart.py
```
Writes **`nasdaq_boom_latest.png`** plus a dated copy in **`history/`**.
Run it on 30 Jun 2026 → red runs to 30 Jun 2026; run it later → it extends further.
Data source order: FRED `NASDAQCOM` → Stooq `^ndq` → yfinance `^IXIC` (first that responds).

## Interactive chart (HTML, hover to read dates/values)
```bash
python3 make_interactive.py            # both lines exact (live FRED)
python3 make_interactive.py --demo     # offline: blue = traced csv, red = built-in sample
python3 make_interactive.py --compare  # prints traced-vs-fetched variance, no file written
```
Open **`nasdaq_boom_interactive.html`** in any browser.

- Hovering any *day from boom start* shows a **unified tooltip with both lines'**
  date, Nasdaq value, and %.
- Past the end of the red line (the latest AI date), the tooltip still shows the
  **projected AI date** for that day — marked *“no data yet.”* The red line itself
  stops at the last real data point.
- Needs internet once per open, to load the Plotly library from a CDN. The chart
  data itself is embedded in the file.

## Scheduling: GitHub Actions (installed — weekday mornings)
This repo runs itself via `.github/workflows/update-chart.yml`: every weekday
at ~11:17 UTC (≈7am US/Eastern) a GitHub-hosted runner checks out the repo,
regenerates both charts, and commits the results straight to `main` if
anything changed. No dependency on your laptop being awake or online.

- Runs Mon–Fri only. The ~1-business-day FRED publish lag is why it fires in
  the morning rather than at market close — by then the prior trading day's
  close is reliably available.
- Trigger a run manually any time from the repo's **Actions** tab →
  *Refresh Nasdaq boom chart* → **Run workflow** (the workflow also has
  `workflow_dispatch` enabled for this).
- Requires only `numpy` + `matplotlib`, installed fresh each run — no venv
  needed on the runner.

(A local `crontab` entry doing the same thing was used earlier in this
project's life but has been removed in favor of Actions, since a closed/
asleep laptop silently skips cron — see project history if you want to
resurrect the local-only version.)

## Files
| file | purpose |
|---|---|
| `update_chart.py` | static PNG — fetches blue + red live, plots |
| `make_interactive.py` | interactive HTML (`--demo`, `--compare` flags) |
| `nasdaq_boom_latest.png` | latest static chart (overwritten each run) |
| `history/` | dated PNG snapshot per run |
| `nasdaq_boom_interactive.html` | latest interactive chart |
| `blue_internet_line.csv` | pixel-traced blue line — offline fallback only |
| `dotcom.png` | the original chart (used once for the trace) |
| `trace_original.py`, `trace2.py` | how the blue line was traced (reference) |
| `nasdaq_boom_chart.py` | the build script used during chat (reference) |

## Config
Near the top of the scripts:
- `AI_START   = "2022-12-01"` — AI-boom start (the −11% Dec-2022 dip anchors this).
- `BLUE_START = "1995-01-03"`, `BLUE_END = "2000-04-07"` — Internet-boom window.

## Note on running inside Cowork
Cowork's sandbox has **no access to market-data sites**, so these scripts must run on
your own machine (or via the cron line above). Inside Cowork the live fetch fails and
the blue line silently falls back to the traced CSV.
