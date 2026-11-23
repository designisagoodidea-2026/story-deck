"""Kit checks. Usage: python3 -I -B check.py [--update-refs DECK]
Prints PASS/FAIL per case and exits 1 on any FAIL:
  build guards (unknown scene, unknown text field, missing case, engine version, forbidden text) each seen failing,
  the library names no audience (and that check catches a seeded name), the engine files name no audience,
  the version stamp, the teleprompter test, the screenshot harness over every deck in harness/decks.json,
  and the live forks in forks.json (decks not on the kit yet) unchanged since their last back-port (sync.py).
--update-refs DECK rebuilds that deck and replaces its reference screenshots (only after an intended change)."""
import ast, json, os, re, shutil, subprocess, sys, tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
H = os.path.join(KIT, "harness")
results = []


def report(name, ok, why=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {why}"))


def build(deck, out):
    return subprocess.run([sys.executable, "-I", "-B", os.path.join(KIT, "build.py"), deck, "--out", out], capture_output=True, text=True)


def decks():
    with open(os.path.join(H, "decks.json"), encoding="utf-8") as f:
        return {k: os.path.join(KIT, v) for k, v in json.load(f).items()}


def audience_hits(root, words):
    """Lines under root naming a past audience, except lines marked audience-ok (a fact, not a tailoring)."""
    hits = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith((".py", ".js", ".css")): continue
            p = os.path.join(dp, f)
            with open(p, encoding="utf-8") as h:
                for n, line in enumerate(h, 1):
                    if "audience-ok" in line: continue
                    w = [x for x in words if x in line]
                    if w: hits.append(f"{os.path.relpath(p, KIT)}:{n} {'/'.join(w)}")
    return hits


def harness(env, *extra):
    if not os.path.isdir(os.path.join(H, "node_modules")):
        return None, f'harness not installed: cd "{H}" && npm ci'
    r = subprocess.run(["npx", "playwright", "test", *extra], cwd=H, capture_output=True, text=True, env={**os.environ, **env})
    return r.returncode == 0, "\n".join(l for l in r.stdout.splitlines() if re.search(r"✘|Snapshot:|pixels|Error:|never|didn't", l))[-2000:]


def chrome_version():
    r = subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"], capture_output=True, text=True)
    return r.stdout.strip()


if "--update-refs" in sys.argv:
    name = sys.argv[sys.argv.index("--update-refs") + 1]
    os.makedirs(os.path.join(H, ".out"), exist_ok=True)
    out = os.path.join(H, ".out", name + ".html")
    r = build(decks()[name], out)
    if r.returncode: sys.exit(r.stderr)
    shutil.rmtree(os.path.join(H, "refs", name), ignore_errors=True)
    ok, why = harness({"DECK_NAME": name, "DECK_HTML": out}, "--update-snapshots")
    with open(os.path.join(H, "refs", "CHROME"), "w") as f: f.write(chrome_version() + "\n")
    sys.exit(0 if ok else why)

AUD_FILE = os.path.join(KIT, "AUDIENCES")  # past audiences' names, one per line (optional; keep it out of public copies)
WORDS = [w for w in open(AUD_FILE, encoding="utf-8").read().split("\n") if w.strip()] if os.path.exists(AUD_FILE) else []
SEED_DECK = next(iter(decks()))  # the first deck in harness/decks.json seeds the guard tests
EX = decks()[SEED_DECK]


def seeds(deck_py):
    """Five deliberate mistakes, each made in this deck's own deck.py: (name, old, new, what the error must name)."""
    use = re.search(r"use=(['\"])([\w/-]+)\1", deck_py)
    field = re.search(r"text=\{(['\"])(\w+)\1", deck_py)
    cases_line = re.search(r"^CASES = (\[.*?\])", deck_py, re.M)
    last = ast.literal_eval(cases_line.group(1))[-1]
    engine = re.search(r"^ENGINE = (\d+)", deck_py, re.M)
    forbid = re.search(r"^FORBID = (\[.*?\])", deck_py, re.M)
    title = re.search(r"^TITLE = (['\"])(\w{3,})", deck_py, re.M).group(2)  # a word that is surely in the page
    return [
        ("unknown scene", use.group(0), use.group(0)[:-1] + "-missing" + use.group(1), use.group(2) + "-missing"),
        ("unknown text field", field.group(0), field.group(0)[:-1] + "zz" + field.group(1), field.group(2) + "zz"),
        ("case not in CASES", cases_line.group(0), "CASES = " + repr(ast.literal_eval(cases_line.group(1))[:-1]), last),
        ("engine version", engine.group(0), f"ENGINE = {int(engine.group(1)) - 1}", "Migration:"),
        ("forbidden text", forbid.group(0), "FORBID = " + repr(ast.literal_eval(forbid.group(1)) + [title]), "deck.py:"),
    ]

with tempfile.TemporaryDirectory() as tmp:
    out = os.path.join(tmp, "out.html")

    def seeded(name, path, old, new):
        d = os.path.join(tmp, name)
        shutil.copytree(EX, d)
        p = os.path.join(d, path)
        with open(p, encoding="utf-8") as h: text = h.read()
        if old not in text: sys.exit(f"check.py: cannot seed {name}: {old!r} not in {path}")
        with open(p, "w", encoding="utf-8") as h: h.write(text.replace(old, new, 1))
        return build(d, out)

    with open(os.path.join(EX, "deck.py"), encoding="utf-8") as h: seed_list = seeds(h.read())
    for name, old, new, expect in seed_list:
        r = seeded(name.replace(" ", "-"), "deck.py", old, new)
        report(f"build stops on {name}", r.returncode != 0 and expect in r.stderr, r.stderr.strip()[-300:] or "build passed")

    hits = audience_hits(os.path.join(KIT, "library"), WORDS)
    report("library names no audience", not hits, "; ".join(hits[:10]))
    lib = os.path.join(tmp, "lib")
    shutil.copytree(os.path.join(KIT, "library"), lib)
    seed_words = WORDS or ["Seed Audience"]
    first_scene = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(lib) for f in fs if f == "scene.py")[0]
    with open(first_scene, "a", encoding="utf-8") as h: h.write(f"\n# {seed_words[0]}\n")
    report("library check catches a seeded audience name", bool(audience_hits(lib, seed_words)), "missed it")

    eng = []
    for f in ("engine/engine.html", "engine/teleprompter.js", "build.py"):
        with open(os.path.join(KIT, f), encoding="utf-8") as h: eng += [f"{f}: {w}" for w in WORDS if w in h.read()]
    report("engine files name no audience", not eng, ", ".join(eng))

    os.makedirs(os.path.join(H, ".out"), exist_ok=True)
    built_ok = True
    for name, d in decks().items():
        r = build(d, os.path.join(H, ".out", name + ".html"))
        built_ok &= r.returncode == 0
        report(f"deck {name} builds", r.returncode == 0, r.stderr.strip()[-300:])
    version = open(os.path.join(KIT, "VERSION")).read().strip()
    with open(os.path.join(H, ".out", SEED_DECK + ".html"), encoding="utf-8") as h:
        report("built page carries the engine version", f'content="story-deck {version}"' in h.read(), "no generator meta")

# forks (optional): the sync check sees a changed file, and every fork in this checkout is unchanged since its last back-port
sys.path.insert(0, KIT)
if os.path.exists(os.path.join(KIT, "sync.py")) and os.path.exists(os.path.join(KIT, "forks.json")):
    import sync
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "deck")
        os.makedirs(d)
        with open(os.path.join(d, "template.html"), "w") as h: h.write("a")
        f = {"deck": d, "example": "examples/x", "synced": "seed", "files": sync.tracked(d), "logged": []}
        with open(os.path.join(d, "template.html"), "w") as h: h.write("b")
        report("sync check catches a changed fork", sync.status("seed", f)[0], "missed it")
    drift = {n: sync.status(n, f) for n, f in sync.load().items()}
    report("live forks unchanged since their last back-port (sync.py)", not any(d for d, _ in drift.values()),
           "\n".join(l for d, ls in drift.values() if d for l in ls))

r = subprocess.run(["node", "teleprompter.test.js"], capture_output=True, text=True, cwd=os.path.join(KIT, "engine"))
report("teleprompter test", r.returncode == 0, (r.stderr or r.stdout).strip()[-300:])

if built_ok:
    with open(os.path.join(H, "refs", "CHROME")) as f: ref_chrome = f.read().strip()
    ok, why = harness({})
    now = chrome_version()
    if ok is not None and not ok and now != ref_chrome: why += f"\n(references were taken with {ref_chrome}; this is {now}: if only a few pixels moved, recapture with --update-refs)"
    report("screenshot harness: every deck, every scene and key press", bool(ok), why)

sys.exit(0 if all(results) else 1)
