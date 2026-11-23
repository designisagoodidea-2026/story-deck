Scene.def("alpha/team", {
  build(v, sec, D) {
    const s = svg(1500, 400); v.appendChild(s);
    [0, 1, 2].forEach(g => {
      el(s, "rect", { x: X(g * 4), y: 40, width: W(4), height: 220, rx: 16, class: "box" });
      label(s, X(g * 4) + 24, 76, ["Research", "Product design", "Content"][g], "lbl h3s");
      [0, 1].forEach(i => person(s, X(g * 4) + 120 + i * 190, 200, "acc", undefined, 92));
    });
    v.insertAdjacentHTML("beforeend", `<p class="queue fragment">One intake form, one weekly review, one queue.</p>`);
  },
  anim(v, tl, D) { tl.from(v.querySelectorAll(".box"), { opacity: 0, y: 14, stagger: 0.1, duration: 0.4, ease: "expo.out" }); },
});
