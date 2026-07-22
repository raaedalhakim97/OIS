"""
The series mascot: a small cloaked "light-carrier" who carries a glowing orb.
Iconic silhouette that reads at thumbnail size. Grounded (cloak hem on floor).

character(h, pose, t) -> (RGBA sprite, foot_y, orb_dx, orb_dy)
  orb_dx/dy = where the glowing orb sits, relative to the figure's feet point.
poses: stand | walk | lift | sit
"""
import math
from PIL import Image, ImageDraw

INK = (5, 6, 11)      # near-black so the silhouette reads against dark scenes


def character(h, pose="stand", t=0.0, face=1, lift=0.0):
    S = 2
    Cw = int(h * 1.25) * S
    Ch = int(h * 1.25) * S
    im = Image.new("RGBA", (Cw, Ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = Cw // 2
    base = Ch - int(h * 0.10) * S           # cloak hem baseline
    hh = h * S
    col = INK + (255,)
    bob = math.sin(t * 2.2) * 0.015 * hh    # gentle breathing

    headr = 0.15 * hh
    neck_y = base - 0.66 * hh + bob
    head_y = base - 0.86 * hh + bob
    baseW = 0.34 * hh
    neckW = 0.13 * hh
    sway = math.sin(t * 3.0) * 0.02 * hh if pose == "walk" else 0.0

    # cloak: flared body with a rounded hem
    d.polygon([(cx - neckW, neck_y), (cx + neckW, neck_y),
               (cx + baseW + sway, base), (cx - baseW - sway, base)], fill=col)
    d.ellipse([cx - baseW - sway, base - 0.10 * hh, cx + baseW + sway, base + 0.06 * hh], fill=col)
    # little walk feet peeking under the hem
    if pose == "walk":
        a = math.sin(t * 6) * 0.06 * hh
        d.ellipse([cx - 0.12 * hh + a, base - 0.02 * hh, cx - 0.02 * hh + a, base + 0.06 * hh], fill=col)
        d.ellipse([cx + 0.02 * hh - a, base - 0.02 * hh, cx + 0.12 * hh - a, base + 0.06 * hh], fill=col)

    # hood + head (a soft point at the back of the hood)
    d.polygon([(cx - headr * 0.9, head_y + headr * 0.2),
               (cx - face * 0.10 * hh, head_y - headr * 1.5),
               (cx + headr * 0.9, head_y + headr * 0.2)], fill=col)   # hood tip
    d.ellipse([cx - headr, head_y - headr, cx + headr, head_y + headr], fill=col)

    # holding arm: interpolate the hand from carried (at the side) to raised
    # (high) by `lift` in [0,1], so raising/lowering the light is continuous.
    if pose == "lift":            # back-compat: 'lift' pose == fully raised
        lift = 1.0
    carr_x, carr_y = cx + face * 0.30 * hh, neck_y + 0.04 * hh
    rais_x, rais_y = cx + face * 0.22 * hh, neck_y - 0.42 * hh
    if pose == "sit":
        hand_x, hand_y = cx + face * 0.26 * hh, neck_y + 0.10 * hh
    elif lift >= 0:               # raise toward the sky
        hand_x = carr_x + (rais_x - carr_x) * lift
        hand_y = carr_y + (rais_y - carr_y) * lift
    else:                         # lower toward the ground/water (lift in [-1,0])
        lowr_x, lowr_y = cx + face * 0.36 * hh, neck_y + 0.54 * hh
        hand_x = carr_x + (lowr_x - carr_x) * (-lift)
        hand_y = carr_y + (lowr_y - carr_y) * (-lift)
    d.line([(cx + face * neckW, neck_y + 0.06 * hh), (hand_x, hand_y)], fill=col, width=int(0.09 * hh))
    d.ellipse([hand_x - 0.05 * hh, hand_y - 0.05 * hh, hand_x + 0.05 * hh, hand_y + 0.05 * hh], fill=col)

    im = im.resize((Cw // S, Ch // S), Image.LANCZOS)
    # foot point and orb offset in downscaled coords, relative to feet (cx, base)
    fy = base / S
    orb_dx = (hand_x - cx) / S + face * 6
    orb_dy = (hand_y - base) / S - 6
    return im, fy, orb_dx, orb_dy


if __name__ == "__main__":
    import numpy as np
    W, H = 600, 800
    for i, pose in enumerate(["stand", "walk", "lift", "sit"]):
        bg = Image.new("RGB", (W, H), (26, 30, 54))
        d = ImageDraw.Draw(bg)
        d.line([(0, int(H * 0.8)), (W, int(H * 0.8))], fill=(12, 14, 24), width=3)
        spr, fy, odx, ody = character(280, pose, t=0.3, face=1)
        sw, sh = spr.size
        cx, gy = W // 2, int(H * 0.8)
        # orb glow
        ox, oy = cx + odx, gy + ody
        for r, a in ((70, 60), (34, 120), (16, 255)):
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse([ox - r, oy - r, ox + r, oy + r],
                                       fill=(255, 200, 120, a))
            bg = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
        bg.paste(spr, (int(cx - sw / 2), int(gy - fy)), spr)
        bg.save(f"char_{pose}.png")
    print("saved char_*.png")
