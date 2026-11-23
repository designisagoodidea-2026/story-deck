"""Test deck for check.py and the screenshot harness: two invented cases that exercise the engine's features.
Not a showcase. Build: python3 -I -B build.py harness/fixture (from the kit folder)"""
ENGINE = 2
TITLE = "Fixture Story Deck"
OUT = "fixture-story-deck.html"
AUDIENCE = {"name": "Sam Rivera", "first": "Sam", "title": "Head of Design", "company": "Example Co", "team": 40}
FOOTER = "Test deck · for {name}, {company}"
CHANNEL = "fixture-deck-notes"
LIBRARIES = ["library"]  # this deck's own cases and scenes
CASES = ["alpha", "beta"]
CASE_TEXT = {"alpha": {"tags": ["Operating model", "Intake"]}, "beta": {"tags": ["Rituals"]}}
CAPTIONS = True
CHAPTERS = True
LEAVE_BEHIND = True
FORBID = []
ALSO = [["thanks", "Skip to the end"]]


def S(id, use, **over):
    return dict(id=id, use=use, **over)


SCENES = [
 S("hello", use="opening/hello"),
 S("cases", use="deck/cases", active="0", label="Two stories", claim="Two stories, each with <em>how I'd do it today</em>.", text={"also": ALSO}),
 S("a-context", use="alpha/context"),
 S("a-team", use="alpha/team"),
 S("a-today", use="alpha/today"),
 S("a-close", use="alpha/close"),
 S("b-context", use="beta/context"),
 S("b-close", use="beta/close"),
 S("thanks", use="deck/thanks", claim="Thank you.", text={"contact": "<b>Test deck</b> · example.com"}),
]
