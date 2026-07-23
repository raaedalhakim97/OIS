"""
Weighted movement logic for THE OBSERVER WORLD. Motion should have mass: things
accelerate, overshoot, settle, drag, and lag — never linear lerps.

- Spring: a critically-ish damped spring; step a value toward a target with weight.
- easing: anticipation / follow-through curves.
- walk_dip / step_phase: body dips on each footfall; steps advance with DISTANCE,
  not clock, so a stop actually stops the feet.
- a lagging light (secondary motion) is just a Spring chasing the hand.
"""
import math


class Spring:
    """Mass-spring-damper. Higher k = snappier; zeta<1 overshoots (weighty)."""
    def __init__(self, x=0.0, k=120.0, zeta=0.68):
        self.x = float(x); self.v = 0.0; self.k = float(k); self.zeta = float(zeta)

    def step(self, target, dt):
        w = math.sqrt(self.k); c = 2 * self.zeta * w
        acc = self.k * (target - self.x) - c * self.v
        self.v += acc * dt
        self.x += self.v * dt
        return self.x


class Spring2:
    def __init__(self, x=0.0, y=0.0, k=120.0, zeta=0.68):
        self.sx = Spring(x, k, zeta); self.sy = Spring(y, k, zeta)
    def step(self, tx, ty, dt):
        return self.sx.step(tx, dt), self.sy.step(ty, dt)


def clamp(x, lo, hi): return max(lo, min(hi, x))
def ease_out_back(x, s=1.70):
    x = clamp(x, 0, 1); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def ease_in_out(x):
    x = clamp(x, 0, 1); return x * x * (3 - 2 * x)


class Walker:
    """Drives one character's weighted locomotion. Feed it a target x each frame;
    it returns everything needed to draw a believable step: position, whether it's
    walking, a body dip synced to footfalls, a lean into acceleration, a cloth
    trail, and a lagging light position."""
    def __init__(self, x, feet_y, k=70.0, zeta=0.72):
        self.pos = Spring(x, k, zeta)
        self.px = x; self.feet = feet_y
        self.stepph = 0.0
        self.light = Spring2(x, feet_y)          # the lantern lags behind the hand

    def update(self, target_x, dt, W, H, hand_dx=0.0, hand_dy=0.0):
        x = self.pos.step(target_x, dt)
        vx = (x - self.px) / max(dt, 1e-4); self.px = x
        speed = abs(vx)
        walking = speed > 0.006
        # steps advance with distance travelled, so stopping stops the feet
        self.stepph += speed * 34.0 * dt / max(dt, 1e-4) * dt
        self.stepph += speed * 40.0
        dip = -abs(math.sin(self.stepph * math.pi)) * 0.02 * H if walking else \
              math.sin(self.stepph) * 0  # rests flat when idle
        lean = clamp(vx * 6.0, -0.16, 0.16)          # lean into acceleration / brake-back
        trail = clamp(-vx * 2.2, -0.10, 0.10)        # cloak drags opposite to motion
        # lagging lantern: chase the hand's world point with a softer spring
        hx = x * W + hand_dx; hy = self.feet * H + dip + hand_dy
        lx, ly = self.light.step(hx, hy, dt)
        return dict(x=x, vx=vx, walking=walking, stepph=self.stepph, dip=dip,
                    lean=lean, trail=trail, light=(lx, ly))
