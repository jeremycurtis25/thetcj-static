# Static WordPress Mirror — Claude Instructions

This project scrapes a WordPress site and hosts a static HTML replica on GitHub Pages.

## Key files

- `cleanup.py` — strips forms, comments, tracking scripts from all HTML files
- `rewrite_links.py` — rewrites absolute domain URLs to root-relative paths
- `fix_mixed_content.py` — upgrades http:// to https:// in src attributes
- `thetcj.org/` — raw wget mirror output (not committed)
- `thetcj-static/` — cleaned output, committed to GitHub Pages

## GitHub

- Repo: `jeremycurtis25/thetcj-static`
- Pages URL: https://jeremycurtis25.github.io/thetcj-static/
- Custom domain: https://cwm.millgrove.org.uk
- DNS: CNAME `cwm` → `jeremycurtis25.github.io` managed via 123-reg

## Correct order of operations

See README.md for the full step-by-step guide. Summary:

1. `wget` mirror → 2. sitemap cross-reference → 3. curl for missing pages →
4. delete `wp-json` → 5. run `cleanup.py` → 6. rewrite absolute URLs →
7. fix `@ver=` filenames → 8. strip `?ver=` query strings →
9. fix mixed content → 10. remove ad/tracking scripts → 11. `rsync` + push

## Common mistakes to avoid

- Do NOT rely on wget `--convert-links` — it doesn't reliably rewrite links. Always run an explicit sed/regex pass (Step 8).
- Do NOT forget to rename `@ver=` asset files before deploying — GitHub Pages serves static files so `?ver=` query strings cause 404s (Step 7).
- Do NOT skip the ad/tracking script removal — Shareaholic preconnect tags alone cause Chrome "Broken HTTPS" even without a script tag (Step 10).
- Always check `wp-json` has been deleted — wget generates 1000+ useless JSON files from the REST API.
- Use `--wait=0` (no delay) on targeted wget passes — the paced pass is for the initial broad crawl only.

## Sitemap URLs

```
https://thetcj.org/sitemap_index.xml
https://thetcj.org/post-sitemap.xml      (1001 posts)
https://thetcj.org/post-sitemap2.xml     (929 posts)
https://thetcj.org/page-sitemap.xml      (18 pages)
```
Total: 1,948 URLs. Pages with URL-encoded curly quotes in slugs (`%e2%80%98` etc.) must be fetched with curl — wget fails on these.
