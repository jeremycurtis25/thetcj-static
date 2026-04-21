#!/usr/bin/env python3
import re
from pathlib import Path

files = list(Path(".").rglob("*.html")) + list(Path(".").rglob("*.css"))
count = 0
for p in files:
    text = p.read_text(encoding="utf-8", errors="replace")
    new = re.sub(r'(src|href|url\()(["\'\ ]?)http://', r'\1\2https://', text)
    if new != text:
        p.write_text(new, encoding="utf-8")
        count += 1
print(f"Fixed {count} files")
