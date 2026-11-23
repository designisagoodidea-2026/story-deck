"""Story deck build: engine + library + one deck folder -> one self-contained page.
Usage: python3 -I -B build.py <deck-dir> [--out <file>]
A deck folder holds deck.py, notes.py, optional emphasis.py, optional scenes/<name>/ (its own scenes) and optional art/.
Contract: specs/007-story-deck-kit/contracts/deck-contract.md and data-model.md."""
import base64, copy, glob, html, json, os, re, sys

KIT = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(KIT, "library")
COMPONENTS = {"cases", "closing", "context", "thanks", "thennow"}  # engine-owned scene code (engine/engine.html)
AUD_KEYS = ("name", "first", "title", "company", "team")


def fail(msg):
    sys.exit(f"build: {msg}")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_py(path):
    ns = {"__file__": path}
    exec(compile(read(path), path, "exec"), ns)
    return ns


def b64(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


# ---------- arguments ----------
args = sys.argv[1:]
out_path = None
if "--out" in args:
    i = args.index("--out")
    if i + 1 >= len(args): fail("--out needs a file path")
    out_path = args[i + 1]
    del args[i:i + 2]
if len(args) != 1: fail("usage: python3 -I -B build.py <deck-dir> [--out <file>]")
DECK = os.path.abspath(args[0])
if not os.path.isfile(os.path.join(DECK, "deck.py")): fail(f"{DECK} has no deck.py")
deck = load_py(os.path.join(DECK, "deck.py"))
NOTES = load_py(os.path.join(DECK, "notes.py")).get("NOTES", {}) if os.path.exists(os.path.join(DECK, "notes.py")) else {}
EMPH = load_py(os.path.join(DECK, "emphasis.py")).get("EMPH", {}) if os.path.exists(os.path.join(DECK, "emphasis.py")) else {}

# ---------- engine version ----------
VERSION = read(os.path.join(KIT, "VERSION")).strip()
major = int(VERSION.split(".")[0])
if deck.get("ENGINE") != major:
    log = read(os.path.join(KIT, "CHANGELOG.md"))
    m = re.search(rf"^## {major}\.0\.0.*?^Migration:(.*?)(?=^## |\Z)", log, re.M | re.S)
    fail(f"this deck is written for engine {deck.get('ENGINE')}, the kit is {VERSION}. Migration:{m.group(1).rstrip() if m else ' see CHANGELOG.md'}")

AUD = deck["AUDIENCE"]
if not AUD.get("company"): fail("AUDIENCE needs 'company'")  # name and first may be empty when the panel isn't known yet


def fill(x):
    """Audience placeholders ({name}, {first}, {title}, {company}, {team}) in any string, list or dict."""
    if isinstance(x, str): return re.sub(r"\{(" + "|".join(AUD_KEYS) + r")\}", lambda m: str(AUD.get(m.group(1), m.group(0))), x)
    if isinstance(x, list): return [fill(v) for v in x]
    if isinstance(x, dict): return {k: fill(v) for k, v in x.items()}
    return x


# ---------- library and deck scenes ----------
def scan(root):
    found = {}
    for p in sorted(glob.glob(os.path.join(root, "**", "scene.py"), recursive=True)):
        ns = load_py(p)
        sid = ns.get("ID")
        if not sid: fail(f"{p} has no ID")
        rel = os.path.relpath(os.path.dirname(p), root).replace(os.sep, "/")
        if sid != rel: fail(f"{p}: ID {sid!r} must equal its folder path {rel!r}")
        found[sid] = dict(ns, _dir=os.path.dirname(p))
    return found


# LIBRARIES in deck.py: more library folders (relative to the deck), laid out like library/, checked after the kit's.
# Later ones win, and the deck's own scenes/ win over all of them.
roots = [LIB] + [os.path.normpath(os.path.join(DECK, r)) for r in deck.get("LIBRARIES", [])]
missing_roots = [r for r in roots if not os.path.isdir(r)]
if missing_roots: fail(f"LIBRARIES: no such folder {missing_roots}")
library, cases = {}, {}
for root in roots:
    found = scan(root)
    for sid in sorted(set(found) & set(library)):
        print(f"note: {os.path.relpath(root, DECK)} replaces the library scene {sid!r}")
    library.update(found)
    for p in sorted(glob.glob(os.path.join(root, "*", "case.py"))):
        ns = load_py(p)
        cases[ns["KEY"]] = dict(ns, _dir=os.path.dirname(p))
local = scan(os.path.join(DECK, "scenes")) if os.path.isdir(os.path.join(DECK, "scenes")) else {}
for sid in sorted(set(local) & set(library)):
    print(f"note: the deck's own scene {sid!r} replaces the library scene of the same id")
scenes = {**library, **local}

CASES = deck["CASES"]
unknown = [c for c in CASES if c not in cases]
if unknown: fail(f"CASES names cases not in the library: {unknown}; have {sorted(cases)}")

# ---------- resolve instances ----------
inst = []
for s in deck["SCENES"]:
    use = s["use"]
    if use not in scenes: fail(f"scene {s['id']!r} uses {use!r}, which is in neither the library nor the deck's scenes/")
    sc = scenes[use]
    code = sc.get("CODE") or use
    if code not in COMPONENTS and code not in scenes: fail(f"{use!r} borrows code {code!r}, which doesn't exist")
    if code not in COMPONENTS and not os.path.exists(os.path.join(scenes[code]["_dir"], "scene.js")): fail(f"{code!r} has no scene.js")
    text = copy.deepcopy(sc.get("TEXT") or {})
    extra = sorted(set(s.get("text", {})) - set(text))
    if extra: fail(f"scene {s['id']!r} overrides text fields {extra}; {use!r} has {sorted(text) or 'none'}")
    text.update(copy.deepcopy(s.get("text", {})))
    case = sc.get("CASE")
    if case and case not in CASES: fail(f"scene {s['id']!r} ({use}) belongs to case {case!r}; add it to CASES")
    notes = NOTES.get(s["id"], fill(sc.get("NOTES")) or [])
    emph = s.get("emph", EMPH.get(s["id"], fill(sc.get("EMPH") or [])))
    inst.append(dict(id=s["id"], use=use, code=code, case=case, text=fill(text), notes=notes, emph=emph,
                     label=fill(s.get("label", sc["LABEL"])), q=fill(s.get("q", sc["Q"])), claim=fill(s.get("claim", sc["CLAIM"])),
                     cap=fill(s.get("cap", sc.get("CAP", ""))), eyebrow=s.get("eyebrow", sc.get("EYEBROW", False)), group=s.get("group"),
                     today=s.get("today", sc.get("TODAY", False)), active=s.get("active")))

ids = [x["id"] for x in inst]
if len(ids) != len(set(ids)): fail(f"duplicate scene id: {sorted({i for i in ids if ids.count(i) > 1})}")
# every emphasis phrase must still appear in its scene's spoken notes
spoken = {x["id"]: " ".join(it["x"] for st in x["notes"] for it in st["items"] if it["t"] in ("p", "d")) for x in inst}
stale = [(x["id"], ph) for x in inst for ph in x["emph"] if ph not in spoken[x["id"]]]
if stale: fail(f"emphasis phrases not in the notes: {stale}")

# CASE_TEXT overrides a case's card for this deck: org, name, q (the card's quote), recap, tags, vignette (one of its variants)
CASE_TEXT = deck.get("CASE_TEXT", {})
bad = {k: sorted(set(v) - {"org", "name", "q", "recap", "tags", "vignette"}) for k, v in CASE_TEXT.items()}
if any(bad.values()) or set(CASE_TEXT) - set(CASES): fail(f"CASE_TEXT: unknown fields {bad} or cases not in CASES {sorted(set(CASE_TEXT) - set(CASES))}")
deck_cases = []
for n, k in enumerate(CASES, 1):
    first = next((x for x in inst if x["case"] == k and not x["group"]), None)
    if not first: fail(f"case {k!r} is in CASES but no scene uses it")
    c, o = cases[k], fill(CASE_TEXT.get(k, {}))
    deck_cases.append(dict(n=n, key=k, go=first["id"], org=o.get("org", c["ORG"]), hint=c["HINT"], name=o.get("name", c["NAME"]), q=o.get("q", first["q"]),
                           recap=o.get("recap", c["RECAP"]), tags=o.get("tags", []), vignette=o.get("vignette", k)))
groups = list(dict.fromkeys(x["group"] for x in inst if x["group"]))
# CHAPTERS = True: a logo wipe into each case's first slide, and out of the last case into the slide after it
chapters = {}
if deck.get("CHAPTERS"):
    order = [x for x in inst if not x["group"]]
    prev = None
    for i, x in enumerate(order):
        k = x["case"]
        if k and k != prev and k in CASES: chapters[x["id"]] = [prev, k]; prev = k
        elif not k and prev and i and order[i - 1]["case"] == prev: chapters[x["id"]] = [prev, None]; prev = None

# LEAVE_BEHIND = True: the deck is also read without a voiceover, so each slide's words stay short
if deck.get("LEAVE_BEHIND"):
    for x in inst:
        words = len(re.sub(r"<br>", " ", re.sub(r"<(?!br)[^>]+>", "", x["claim"])).split())
        if words > 12 and x["use"] != "opening/intro" and x["code"] != "context": fail(f"LEAVE_BEHIND: {x['id']!r} claim has {words} words (12 at most)")
        if len(x["cap"].split()) > 30: fail(f"LEAVE_BEHIND: {x['id']!r} caption has {len(x['cap'].split())} words (30 at most)")


# ---------- slides ----------
def no_widow(claim):
    # join the last two words so a headline never ends on one stranded word
    i = claim.rfind(" ")
    return claim if i < 0 or "<" in claim[i:].split(">")[-1] else claim[:i] + "&nbsp;" + claim[i + 1:]


def notes_html(steps):
    out = []
    for i, st in enumerate(steps):
        if len(steps) > 1: out.append(f"<p><b>Key press {i + 1} · {html.escape(st['label'])}</b></p>")
        for n in st["items"]:
            x = html.escape(n["x"])
            out.append(f"<p><b>{x}</b></p>" if n["t"] == "q" else f"<p><i>{x}</i></p>" if n["t"] == "d" else f"<p>{x}</p>")
    return "".join(out)


footer = html.escape(fill(deck.get("FOOTER", "for {name}, {company}")))
CAPTIONS, TODAY_TAG = deck.get("CAPTIONS", False), fill(deck.get("TODAY_TAG", "How I'd approach this work today"))
by_key = {c["key"]: c for c in deck_cases}


def eyebrow(x):
    # "Case n of N" (or "Appendix" in a group), the case's logo, and its org, above the claim
    if not x["eyebrow"] or not x["case"]: return ""
    c = by_key[x["case"]]
    n = "Appendix" if x["group"] else f"Case {c['n']} of {len(deck_cases)}"
    return f'<div class="eyebrow"><span class="cn">{n}</span><span class="mk" data-logo="{x["case"]}"></span><span class="on">{html.escape(c["org"])}</span></div>\n'


slides = []
for x in inst:
    attrs = f'data-scene="{x["id"]}" data-q="{html.escape(x["q"])}"'
    if x["case"]: attrs += f' data-case="{x["case"]}"'
    if x["group"]: attrs += f' data-group="{x["group"]}"'
    attrs += f' data-build="{x["code"]}"'
    if x["active"] is not None: attrs += f' data-active="{x["active"]}"'
    if x["today"]: attrs += ' data-today=""'
    cap = (f'<p class="cap{" org" if x["code"] == "context" else ""}">' + (f'<span class="tt">{html.escape(TODAY_TAG)}</span>' if x["today"] else "")
           + html.escape(x["cap"]) + "</p>\n") if CAPTIONS else ""
    slides.append(f'''<section {attrs}><div class="scene{' has-cap' if CAPTIONS else ''}">
<div class="band"><span class="case">{html.escape(x["label"])}</span><span class="q{' now' if x["today"] else ''}">{html.escape(x["q"])}</span></div>
{eyebrow(x)}<h2 class="claim">{no_widow(x["claim"])}</h2>
{cap}<div class="viz"></div>
<div class="foot"><span class="who">{footer}</span><span class="trail"></span><span class="sheet"></span></div>
</div><aside class="notes">{notes_html(x["notes"])}</aside></section>''')

# ---------- case and scene code, in deck order, each in its own scope ----------
codes = list(dict.fromkeys(x["code"] for x in inst if x["code"] not in COMPONENTS))
css_parts = [read(os.path.join(cases[k]["_dir"], "case.css")) for k in CASES if os.path.exists(os.path.join(cases[k]["_dir"], "case.css"))]
scene_css = [read(os.path.join(scenes[c]["_dir"], "scene.css")) for c in codes if os.path.exists(os.path.join(scenes[c]["_dir"], "scene.css"))]
wrap = lambda js: "(() => {\n" + js.rstrip("\n") + "\n})();"
cases_js = [wrap(read(os.path.join(cases[k]["_dir"], "case.js"))) for k in CASES]
scenes_js = []
for c in codes:
    js = read(os.path.join(scenes[c]["_dir"], "scene.js"))
    if not re.search(r"Scene\.def\(['\"]" + re.escape(c) + r"['\"]", js): fail(f"{c}/scene.js must call Scene.def({c!r}, ...)")
    scenes_js.append(wrap(js))

# ---------- art ----------
def art_files(sub, pattern):
    """Kit art and deck art for one category, by file name; the deck's file wins."""
    found = {}
    for root in (os.path.join(KIT, "art"), os.path.join(DECK, "art")):
        for f in glob.glob(os.path.join(root, sub, pattern)):
            found[os.path.basename(f)] = f
    return [found[n] for n in sorted(found)]


ART = {os.path.basename(f)[:-5]: b64(f, "image/webp") for f in art_files("cut", "*.webp")}
ART.update({"wm-" + os.path.basename(f)[:-4]: b64(f, "image/svg+xml") for f in art_files("wordmarks", "*.svg")})
ART.update({"logo-" + os.path.basename(f)[:-4]: b64(f, "image/svg+xml") for f in art_files("logos", "*.svg")})
VID = {os.path.basename(f)[:-4]: b64(f, "video/mp4") for f in art_files("video", "*.mp4")}  # the cameo's clips and vignette movies
logo = read(os.path.join(DECK, AUD["logo"])).strip() if AUD.get("logo") else ""

DECK_DATA = {
    "audience": {k: AUD.get(k, "") for k in AUD_KEYS} | {"color": AUD.get("color", "#232836"), "logo": logo},
    "cases": deck_cases,
    "groups": groups,
    "chapters": chapters,
    "scenes": {x["id"]: {"code": x["code"], "case": x["case"], "text": x["text"], "active": x["active"]} for x in inst},
}

fill_in = {
    "TITLE": html.escape(fill(deck["TITLE"])),
    "VERSION": VERSION,
    "AUDIENCE_COLOR": DECK_DATA["audience"]["color"],
    "CASE_CSS": "\n".join(css_parts),
    "SCENE_CSS": "\n".join(scene_css),
    "DECK_CSS": read(os.path.join(DECK, "deck.css")) if os.path.exists(os.path.join(DECK, "deck.css")) else "",
    "CASES_JS": "\n".join(cases_js),
    "SCENES_JS": "\n".join(scenes_js),
    "DECK": json.dumps(DECK_DATA),
    "CHANNEL": deck.get("CHANNEL", re.sub(r"\W+", "-", AUD["company"].lower()) + "-deck-notes"),
    "REVEAL_CSS": read(os.path.join(KIT, "engine", "reveal-6.0.1.css")),
    "SLIDES": "\n".join(slides),
    "NOTES": json.dumps({x["id"]: x["notes"] for x in inst if x["notes"]}),
    "EMPH": json.dumps({x["id"]: x["emph"] for x in inst if x["emph"]}),
    "TELE": read(os.path.join(KIT, "engine", "teleprompter.js")),
    "ART": json.dumps(ART),
    "VID": json.dumps(VID),
}
engine = read(os.path.join(KIT, "engine", "engine.html"))
pat = re.compile(r"/\*(" + "|".join(fill_in) + r")\*/")
counts = {k: 0 for k in fill_in}
for m in pat.finditer(engine): counts[m.group(1)] += 1
wrong = {k: n for k, n in counts.items() if n != 1}
if wrong: fail(f"engine.html placeholders must appear exactly once: {wrong}")
t = pat.sub(lambda m: fill_in[m.group(1)], engine)  # one pass, so filled content is never rescanned
links = "".join(f'<link rel="stylesheet" href="{html.escape(cases[k]["FONT_LINK"])}">\n' for k in CASES if cases[k].get("FONT_LINK"))
if links: t = t.replace("<style>", links + "<style>", 1)

# ---------- leftovers from an earlier audience ----------
forbid = deck.get("FORBID", [])
leaks = {s: t.count(s) for s in forbid if s in t}
if leaks:
    where = []
    deck_files = [os.path.join(DECK, f) for f in ("deck.py", "notes.py", "emphasis.py")] + sorted(glob.glob(os.path.join(DECK, "scenes", "**", "*.*"), recursive=True))
    for f in deck_files:
        if not os.path.isfile(f): continue
        for n, line in enumerate(read(f).split("\n"), 1):
            hit = [s for s in leaks if s in line] if not line.startswith("FORBID") else []
            if hit: where.append(f"  {os.path.relpath(f, DECK)}:{n} {'/'.join(hit)}: {line.strip()[:90]}")
    fail(f"forbidden text in the output (left over from an earlier deck?): {leaks}\n" + ("\n".join(where) or "  not in the deck's files: check the library scenes it uses"))

out_path = out_path or os.path.join(DECK, deck["OUT"])
with open(out_path, "w", encoding="utf-8") as f:
    f.write(t)
missing = [x["id"] for x in inst if not x["notes"] and not x["use"] == "deck/cases"]
print(f"ok engine {VERSION}, {len(inst)} scenes, {len(t)} bytes; missing notes: {missing}")
