"""Start a deck from the starter in harness/fixture/: two invented cases with their own library, ready to rename and rewrite.
Usage: python3 -I -B new.py <deck-dir> --company "Example Co" --name "Sam Rivera" [--title "Head of Design"] [--first Sam]"""
import argparse, os, re, shutil, sys

KIT = os.path.dirname(os.path.abspath(__file__))
STARTER = os.path.join(KIT, "harness", "fixture")

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("deck_dir")
ap.add_argument("--company", required=True)
ap.add_argument("--name", default="")
ap.add_argument("--first")
ap.add_argument("--title", default="")
a = ap.parse_args()

deck = os.path.abspath(a.deck_dir)
if os.path.exists(os.path.join(deck, "deck.py")): sys.exit(f"new: {deck} already has a deck.py")
os.makedirs(deck, exist_ok=True)
for item in ("deck.py", "notes.py", "emphasis.py", "library", "art"):
    src = os.path.join(STARTER, item)
    (shutil.copytree if os.path.isdir(src) else shutil.copy)(src, os.path.join(deck, item))

slug = re.sub(r"[^a-z0-9]+", "-", a.company.lower()).strip("-")
first = a.first or (a.name.split()[0] if a.name else "")
aud = {"name": a.name, "first": first, "title": a.title, "company": a.company, "team": 0}
p = os.path.join(deck, "deck.py")
with open(p, encoding="utf-8") as f: s = f.read()
for pattern, value in ((r'^""".*?"""', f'"""{a.company} deck. Started from the kit\'s two-case starter: rename the cases in library/ and rewrite.\nBuild: python3 -I -B "{os.path.join(KIT, "build.py")}" "{deck}" """'),
                       (r"^TITLE = .*$", f'TITLE = "{a.company} Story Deck"'),
                       (r"^OUT = .*$", f'OUT = "{slug}-story-deck.html"'),
                       (r"^AUDIENCE = .*$", f"AUDIENCE = {aud!r}"),
                       (r"^FOOTER = .*$", 'FOOTER = "for {name}, {company}"' if a.name else 'FOOTER = "{company}"'),
                       (r"^CHANNEL = .*$", f'CHANNEL = "{slug}-deck-notes"')):
    s, n = re.subn(pattern, lambda m: value, s, count=1, flags=re.M | (re.S if pattern.startswith('^"""') else 0))
    if not n: sys.exit(f"new: the starter's deck.py has no {pattern!r}")
with open(p, "w", encoding="utf-8") as f: f.write(s)
print(f'new: {deck}. Build: python3 -I -B "{os.path.join(KIT, "build.py")}" "{deck}"')
