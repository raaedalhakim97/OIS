#!/usr/bin/env python3
"""
Tiny web UI for the AI image-to-video generator (Grok-style: drop image + prompt).

Runs a local page in your browser; generation happens on fal.ai's cloud GPU.

SETUP (once):
    pip install flask fal-client requests
    export FAL_KEY="your-key-here"          # Windows: set FAL_KEY=your-key-here

RUN:
    python webui.py
    # then open http://127.0.0.1:5000 in your browser

Pick a model, upload an image, type the motion you want, click Generate.
"""
import os
import sys
import tempfile

try:
    from flask import Flask, request, send_file, Response
    import fal_client
    import requests
except ImportError:
    sys.exit("ERROR: pip install flask fal-client requests")

MODELS = {
    "kling": "fal-ai/kling-video/v1.6/standard/image-to-video",
    "kling2": "fal-ai/kling-video/v2/master/image-to-video",
    "wan":   "fal-ai/wan-i2v",
    "svd":   "fal-ai/stable-video",
    "ltx":   "fal-ai/ltx-video-13b-distilled/image-to-video",
}

app = Flask(__name__)

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>CineEngine · AI Video Generator</title>
<style>
 body{background:#0b0d12;color:#e7ecf3;font-family:system-ui,sans-serif;max-width:640px;margin:40px auto;padding:0 16px}
 h1{font-weight:800;letter-spacing:-.5px} label{display:block;margin:14px 0 6px;color:#9aa7b8;font-size:14px}
 input,select,textarea,button{width:100%;padding:12px;border-radius:10px;border:1px solid #263041;background:#141922;color:#e7ecf3;font-size:15px;box-sizing:border-box}
 button{background:#3a7afe;border:0;font-weight:700;margin-top:18px;cursor:pointer}
 button:disabled{opacity:.5} .note{color:#6b7688;font-size:13px;margin-top:8px}
 video{width:100%;border-radius:12px;margin-top:20px;background:#000}
</style></head><body>
<h1>AI Video Generator</h1>
<p class=note>Image → real motion, via fal.ai cloud GPU. A few cents per clip.</p>
<form id=f>
 <label>Model</label>
 <select name=model>
  <option value=kling>Kling 1.6 — best motion</option>
  <option value=wan>Wan 2.1 — cheapest</option>
  <option value=svd>Stable Video Diffusion</option>
  <option value=ltx>LTX — fast</option>
 </select>
 <label>Image</label><input type=file name=image accept=image/* required>
 <label>Prompt (describe the motion)</label>
 <textarea name=prompt rows=3>cinematic subtle motion, high quality</textarea>
 <button type=submit id=go>Generate</button>
</form>
<div id=out></div>
<script>
 const f=document.getElementById('f'),go=document.getElementById('go'),out=document.getElementById('out');
 f.onsubmit=async e=>{e.preventDefault();go.disabled=true;go.textContent='Generating… (30–90s)';out.innerHTML='';
  try{const r=await fetch('/generate',{method:'POST',body:new FormData(f)});
   if(!r.ok){out.textContent='Error: '+await r.text();}
   else{const b=await r.blob();const u=URL.createObjectURL(b);
    out.innerHTML='<video src="'+u+'" controls autoplay loop></video>'+
     '<p class=note><a style="color:#3a7afe" download="ai_result.mp4" href="'+u+'">Download</a></p>';}
  }catch(err){out.textContent='Error: '+err;}
  go.disabled=false;go.textContent='Generate';};
</script></body></html>"""


@app.get("/")
def index():
    return PAGE


@app.post("/generate")
def generate():
    if not os.getenv("FAL_KEY"):
        return Response("Set FAL_KEY before starting the server.", status=400)
    file = request.files.get("image")
    if not file:
        return Response("No image uploaded.", status=400)
    prompt = request.form.get("prompt", "cinematic subtle motion")
    endpoint = MODELS.get(request.form.get("model", "kling"), MODELS["kling"])

    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(file.filename)[1] or ".png", delete=False) as tmp:
        file.save(tmp.name)
        img_path = tmp.name
    try:
        image_url = fal_client.upload_file(img_path)
        result = fal_client.subscribe(endpoint, arguments={"prompt": prompt, "image_url": image_url}, with_logs=False)
        video = result.get("video") or {}
        url = (video.get("url") if isinstance(video, dict) else None) or result.get("video_url")
        if not url:
            return Response(f"No video in response: {result}", status=500)
        data = requests.get(url, timeout=300).content
        out_path = img_path + ".mp4"
        with open(out_path, "wb") as fh:
            fh.write(data)
        return send_file(out_path, mimetype="video/mp4")
    except Exception as e:
        return Response(f"{type(e).__name__}: {e}", status=500)
    finally:
        try:
            os.unlink(img_path)
        except OSError:
            pass


if __name__ == "__main__":
    if not os.getenv("FAL_KEY"):
        print("WARNING: FAL_KEY not set — generation will fail until you set it.")
    print("Open http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
