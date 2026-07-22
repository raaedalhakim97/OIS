"""
High-quality 5s cinematic NATURE video (mountain lake at golden hour).

Driven by the repo's REAL camera (cineengine.camera.Camera / CameraMotion /
CameraShake) for the push-in + parallax, and the engine's own effect math
(ACES colorgrade, bloom, vignette, film grain, chromatic aberration) ported
from its GLSL shaders. Scene is painted + animated procedurally (the AI image
module needs a GPU that isn't available here).

Rendered with supersampling (SS x) for anti-aliasing, then downscaled.
Run with `--preview` to dump a single mid frame as PNG (fast).
"""
import os, sys, argparse
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from cineengine.config import Config
from cineengine.camera.camera import Camera
import imageio.v2 as imageio
import imageio_ffmpeg  # noqa

config = Config(fps=30, resolution=(1080, 1920))
W, H = config.RESOLUTION
FPS = config.FPS
DURATION = 5.0
SS = 1.5                                   # supersample factor
RW, RH = int(W * SS), int(H * SS)          # render (super) resolution
MARGIN = 1.30                              # oversize canvas for camera crop
CW, CH = int(RW * MARGIN), int(RH * MARGIN)
OUT = os.path.join(os.path.dirname(__file__), "nature_hq.mp4")

# ---- real engine camera: slow push + tiny handheld drift ----
camera = Camera(config)
camera.cinematic_push(duration=DURATION, start_zoom=1.0, end_zoom=1.18)
camera.add_shake(intensity=0.0025, frequency=1.2, seed=11)

rng = np.random.default_rng(2024)
HORIZON = 0.60          # fraction of canvas height where water begins


# ---------------- procedural helpers ----------------
def fbm(w, h, octaves=5, seed=0, aspect=1.0):
    """Fractional Brownian noise in [0,1] via summed, smoothed random octaves."""
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    base = 4
    for o in range(octaves):
        gw = max(2, int(base * (2 ** o) * aspect))
        gh = max(2, int(base * (2 ** o)))
        grid = r.random((gh, gw)).astype(np.float32)
        layer = np.asarray(Image.fromarray((grid * 255).astype(np.uint8))
                           .resize((w, h), Image.BICUBIC), np.float32) / 255.0
        out += layer * amp
        tot += amp
        amp *= 0.5
    return out / tot


def vgrad(h, top, bot):
    """Vertical color gradient (h,3)."""
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    return np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t


# ---------------- static sky + sun ----------------
def build_sky():
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    nx, ny = xx / CW, yy / CH
    # golden-hour vertical gradient (indigo top -> warm horizon)
    g = vgrad(CH, [38, 44, 92], [255, 176, 96])           # (CH,3)
    sky = np.repeat(g[:, None, :], CW, axis=1)
    # sun disk + bloomy glow, just above horizon
    sx, sy = 0.52, HORIZON - 0.11
    ar = CW / CH
    d = np.sqrt(((nx - sx) * ar) ** 2 + (ny - sy) ** 2)
    glow = np.clip(1.0 - d * 2.2, 0, 1) ** 2.2
    disk = np.clip(1.0 - d * 26.0, 0, 1) ** 0.6
    sky += glow[..., None] * np.array([120, 70, 20], np.float32)
    sky += disk[..., None] * np.array([255, 240, 200], np.float32)
    return np.clip(sky, 0, 255), (sx, sy)


SKY, (SUNX, SUNY) = build_sky()

# drifting clouds: a wide fbm field we scroll horizontally
CLOUD = fbm(int(CW * 1.6), int(CH * 0.6), octaves=5, seed=7, aspect=2.2)
CLOUD = np.clip((CLOUD - 0.5) * 2.2, 0, 1) ** 1.6   # wispy


def mountain_layer(base_y, amp, freq, color, seed, haze):
    """Return (rgb over canvas, alpha mask) for one ridge."""
    xs = np.linspace(0, 1, CW, dtype=np.float32)
    r = np.random.default_rng(seed)
    ridge = base_y \
        - amp * np.sin(xs * freq * 6.28318 + r.uniform(0, 6.28)) \
        - amp * 0.45 * np.sin(xs * freq * 2.3 * 6.28318 + r.uniform(0, 6.28)) \
        - amp * 0.06 * fbm(CW, 1, octaves=4, seed=seed + 1)[0]
    ridge = np.maximum(ridge, base_y - amp * 1.4)   # keep a continuous range
    yy = (np.arange(CH, dtype=np.float32) / CH)[:, None]
    mask = (yy > ridge[None, :]).astype(np.float32)
    # vertical shading within the mountain + atmospheric haze toward ridge
    shade = np.clip((yy - ridge[None, :]) * 3.0, 0, 1)
    col = np.array(color, np.float32)
    haze_col = np.array([150, 150, 175], np.float32)
    body = col[None, None, :] * (0.55 + 0.45 * shade[..., None])
    body = body * (1 - haze) + haze_col[None, None, :] * haze
    return body, mask


# distant -> near mountains (continuous ridges, near one taller)
MTN = [
    (*mountain_layer(HORIZON - 0.045, 0.035, 2.4, [96, 104, 140], 21, 0.62), 0.25),
    (*mountain_layer(HORIZON - 0.020, 0.055, 1.8, [58, 78, 98], 22, 0.38), 0.45),
    (*mountain_layer(HORIZON - 0.002, 0.075, 1.3, [30, 50, 58], 23, 0.16), 0.70),
]

# fireflies
NP = 28
fx = rng.uniform(0.05, 0.95, NP)
fy = rng.uniform(0.32, 0.95, NP)
fphase = rng.uniform(0, 6.28, NP)
fspeed = rng.uniform(0.15, 0.5, NP)
fsize = rng.uniform(2.0, 4.5, NP) * SS
fbright = rng.uniform(0.4, 0.85, NP)

# static coord grids at super res for effects
_yy, _xx = np.mgrid[0:RH, 0:RW].astype(np.float32)
_tcx, _tcy = _xx / RW, _yy / RH


# ---------------- effect ports ----------------
def aces(a):
    x = a / 255.0
    o = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
    return np.clip(o, 0, 1) * 255.0


def bloom(img):
    b = Image.fromarray(img.astype(np.uint8)).filter(ImageFilter.GaussianBlur(9 * SS))
    ba = np.asarray(b, np.float32)
    bright = np.clip(ba - 165, 0, 255) * 1.5
    return np.clip(img + bright, 0, 255)


def vignette(a, strength=0.55):
    ux = (_tcx - 0.5) * (RW / RH)
    uy = (_tcy - 0.5)
    dist = np.sqrt(ux ** 2 + uy ** 2) * (1.0 + strength)
    tt = np.clip((dist - 0.85) / (0.35 - 0.85), 0, 1)
    return a * (tt * tt * (3 - 2 * tt))[..., None]


def grain(a, t):
    n = np.sin((_tcx * RW + t) * 12.9898 + (_tcy * RH + t) * 78.233) * 43758.5453
    n = (n - np.floor(n)) * 2 - 1
    return a + n[..., None] * 0.045 * 255.0


def chromatic(a, amount=1.6):
    a = a.astype(np.float32)
    dx = ((_tcx - 0.5)) * amount * SS
    dy = ((_tcy - 0.5)) * amount * SS
    xr = np.clip(_xx + dx, 0, RW - 1).astype(np.int32)
    yr = np.clip(_yy + dy, 0, RH - 1).astype(np.int32)
    xb = np.clip(_xx - dx, 0, RW - 1).astype(np.int32)
    yb = np.clip(_yy - dy, 0, RH - 1).astype(np.int32)
    out = a.copy()
    out[..., 0] = a[yr, xr, 0]
    out[..., 2] = a[yb, xb, 2]
    return out


# ---------------- per-frame scene ----------------
def compose_canvas(t):
    """Build the full oversized scene at canvas res for time t (RGB float)."""
    canvas = SKY.copy()

    # drifting clouds over the sky band
    cw, ch = CLOUD.shape[1], CLOUD.shape[0]
    off = int((t / DURATION) * (cw - CW) * 0.6)
    band = CLOUD[:, off:off + CW]
    if band.shape[1] < CW:
        band = np.pad(band, ((0, 0), (0, CW - band.shape[1])), mode="edge")
    cloud_alpha = np.zeros((CH, CW), np.float32)
    cloud_alpha[:ch, :] = band * 0.8
    fade = np.clip(1 - (np.arange(CH)[:, None] / CH) / HORIZON, 0, 1) ** 1.5
    cloud_alpha *= fade
    canvas = canvas * (1 - cloud_alpha[..., None]) + np.array([255, 238, 214]) * cloud_alpha[..., None]

    # mountains (far -> near)
    for body, mask, _depth in MTN:
        m = mask[..., None]
        canvas = canvas * (1 - m) + body * m

    # ---- water: reflect everything above the horizon ----
    wl = int(HORIZON * CH)
    top = canvas[:wl]
    refl = top[::-1]                                   # mirror
    if refl.shape[0] < CH - wl:
        refl = np.pad(refl, ((0, CH - wl - refl.shape[0]), (0, 0), (0, 0)), mode="edge")
    else:
        refl = refl[:CH - wl]
    # gentle horizontal wobble (smooth, per-row) + shimmer, deepen with distance
    rows = np.arange(refl.shape[0])
    shift = (np.sin(rows / 34.0 + t * 2.2) * 3.0 * SS
             + np.sin(rows / 13.0 - t * 1.4) * 1.2 * SS).astype(np.int32)
    idx = (np.arange(refl.shape[1])[None, :] - shift[:, None]) % refl.shape[1]
    refl = np.take_along_axis(refl, idx[..., None].repeat(3, axis=2), axis=1)
    depth = (rows / refl.shape[0])[:, None, None]
    water_tint = np.array([34, 60, 96], np.float32)
    refl = refl * (0.55 - 0.30 * depth) + water_tint * (0.30 + 0.30 * depth)  # dimmer water
    # soften reflection so it reads as water, not a mirror
    refl = np.asarray(Image.fromarray(np.clip(refl, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(1.4 * SS)), np.float32)
    shimmer = fbm(refl.shape[1], refl.shape[0], octaves=4, seed=int(t * 30) % 97, aspect=1.0)
    refl += (np.clip(shimmer - 0.80, 0, 1) * 200)[..., None] * np.array([1.0, 0.95, 0.8])
    canvas[wl:] = np.clip(refl, 0, 255)

    # sun glitter column on the water (soft, low-frequency)
    sun_col = int(SUNX * CW)
    gy = np.arange(CH - wl)
    glit = np.exp(-((np.arange(CW)[None, :] - sun_col) ** 2) / (2 * (40 * SS) ** 2))
    glit = glit * (0.78 + 0.22 * np.sin(gy[:, None] / 26.0 + t * 2.2)) * \
        (1 - gy[:, None] / (CH - wl)) ** 1.6
    canvas[wl:] += glit[..., None] * np.array([255, 205, 140]) * 0.5

    return np.clip(canvas, 0, 255)


def add_fireflies(img, t):
    """Screen-space warm fireflies, added AFTER color grade (stay warm)."""
    h, w = img.shape[:2]
    for i in range(NP):
        px = (fx[i] + 0.03 * np.sin(t * fspeed[i] * 2 + fphase[i])) % 1.0
        py = (fy[i] - (t * fspeed[i] * 0.04) + 0.012 * np.cos(t * 2 + fphase[i]))
        py = 0.30 + (py - 0.30) % 0.70          # drift within lower 70%
        cxp, cyp = int(px * w), int(py * h)
        r = int(fsize[i] * 3)
        x0, x1 = max(0, cxp - r), min(w, cxp + r)
        y0, y1 = max(0, cyp - r), min(h, cyp + r)
        if x1 <= x0 or y1 <= y0:
            continue
        yg, xg = np.mgrid[y0:y1, x0:x1]
        d2 = (xg - cxp) ** 2 + (yg - cyp) ** 2
        flick = 0.55 + 0.45 * np.sin(t * 6 + fphase[i] * 3)
        glow = np.exp(-d2 / (2 * fsize[i] ** 2)) * fbright[i] * flick
        img[y0:y1, x0:x1] += glow[..., None] * np.array([255, 214, 140]) * 0.95
    return np.clip(img, 0, 255)


def render_frame(t):
    (cam_x, cam_y), zoom = camera.get_state(t)
    canvas = compose_canvas(t)

    # camera crop with parallax already baked via single canvas; apply zoom+pan
    cw, ch = int(RW / zoom), int(RH / zoom)
    ox = int(cam_x * RW * 2.0)
    oy = int(cam_y * RH * 2.0 - (zoom - 1.0) * RH * 0.15)   # slight downward reveal
    left = int(np.clip((CW - cw) / 2 + ox, 0, CW - cw))
    top = int(np.clip((CH - ch) / 2 + oy, 0, CH - ch))
    crop = canvas[top:top + ch, left:left + cw]
    frame = np.asarray(Image.fromarray(crop.astype(np.uint8)).resize((RW, RH), Image.LANCZOS),
                       np.float32)

    # effect stack (engine formulas): grade + lens distortion on the scene,
    # then add warm fireflies, then bloom picks up their glow, then grain/vignette.
    frame = aces(frame)
    frame = chromatic(frame, 1.0)
    frame = add_fireflies(frame, t)
    frame = bloom(frame)
    frame = grain(frame, t * FPS)
    frame = vignette(frame, 0.5)
    frame = np.clip(frame, 0, 255).astype(np.uint8)

    # downscale supersample -> final (anti-alias)
    return np.asarray(Image.fromarray(frame).resize((W, H), Image.LANCZOS), np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, default=None, help="dump one frame at time T")
    args = ap.parse_args()
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

    if args.preview is not None:
        Image.fromarray(render_frame(args.preview)).save(
            os.path.join(os.path.dirname(__file__), "hq_preview.png"))
        print("preview saved")
        return

    n = int(DURATION * FPS)
    writer = imageio.get_writer(OUT, fps=FPS, codec="libx264",
                                output_params=["-crf", "17", "-preset", "slow",
                                               "-pix_fmt", "yuv420p",
                                               "-movflags", "+faststart"],
                                macro_block_size=8, ffmpeg_log_level="error")
    print(f"Rendering {n} frames @ {W}x{H} (super {RW}x{RH}, {FPS}fps)...")
    for i in range(n):
        writer.append_data(render_frame(i / FPS))
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{n}")
    writer.close()
    print(f"Done -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
