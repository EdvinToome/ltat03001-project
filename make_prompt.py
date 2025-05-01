#!/usr/bin/env python
"""
make_prompt.py  –  builds the AI prompt, calls OpenAI Vision,
and stores description.json next to each banner.

Usage:  python make_prompt.py  output/  [--context "extra text for GPT"]
"""

import os
import base64
import json
import argparse
from pathlib import Path
from openai import OpenAI
from woocommerce import API

# ─── Manual .env loader ───────────────────────────────────────────────────────
def load_env(env_file: str = ".env"):
    if not os.path.exists(env_file):
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ[key] = val

load_env()
# ──────────────────────────────────────────────────────────────────────────────

# --- CLI args ---
parser = argparse.ArgumentParser()
parser.add_argument("out_dir", help="Path to the 'output' folder from banner_pdf")
parser.add_argument("--context", help="Extra context appended to GPT prompt")
args = parser.parse_args()
OUT = Path(args.out_dir)

# --- OpenAI client ---
if "OPENAI_API_KEY" not in os.environ:
    raise SystemExit("ERROR: OPENAI_API_KEY not set in environment or .env")
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# --- Fetch valid slugs to list in the prompt ---
wc = API(
    url=os.environ.get("SITE_URL", "").rstrip("/"),
    consumer_key=os.environ.get("WC_CONSUMER_KEY", ""),
    consumer_secret=os.environ.get("WC_CONSUMER_SECRET", ""),
    version="wc/v3"
)
categories = wc.get("products/categories", params={'per_page':100}).json()
tags_list   = wc.get("products/tags",       params={'per_page':100}).json()
cat_slugs = ",".join(c["slug"] for c in categories if c.get("slug"))
tag_slugs = ",".join(t["slug"] for t in tags_list if t.get("slug"))

BASE_PROMPT = f"""
Generate WooCommerce product metadata in English.

Return **exactly** one JSON object with keys:
"title", "short_description", "description", "category", "tags".

Title: [Material Type] – [Topic]: [Hook]  (no emoji)
Description: 2–3 sentences in <p> tags, include emojis
Short description: concise, ≤2 emojis
Use one category & up to 3 tags.

Valid categories: {cat_slugs}
Valid tags: {tag_slugs}
""".strip()

if args.context:
    BASE_PROMPT += f"\n\nAdditional context: {args.context}"

def encode_b64(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode()

# ─── Main ─────────────────────────────────────────────────────────────────────
for folder in OUT.iterdir():
    if not folder.is_dir():
        continue

    # pick the banner (Banner.jpg or 1_banner.jpg…)
    banner = folder / "Banner.jpg"
    if not banner.exists():
        candidates = sorted(folder.glob("*_banner.jpg"))
        if not candidates:
            print(f"⚠️  no banner found in '{folder.name}', skipping")
            continue
        banner = candidates[0]

    print(f"→ prompting for {folder.name}")
    content = [
        {"type":"text", "text": BASE_PROMPT},
        {"type":"image_url", "image_url":{
            "url": f"data:image/jpeg;base64,{encode_b64(banner)}",
            "detail": "high"
        }}
    ]

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"user", "content":content}],
        response_format={"type":"json_object"}
    )

    # write out description.json
    out_file = folder / "description.json"
    out_file.write_text(resp.choices[0].message.content, encoding="utf-8")
    print(f"  Saved {out_file.name}")

print("✅  description.json files created.")
