#!/usr/bin/env python3
"""
Refresh the Nasdaq "Internet boom vs AI boom" chart.

BLUE line  = Internet Boom & Bust -- FROZEN. It is the original line, traced once,
             read from blue_internet_line.csv (never changes).
RED  line  = AI boom -- RE-FETCHED LIVE every run, from AI_START up to the most
             recent trading day, plotted as "% change from start" vs
             "trading days from start" (same convention as the blue line).

Run it whenever you want a fresh chart (e.g. every 2 weeks):
    python3 update_chart.py

Output: nasdaq_boom_latest.png (saved next to this script).

Needs internet. Packages: numpy + matplotlib (always); pandas + yfinance only if
you want the yfinance fallback. Install with:  pip install numpy matplotlib
"""

import os, io, sys, csv, datetime as dt, urllib.request
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# ----------------------------------------------------------------------------
HERE     = os.path.dirname(os.path.abspath(__file__))
BLUE_CSV = os.path.join(HERE, "blue_internet_line.csv")
OUT_PNG  = os.path.join(HERE, "nasdaq_boom_latest.png")
AI_START   = "2022-12-01"        # AI-boom start date (gives the -11% Dec-2022 dip)
BLUE_START = "1994-12-15"         # Internet-boom start (near late-94 low, base ~730.7 -> +591% peak)
BLUE_END   = "2000-04-07"         # ends ~+509%, matching the original's right edge
# ----------------------------------------------------------------------------

BLUE, ORANGE, PANEL, GRID, INK = "#6E79D6", "#E2703A", "#E9EDF5", "#FFFFFF", "#2A3F5F"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode()


def fetch_nasdaq(start):
    """Return (dates[list of date], closes[np.array]) of Nasdaq Composite daily
    closes from `start`. Tries FRED, then Stooq, then yfinance."""
    today = dt.date.today().isoformat()

    # 1) FRED NASDAQCOM (no key) ------------------------------------------------
    try:
        raw = _get("https://fred.stlouisfed.org/graph/fredgraph.csv"
                   f"?id=NASDAQCOM&cosd={start}&coed={today}")
        dates, closes = [], []
        for row in csv.reader(io.StringIO(raw)):
            if not row or row[0][:1].isalpha():      # skip header
                continue
            try:
                closes.append(float(row[1])); dates.append(dt.date.fromisoformat(row[0]))
            except ValueError:
                continue                              # "." = market holiday
        if len(closes) > 50:
            print(f"[data] FRED NASDAQCOM: {len(closes)} rows, "
                  f"latest {dates[-1]} = {closes[-1]:,.2f}")
            return dates, np.array(closes)
    except Exception as e:
        print(f"[data] FRED failed: {e}")

    # 2) Stooq ^ndq -------------------------------------------------------------
    try:
        raw = _get(f"https://stooq.com/q/d/l/?s=^ndq&i=d"
                   f"&d1={start.replace('-','')}&d2={today.replace('-','')}")
        dates, closes = [], []
        rows = list(csv.reader(io.StringIO(raw)))
        for row in rows[1:]:
            try:
                closes.append(float(row[4])); dates.append(dt.date.fromisoformat(row[0]))
            except (ValueError, IndexError):
                continue
        if len(closes) > 50:
            print(f"[data] Stooq ^ndq: {len(closes)} rows, latest {dates[-1]} = {closes[-1]:,.2f}")
            return dates, np.array(closes)
    except Exception as e:
        print(f"[data] Stooq failed: {e}")

    # 3) yfinance ^IXIC (needs pandas) -----------------------------------------
    try:
        import yfinance as yf
        d = yf.download("^IXIC", start=start, progress=False, auto_adjust=False)
        closes = d["Close"].dropna().values.astype(float).ravel()
        dates  = [x.date() for x in d.index]
        if len(closes) > 50:
            print(f"[data] yfinance ^IXIC: {len(closes)} rows, latest {dates[-1]} = {closes[-1]:,.2f}")
            return dates, np.array(closes)
    except Exception as e:
        print(f"[data] yfinance failed: {e}")

    sys.exit("ERROR: could not fetch Nasdaq data (FRED / Stooq / yfinance all failed). "
             "Check your internet connection.")


def fetch_blue():
    """Internet-boom line from real FRED data (exact). Falls back to the traced
    CSV if offline. Returns (day[np], pct[np])."""
    try:
        url = ("https://fred.stlouisfed.org/graph/fredgraph.csv"
               f"?id=NASDAQCOM&cosd={BLUE_START}&coed={BLUE_END}")
        closes = []
        for row in csv.reader(io.StringIO(_get(url))):
            if not row or row[0][:1].isalpha():
                continue
            try:
                closes.append(float(row[1]))
            except ValueError:
                continue
        c = np.array(closes)
        if len(c) > 200:
            print(f"[data] FRED blue 1995-2000: {len(c)} days, peak +{(c.max()/c[0]-1)*100:.0f}%")
            return np.arange(len(c)), (c/c[0]-1)*100
    except Exception as e:
        print(f"[data] FRED blue failed ({e}); using traced fallback")
    a = np.genfromtxt(BLUE_CSV, delimiter=",", names=True)
    return a["day"], a["pct"]


def main():
    # --- internet (blue) line: exact from FRED, traced csv as fallback ---
    gi, pi_ = fetch_blue()

    # --- live red line ---
    dates, closes = fetch_nasdaq(AI_START)
    ga = np.arange(len(closes))                       # trading days from start
    pa = (closes / closes[0] - 1.0) * 100.0
    latest_date, latest_val, latest_pct = dates[-1], closes[-1], pa[-1]

    # --- plot (styled like the original) ---
    fig, ax = plt.subplots(figsize=(12.8, 6.0), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(PANEL)
    ax.plot(gi, pi_, color=BLUE,   lw=1.4, label="Internet Boom & Bust (1994–2000)")
    ax.plot(ga, pa, color=ORANGE, lw=1.6, label="AI Boom (2022–present)")
    ax.plot([ga[-1]], [pa[-1]], "o", ms=4.5, color=ORANGE)
    ax.annotate(f"{latest_date:%d %b %Y}  +{latest_pct:.0f}%",
                xy=(ga[-1], pa[-1]), xytext=(ga[-1]+10, pa[-1]-3),
                fontsize=8, color="#9A3A22", va="center")

    ax.grid(True, color=GRID, lw=1.0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=INK, labelsize=10)
    ax.set_xlim(0, max(gi.max(), ga.max()) + 60)
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.xaxis.set_major_locator(MultipleLocator(200))
    ax.set_xlabel("Days from boom start", color=INK, fontsize=11)
    ax.set_ylabel("Percent change (%)", color=INK, fontsize=11)

    fig.text(0.068, 0.945,
             "Nasdaq Composite: Internet Boom vs AI Boom (Percentage change from start)",
             color=INK, fontsize=15, fontweight="normal")
    fig.text(0.068, 0.905,
             f"Blue = Nasdaq {BLUE_START[:4]}–{BLUE_END[:4]} (exact).  Red = Nasdaq from {AI_START}, "
             f"refreshed live to {latest_date:%d %b %Y} ({latest_val:,.0f}, +{latest_pct:.0f}%).",
             color="#5A6B85", fontsize=8.6)

    leg = ax.legend(loc="upper left", frameon=False, fontsize=9.5,
                    bbox_to_anchor=(1.012, 0.99), handlelength=1.6)
    for t in leg.get_texts():
        t.set_color(INK)
    plt.subplots_adjust(left=0.068, right=0.755, top=0.85, bottom=0.105)
    fig.savefig(OUT_PNG, facecolor="white")
    print(f"[ok] wrote {OUT_PNG}")

    # dated snapshot, kept in history/ so you build a timeline
    hist_dir = os.path.join(HERE, "history")
    os.makedirs(hist_dir, exist_ok=True)
    dated = os.path.join(hist_dir, f"nasdaq_boom_{dt.date.today():%Y-%m-%d}.png")
    fig.savefig(dated, facecolor="white")
    print(f"[ok] snapshot  {dated}")
    print(f"[ok] red line: {len(closes)} trading days, latest +{latest_pct:.1f}% on {latest_date}")


if __name__ == "__main__":
    main()
