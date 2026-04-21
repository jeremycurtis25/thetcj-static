#!/usr/bin/env python3
"""
Rewrite all absolute thetcj.org URLs to relative paths in the static mirror.
Works on both HTML attributes and inline CSS url() references.
"""

import re
from pathlib import Path

SITE_DIR = Path(__file__).parent / "thetcj-static"
DOMAIN = "https://thetcj.org"
DOMAIN_HTTP = "http://thetcj.org"

stats = {"files": 0, "replacements": 0}


def relative_path(from_file: Path, to_path: str) -> str:
    """Compute relative URL from from_file to to_path (absolute URL path)."""
    from_dir = from_file.parent
    target = SITE_DIR / to_path.lstrip("/")
    try:
        rel = target.relative_to(from_dir)
        return str(rel)
    except ValueError:
        # Fall back to root-relative (shouldn't happen often)
        return to_path


def rewrite_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  SKIP: {path} — {e}")
        return

    original = content

    # Replace all absolute thetcj.org URLs with root-relative paths
    # Root-relative (starting with /) works fine for GitHub Pages custom domain
    content = re.sub(
        r'https?://thetcj\.org(/[^"\'>\s]*|(?=["\'\s>]))',
        lambda m: m.group(1) if m.group(1) else "/",
        content
    )

    if content != original:
        count = original.count("thetcj.org") - content.count("thetcj.org")
        stats["replacements"] += count
        stats["files"] += 1
        path.write_text(content, encoding="utf-8")


def main():
    html_files = list(SITE_DIR.rglob("*.html"))
    css_files = list(SITE_DIR.rglob("*.css"))
    all_files = html_files + css_files
    total = len(all_files)
    print(f"Processing {total} files...\n")

    for i, path in enumerate(all_files, 1):
        if i % 300 == 0:
            print(f"  {i}/{total}...")
        rewrite_file(path)

    print(f"\nDone.")
    print(f"  Files modified:  {stats['files']}")
    print(f"  URLs rewritten:  {stats['replacements']}")


if __name__ == "__main__":
    main()
