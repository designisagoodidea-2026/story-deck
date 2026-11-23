"""Test: then and today, on the engine's thennow component."""
ID = "alpha/today"
CASE = "alpha"
CODE = "thennow"
LABEL = "Alpha Studio · Today"
Q = "How would you do that today?"
CLAIM = "The same intake, today: <em>agents draft, people decide</em>."
CAP = "Then on the left; a key press shows today."
TODAY = True
TEXT = {"step": 0, "steps": ["Intake", "Review"], "then_label": "Then", "now_label": "What I'd explore today",
        "then": ["Intake by email", "Review notes by hand"],
        "now": [["agent", "Drafts the intake from the request"], ["person", "A lead confirms it"], ["agent", "Drafts the review notes"]]}
NOTES = None
EMPH = []
