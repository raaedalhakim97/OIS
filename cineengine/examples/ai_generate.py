#!/usr/bin/env python3
"""
Real AI image-to-video generator (cloud GPU via fal.ai).

Unlike the procedural examples in this repo, this calls a REAL video model
that generates genuinely new motion from your image. The GPU runs in the
cloud, so it works even on a laptop with a tiny GPU.

SETUP (once):
    pip install fal-client requests
    # get a key at https://fal.ai/dashboard/keys  then:
    export FAL_KEY="your-key-here"        # Windows: set FAL_KEY=your-key-here

RUN:
    python ai_generate.py --image face.jpg \
        --prompt "the man turns his head slightly, data particles drift, cinematic" \
        --model kling --out result.mp4

    python ai_generate.py -i photo.png -p "gentle parallax, glowing energy" -m wan

Cost is a few cents per clip (billed by fal.ai to your key).

NOTE: model endpoint ids on fal.ai change over time. If one 404s, open
https://fal.ai/models (filter: image-to-video), copy the current id, and pass
it directly with --model <full/endpoint/id>.
"""
import os
import sys
import argparse

# friendly name -> fal.ai endpoint id  (verify/update at https://fal.ai/models)
MODELS = {
    "kling": "fal-ai/kling-video/v1.6/standard/image-to-video",   # best motion
    "kling2": "fal-ai/kling-video/v2/master/image-to-video",      # newer, pricier
    "wan":   "fal-ai/wan-i2v",                                    # cheap, solid
    "svd":   "fal-ai/stable-video",                               # Stable Video Diffusion
    "ltx":   "fal-ai/ltx-video-13b-distilled/image-to-video",     # fast
}


def main():
    ap = argparse.ArgumentParser(description="AI image-to-video via fal.ai")
    ap.add_argument("--image", "-i", required=True, help="input image path")
    ap.add_argument("--prompt", "-p", default="cinematic subtle motion, high quality",
                    help="describe the motion you want")
    ap.add_argument("--model", "-m", default="kling",
                    help="kling | kling2 | wan | svd | ltx | or a full fal endpoint id")
    ap.add_argument("--out", "-o", default="ai_result.mp4")
    ap.add_argument("--duration", "-d", type=int, default=5, help="seconds (if the model supports it)")
    a = ap.parse_args()

    if not os.getenv("FAL_KEY"):
        sys.exit("ERROR: set your key first ->  export FAL_KEY=\"...\"  (get one at https://fal.ai/dashboard/keys)")
    if not os.path.isfile(a.image):
        sys.exit(f"ERROR: image not found: {a.image}")

    try:
        import fal_client
        import requests
    except ImportError:
        sys.exit("ERROR: pip install fal-client requests")

    endpoint = MODELS.get(a.model, a.model)   # allow passing a raw endpoint id
    print(f"[1/3] uploading {a.image} ...")
    image_url = fal_client.upload_file(a.image)

    print(f"[2/3] generating with {endpoint} ...  (this runs on a cloud GPU)")

    def on_update(update):
        for log in getattr(update, "logs", None) or []:
            print("   ", log.get("message", ""))

    args = {
        "prompt": a.prompt,
        "image_url": image_url,
        "duration": str(a.duration),   # some models expect "5"/"10"; ignored if unsupported
    }
    try:
        result = fal_client.subscribe(endpoint, arguments=args,
                                      with_logs=True, on_queue_update=on_update)
    except Exception as e:
        # retry once without the optional duration arg (models differ)
        print("   (retry without duration arg:", e, ")")
        args.pop("duration", None)
        result = fal_client.subscribe(endpoint, arguments=args, with_logs=True, on_queue_update=on_update)

    # result shape varies: {"video": {"url": ...}} or {"video_url": ...}
    video = result.get("video") or {}
    url = video.get("url") if isinstance(video, dict) else None
    url = url or result.get("video_url")
    if not url:
        sys.exit(f"No video url in response: {result}")

    print(f"[3/3] downloading -> {a.out}")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    with open(a.out, "wb") as f:
        f.write(r.content)
    print(f"Done -> {a.out} ({len(r.content)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
