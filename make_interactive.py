#!/usr/bin/env python3
"""
Build an INTERACTIVE html version of the Nasdaq boom chart, with EXACT data for
both lines fetched live from FRED (NASDAQCOM).

Hovering a "day from boom start" shows a unified tooltip with BOTH lines' date,
Nasdaq Composite value, and % change for that day.

  python3 make_interactive.py            # both lines fetched live (exact)
  python3 make_interactive.py --demo     # offline: blue=traced csv, red=sample
  python3 make_interactive.py --compare  # print traced-vs-fetched variance report

Output: nasdaq_boom_interactive.html  (needs internet once for the Plotly CDN).

Lines / windows:
  BLUE Internet boom : NASDAQCOM 1994-12-15 -> 2000-04-07  (0% -> ~+591% peak/top)
  RED  AI boom       : NASDAQCOM 2022-12-01 -> today
Both indexed as "% change from start" vs "trading days from start".
"""

import os, sys, io, csv, json, datetime as dt, urllib.request
import numpy as np

HERE      = os.path.dirname(os.path.abspath(__file__))
BLUE_CSV  = os.path.join(HERE, "blue_internet_line.csv")
OUT_HTML  = os.path.join(HERE, "nasdaq_boom_interactive.html")

AI_START    = "2022-12-01"
BLUE_START  = "1994-12-15"           # near late-94 low, base ~730.7 -> peak +591% (matches original)
BLUE_END    = "2000-04-07"           # ends ~+509%, like the original's right edge

# sample AI anchors for --demo only (real closes, smooth between)
DEMO_AI = [
    ("2022-12-01",11482.45),("2022-12-30",10466.48),("2023-03-31",12221.91),
    ("2023-06-30",13787.92),("2023-09-29",13219.32),("2023-12-29",15011.35),
    ("2024-03-28",16379.46),("2024-06-28",17732.60),("2024-09-30",18189.17),
    ("2024-12-16",20173.89),("2024-12-31",19310.79),("2025-02-19",19962.36),
    ("2025-04-08",15267.91),("2025-06-30",20369.73),("2025-09-30",22640.00),
    ("2025-12-31",23419.08),("2026-03-31",24850.00),("2026-06-12",25888.84),
]


def fetch_fred(start, end=None):
    """Nasdaq Composite (FRED NASDAQCOM) daily closes -> (dates[str], closes[np])."""
    end = end or dt.date.today().isoformat()
    url = ("https://fred.stlouisfed.org/graph/fredgraph.csv"
           f"?id=NASDAQCOM&cosd={start}&coed={end}")
    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30).read().decode()
    dates, closes = [], []
    for row in csv.reader(io.StringIO(raw)):
        if not row or row[0][:1].isalpha():
            continue
        try:
            closes.append(float(row[1])); dates.append(row[0])
        except ValueError:
            continue                      # "." = holiday
    if len(closes) < 30:
        raise RuntimeError(f"FRED returned too few rows for {start}..{end}")
    return dates, np.array(closes)


def series(dates, closes):
    closes = np.asarray(closes, float)
    day = list(range(len(closes)))
    pct = ((closes/closes[0]-1)*100).round(2).tolist()
    cd  = [[str(d), round(float(c))] for d, c in zip(dates, closes)]
    return day, pct, cd, str(dates[-1]), float(closes[-1]), pct[-1]


def blue_live():   return series(*fetch_fred(BLUE_START, BLUE_END))
def red_live():
    from update_chart import fetch_nasdaq
    d, c = fetch_nasdaq(AI_START)
    return series([str(x) for x in d], c)


def blue_traced():
    a = np.genfromtxt(BLUE_CSV, delimiter=",", names=True)
    day, pct = a["day"], a["pct"]
    base, start = 744.0, np.busday_offset("2000-03-10", -1320)
    val  = base*(1+pct/100.0)
    date = [str(np.busday_offset(start, int(round(d)))) for d in day]
    cd   = [[ds, round(float(v))] for ds, v in zip(date, val)]
    return day.tolist(), pct.round(2).tolist(), cd, date[-1], float(val[-1]), float(pct[-1])


def red_demo():
    d0 = np.datetime64(DEMO_AI[0][0])
    ad = np.array([np.busday_count(d0, np.datetime64(d)) for d, _ in DEMO_AI], float)
    ac = np.array([c for _, c in DEMO_AI], float)
    grid = np.arange(0, ad[-1]+1)
    close = np.exp(np.interp(grid, ad, np.log(ac)))
    dates = [str(np.busday_offset(d0, int(g))) for g in grid]
    return series(dates, close)


def compare():
    """Quantify how far the one-off traced blue line sits from the real data."""
    dates, closes = fetch_fred(BLUE_START, BLUE_END)
    real_day = np.arange(len(closes))
    real_pct = (closes/closes[0]-1)*100
    a = np.genfromtxt(BLUE_CSV, delimiter=",", names=True)
    tr = np.interp(real_day, a["day"], a["pct"])     # traced, sampled on real days
    diff = tr - real_pct
    print(f"compared {len(closes)} trading days ({dates[0]} .. {dates[-1]})")
    print(f"  mean abs error : {np.abs(diff).mean():6.1f} pp")
    print(f"  RMS error      : {np.sqrt((diff**2).mean()):6.1f} pp")
    print(f"  max abs error  : {np.abs(diff).max():6.1f} pp  (steep 1999-2000 zone)")
    print(f"  median error   : {np.median(np.abs(diff)):6.1f} pp")
    print(f"  real peak      : {real_pct.max():.1f}%   traced peak: {a['pct'].max():.1f}%")


HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Nasdaq: Internet Boom vs AI Boom</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
 body{{margin:0;font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;background:#fff;color:#2A3F5F}}
 #wrap{{max-width:1180px;margin:18px auto;padding:0 14px}}
 h2{{font-weight:600;margin:0 0 2px}} .sub{{color:#5A6B85;font-size:13px;margin-bottom:6px}}
 #chart{{width:100%;height:620px}}
</style></head><body><div id="wrap">
<h2>Nasdaq Composite: Internet Boom vs AI Boom (Percentage change from start)</h2>
<div class="sub">{sub}</div>
<div id="chart"></div></div>
<script>
const BLUE={blue}, RED={red}, PROJ={proj};
const tBlue={{x:BLUE.x,y:BLUE.y,customdata:BLUE.cd,name:"Internet Boom & Bust (1994–2000)",
  mode:"lines",line:{{color:"#6E79D6",width:1.4}},
  hovertemplate:"%{{customdata[0]}}<br>Nasdaq %{{customdata[1]:,.0f}}<br>+%{{y:.1f}}%<extra>Internet boom</extra>"}};
const tRed={{x:RED.x,y:RED.y,customdata:RED.cd,name:"AI Boom (2022–present)",
  mode:"lines",line:{{color:"#E2703A",width:1.7}},
  hovertemplate:"%{{customdata[0]}}<br>Nasdaq %{{customdata[1]:,.0f}}<br>+%{{y:.1f}}%<extra>AI boom</extra>"}};
// invisible companion: beyond the red line's end, still report the projected AI date
const tProj={{x:PROJ.x,y:PROJ.x.map(()=>PROJ.y0),customdata:PROJ.date,
  mode:"markers",marker:{{opacity:0,size:8,color:"#E2703A"}},showlegend:false,hoverinfo:"text",
  hovertemplate:"%{{customdata}} (projected)<br><i>AI boom — no data yet</i><extra>AI boom</extra>"}};
const layout={{hovermode:"x unified",hoverdistance:1,spikedistance:1,
  plot_bgcolor:"#E9EDF5",paper_bgcolor:"#fff",
  margin:{{l:60,r:30,t:10,b:55}},
  xaxis:{{title:"Days from boom start",gridcolor:"#fff",zeroline:false}},
  yaxis:{{title:"Percent change (%)",gridcolor:"#fff",zeroline:false,ticksuffix:"%"}},
  legend:{{orientation:"h",y:1.08,x:0}},
  hoverlabel:{{bgcolor:"#fff",bordercolor:"#ccc"}}}};
Plotly.newPlot("chart",[tBlue,tRed,tProj],layout,{{responsive:true,displayModeBar:false}});
</script></body></html>"""


def main():
    if "--compare" in sys.argv:
        compare(); return
    demo = "--demo" in sys.argv
    if demo:
        bx, by, bcd, *_ = blue_traced()
        rx, ry, rcd, ld, lv, lp = red_demo()
        bsrc = "traced (approximate)"
    else:
        bx, by, bcd, *_ = blue_live()
        rx, ry, rcd, ld, lv, lp = red_live()
        bsrc = "live FRED (exact)"
    # projected AI dates for days beyond the red line's end (no value yet)
    maxday   = int(max(bx))
    last_red = int(rx[-1])
    proj_x   = list(range(last_red + 1, maxday + 1))
    proj_d   = [str(np.busday_offset(np.datetime64(AI_START), d)) for d in proj_x]
    proj     = {"x": proj_x, "date": proj_d, "y0": ry[-1]}

    sub = (f"Hover any day to compare both eras. Blue = Internet boom {BLUE_START}→{BLUE_END} "
           f"[{bsrc}]. Red = AI boom from {AI_START} to {ld} ({lv:,.0f}, +{lp:.0f}%); "
           f"past day {last_red} the tooltip shows the projected AI date (no data yet).")
    html = HTML.format(sub=sub,
                       blue=json.dumps({"x": bx, "y": by, "cd": bcd}),
                       red=json.dumps({"x": rx, "y": ry, "cd": rcd}),
                       proj=json.dumps(proj))
    with open(OUT_HTML, "w") as f:
        f.write(html)
    print(f"[ok] wrote {OUT_HTML}")
    print(f"[ok] blue {bsrc} ; red latest {ld} = {lv:,.2f} (+{lp:.1f}%)")


if __name__ == "__main__":
    main()
