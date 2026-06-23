"""
Replace all hardcoded brand strings in templates with Django template variables.

Run from crm1/:  python replace_brand.py

What it does:
  - Replaces literal 'FoodVendor' in template text/titles → {{ COMPANY_SHORT_NAME }}
  - Skips lines that already use {{ COMPANY_NAME }} or {{ COMPANY_SHORT_NAME }}
  - Reports every changed file and line count

To rebrand for a new client:
  1. Edit COMPANY_NAME, COMPANY_SHORT_NAME, COMPANY_TAGLINE in .env
  2. That's it — all templates pick up the change via context_processors.py
"""
import pathlib
import re

TEMPLATES = pathlib.Path("accounts/templates")

# Pattern: bare 'FoodVendor' not already inside a {{ }} tag
BRAND_PATTERN = re.compile(r'(?<!\{)(?<!\{ )FoodVendor(?! \})(?!\})')
REPLACEMENT = '{{ COMPANY_SHORT_NAME }}'

changed_files = []

for html in sorted(TEMPLATES.rglob("*.html")):
    try:
        txt = html.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"  SKIP (read error): {html} — {exc}")
        continue

    if 'FoodVendor' not in txt:
        continue  # nothing to do

    lines = txt.splitlines(keepends=True)
    new_lines = []
    file_changed = False
    replacements_in_file = 0

    for line in lines:
        # Skip lines already using a template variable for the brand
        if 'COMPANY_NAME' in line or 'COMPANY_SHORT_NAME' in line:
            new_lines.append(line)
            continue

        new_line, n = BRAND_PATTERN.subn(REPLACEMENT, line)
        if n:
            file_changed = True
            replacements_in_file += n
        new_lines.append(new_line)

    if file_changed:
        html.write_text(''.join(new_lines), encoding="utf-8")
        changed_files.append((html.name, replacements_in_file))

# Report
if changed_files:
    print(f"Updated {len(changed_files)} template(s):")
    for fname, count in sorted(changed_files):
        print(f"  {fname}  ({count} replacement{'s' if count != 1 else ''})")
else:
    print("No changes — all templates already use template variables for branding.")
