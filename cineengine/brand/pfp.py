"""Clean circular profile logo for THE OBSERVER — mascot + orb, reads small."""
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from character import character

S = 1080
a = np.zeros((S, S, 3), np.float32)
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
# radial gradient background (deep indigo -> near black at edges)
d = np.sqrt((xx - S/2)**2 + (yy - S*0.52)**2) / (S*0.7)
base = np.array([26, 28, 58]) * (1 - d)[..., None] + np.array([6, 7, 16]) * d[..., None]
a += np.clip(base, 0, 255)

def glow(cx, cy, rad, col, al):
    dd = (xx - cx)**2 + (yy - cy)**2
    a[:] += (np.exp(-dd / (2*rad**2)) * al)[..., None] * np.array(col, np.float32)

# a scatter of soft stars
rng = np.random.default_rng(3)
for _ in range(70):
    sx, sy = rng.integers(0, S), rng.integers(0, int(S*0.7))
    b = rng.uniform(0.3, 1.0) * 180
    a[sy, sx] += [b, b, b*1.05]

# the orb (raised, warm) + its glow
ox, oy = S*0.58, S*0.44
glow(ox, oy, 130, [255, 196, 120], 0.9)
glow(ox, oy, 40, [255, 235, 200], 1.2)

im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
# mascot, lifting the light, centered low
spr, fy, odx, ody = character(430, "stand", 0.0, 1, lift=1.0)
im.paste(spr, (int(S*0.42 - spr.size[0]/2), int(S*0.80 - fy)), spr)

# soft circular vignette so it sits well in the round crop
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).ellipse([S*0.02, S*0.02, S*0.98, S*0.98], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(40))
dark = Image.new("RGB", (S, S), (4, 5, 12))
im = Image.composite(im, dark, mask)

# subtle wordmark at the bottom (still legible-ish in circle center-safe zone)
draw = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 62)
except Exception:
    f = ImageFont.load_default()
txt = "THE OBSERVER"
bb = draw.textbbox((0, 0), txt, font=f)
draw.text(((S-(bb[2]-bb[0]))//2, int(S*0.88)), txt, font=f, fill=(210, 214, 228))

im.save("observer_pfp.png")
# also a version with no text (cleaner for tiny sizes)
im2 = Image.composite(Image.fromarray(a.clip(0,255).astype(np.uint8)), dark, mask)
im2.paste(spr, (int(S*0.42 - spr.size[0]/2), int(S*0.80 - fy)), spr)
im2.save("observer_pfp_notext.png")
print("saved observer_pfp.png + observer_pfp_notext.png")
