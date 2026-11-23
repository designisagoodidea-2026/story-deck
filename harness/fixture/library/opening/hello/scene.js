Scene.def("opening/hello", {
  build(v, sec, D) {
    v.innerHTML = `<ol class="hello">${D.text.lines.map((t, i) => `<li><img src="${ART["face-0" + (i + 2)]}" alt=""><span>${esc(t)}</span></li>`).join("")}</ol>`;
  },
  anim(v, tl, D) { tl.from(v.querySelectorAll(".hello li"), { y: 20, opacity: 0, stagger: 0.1, duration: 0.5, ease: "expo.out" }); },
});
