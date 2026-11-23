"""Speaker notes for the test deck. One step per key press."""


def P(*xs): return [{"t": "p", "x": x} for x in xs]
def D(*xs): return [{"t": "d", "x": x} for x in xs]
def step(label, *parts): return {"label": label, "items": sum(parts, [])}
def one(*parts): return [step("This slide", *parts)]


NOTES = {
    "hello": one(P("I set up how teams run, often as the first person doing it. This deck walks through two short cases."), D("A detail the audience never sees.")),
    "cases": one(P("Two cases, each with the situation, the work and how I would do it today.")),
    "a-context": one(P("The first case is Alpha Studio, a forty person team with no shared intake.")),
    "a-team": [step("The team", P("Six people across three groups, each with its own way of taking on work.")),
               step("The change", P("One intake form and one weekly review brought the groups onto a single queue."))],
    "a-today": [step("Then", P("Back then the intake and the review were run by hand every week.")),
                step("Today", P("Today an agent drafts the intake and a person confirms it before review."))],
    "a-close": one(P("The lesson from Alpha is to start with a practice the team wants, and measure it.")),
    "b-context": one(P("The second case is Beta Works, where rituals had drifted apart across two offices.")),
    "b-close": one(P("The lesson from Beta is that one shared rhythm beats many good local ones.")),
    "thanks": one(P("Thank you. Happy to go deeper on either case.")),
}
