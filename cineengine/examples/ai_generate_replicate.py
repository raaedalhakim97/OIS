#!/usr/bin/env python3
"""
Real AI image-to-video via Replicate (cloud GPU) — fallback to the fal.ai script.

SETUP (once):
    pip install replicate
    # get a token at https://replicate.com/account/api-tokens  then:
    export REPLICATE_API_TOKEN="r8_your_token"   # Windows: set REPLICATE_API_TOKEN=...

RUN:
    python ai_generate_replicate.py -i face.jpg \
        -p "the man turns his head slightly, data drifts, cinematic" -m kling -o out.mp4

Cost is billed per second of GPU by Replicate to your token.

NOTE: model ids/versions on Replicate change. If one 404s, open
https://replicate.com/collections/image-to-video, copy the current
"owner/model" slug, and pass it with --model <owner/model>.
"""
import os
import sys
import argparse

# friendly name -> replicate model slug  (verify at replicate.com/collections/image-to-video)
MODELS = {
    "kling": "kwaivgi/kling-v1.6-standard",
    "wan":   "wavespeedai/wan-2.1-i2v-480p",
    "svd":   "stability-ai/stable-video-diffusion",
    "ltx":   "lightricks/ltx-video",
}


def _write_output(output, out):
    """Replicate output may be a URL str, a list, or a FileOutput object."""
    import requests
    if isinstance(output, (list, tuple)):
        output = output[0]
    # newer client returns FileOutput with .read()/.url
    if hasattr(output, "read"):
        data = output.read()
        with open(out, "wb") as f:
            f.write(data)
        return len(data)
    url = getattr(output, "url", None) or (output if isinstance(output, str) else None)
    if not url:
        sys.exit(f"Unexpected output type: {type(output)} -> {output}")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    with open(out, "wb") as f:
        f.write(r.content)
    return len(r.content)


def main():
    ap = argparse.ArgumentParser(description="AI image-to-video via Replicate")
    ap.add_argument("--image", "-i", required=True)
    ap.add_argument("--prompt", "-p", default="cinematic subtle motion, high quality")
    ap.add_argument("--model", "-m", default="kling",
                    help="kling | wan | svd | ltx | or a replicate owner/model slug")
    ap.add_argument("--out", "-o", default="ai_result.mp4")
    a = ap.parse_args()

    if not os.getenv("REPLICATE_API_TOKEN"):
        sys.exit("ERROR: set REPLICATE_API_TOKEN (https://replicate.com/account/api-tokens)")
    if not os.path.isfile(a.image):
        sys.exit(f"ERROR: image not found: {a.image}")
    try:
        import replicate
    except ImportError:
        sys.exit("ERROR: pip install replicate")

    model = MODELS.get(a.model, a.model)
    print(f"[1/2] generating with {model} on Replicate ... (cloud GPU)")
    with open(a.image, "rb") as img:
        output = replicate.run(model, input={
            "image": img,
            "prompt": a.prompt,
        })
    print(f"[2/2] downloading -> {a.out}")
    n = _write_output(output, a.out)
    print(f"Done -> {a.out} ({n/1024:.0f} KB)")


if __name__ == "__main__":
    main()
