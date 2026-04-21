# Static Site Mirror — thetcj.org

Produces a fully static HTML replica of a WordPress site hosted on GitHub Pages with a custom domain. No dynamic functionality (forms, comments, tracking) is included.

**Live site:** https://cwm.millgrove.org.uk  
**Repo:** https://github.com/jeremycurtis25/thetcj-static  
**Source:** https://thetcj.org

---

## Prerequisites

```bash
sudo apt install wget curl python3 python3-pip
pip install beautifulsoup4
gh auth login
```

---

## Step 1 — Create the GitHub Pages repo

```bash
gh repo create thetcj-static --public --description "Static HTML replica of thetcj.org"
mkdir thetcj-static && cd thetcj-static
git init && git checkout -b main
git remote add origin git@github.com:YOURUSER/thetcj-static.git

# Placeholder commit so Pages can be enabled
echo '<html><body><h1>Coming soon</h1></body></html>' > index.html
git add index.html && git commit -m "Initial placeholder"
git push -u origin main

# Enable GitHub Pages
gh api repos/YOURUSER/thetcj-static/pages --method POST --input - <<'EOF'
{"source": {"branch": "main", "path": "/"}}
EOF
```

---

## Step 2 — Set up custom domain (optional)

**DNS (123-reg or similar):**  
Add a CNAME record: `subdomain` → `YOURUSER.github.io`  
No trailing dot in the control panel.

**GitHub:**  
```bash
gh api repos/YOURUSER/thetcj-static/pages --method PUT --input - <<'EOF'
{"cname": "subdomain.yourdomain.com"}
EOF
```

GitHub auto-provisions the HTTPS certificate once DNS propagates (~15 min).

---

## Step 3 — Mirror the site with wget

Run from the project root (e.g. `/home/user/Development/TCJ`):

```bash
wget \
  --recursive \
  --level=5 \
  --page-requisites \
  --html-extension \
  --convert-links \
  --restrict-file-names=windows \
  --no-parent \
  --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  --domains=thetcj.org \
  --reject="*wp-login*,*wp-admin*,*xmlrpc*" \
  -e robots=off \
  https://thetcj.org \
  2>&1 | tee wget_mirror.log
```

> **Note:** `--convert-links` does NOT reliably rewrite links — we fix this in Step 6. Do not rely on it.

---

## Step 4 — Verify coverage against sitemap

WordPress sitemaps are usually at `/sitemap_index.xml`. Extract all post/page URLs:

```bash
curl -s https://thetcj.org/post-sitemap.xml \
     https://thetcj.org/post-sitemap2.xml \
     https://thetcj.org/page-sitemap.xml \
  | grep -oP '(?<=<loc>)[^<]+' \
  | sed 's|https://thetcj.org||' \
  | sed 's|/$||' > /tmp/sitemap_urls.txt

# Cross-reference
found=0; missing=0
while IFS= read -r url; do
  path="thetcj.org${url}"
  if [ -f "${path}/index.html" ] || [ -f "${path}.html" ] || [ -f "${path}" ]; then
    ((found++))
  else
    echo "MISSING: $url"
    ((missing++))
  fi
done < /tmp/sitemap_urls.txt
echo "Found: $found / $(wc -l < /tmp/sitemap_urls.txt)"
echo "Missing: $missing"
```

---

## Step 5 — Fetch missing pages

wget may miss pages with URL-encoded curly quotes or other special characters. Fetch them with curl:

```bash
# Build list of missing URLs
while IFS= read -r url; do
  path="thetcj.org${url}"
  if [ ! -f "${path}/index.html" ] && [ ! -f "${path}.html" ] && [ ! -f "${path}" ]; then
    echo "https://thetcj.org${url}"
  fi
done < /tmp/sitemap_urls.txt > /tmp/missing_urls.txt

# Targeted wget pass (fast, no delay)
wget \
  --input-file=/tmp/missing_urls.txt \
  --page-requisites \
  --html-extension \
  --convert-links \
  --restrict-file-names=windows \
  --no-parent \
  --user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  --domains=thetcj.org \
  -e robots=off \
  2>&1 | tee wget_mirror2.log

# For any still missing (URL-encoded special chars), use curl:
while IFS= read -r url; do
  path="thetcj.org${url}"
  if [ ! -f "${path}/index.html" ] && [ ! -f "${path}.html" ] && [ ! -f "${path}" ]; then
    mkdir -p "thetcj.org${url}"
    curl -s -L \
      -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
      "https://thetcj.org${url}" \
      -o "thetcj.org${url}/index.html"
  fi
done < /tmp/sitemap_urls.txt
```

---

## Step 6 — Remove wp-json

wget crawls the WordPress REST API, generating hundreds of useless JSON files:

```bash
rm -rf thetcj.org/wp-json
```

---

## Step 7 — Clean HTML (remove dynamic elements)

Run `cleanup.py` — strips forms, comment sections, tracking scripts, analytics:

```bash
python3 cleanup.py
```

See `cleanup.py` for full list of what's removed.

---

## Step 8 — Rewrite absolute URLs to root-relative

`--convert-links` doesn't reliably work. Do it explicitly:

```bash
find thetcj.org -name "*.html" -exec sed -i 's|https://thetcj.org/|/|g; s|https://thetcj.org"|"/|g' {} +
```

Or use `rewrite_links.py` for a more thorough regex-based pass.

---

## Step 9 — Fix versioned asset filenames

wget saves `style.min.css?ver=3.6.0` as `style.min.css@ver=3.6.0.css`. GitHub Pages can't serve these — rename them and strip the query strings from HTML/CSS:

```bash
# Rename files
find thetcj-static -name "*@ver*" | while read f; do
  mv "$f" "$(echo "$f" | sed 's/@ver[^/]*$//')"
done

# Strip ?ver= from HTML and CSS references
find thetcj-static \( -name "*.html" -o -name "*.css" \) \
  -exec sed -i 's/?ver=[a-zA-Z0-9._-]*//g' {} +
```

---

## Step 10 — Fix mixed content (HTTPS)

Upgrade all `src="http://` to `src="https://` and remove external ad/tracking scripts:

```bash
# Upgrade http src to https
find thetcj-static -name "*.html" \
  -exec sed -i 's|src="http://|src="https://|g' {} +

# Remove ad/tracking domains (Shareaholic, Google Ads, Amazon widgets, Mailchimp)
python3 << 'EOF'
from bs4 import BeautifulSoup
from pathlib import Path

BLOCK = ["shareaholic", "openshareweb", "googlesyndication", "amazon-adsystem", "mailchimp.com"]

for p in Path("thetcj-static").rglob("*.html"):
    text = p.read_text(encoding="utf-8", errors="replace")
    if not any(d in text for d in BLOCK):
        continue
    soup = BeautifulSoup(text, "html.parser")
    changed = False
    for tag in soup.find_all(["script", "iframe", "link", "ins", "noscript", "div"]):
        if any(d in " ".join(str(v) for v in tag.attrs.values()) for d in BLOCK):
            tag.decompose()
            changed = True
    if changed:
        p.write_text(str(soup), encoding="utf-8")
print("Done")
EOF
```

---

## Step 11 — Copy to repo and deploy

```bash
rsync -a --exclude='.git' thetcj.org/ thetcj-static/
cd thetcj-static
git add -A
git commit -m "Add full static mirror"
git push
```

GitHub Pages deploys automatically. HTTPS cert provisions within ~15 min of DNS resolving.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Links go to thetcj.org | `--convert-links` didn't fire | Run Step 8 |
| CSS broken / menu vertical | `@ver=` filenames not found | Run Step 9 |
| Chrome "Not Secure" | Mixed content HTTP resources | Run Step 10 |
| Chrome "Broken HTTPS" | Active scripts loading HTTP | Remove ad/tracking tags (Step 10) |
| Pages say "Not Secure" after fix | Browser cached old permission | Chrome → Site Settings → remove "Allow insecure content" |
| ~50 pages missing | URL-encoded curly quotes in slugs | Use curl loop (Step 5) |
| Thousands of wp-json files | wget followed REST API links | Delete wp-json dir (Step 6) |
