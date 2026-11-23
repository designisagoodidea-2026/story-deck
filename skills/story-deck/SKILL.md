---
name: story-deck
description: Create and iterate on an illustrated, animated case-study presentation (one HTML page) with a presenter screen and a voice-following teleprompter, using the story deck kit. Use when someone asks for a "story deck", "case-study deck" or "interview deck", wants to change how the presentation software behaves, or wants to add a reusable scene or case.
---

# Story deck

The kit is this plugin's root: two folders up from this skill's base directory (`<base>/../..`), holding `build.py`, `new.py`, `check.py`, `engine/`, `library/` and `README.md`. Call it `KIT`. Read `KIT/README.md` before the first deck in a session.

Three layers. Decide which one a request touches before editing anything:

| The person asks for | Layer | Do |
|---|---|---|
| A new deck | deck | Sections 1 to 4 |
| Different words, order, notes, a slide of their own | deck | Section 2 |
| The software to behave differently (keys, presenter screen, transitions, motion, teleprompter) | engine | Section 5 |
| A scene or case reused across decks | library | Section 6 |

## 1. Start a deck

Ask for what you can't infer: the audience (company, person, title), what each story should answer, and the one or two things they want the audience to leave with. Don't invent facts, figures or quotes; ask.

```bash
cd "<KIT>" && python3 -I -B new.py "<deck folder>" --company "<Company>" --name "<First Last>" --title "<Title>"
```

The deck starts as a two-case example. Its `library/` folder holds the deck's own cases and scenes (`LIBRARIES = ["library"]` in `deck.py`); rename and rewrite them.

## 2. Iterate

All edits happen in the deck folder (README, "Making a deck yours"):

- `deck.py`: order `SCENES`, override `label`, `q`, `claim`, `cap` and `text={...}` per slide, set options (`CAPTIONS`, `CHAPTERS`, `LEAVE_BEHIND`, `CASE_TEXT`, `group=`).
- `notes.py`: one step per key press. The build lists slides with no notes.
- `emphasis.py`: phrases from the spoken notes for the teleprompter to bold; the build stops if one isn't in the notes.
- A new scene: copy the closest existing scene folder, keep its structure, change its `ID` to match its new folder path.

## 3. Build and preview

```bash
cd "<KIT>" && python3 -I -B build.py "<deck folder>"
```

Open the built page in Chrome and step through every slide and key press. Open the notes drawer (`Shift+n`) and the notes screen (`p`), and check the browser console.

## 4. Present and rehearse

Open the page twice; press `p` in the window on your own screen. Voice tracking (`m`) works when the page is published as a claude.ai Artifact and opened in Chrome; elsewhere the notes screen works without it. For a leave-behind PDF: `node harness/pdf.js <built page> <out.pdf>` from `KIT/harness` (after `npm ci` there).

## 5. Changing the engine

Engine changes never go in a deck. Edit `KIT/engine/engine.html` (or `engine/teleprompter.js` with its test), bump `KIT/VERSION` (patch fix, minor feature, major when decks or scenes must change), add a `CHANGELOG.md` line (a major one starts `Migration:`), then run `cd "<KIT>" && python3 -I -B check.py`. If the harness flags slides the change was meant to move, show the person the before and after (`harness/test-results/`) and recapture only on their OK: `python3 -I -B check.py --update-refs <deck>`.

## 6. Growing a library

A scene worth reusing moves from a deck's `scenes/` or `library/` into a shared library folder (the kit's `library/`, or a folder several decks list in `LIBRARIES`). Its words should come from `TEXT` fields or `{company}`-style placeholders, not one audience's names. A new case needs `case.py`, `case.js` (its vignette) and `case.css` (its colors). Run `check.py` after.

## Rules

- `check.py` must pass before an engine or library change is called done.
- Start new decks with `new.py`, never by copying another deck's folder: earlier audiences' names travel with copies (`FORBID` in `deck.py` catches them).
