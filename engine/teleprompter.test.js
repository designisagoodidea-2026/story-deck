// node teleprompter.test.js  (from deck/) — checks the matcher on a sample paragraph
const assert = require("assert");
const T = require("./teleprompter.js");
const text = "At Harbor I was the first design program manager in the Freight business: about 120 internal tools for planning, routing and tracking shipments, and a 30-person design team. Freight had tried design systems before, but adoption stayed limited and none fit the whole Freight.";
const notes = T.words(text);
const at = w => notes.indexOf(w);

// Feed speech a few words at a time, the way partial results arrive
function speak(said, cursor = 0) {
  const sp = T.words(said); let c = cursor;
  for (let n = 2; n <= sp.length; n++) c = T.advance(notes, c, sp.slice(0, n));
  return c;
}

// 1. Read verbatim: the cursor ends just past the last word spoken
assert.strictEqual(speak("At Harbor I was the first design program manager in the Freight business"), at("business") + 1);

// 2. Paraphrase: loose wording still tracks
assert(speak("so at Harbor I was the very first program manager for design in Freight") >= at("freight") + 1);

// 3. Skip a whole section: jump from the opening to the last sentence
let c = speak("At Harbor I was the first design program manager");
c = speak("At Harbor I was the first design program manager. Anyway freight had tried design systems before", c);
assert.strictEqual(c, at("before") + 1);

// 4. Off-script chatter (or silence) does not move the cursor
const c0 = speak("At Harbor I was the first design program manager");
assert.strictEqual(T.advance(notes, c0, T.words("um sorry can you hear me okay")), c0);
assert.strictEqual(T.advance(notes, c0, []), c0);

// 5. Never moves backward when you repeat an earlier phrase
const c1 = speak("about 120 internal tools for planning routing and tracking shipments");
assert.strictEqual(T.advance(notes, c1, T.words("at Harbor I was the first")), c1);

// 6. Numbers and hyphens split the same way on both sides
assert.deepStrictEqual(T.words("a 30-person design team, Material-UI, 4.7 out of 5"), ["a", "30", "person", "design", "team", "material", "ui", "47", "out", "of", "5"]);
console.log("teleprompter: 6 checks passed");

// 7. Hits are the words actually said: after a skip, the skipped middle is not a hit
{
  const said = new Set(); let c = 0;
  const run = t => { const sp = T.words(t); for (let n = 2; n <= sp.length; n++) { const r = T.align(notes, c, sp.slice(0, n)); r.hits.forEach(h => said.add(h)); c = r.cursor; } };
  run("At Harbor I was the first design program manager. Anyway freight had tried design systems before");
  assert(said.has(at("harbor")) && said.has(at("before")), "spoken words are hits");
  assert(!said.has(at("internal")) && !said.has(at("shipments")), "skipped words are not hits");
  console.log("teleprompter: hits check passed");
}

// 8. Going back: skip ahead, then speak the skipped middle; the place rolls back to it
{
  let c = speak("At Harbor I was the first design program manager. Anyway freight had tried design systems before");
  assert.strictEqual(c, at("before") + 1);
  const said = new Set([at("harbor"), at("first"), at("design"), at("program"), at("manager"), at("freight") /* first freight */, at("tried"), at("systems"), at("before")]);
  const back = T.relocate(notes, c, T.words("about 120 internal tools for planning routing and tracking shipments"), i => said.has(i));
  assert(back && back.cursor === at("shipments") + 1, "rolls back to the skipped part you're now saying");
  // repeating a line you already said does not roll back
  assert.strictEqual(T.relocate(notes, c, T.words("at Harbor I was the first design program manager"), i => i <= at("manager")), null, "a repeat is not a rollback");
  // short or off-script speech does not roll back
  assert.strictEqual(T.relocate(notes, c, T.words("tools for planning"), () => false), null, "too little evidence");
  assert.strictEqual(T.relocate(notes, c, T.words("um sorry where was I with all of this"), () => false), null, "chatter");
  console.log("teleprompter: rollback checks passed");
}
