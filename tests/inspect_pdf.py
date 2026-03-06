import re
from modules.pdf2md.pdf2md import extract_md_from_url

md = extract_md_from_url("https://arxiv.org/pdf/2410.09016")
print(repr(md[:2000]))
print("\n---HEADING LINES---")
lines = md.split("\n")
heading_lines = [
    (i, l) for i, l in enumerate(lines)
    if l.strip() and (
        l.startswith("#")
        or re.match(r"^\d+[\. ]", l.strip())
        or re.match(r"^[A-Z][A-Z\s]{3,}[A-Z]$", l.strip())
    )
]
for i, l in heading_lines[:40]:
    print(f"L{i:4d}: {repr(l[:100])}")
