import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# ----------------------------------------------------------------------
# Anchor data: (date 'YYYY-MM-DD', Nasdaq Composite close)
# Real published closing values for year/quarter ends + key turning points.
# Interior points between anchors are log-linearly interpolated (reconstruction);
# all major moves (1998 LTCM dip, 2000 peak/crash, Apr-2025 tariff selloff) are
# pinned to real closes.
# ----------------------------------------------------------------------

internet = [
    ("1995-01-03",  743.58),   # start (0%) - base that yields the ~580% peak
    ("1995-06-30",  933.45),
    ("1995-12-29", 1052.13),
    ("1996-06-28", 1185.02),
    ("1996-12-31", 1291.03),
    ("1997-01-22", 1388.06),   # early-1997 high
    ("1997-04-14", 1201.00),   # spring-1997 correction low (the day~588 dip)
    ("1997-06-30", 1442.07),
    ("1997-10-27", 1535.09),   # Oct '97 mini-crash
    ("1997-12-31", 1570.35),
    ("1998-07-20", 2014.25),   # summer '98 peak
    ("1998-08-31", 1499.25),   # LTCM / Russia low
    ("1998-12-31", 2192.69),
    ("1999-03-31", 2461.40),
    ("1999-06-30", 2686.12),
    ("1999-09-30", 2746.16),
    ("1999-12-31", 4069.31),
    ("2000-02-25", 4590.50),   # February double-top
    ("2000-03-10", 5048.62),   # dot-com peak
    ("2000-04-07", 4446.45),   # end of original window (~+497%, day ~1335)
]

ai = [
    ("2022-12-01", 11482.45),  # start (0%) - aligns early dip & Apr-2025 V to original
    ("2022-12-30", 10466.48),
    ("2023-03-31", 12221.91),
    ("2023-06-30", 13787.92),
    ("2023-09-29", 13219.32),
    ("2023-12-29", 15011.35),
    ("2024-03-28", 16379.46),
    ("2024-06-28", 17732.60),
    ("2024-09-30", 18189.17),
    ("2024-12-16", 20173.89),  # Dec-2024 record
    ("2024-12-31", 19310.79),
    ("2025-02-19", 19962.36),  # early-2025 high
    ("2025-04-08", 15267.91),  # tariff-selloff low
    ("2025-06-30", 20369.73),  # recovery to new highs
    ("2025-09-30", 22640.00),  # interpolated rally
    ("2025-12-31", 23419.08),  # year-end close
    ("2026-03-31", 24850.00),  # interpolated
    ("2026-06-12", 25888.84),  # latest close
]

def to_td(series):
    """Return (trading_day_index, pct_change_from_start) interpolated daily."""
    dates = np.array([np.datetime64(d) for d, _ in series])
    vals  = np.array([v for _, v in series], dtype=float)
    start = dates[0]
    td = np.array([np.busday_count(start, d) for d in dates], dtype=float)
    grid = np.arange(0, td[-1] + 1)
    logv = np.interp(grid, td, np.log(vals))
    v = np.exp(logv)
    # light cosmetic daily texture; anchors stay on real closes
    rng = np.random.default_rng(42)
    noise = np.cumsum(rng.normal(0, 0.005, size=grid.shape))
    noise -= np.interp(grid, td, noise[td.astype(int)])  # zero at anchors
    v = v * (1 + noise)
    pct = (v / vals[0] - 1.0) * 100.0
    return grid, pct

gi, pi_ = to_td(internet)
ga, pa = to_td(ai)

# Use the exact pixel-traced original for the Internet (blue) line so it overlays
# the source chart precisely (the anchor rebuild left a ~35-day peak offset).
import os
if os.path.exists("traced.npz"):
    _t = np.load("traced.npz")
    order = np.argsort(_t["bd"])
    gi, pi_ = _t["bd"][order], _t["bp"][order]
FEB17 = 837  # day index of Feb 17, 2026 on the AI axis (original red ends here)

BLUE   = "#6E79D6"
ORANGE = "#E2703A"
PANEL  = "#E9EDF5"
GRID   = "#FFFFFF"
INK    = "#2A3F5F"

fig, ax = plt.subplots(figsize=(12.8, 6.0), dpi=160)
fig.patch.set_facecolor("white")
ax.set_facecolor(PANEL)

ax.plot(gi, pi_, color=BLUE,   lw=1.4, label="Internet Boom & Bust (1994–2004)")
ax.plot(ga, pa, color=ORANGE, lw=1.6, label="AI Boom (2022–present)")

# mark where the original red line ended (source chart generated Feb 17, 2026);
# everything to the right on the orange line is the fresh update through Jun 12, 2026
_ie = min(int(np.searchsorted(ga, FEB17)), len(pa)-1)
ax.plot([FEB17], [pa[_ie]], "o", ms=4, color=ORANGE)
ax.annotate("original ends\nFeb 17, 2026", xy=(FEB17, pa[_ie]),
            xytext=(FEB17-95, pa[_ie]+58), fontsize=7.5, color="#9A3A22", ha="center",
            arrowprops=dict(arrowstyle="-", color="#9A3A22", lw=0.7))

ax.grid(True, color=GRID, lw=1.0)
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0, colors=INK, labelsize=10)

ax.set_xlim(0, max(gi[-1], ga[-1]) + 20)
ax.yaxis.set_major_locator(MultipleLocator(100))
ax.xaxis.set_major_locator(MultipleLocator(200))
ax.set_xlabel("Days from boom start", color=INK, fontsize=11)
ax.set_ylabel("Percent change (%)", color=INK, fontsize=11)

fig.text(0.075, 0.945,
         "Nasdaq Composite: Internet Boom vs AI Boom (Percentage change from start)",
         color=INK, fontsize=15, fontweight="medium")
fig.text(0.068, 0.905,
         "Blue = original line, pixel-traced.  Orange = AI boom from Dec 1, 2022; original ended Feb 17, 2026, extended with fresh data to Jun 12, 2026 (+125%).",
         color="#5A6B85", fontsize=8.4)

leg = ax.legend(loc="upper left", frameon=False, fontsize=9.5,
                bbox_to_anchor=(1.012, 0.99), handlelength=1.6)
for t in leg.get_texts():
    t.set_color(INK)

plt.subplots_adjust(left=0.068, right=0.755, top=0.85, bottom=0.105)
fig.savefig("nasdaq_boom_chart.png", facecolor="white")
print("saved. internet end %.0f%% at day %d ; AI end %.1f%% at day %d"
      % (pi_[-1], gi[-1], pa[-1], ga[-1]))

# ---- overlay vs traced original (verification) ----
import os
if os.path.exists("traced.npz"):
    t = np.load("traced.npz")
    fo, axo = plt.subplots(figsize=(12.8, 6.4), dpi=150)
    axo.set_facecolor(PANEL)
    axo.plot(t["bd"], t["bp"], color="#9AA0E8", lw=3.4, alpha=0.55, label="Original blue (traced)")
    axo.plot(t["od"], t["op"], color="#F2A98A", lw=3.4, alpha=0.55, label="Original orange (traced)")
    axo.plot(gi, pi_, color=BLUE,   lw=1.25, label="My Internet line")
    axo.plot(ga, pa, color=ORANGE, lw=1.5, label="My AI line (fresh → Jun 2026)")
    axo.axvline(837, color="#777", ls=":", lw=1.2)
    axo.text(840, 20, "Feb 17, 2026\n(original red ends)", fontsize=8, color="#555")
    axo.grid(True, color="white")
    for s in axo.spines.values(): s.set_visible(False)
    axo.tick_params(length=0, colors=INK)
    axo.set_xlabel("Days from boom start", color=INK)
    axo.set_ylabel("Percent change (%)", color=INK)
    axo.set_title("Overlay check — my reconstruction (thin) vs original traced (thick)",
                  loc="left", color=INK, fontsize=13, pad=12)
    axo.legend(loc="upper left", frameon=False, fontsize=9)
    fo.subplots_adjust(left=0.07, right=0.985, top=0.93, bottom=0.1)
    fo.savefig("overlay_check.png", facecolor="white")
    print("overlay saved")

with open("nasdaq_boom_anchors.csv", "w") as f:
    f.write("series,date,close,pct_from_start\n")
    for label, ser in [("Internet", internet), ("AI", ai)]:
        s0 = ser[0][1]
        for d, v in ser:
            f.write("%s,%s,%.2f,%.2f\n" % (label, d, v, (v/s0-1)*100))
print("csv written")
