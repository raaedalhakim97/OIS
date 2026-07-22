import numpy as np
from PIL import Image

SRC = "/root/.claude/uploads/1cf96a14-5973-546d-bc36-49c9faf0f7a5/7ba14e6e-IMG_2537.png"
img = Image.open(SRC).convert("RGB")
print("orig size", img.size)
W0, H0 = img.size

# crop out phone UI: keep the artwork band (below search bar, above captions)
# original is 1179x2556
x0, x1 = 150, 1094
y0, y1 = 305, 1990
crop = img.crop((x0, y0, x1, y1))
a = np.asarray(crop).astype(np.float32)
h, w = a.shape[:2]
print("crop size", crop.size, "aspect", w / h, "target", 1080/1920)

# feathered mask to remove residual UI islands without leaving hard edges
from PIL import ImageFilter
mask = np.ones((h, w), np.float32)
# observer logo circle (right-middle) -> extend to right edge
mask[int(h*0.49):int(h*0.585), int(w*0.90):] = 0
# right-side icon column: heart / comment / bookmark / "A" -> down to bottom edge
mask[int(h*0.585):, int(w*0.93):] = 0
# left-side avatar bubbles near bottom-left
mask[int(h*0.66):, :int(w*0.05)] = 0
mask = np.asarray(Image.fromarray((mask*255).astype(np.uint8)).filter(
    ImageFilter.GaussianBlur(18)), np.float32) / 255.0
a = a * mask[..., None]

out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((1080, 1920), Image.LANCZOS)
out.save("/tmp/claude-0/-home-user/1cf96a14-5973-546d-bc36-49c9faf0f7a5/scratchpad/ois-fresh2/base_clean.png")
print("saved base_clean.png")
