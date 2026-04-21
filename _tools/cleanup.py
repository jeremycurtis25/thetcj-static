#!/usr/bin/env python3
"""
Cleanup script for thetcj.org static mirror.
Removes: tracking scripts, external analytics, forms, comment sections,
         social share widgets, recaptcha, and other dynamic-only elements.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

SITE_DIR = Path(__file__).parent / "thetcj.org"

# External script domains/patterns to remove entirely
SCRIPT_BLOCKLIST = [
    "googletagmanager.com",
    "google-analytics.com",
    "google.com/recaptcha",
    "shareaholic.net",
    "assoc-amazon.com",       # Amazon affiliate tracking
    "cdn-cgi/scripts",        # Cloudflare email obfuscation
]

# Script src substrings (local WP files) to remove
LOCAL_SCRIPT_BLOCKLIST = [
    "contact-form-7",
    "recaptcha",
]

# IDs/classes of elements to remove entirely
REMOVE_IDS = [
    "comments",
    "respond",               # WordPress "Leave a reply" block
    "comment-form",
    "mc-embedded-subscribe-form",  # Mailchimp
]

REMOVE_CLASSES = [
    "comment-list",
    "comment-respond",
    "cookie-notice",
    "cookie-banner",
    "gdpr",
    "shareaholic",
]

stats = {"files": 0, "scripts_removed": 0, "forms_removed": 0, "elements_removed": 0}


def clean_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  SKIP (read error): {path} — {e}")
        return

    soup = BeautifulSoup(content, "html.parser")
    changed = False

    # 1. Remove blocked external scripts
    for tag in soup.find_all("script", src=True):
        src = tag.get("src", "")
        if any(blocked in src for blocked in SCRIPT_BLOCKLIST):
            tag.decompose()
            stats["scripts_removed"] += 1
            changed = True

    # 2. Remove blocked local scripts
    for tag in soup.find_all("script", src=True):
        src = tag.get("src", "")
        if any(blocked in src for blocked in LOCAL_SCRIPT_BLOCKLIST):
            tag.decompose()
            stats["scripts_removed"] += 1
            changed = True

    # 3. Remove inline GTM / analytics script blocks
    for tag in soup.find_all("script", src=False):
        text = tag.get_text()
        if any(kw in text for kw in ["gtag(", "GoogleTagManager", "ga(", "_gaq", "shareaholic"]):
            tag.decompose()
            stats["scripts_removed"] += 1
            changed = True

    # 4. Remove all <form> elements
    for tag in soup.find_all("form"):
        tag.decompose()
        stats["forms_removed"] += 1
        changed = True

    # 5. Remove elements by ID
    for id_ in REMOVE_IDS:
        tag = soup.find(id=id_)
        if tag:
            tag.decompose()
            stats["elements_removed"] += 1
            changed = True

    # 6. Remove elements by class
    for cls in REMOVE_CLASSES:
        for tag in soup.find_all(class_=lambda x: x and cls in " ".join(x)):
            tag.decompose()
            stats["elements_removed"] += 1
            changed = True

    # 7. Remove Yoast / ld+json schema scripts (not needed for static display)
    for tag in soup.find_all("script", type="application/ld+json"):
        tag.decompose()
        stats["scripts_removed"] += 1
        changed = True

    # 8. Remove noscript GTM iframes
    for tag in soup.find_all("noscript"):
        if "googletagmanager" in str(tag):
            tag.decompose()
            stats["scripts_removed"] += 1
            changed = True

    if changed:
        path.write_text(str(soup), encoding="utf-8")
        stats["files"] += 1


def main():
    html_files = list(SITE_DIR.rglob("*.html"))
    total = len(html_files)
    print(f"Processing {total} HTML files in {SITE_DIR}...\n")

    for i, path in enumerate(html_files, 1):
        if i % 200 == 0:
            print(f"  {i}/{total} files processed...")
        clean_file(path)

    print(f"\nDone.")
    print(f"  Files modified:    {stats['files']}")
    print(f"  Scripts removed:   {stats['scripts_removed']}")
    print(f"  Forms removed:     {stats['forms_removed']}")
    print(f"  Elements removed:  {stats['elements_removed']}")


if __name__ == "__main__":
    main()
