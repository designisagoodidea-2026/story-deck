// Teleprompter matcher: finds where the speaker is in the notes from the last few spoken words.
// Pure functions, no DOM; build.py inlines this file, teleprompter.test.js runs it in Node.
const Tele = (() => {
  const STOP = new Set("a an and are as at be but by for from had has have i i'd i'm in is it it's its of on or our so that the their then there they this to was we were what when where which who with would you your".split(" "));
  const norm = w => w.toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9']/g, "").replace(/^'+|'+$/g, "");
  // Words with their character spans, so the page can wrap each one in a span.
  function words(text) {
    const out = []; const re = /[A-Za-z0-9’'&.%-]+/g; let m;
    while ((m = re.exec(text))) for (const part of m[0].split(/(?<=[0-9A-Za-z])[-.](?=[A-Za-z])/)) { const n = norm(part); if (n) out.push(n); }
    return out;
  }
  // Same word, or the same stem (plural, tense) for longer words
  const same = (a, b) => a === b || (a.length >= 5 && b.length >= 5 && a.slice(0, 5) === b.slice(0, 5) && Math.abs(a.length - b.length) <= 3);
  const weight = w => (STOP.has(w) ? 0.35 : 1);

  // Local alignment of spoken words S against notes[from..]: the best alignment that ends on one of the newest
  // spoken words, on a matched note word whose index passes ok(end). cost(end) penalizes distance.
  // Returns {end, hits, score} or null; hits are the note indices actually matched (words jumped over are not hits).
  function search(notes, S, from, ok, cost, MIN) {
    const N = notes.length - from, rows = [new Float64Array(N + 1)]; let best = { score: 0, i: 0, j: 0 };
    for (let i = 1; i <= S.length; i++) {
      const prev = rows[i - 1], cur = new Float64Array(N + 1);
      for (let j = 1; j <= N; j++) {
        const nw = notes[from + j - 1], hit = same(S[i - 1], nw);
        cur[j] = Math.max(0, prev[j - 1] + (hit ? weight(nw) : -0.6), prev[j] - 0.5, cur[j - 1] - 0.5);
        if (hit && i >= S.length - 1 && ok(from + j - 1)) {
          const sc = cur[j] - cost(from + j - 1);
          if (sc > best.score) best = { score: sc, i, j };
        }
      }
      rows.push(cur);
    }
    if (best.score < MIN) return null;
    const hits = []; let i = best.i, j = best.j;
    while (i > 0 && j > 0 && rows[i][j] > 0) {
      const nw = notes[from + j - 1], hit = same(S[i - 1], nw), v = rows[i][j];
      if (v === rows[i - 1][j - 1] + (hit ? weight(nw) : -0.6)) { if (hit) hits.push(from + j - 1); i--; j--; }
      else if (v === rows[i - 1][j] - 0.5) i--;
      else j--;
    }
    return { end: from + best.j - 1, hits: hits.reverse(), score: best.score };
  }

  // Forward: notes are normalized note words, cursor the index of the first unspoken word, spoken the spoken words.
  // Moves the cursor just past the matched words, skips allowed. Returns {cursor, hits}; never moves backward.
  function align(notes, cursor, spoken, opts = {}) {
    const K = opts.tail ?? 7, JUMP_COST = opts.jumpCost ?? 0.004;
    const S = spoken.slice(-K); if (S.length < 2 || cursor >= notes.length) return { cursor, hits: [] };
    // look back so a phrase spanning the cursor keeps its earlier matches
    const r = search(notes, S, Math.max(0, cursor - 2 * K), end => end >= cursor, end => JUMP_COST * (end - cursor), opts.min ?? 2.0);
    return r ? { cursor: r.end + 1, hits: r.hits } : { cursor, hits: [] };
  }
  const advance = (notes, cursor, spoken, opts) => align(notes, cursor, spoken, opts).cursor;

  // Backward: you went back to an earlier part. Needs stronger evidence than going forward (a higher score and at
  // least three matched content words), and only lands on words you haven't said, so repeating an earlier line
  // ("as I said before...") never rolls the place back. said(i) tells whether note word i was already spoken.
  function relocate(notes, cursor, spoken, said, opts = {}) {
    const K = opts.tail ?? 8, S = spoken.slice(-K); if (S.length < 4) return null;
    const r = search(notes, S, 0, end => end < cursor - 1 && !said(end), end => 0.002 * (cursor - end), opts.min ?? 3.4);
    if (!r || r.hits.filter(h => !STOP.has(notes[h])).length < 3) return null;
    return { cursor: r.end + 1, hits: r.hits };
  }
  return { words, align, advance, relocate, norm };
})();
if (typeof module !== "undefined") module.exports = Tele;
