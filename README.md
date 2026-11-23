# Story deck

A kit for building case-study presentations you can present, rehearse and reuse: illustrated, animated slides in one self-contained HTML page, with a presenter screen and a teleprompter that follows your voice.

I built this to present case studies in interview rounds and rehearse them out loud. The teleprompter came from wanting to stop reading slides.

## What you get

**A teleprompter that listens.** On the presenter screen, press `m` and speak. It finds your place in the notes for the current key press as you talk, dims what you've already said, bolds the phrase you marked to land next, and scrolls with you. Paraphrase, skip ahead or go back to a point you missed: it follows forward, rolls back when you return to skipped material, and ignores off-script chatter. Over a few rehearsals it learns which paragraphs you keep skipping and folds them away.

**A presenter workflow built around key presses.** Speaker notes are written per key press, not per slide, so the notes always match what's on screen. Open the deck twice: press `p` in one window and it becomes the notes screen, linked to the other over a `BroadcastChannel`, and either window drives both. A case map (`c`) jumps between stories, a scroll view (`s`) reads like a document, and `?print-pdf` makes a leave-behind with every step showing.

**Software versioned apart from content.** Three layers:

| Layer | Where | Changes when |
|---|---|---|
| Engine | `engine/`, `VERSION`, `CHANGELOG.md` | You want the software to behave differently. One copy; every deck gets it on its next build. |
| Library | `library/`, or any folder a deck lists in `LIBRARIES` | A scene or case is worth reusing. Grows over time. |
| Deck | your own folder | You're preparing one presentation. |

A deck pins the engine's major version (`ENGINE = 2`). A newer minor version arrives on the next build; a new major version stops the build with the migration note from the changelog. Built pages carry `<meta name="generator" content="story-deck 2.3.0">`.

**Checks you can trust.** `check.py` seeds a mistake in a deck for each build guard and confirms the build stops, runs the teleprompter's matching tests, and walks every registered deck key press by key press in Chrome, comparing each settled state with a reference screenshot.

## Requirements

- Python 3.9 or later (standard library only)
- Node 18 or later and Google Chrome, for the screenshot harness and PDF export
- The voice teleprompter uses the dictation capability of the claude.ai Artifact runtime, so it listens only in a deck published as a claude.ai Artifact and opened in Chrome. Everywhere else the notes screen works the same, without voice tracking.
- Reveal.js, GSAP and Google Fonts load from public CDNs at view time.

## Install

As a Claude Code plugin (adds the `story-deck` skill, which runs the steps below for you):

```
/plugin marketplace add designisagoodidea-2026/story-deck
/plugin install story-deck@story-deck
```

Or clone it:

```bash
cd "$HOME" && git clone https://github.com/designisagoodidea-2026/story-deck.git && cd story-deck/harness && npm ci
```

## Quick start

```bash
cd "$HOME/story-deck" && python3 -I -B new.py ../my-deck --company "Example Co" --name "Sam Rivera" --title "Head of Design"
```

This copies a small two-case starter (from `harness/fixture/`) into `../my-deck`: `deck.py` lists the slides, `notes.py` holds the speaker notes, and `library/` holds the deck's own cases and scenes.

```bash
cd "$HOME/story-deck" && python3 -I -B build.py ../my-deck
```

Open `../my-deck/example-co-story-deck.html` in Chrome. Arrow keys step through; `n` shows the keyboard help.

## Making a deck yours

- **Order and pick slides** in `SCENES` in `deck.py`: `S(id, use="<case>/<scene>")`.
- **Change words** per slide: `S(..., label=..., q=..., claim=..., cap=...)` for the footer label, the question it answers, the headline and the caption; `text={field: value}` for a scene's own fields (listed in its `scene.py` `TEXT`). `{name}`, `{first}`, `{title}`, `{company}` and `{team}` fill in from `AUDIENCE`.
- **Notes** go in `notes.py`, one step per key press: `P` is spoken, `D` is detail you know but don't say, `Q` is a question heading. `emphasis.py` lists phrases the teleprompter bolds; the build stops if one isn't in the notes.
- **A case** is a folder with `case.py` (name, card text, recap), `case.js` (its animated vignette, drawn in a 400 by 210 frame) and `case.css` (its colors). **A scene** is a folder with `scene.py` (defaults: label, question, headline, text fields, notes) and usually `scene.js`, which registers `Scene.def(id, { build, anim, enter, state, frag })`. The engine calls scenes only through that object.
- **Shared components** need no code: `CODE = "cases"` (case map), `"context"` (where, when, team, role, then the problem), `"thennow"` (then, and what you'd do today on a key press), `"closing"` (three takeaways and a cameo) and `"thanks"`.
- **Options** in `deck.py`, all off by default: `CAPTIONS` (a caption under each headline), `CHAPTERS` (a logo transition between cases), `LEAVE_BEHIND` (short headlines and captions, for a deck people also read), `CASE_TEXT` (a case card's name, tags and recap for this deck), `group=` (an appendix), `FORBID` (names from earlier decks that must not appear).
- **Look**: `deck.css` overrides tokens, for example `:root { --claim-size: 84px; --q-label: "From the JD"; }`. Everything sits on a 12-column grid.
- **Art**: `art/` holds an illustrated cast of invented people (`face-*`, `body-*`), drawn by `person()` and `im()`. A deck's own `art/` adds to it; a file with the same name replaces the kit's.

## Changing the engine

Edit `engine/engine.html` (or `engine/teleprompter.js` and its test), bump `VERSION` (patch for a fix, minor for a feature, major when decks or scenes must change), add a line to `CHANGELOG.md` (a major one starts with `Migration:`), and run:

```bash
cd "$HOME/story-deck" && python3 -I -B check.py
```

If the screenshot harness flags slides you meant to change, look at the before and after in `harness/test-results/`, then recapture with `python3 -I -B check.py --update-refs fixture`. To guard your own deck, add it to `harness/decks.json` and capture its references once you're happy with it. A Chrome update can move a few pixels; `harness/refs/CHROME` records the version the references came from.

## Keyboard

| Key | Does |
|---|---|
| Arrows, space, clicker | Step through key presses and slides |
| `n` / `Shift+n` | Keyboard help / notes drawer |
| `p` | This window becomes the notes screen |
| `m` | Voice teleprompter, on the notes screen |
| `Esc` | Leave the notes screen |
| `s` | Scroll view |
| `c` | Case map |
| `g` | 12-column grid overlay |

## How it was made

I designed this and shipped it by directing Claude: I set the architecture (the three layers, the scene contract, versioning, the screenshot proof), made the trade-off calls and reviewed each step, and Claude wrote most of the code. It began as a single interview deck and became a kit once a second deck needed the same features.

## License

Code: MIT (`LICENSE`). The illustrated cast in `art/`: CC BY 4.0, with a note on how it was made (`art/LICENSE.md`). `engine/reveal-6.0.1.css` is from reveal.js (MIT).
