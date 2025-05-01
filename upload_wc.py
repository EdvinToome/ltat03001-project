#!/usr/bin/env python
# upload_wc.py ────────────────────────────────────────────────────────────────
"""
Usage:
    python upload_wc.py  output/
"""
import json, os, time, requests, argparse
from pathlib import Path
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from woocommerce import API

load_dotenv()
p = argparse.ArgumentParser()
p.add_argument("out_dir", help="Path to 'output'")
args = p.parse_args()
OUT = Path(args.out_dir)

SITE      = os.environ["SITE_URL"].rstrip("/")
MEDIA_URL = f"{SITE}/wp-json/wp/v2/media"
auth      = HTTPBasicAuth(os.environ["WP_USER"], os.environ["WP_APP_PASS"])

wc = API(
    url=SITE,
    consumer_key=os.environ["WC_CONSUMER_KEY"],
    consumer_secret=os.environ["WC_CONSUMER_SECRET"],
    version="wc/v3"
)
cat_map = {c["slug"]:c["id"] for c in wc.get("products/categories",params={'per_page':100}).json()}
tag_map = {t["slug"]:t["id"] for t in wc.get("products/tags",params={'per_page':100}).json()}

def upload(file, mime):
    for _ in range(3):
        r = requests.post(
            MEDIA_URL,
            headers={
                "Content-Disposition":f"attachment; filename={file.name}",
                "Content-Type":mime,
                "Accept":"application/json"
            },
            data=file.read_bytes(),
            auth=auth, timeout=40
        )
        if r.status_code in (200,201):
            return r.json()
        time.sleep(2)
    print("❌ upload failed", file.name)
    return None

for folder in OUT.iterdir():
    if not folder.is_dir(): continue
    meta = folder / "description.json"
    pdf  = folder / "Worksheet.pdf"
    b    = folder / "Banner.jpg"
    if not b.exists():
        banners = sorted(folder.glob("*_banner.jpg"))
        if not banners:
            print("⚠️ skip", folder.name); continue
        b = banners[0]
    if not (meta.exists() and pdf.exists()):
        print("⚠️ skip", folder.name); continue

    data = json.loads(meta.read_text())
    print("→ uploading", data["title"])
    pdf_j    = upload(pdf, "application/pdf")
    banner_j = upload(b,   "image/jpeg")
    gal_j    = [upload(g, "image/jpeg") for g in sorted(folder.glob("*_banner.jpg"))[1:4]]

    if not (pdf_j and banner_j): continue

    payload = {
        "name": data["title"],
        "type": "simple",
        "regular_price": "4.99",
        "downloadable": True,
        "virtual": True,
        "short_description": data["short_description"],
        "description": data["description"],
        "downloads": [{"name":"Worksheet","file": pdf_j["source_url"]}],
        "images": [{"id": banner_j["id"]}] + [{"id":g["id"]} for g in gal_j if g]
    }
    cid = cat_map.get(data["category"])
    if cid: payload["categories"]=[{"id":cid}]
    tids = [tag_map.get(t) for t in data["tags"] if tag_map.get(t)]
    if tids: payload["tags"]=[{"id":i} for i in tids]

    resp = wc.post("products", payload)
    if resp.status_code in (200,201):
        print("✅ draft product", resp.json()["id"])
    else:
        print("❌ Woo error", resp.status_code, resp.text)
