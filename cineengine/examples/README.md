# CineEngine examples

Two kinds of generators live here.

## 1. Procedural / compositing (no GPU, no API, free)

Render motion, light and effects on CPU using the engine's real Camera and
effect math. Great for cinematic looks, but they do **not** invent new content.

| Script | What it makes |
|---|---|
| `../generator.py` | Prompt- or image-driven video (`python -m cineengine.generator -p "cosmic nebula"` / `-i photo.png`) |
| `generate_nature_hq.py` | High-quality golden-hour mountain-lake scene |
| `poster_anim.py` | Animate a text poster — graphic side flows, text stays calm (`--flow lr|diag|up`) |
| `face_dissolve.py` | Scanner beam + flowing data grid + data-sparks on the face poster |

Setup: `pip install numpy Pillow imageio imageio-ffmpeg`

## 2. Real AI image-to-video (cloud GPU, needs an API key, ~cents/clip)

These call a real video model that generates **genuinely new motion** from an
image. The GPU runs in the cloud, so a weak local GPU is fine.

| Script | Service | Run |
|---|---|---|
| `ai_generate.py` | fal.ai | `export FAL_KEY=...` then `python ai_generate.py -i img.jpg -p "..." -m kling` |
| `ai_generate_replicate.py` | Replicate | `export REPLICATE_API_TOKEN=...` then `python ai_generate_replicate.py -i img.jpg -p "..."` |
| `webui.py` | fal.ai (browser UI) | `export FAL_KEY=...` then `python webui.py` → open http://127.0.0.1:5000 |

Setup: `pip install fal-client replicate flask requests`

Models: `kling` (best motion), `wan` (cheapest), `svd`, `ltx`. Endpoint ids on
fal.ai/Replicate change over time — if one 404s, grab the current id from the
provider's model list and pass it to `--model`.
