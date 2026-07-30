#!/usr/bin/env python3
"""
keywords — free keyword research for THE OBSERVER WORLD. No API key, no subscription.

Ahrefs' keyword endpoints need a paid API plan. This gets comparable *intent* data for
nothing by harvesting public autocomplete: the suggestions are literally what people
typed, ranked by how often the engines think they're typed. That is closer to TikTok
search behaviour than web search volume is anyway.

Three sources, all key-free:
  google   — web search intent
  youtube  — video search intent  (the best free proxy for TikTok)
  tiktok   — TikTok's own suggestion endpoint, when it answers

A term suggested for several different seeds is a term with real gravity, so the score
is (number of seeds that surfaced it) first, then how high it ranked within each.

  python3 tools/keywords.py                        # the series' default seeds
  python3 tools/keywords.py --source youtube       # video intent only
  python3 tools/keywords.py --seeds "what is an octave" "power chord"
  python3 tools/keywords.py --depth 2              # also expand each suggestion

NOTE: must be run somewhere with open internet. The render container's egress policy
denies google.com and tiktok.com (403 on CONNECT), so run this on your own machine.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

SEEDS = [
    "music theory", "music theory for beginners", "how to read sheet music",
    "solfege", "do re mi", "what is an octave", "what is a chord",
    "what is a power chord", "what is a half step", "treble clef",
    "ear training", "what is a rest in music", "learn music theory",
    "major scale", "what is tempo in music",
]

ENDPOINTS = {
    "google":  "https://suggestqueries.google.com/complete/search?client=firefox&hl=en&q={q}",
    "youtube": "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=en&q={q}",
    "tiktok":  "https://www.tiktok.com/api/search/general/sug/?keyword={q}",
}


def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def suggest(source, seed):
    """Return the engine's suggestions for one seed, best-first. [] on any failure."""
    url = ENDPOINTS[source].format(q=urllib.parse.quote(seed))
    try:
        raw = fetch(url)
    except Exception as e:
        print(f"  ! {source}/{seed!r}: {e}", file=sys.stderr)
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if source == "tiktok":                       # {"sug_list":[{"content":...}]}
        return [s.get("content", "") for s in (data.get("sug_list") or []) if s.get("content")]
    return [s for s in (data[1] if len(data) > 1 else []) if isinstance(s, str)]


def harvest(sources, seeds, depth=1, pause=0.35):
    """seed -> suggestions, optionally expanding each suggestion one more level."""
    hits = defaultdict(lambda: {"seeds": set(), "best": 99, "sources": set()})
    queue = [(s, 1) for s in seeds]
    seen = set()
    while queue:
        seed, lvl = queue.pop(0)
        if seed.lower() in seen:
            continue
        seen.add(seed.lower())
        for src in sources:
            for rank, term in enumerate(suggest(src, seed)):
                t = term.strip().lower()
                if not t or t == seed.lower():
                    continue
                h = hits[t]
                h["seeds"].add(seed)
                h["sources"].add(src)
                h["best"] = min(h["best"], rank)
                if lvl < depth:
                    queue.append((t, lvl + 1))
            time.sleep(pause)                    # be a polite guest
    return hits


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="google,youtube",
                   help="comma list of: google, youtube, tiktok")
    p.add_argument("--seeds", nargs="*", default=None)
    p.add_argument("--depth", type=int, default=1)
    p.add_argument("--top", type=int, default=60)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    sources = [s.strip() for s in a.source.split(",") if s.strip() in ENDPOINTS]
    if not sources:
        sys.exit("no valid --source; pick from: " + ", ".join(ENDPOINTS))
    seeds = a.seeds or SEEDS

    print(f"harvesting {len(seeds)} seeds from {'+'.join(sources)} (depth {a.depth})…",
          file=sys.stderr)
    hits = harvest(sources, seeds, a.depth)
    if not hits:
        sys.exit("nothing came back — the network is probably blocking these hosts.")

    # gravity first (how many different seeds surfaced it), then how high it ranked
    ranked = sorted(hits.items(), key=lambda kv: (-len(kv[1]["seeds"]), kv[1]["best"]))[:a.top]

    if a.json:
        print(json.dumps([{"keyword": k, "seed_count": len(v["seeds"]),
                           "best_rank": v["best"], "sources": sorted(v["sources"])}
                          for k, v in ranked], indent=2))
        return

    print(f"\n{'keyword':<52} seeds  rank  sources")
    print("-" * 78)
    for k, v in ranked:
        print(f"{k[:52]:<52} {len(v['seeds']):>4}  {v['best']:>4}  {','.join(sorted(v['sources']))}")
    print("\nseeds = how many different searches surfaced it (higher = more gravity)")
    print("rank  = best position it held in a suggestion list (lower = stronger)")


if __name__ == "__main__":
    main()
