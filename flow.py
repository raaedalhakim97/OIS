"""
flow — organic motion helpers for THE OBSERVER WORLD.
Everything that moves should breathe: eased starts, curved flights, soft
overshoot landings, layered (two-frequency) hovering instead of metronome sine.
"""
import math


def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))


def ease_io(u):
    """Sine ease in-out — gentle start, gentle stop."""
    u = clamp(u); return 0.5 - 0.5 * math.cos(math.pi * u)


def ease_out(u):
    u = clamp(u); return math.sin(0.5 * math.pi * u)


def back_out(u, k=0.30):
    """Arrive with a tiny overshoot and settle (k = overshoot amount)."""
    u = clamp(u); v = u - 1.0
    return 1.0 + (k + 1.0) * v ** 3 + k * v ** 2


def bob(ts, amp=1.0, f1=0.83, f2=1.71, ph=0.0):
    """Layered two-frequency hover — organic, never metronomic."""
    return amp * (0.62 * math.sin(f1 * ts + ph) + 0.38 * math.sin(f2 * ts + ph * 1.7 + 1.1))


def bez(p0, pc, p1, u):
    a = (1 - u) ** 2; b = 2 * (1 - u) * u; c = u ** 2
    return (a * p0[0] + b * pc[0] + c * p1[0], a * p0[1] + b * pc[1] + c * p1[1])


def flight(p0, p1, u, rise=0.14, settle=0.0):
    """Curved flight from p0 to p1: an eased bezier arcing gently upward.
    settle > 0 lands with a soft overshoot (use for placements)."""
    uu = back_out(u, settle) if settle > 0 else ease_io(u)
    dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + 1e-6
    pc = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 - rise * dist)
    return bez(p0, pc, p1, uu)


def path(ts, segs, last):
    """Segmented motion: segs = [(t0, t1, p0, p1, style)]
    style: 'hold' stay at p0 · 'fly' curved eased flight · 'land' flight with settle."""
    for (t0, t1, p0, p1, st) in segs:
        if ts <= t1:
            if st == "hold" or p0 == p1 or t1 <= t0:
                return p0
            u = clamp((ts - t0) / (t1 - t0))
            if st == "land":
                return flight(p0, p1, u, rise=0.10, settle=0.32)
            return flight(p0, p1, u, rise=0.14)
    return last


def vlean(pos_fn, ts, dt=0.12, gain=0.0009, mx=0.09):
    """Lean from actual horizontal velocity — the body leans into its motion."""
    v = (pos_fn(ts) - pos_fn(ts - dt)) / dt
    return clamp(v * gain, -mx, mx)


def idle_sway(ts, a1=0.016, a2=0.010):
    """Slow living sway for a standing figure (two incommensurate frequencies)."""
    return a1 * math.sin(0.7 * ts) + a2 * math.sin(1.9 * ts + 0.8)
