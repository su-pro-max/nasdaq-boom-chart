import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

img = plt.imread("/sessions/ecstatic-kind-euler/mnt/Projects--dot-com/dotcom.png")
if img.dtype != np.uint8:
    img = (img[..., :3] * 255).astype(np.uint8)
else:
    img = img[..., :3]
H, W, _ = img.shape
R = img[:, :, 0].astype(int); G = img[:, :, 1].astype(int); B = img[:, :, 2].astype(int)
print("image", W, "x", H)

# ---- locate panel (light lavender-grey background ~ (232,236,245)) ----
panel = (np.abs(R-232) < 12) & (np.abs(G-236) < 12) & (np.abs(B-245) < 12)
cols = np.where(panel.sum(axis=0) > 0.3*panel.sum(axis=0).max())[0]
rows = np.where(panel.sum(axis=1) > 0.3*panel.sum(axis=1).max())[0]
x0, x1 = cols.min(), cols.max()
y0, y1 = rows.min(), rows.max()
print("panel x:", x0, x1, " y:", y0, y1)

# ---- detect white gridlines inside panel ----
sub = panel[y0:y1+1, x0:x1+1]
white = (R>250)&(G>250)&(B>250)
wsub = white[y0:y1+1, x0:x1+1]
colscore = wsub.sum(axis=0)
rowscore = wsub.sum(axis=1)

def peaks(score, min_frac=0.5):
    thr = min_frac*score.max()
    idx = np.where(score>thr)[0]
    groups=[]; cur=[idx[0]]
    for v in idx[1:]:
        if v-cur[-1]<=3: cur.append(v)
        else: groups.append(int(np.mean(cur))); cur=[v]
    groups.append(int(np.mean(cur)))
    return groups

vg = peaks(colscore); hg = peaks(rowscore)
print("vertical gridlines (panel px):", vg)
print("horizontal gridlines (panel px):", hg)
