"""
The series mascot: a small cloaked "light-carrier" who carries a glowing orb.
Iconic silhouette that reads at thumbnail size. Grounded (cloak hem on floor).

character(h, pose, t, face, lift, lean) -> (RGBA sprite, foot_y, orb_dx, orb_dy)
  orb_dx/dy = where the glowing orb sits, relative to the figure's feet point.
  lean = inverted-pendulum body swing from the feet (radians-ish, ~±0.15). The
         hem stays planted; the head, shoulders and carried light swing out with
         weight — the light swings most (it's highest), like a heavy lantern.
poses: stand | walk | lift | sit | front
"""
import math
from PIL import Image, ImageDraw

INK = (5, 6, 11)      # near-black so the silhouette reads against dark scenes


def character(h, pose="stand", t=0.0, face=1, lift=0.0, lean=0.0):
    S = 2
    Cw = int(h * 1.5) * S           # a little wider so a deep lean never clips
    Ch = int(h * 1.3) * S
    im = Image.new("RGBA", (Cw, Ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = Cw // 2
    base = Ch - int(h * 0.10) * S           # cloak hem baseline (planted)
    hh = h * S
    col = INK + (255,)
    bob = math.sin(t * 2.2) * 0.015 * hh    # gentle breathing

    # inverted-pendulum shear: a point at height y above the base slides sideways
    # in proportion to how high it is, so the body leans/swings from the feet.
    def LX(y):
        return lean * (base - y)

    headr = 0.15 * hh
    neck_y = base - 0.66 * hh + bob
    head_y = base - 0.86 * hh + bob
    baseW = 0.34 * hh
    neckW = 0.13 * hh
    sway = math.sin(t * 3.0) * 0.02 * hh if pose == "walk" else 0.0

    if pose == "front":                 # facing the viewer (for direct address)
        nx = cx + LX(neck_y); hx = cx + LX(head_y)
        d.ellipse([cx - 0.13 * hh, base - 0.02 * hh, cx - 0.02 * hh, base + 0.06 * hh], fill=col)
        d.ellipse([cx + 0.02 * hh, base - 0.02 * hh, cx + 0.13 * hh, base + 0.06 * hh], fill=col)
        d.polygon([(nx - neckW, neck_y), (nx + neckW, neck_y),
                   (cx + baseW, base), (cx - baseW, base)], fill=col)
        d.ellipse([cx - baseW, base - 0.10 * hh, cx + baseW, base + 0.06 * hh], fill=col)
        d.polygon([(hx - 0.6 * headr, head_y - headr * 0.5), (hx, head_y - headr * 1.8),
                   (hx + 0.6 * headr, head_y - headr * 0.5)], fill=col)     # hood tip up
        d.ellipse([hx - headr, head_y - headr, hx + headr, head_y + headr], fill=col)
        hand_y = neck_y + 0.30 * hh                            # orb in both hands, front
        hxx = cx + LX(hand_y)
        d.line([(nx - neckW, neck_y + 0.06 * hh), (hxx - 0.05 * hh, hand_y)], fill=col, width=int(0.09 * hh))
        d.line([(nx + neckW, neck_y + 0.06 * hh), (hxx + 0.05 * hh, hand_y)], fill=col, width=int(0.09 * hh))
        ey = head_y - headr * 0.05; er = headr * 0.17                       # two warm eye-glints
        for s_ in (-1, 1):
            exx = hx + s_ * headr * 0.42
            d.ellipse([exx - er, ey - er, exx + er, ey + er], fill=(255, 216, 150, 255))
        im = im.resize((Cw // S, Ch // S), Image.LANCZOS)
        return im, base / S, LX(hand_y) / S, (hand_y - base) / S - 4

    nx = cx + LX(neck_y); hx = cx + LX(head_y)
    # cloak: flared body with a rounded hem (neck leans, hem stays planted)
    d.polygon([(nx - neckW, neck_y), (nx + neckW, neck_y),
               (cx + baseW + sway, base), (cx - baseW - sway, base)], fill=col)
    d.ellipse([cx - baseW - sway, base - 0.10 * hh, cx + baseW + sway, base + 0.06 * hh], fill=col)
    # little walk feet peeking under the hem (planted, no lean)
    if pose == "walk":
        a = math.sin(t * 6) * 0.06 * hh
        d.ellipse([cx - 0.12 * hh + a, base - 0.02 * hh, cx - 0.02 * hh + a, base + 0.06 * hh], fill=col)
        d.ellipse([cx + 0.02 * hh - a, base - 0.02 * hh, cx + 0.12 * hh - a, base + 0.06 * hh], fill=col)

    # hood + head (a soft point at the back of the hood), swinging with the lean
    d.polygon([(hx - headr * 0.9, head_y + headr * 0.2),
               (hx - face * 0.10 * hh, head_y - headr * 1.5),
               (hx + headr * 0.9, head_y + headr * 0.2)], fill=col)   # hood tip
    d.ellipse([hx - headr, head_y - headr, hx + headr, head_y + headr], fill=col)

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
    hand_x += LX(hand_y)          # the hand (and its light) swing out with the lean
    d.line([(nx + face * neckW, neck_y + 0.06 * hh), (hand_x, hand_y)], fill=col, width=int(0.09 * hh))
    d.ellipse([hand_x - 0.05 * hh, hand_y - 0.05 * hh, hand_x + 0.05 * hh, hand_y + 0.05 * hh], fill=col)

    im = im.resize((Cw // S, Ch // S), Image.LANCZOS)
    # foot point and orb offset in downscaled coords, relative to feet (cx, base)
    fy = base / S
    orb_dx = (hand_x - cx) / S + face * 6
    orb_dy = (hand_y - base) / S - 6
    return im, fy, orb_dx, orb_dy


if __name__ == "__main__":
    W, H = 600, 800
    for i, (pose, ln) in enumerate([("stand", 0.10), ("walk", -0.08), ("lift", 0.12), ("sit", 0.0)]):
        bg = Image.new("RGB", (W, H), (26, 30, 54))
        d = ImageDraw.Draw(bg)
        d.line([(0, int(H * 0.8)), (W, int(H * 0.8))], fill=(12, 14, 24), width=3)
        spr, fy, odx, ody = character(280, pose, t=0.3, face=1, lean=ln)
        sw, sh = spr.size
        cx, gy = W // 2, int(H * 0.8)
        ox, oy = cx + odx, gy + ody
        for r, a in ((70, 60), (34, 120), (16, 255)):
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse([ox - r, oy - r, ox + r, oy + r],
                                       fill=(255, 200, 120, a))
            bg = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
        bg.paste(spr, (int(cx - sw / 2), int(gy - fy)), spr)
        bg.save(f"char_{pose}.png")
    print("saved char_*.png")
