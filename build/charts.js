(() => {
  const tip = document.getElementById("tip");
  const showTip = (ev, text) => {
    tip.textContent = text; tip.style.opacity = 1;
    const x = Math.min(ev.clientX + 14, innerWidth - tip.offsetWidth - 8);
    const y = ev.clientY + 16 + tip.offsetHeight > innerHeight ? ev.clientY - tip.offsetHeight - 10 : ev.clientY + 16;
    tip.style.left = x + "px"; tip.style.top = y + "px";
  };
  const hideTip = () => { tip.style.opacity = 0; };
  document.querySelectorAll("[data-tip]").forEach(el => {
    el.addEventListener("pointermove", ev => showTip(ev, el.dataset.tip));
    el.addEventListener("pointerleave", hideTip);
  });
  if (!window.d3) return;  // the force and scatter charts need d3; the unit bar chart is plain HTML

  // Glyphs stand on the baseline and are about 0.68em tall, so shift down to center one on a point.
  const LIFT = 0.34;
  const legend = (id, items) => {
    document.getElementById(id).innerHTML = items.map(([label, color, ch]) =>
      `<li><span class="lilpuppies" style="color:${color}" aria-hidden="true">${ch}</span>${label}</li>`).join("");
  };

  // ---- Force layout: 100 dogs ----
  {
    const svg = d3.select("#force"), W = 960, H = 400, SIZE = 34, R = 17;
    const OUT = [
      { key: "Adopted", n: 58, color: "var(--s1)" },
      { key: "In foster care", n: 27, color: "var(--s2)" },
      { key: "Waiting", n: 15, color: "var(--s3)" },
    ];
    legend("force-legend", OUT.map(o => [`${o.key} (${o.n})`, o.color, "Q"]));
    const nodes = [];
    OUT.forEach((o, gi) => { for (let i = 0; i < o.n; i++) nodes.push({ g: gi }); });
    // Deterministic pseudo-random start so the pack looks the same on every load.
    let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    nodes.forEach((d, i) => {
      d.b = BREEDS[(i * 17) % BREEDS.length];
      const a = rnd() * Math.PI * 2, r = rnd() * 160;
      d.x = W / 2 + Math.cos(a) * r; d.y = H / 2 + Math.sin(a) * r;
    });
    // Cluster centers for split mode; each cluster's width grows with the square root of its count.
    const cx = [0.29, 0.65, 0.875].map(f => f * W);
    const labels = svg.append("g");
    const dogs = svg.append("g").selectAll("text").data(nodes).join("text")
      .attr("class", "dog").attr("text-anchor", "middle").attr("font-size", SIZE)
      .attr("fill", d => OUT[d.g].color).text(d => d.b.c)
      .on("pointermove", (ev, d) => showTip(ev, `${d.b.breed} · ${OUT[d.g].key}`))
      .on("pointerleave", hideTip);
    const sim = d3.forceSimulation(nodes)
      .force("collide", d3.forceCollide(R).strength(0.9))
      .on("tick", () => dogs.attr("x", d => d.x).attr("y", d => d.y + SIZE * LIFT));
    const setMode = mode => {
      const split = mode === "split";
      sim.force("x", d3.forceX(d => split ? cx[d.g] : W / 2).strength(split ? 0.12 : 0.06))
         .force("y", d3.forceY(H / 2 + (split ? 14 : 0)).strength(split ? 0.12 : 0.06))
         .alpha(1).restart();
      labels.selectAll("text").data(split ? OUT : []).join("text").attr("class", "clabel")
        .attr("text-anchor", "middle").attr("x", (o, i) => cx[i]).attr("y", 16)
        .text(o => o.key).append("tspan").attr("dx", 6).text(o => o.n);
      document.querySelectorAll(".vbtns button").forEach(b => b.setAttribute("aria-pressed", b.dataset.mode === mode));
    };
    document.querySelectorAll(".vbtns button").forEach(b => b.addEventListener("click", () => setMode(b.dataset.mode)));
    setMode("pack");
  }

  // ---- Scatter: weight vs lifespan ----
  {
    const svg = d3.select("#scatter"), W = 960, H = 540, SIZE = 30;
    const m = { top: 16, right: 24, bottom: 52, left: 56 };
    const COLORED = { Hound: "var(--s1)", Working: "var(--s2)", Toy: "var(--s3)" };
    const color = g => COLORED[g] || "var(--other)";
    legend("scatter-legend", [
      ["Hound", COLORED.Hound, "A"], ["Working", COLORED.Working, "N"], ["Toy", COLORED.Toy, "C"],
      ["Other groups", "var(--other)", "U"],
    ]);
    const x = d3.scaleLog().domain([1.5, 90]).range([m.left, W - m.right]);
    const y = d3.scaleLinear().domain([6.5, 17]).range([H - m.bottom, m.top]);
    svg.append("g").attr("class", "grid").selectAll("line").data(y.ticks(6)).join("line")
      .attr("x1", m.left).attr("x2", W - m.right).attr("y1", d => y(d)).attr("y2", d => y(d));
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${H - m.bottom})`)
      .call(d3.axisBottom(x).tickValues([2, 5, 10, 20, 50]).tickFormat(d => d + " kg").tickSizeOuter(0));
    svg.append("g").attr("class", "axis").attr("transform", `translate(${m.left},0)`)
      .call(d3.axisLeft(y).ticks(6).tickFormat(d => d + " yr").tickSizeOuter(0)).call(g => g.select(".domain").remove());
    svg.append("text").attr("class", "note").attr("x", W - m.right).attr("y", H - 10).attr("text-anchor", "end")
      .text("Typical adult weight (log scale) →");
    svg.append("text").attr("class", "note").attr("x", m.left + 6).attr("y", m.top + 4).text("↑ Typical lifespan");
    // Colored breeds draw on top of the gray ones.
    const data = BREEDS.map(b => ({ ...b, tx: x(b.kg), ty: y(b.yrs) }))
      .sort((a, b) => (a.group in COLORED) - (b.group in COLORED));
    data.forEach(d => { d.x = d.tx; d.y = d.ty; });
    // Settle once, without animation: pull each dog to its true point, push overlapping dogs apart.
    const sim = d3.forceSimulation(data).stop()
      .force("x", d3.forceX(d => d.tx).strength(0.5)).force("y", d3.forceY(d => d.ty).strength(0.5))
      .force("collide", d3.forceCollide(13));
    for (let i = 0; i < 200; i++) sim.tick();
    svg.append("g").selectAll("text").data(data).join("text")
      .attr("class", "dog").attr("text-anchor", "middle").attr("font-size", SIZE)
      .attr("x", d => d.x).attr("y", d => d.y + SIZE * LIFT).attr("fill", d => color(d.group)).text(d => d.c)
      .on("pointermove", (ev, d) => showTip(ev, `${d.breed} (${d.group}) · ${d.kg} kg · ${d.yrs} yr`))
      .on("pointerleave", hideTip);
    // A few direct labels for the extremes: [label, dx, dy, anchor] relative to the dog.
    const call = { C: ["Chihuahua", 18, 4, "start"], z: ["St. Bernard", 0, -16, "middle"], I: ["Irish Wolfhound", -18, 4, "end"] };
    svg.append("g").selectAll("text").data(data.filter(d => d.c in call)).join("text")
      .attr("class", "note").attr("x", d => d.x + call[d.c][1]).attr("y", d => d.y + call[d.c][2])
      .attr("text-anchor", d => call[d.c][3]).text(d => call[d.c][0]);
  }
})();
