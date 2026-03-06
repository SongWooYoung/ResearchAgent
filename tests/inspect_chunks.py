import re
from modules.chunker.chunker import split_sections, get_abstract, get_intro, get_conclusion, get_body_sections
from modules.pdf2md.pdf2md import extract_md_from_url

md = extract_md_from_url("https://arxiv.org/pdf/2410.09016")
sections = split_sections(md)
print(f"Total sections: {len(sections)}")
for s in sections[:20]:
    print(f"  [L{s.level}] {s.title[:60]!r}  ({len(s.content)} chars)")

print("\nAbstract found:", get_abstract(sections) is not None)
print("Intro found:   ", get_intro(sections) is not None)
print("Conclusion:    ", get_conclusion(sections) is not None)
print("\nBody sections:")
for s in get_body_sections(sections):
    print(f"  {s.title[:60]!r}  ({len(s.content)} chars)")
