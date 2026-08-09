import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

img = plt.imread("/sessions/ecstatic-kind-euler/mnt/Projects--dot-com/dotcom.png")
img = (img[..., :3]*255).astype(int) if img.max() <= 1.0 else img[..., :3].astype(int)
H, W, _ = img.shape
R, G, B = img[:,:,0], img[:,:,1], img[:,:,2]

x0 = 93            # panel left (full-img px)
# x calibration: panel-relative px -> day.  gridlines [119..743] = 200..1200
vg = np.array([119,244,369,493,618,743]) + x0
vd = np.array([200,400,600,800,1000,1200])
mx = np.polyfit(vg, vd, 1)          # px(full) -> day
def px2day(px): return mx[0]*px + mx[1]
# y calibration
y0 = 97
hg = np.array([16,81,147,213,279,345,410]) + y0
hv = np.array([600,500,400,300,200,100,0])
my = np.polyfit(hg, hv, 1)
def py2pct(py): return my[0]*py + my[1]

xL, xR = 95, 922
yT, yB = 98, 535

blue   = (B>150) & (B > R+35) & (G < B-10)
orange = (R>175) & (B < 140) & (R > B+55) & (G>70) & (G<175)

def trace(mask):
    days, pct = [], []
    for x in range(xL, xR+1):
        rs = np.where(mask[yT:yB+1, x])[0]
        if len(rs)==0: continue
        py = rs.mean() + yT
        days.append(px2day(x)); pct.append(py2pct(py))
    return np.array(days), np.array(pct)

bd, bp = trace(blue)
od, op = trace(orange)

print("BLUE : day range %.0f..%.0f  pct range %.0f..%.0f" % (bd.min(), bd.max(), bp.min(), bp.max()))
imax = np.argmax(bp)
print("       peak  %.0f%% at day %.0f" % (bp[imax], bd[imax]))
print("       start pct %.1f at day %.0f ; end pct %.0f at day %.0f" % (bp[0], bd[0], bp[-1], bd[-1]))
print("ORANGE: day range %.0f..%.0f  pct range %.0f..%.0f" % (od.min(), od.max(), op.min(), op.max()))
print("       start pct %.1f at day %.0f ; end pct %.0f at day %.0f" % (op[0], od[0], op[-1], od[-1]))
# blue dip near day 590
m = (bd>520)&(bd<660)
print("       blue local min in 520-660: %.0f%% at day %.0f" % (bp[m].min(), bd[m][np.argmin(bp[m])]))

np.savez("/sessions/ecstatic-kind-euler/mnt/outputs/traced.npz", bd=bd, bp=bp, od=od, op=op)

# quick visual of the trace
fig, ax = plt.subplots(figsize=(11,5.5), dpi=130)
ax.set_facecolor("#E9EDF5")
ax.plot(bd, bp, color="#6E79D6", lw=1.2, label="blue traced")
ax.plot(od, op, color="#E2703A", lw=1.2, label="orange traced")
ax.grid(True, color="white"); ax.set_xlabel("Days"); ax.set_ylabel("%")
ax.legend(); fig.savefig("/sessions/ecstatic-kind-euler/mnt/outputs/traced_check.png")
print("saved traced_check.png")
