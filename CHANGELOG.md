# Story deck engine changelog

One section per version. MAJOR: a deck or scene must change (starts with a `Migration:` line). MINOR: new engine feature, decks unaffected. PATCH: a fix. Every change bumps `VERSION`, adds a line here, and runs `check.py`.

## 2.3.0

First public release.

- Engine: reveal.js slides on a 12-column grid, GSAP motion, headline line reveals, case vignettes, a scroll view, a case map and a print/PDF view (`?print-pdf`, or `harness/pdf.js`).
- Presenter: notes per key press, a second window as the notes screen (`p`), and a voice teleprompter (`m`) that follows your place, dims what you've said, bolds marked phrases and learns which paragraphs you skip. Voice tracking uses the claude.ai Artifact runtime's dictation.
- Shared components: case map, context, then and today, closing with a cameo, thank you.
- Deck options: captions, chapter transitions, leave-behind word limits, per-deck case card text and tags, appendix groups, `deck.css` token overrides, `LIBRARIES` for a deck's own cases and scenes.
- Build guards: unknown scenes and text fields, cases missing from `CASES`, engine version, forbidden names from earlier decks, emphasis phrases missing from the notes.
- `check.py`: seeded guard tests, the teleprompter's matching tests, and a screenshot harness over every scene and key press.

## 2.0.0

Migration: a deck lists `ENGINE = 2`, an `AUDIENCE` block, `CASES`, and `SCENES` entries that point at library scenes with `use=`. Anything the library doesn't have goes in the deck's own `scenes/` or a folder named in `LIBRARIES`.
