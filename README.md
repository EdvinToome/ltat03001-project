# WooCommerce Bulk Uploader

Turn PNG or ZIP “worksheets” into watermarked banners + PDFs, generate
English product metadata via GPT-4o, and upload them as downloadable
digital products to WooCommerce in three simple steps.

---

## Prerequisites

- Python 3.8 or above  
- Git (optional, to clone)  
- A WooCommerce‐enabled WordPress site  
- OpenAI API access (GPT-4o with vision)  

---

## Setup

1. **Clone or copy** this repo  
2. **Create these directories** at project root:  
assets/ ── put your PNG templates/watermarks here input/ ── drop your source PNGs & ZIPs here output/ ── pipelines write into here

markdown
Copy
Edit
3. **Populate `assets/`** with:
- `dark.png`
- `bright.png`
- `dark-wide.png`
- `bright-wide.png`
- `banner_template.png`
- `watermark.png`
4. **Create a `.env`** file (no quotes) with:
```dotenv
SITE_URL=https://your-site.com
WC_CONSUMER_KEY=ck_xxx…
WC_CONSUMER_SECRET=cs_xxx…
WP_USER=your-wp-username
WP_APP_PASS=abcd efgh ijkl mnop qrst
OPENAI_API_KEY=sk-xxx…
Install dependencies:


pip install -r requirements.txt
Usage
Run the three scripts in order:

Create banners & PDFs


python banner_pdf.py
Interactive prompts for watermark mode.

Outputs per‐folder: Banner.jpg (or 1_banner.jpg…) and Worksheet.pdf.

Generate AI metadata


python make_prompt.py output/ [--context "extra hint"]
Produces description.json in each product folder.

Upload to WooCommerce


python upload_wc.py output/
Uploads PDFs and images, then creates WooCommerce draft products.

File reference
banner_pdf.py
Reads input/, writes watermarked banners + Worksheet.pdf to output/.

make_prompt.py
Calls GPT-4o vision on banners, saves description.json with title, tags, etc.

upload_wc.py
Uploads media & metadata to your WooCommerce store via REST API.

