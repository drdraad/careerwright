// Renders the route comparison from fixture data: TRACE-01 (economic-cost mode) for the
// default and failure states, DIRECTAI (direct-spending mode) for the unknown state.
// Layers are recomputed by peeling and checked against the fixture's expected fronts;
// a mismatch is logged as a console error, which fails tools/screenshots.mjs.
(function () {
  const { FIXTURES: F, state, fmt } = window.NESSA;
  const SVG = "http://www.w3.org/2000/svg";
  const gbp = (minor) => fmt.gbp(minor);

  function el(name, attrs = {}, parent) {
    const node = document.createElementNS(SVG, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (parent) parent.appendChild(node);
    return node;
  }
  function text(parent, x, y, content, cls, anchor = "start") {
    const t = el("text", { x, y, class: cls, "text-anchor": anchor }, parent);
    t.textContent = content;
    return t;
  }

  // ---------- Data for the state ----------
  const TRACE_NAMES = {
    A: "Intensive course with a 2-month study break",
    B: "Evening course, keeping full hours",
    C: "Day-release course on reduced hours",
    D: "Evening course with higher fees",
    E: "Longer evening course",
  };
  const economic = state !== "unknown";
  const t = F.trace01;
  const routes = economic
    ? t.routes.map((r) => ({ ...r, cost: r.economicMinor, layer: t.fronts.findIndex((f) => f.includes(r.id)) + 1, name: TRACE_NAMES[r.id] }))
    : F.directai.routes.map((r) => ({ ...r, cost: r.directMinor, name: `Route ${r.id}` }));
  const selectedId = economic ? t.selectedRoute : "B";

  // Independent peeling: p dominates q iff no worse on both and different.
  const dominates = (p, q) => p.timeMonths <= q.timeMonths && p.cost <= q.cost && (p.timeMonths !== q.timeMonths || p.cost !== q.cost);
  (function checkLayers() {
    let rest = routes.slice();
    let layer = 1;
    while (rest.length) {
      const front = rest.filter((q) => !rest.some((p) => dominates(p, q)));
      for (const r of front) if (r.layer !== layer) console.error(`layer mismatch for ${r.id}: fixture ${r.layer}, peeled ${layer}`);
      rest = rest.filter((r) => !front.includes(r));
      layer += 1;
    }
  })();

  // Declared comparator rule: among the routes that dominate this one, name the cheapest;
  // ties go to the shorter time, then the route ID. The others are listed after it.
  function comparison(route) {
    const doms = routes.filter((p) => dominates(p, route)).sort((a, b) => a.cost - b.cost || a.timeMonths - b.timeMonths || a.id.localeCompare(b.id));
    if (!doms.length) return null;
    const [c, ...others] = doms;
    const months = route.timeMonths - c.timeMonths;
    const saving = route.cost - c.cost;
    const timePart = months === 0 ? `for the same ${route.timeMonths} months` : `${months} month${months === 1 ? "" : "s"} faster`;
    const costPart = saving === 0 ? "at the same cost" : `${gbp(saving)} cheaper`;
    const basis = economic ? "economic cost" : "direct spending";
    const lead = months === 0 ? `Route ${c.id} is as fast and ${gbp(saving)} cheaper in ${basis}`
      : saving === 0 ? `Route ${c.id} is ${timePart} at the same ${basis}`
      : `Route ${c.id} is ${timePart} and ${costPart} in ${basis}`;
    return { text: `${lead}.`, others: others.map((o) => o.id) };
  }

  function paymentPattern(r) {
    const nonzero = r.paymentsMinor.map((p, i) => [p, i]).filter(([p]) => p > 0);
    if (nonzero.length === 1) return `${gbp(nonzero[0][0])} due in ${fmt.monthName(nonzero[0][1])}`;
    if (nonzero.every(([p]) => p === nonzero[0][0])) return `${gbp(nonzero[0][0])} a month for ${nonzero.length} months`;
    return `${nonzero.map(([p]) => gbp(p)).join(", ")} from ${fmt.monthName(nonzero[0][1])}`;
  }

  // ---------- Chart ----------
  function renderChart() {
    const svg = document.querySelector("#tradeoff");
    const W = 860, H = 400, L = 70, R = 28, T = 36, B = 54;
    const xMax = economic ? 6 : 18;
    const yMax = economic ? 600000 : 700000;
    const yStep = economic ? 150000 : 100000;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const x = (m) => L + (m / xMax) * (W - L - R);
    const y = (c) => H - B - (c / yMax) * (H - T - B);
    for (let c = 0; c <= yMax; c += yStep) {
      el("line", { x1: L, x2: W - R, y1: y(c), y2: y(c), class: "gridline" }, svg);
      text(svg, L - 10, y(c) + 4, gbp(c), "axis-text", "end");
    }
    for (let m = 0; m <= xMax; m += economic ? 1 : 2) text(svg, x(m), H - B + 20, String(m), "axis-text", "middle");
    text(svg, (L + W - R) / 2, H - 8, "Months until you can apply", "axis-title", "middle");
    text(svg, 4, 14, economic ? "Economic cost, pounds" : "Direct spending, pounds", "axis-title", "start");

    // Staircase through front 1: a reading aid, labelled as such.
    const f1 = routes.filter((r) => r.layer === 1).sort((a, b) => a.timeMonths - b.timeMonths);
    let d = `M${x(f1[0].timeMonths)},${y(f1[0].cost)}`;
    for (let i = 1; i < f1.length; i += 1) d += ` H${x(f1[i].timeMonths)} V${y(f1[i].cost)}`;
    d += ` H${x(xMax)}`;
    // Shade the region the boundary betters, then draw the boundary over it.
    el("path", { d: `${d} V${T} H${x(f1[0].timeMonths)} Z`, class: "dominated" }, svg);
    const boundary = el("path", { d, class: "boundary" }, svg);

    // Marks first, then labels placed greedily: front 1 first, each at the first of
    // eight positions that collides with no mark, no placed label and no plot edge.
    const groups = new Map();
    for (const r of routes.slice().sort((a, b) => b.layer - a.layer)) {
      const g = el("g", { role: "img", "aria-label": `Route ${r.id}, ${r.name}: ${r.timeMonths} months, ${gbp(r.cost)}${r.layer > 1 ? `, layer ${r.layer}` : ", best trade-off"}${r.id === selectedId ? ", selected" : ""}` }, svg);
      const cx = x(r.timeMonths), cy = y(r.cost);
      if (r.layer === 1) el("circle", { cx, cy, r: 13, class: "glow" }, g);
      else el("circle", { cx, cy, r: 9.5, class: "point-halo" }, g);
      if (r.id === selectedId) el("circle", { cx, cy, r: 15, class: "point-selected", "data-mark": "" }, g);
      el("circle", { cx, cy, r: r.layer === 1 ? 7 : 5.5, class: r.layer === 1 ? "point-f1" : r.layer === 2 ? "point-f2" : "point-f3", "data-mark": "" }, g);
      groups.set(r.id, { g, cx, cy });
    }
    // A chart hidden by the phone layout has no geometry to measure; it is drawn when opened.
    if (!svg.getBoundingClientRect().width) return;
    const marks = [...svg.querySelectorAll("circle[data-mark]")].map((c) => c.getBBox());
    // Boundary segments are obstacles too, so no label is struck through by the line.
    const pts = [[x(f1[0].timeMonths), y(f1[0].cost)]];
    for (let i = 1; i < f1.length; i += 1) pts.push([x(f1[i].timeMonths), y(f1[i - 1].cost)], [x(f1[i].timeMonths), y(f1[i].cost)]);
    pts.push([x(xMax), y(f1[f1.length - 1].cost)]);
    for (let i = 1; i < pts.length; i += 1) {
      const [a, b] = [pts[i - 1], pts[i]];
      marks.push({ x: Math.min(a[0], b[0]) - 2, y: Math.min(a[1], b[1]) - 2, width: Math.abs(a[0] - b[0]) + 4, height: Math.abs(a[1] - b[1]) + 4 });
    }
    boundary.setAttribute("data-segments", String(pts.length - 1));
    const placed = [];
    const clear = (b) => b.x >= 0 && b.y >= T - 14 && b.x + b.width <= W && b.y + b.height <= H - B
      && ![...marks, ...placed].some((o) => b.x < o.x + o.width && o.x < b.x + b.width && b.y < o.y + o.height && o.y < b.y + b.height);
    for (const r of routes.slice().sort((a, b) => a.layer - b.layer || a.timeMonths - b.timeMonths)) {
      const { g, cx, cy } = groups.get(r.id);
      const k = (r.id === selectedId ? 15 : r.layer === 1 ? 7 : 5.5) + 6;
      const OFFSETS = [[k, 4, "start"], [-k, 4, "end"], [0, -k - 2, "middle"], [0, k + 12, "middle"], [k, -k + 2, "start"], [k, k + 6, "start"], [-k, -k + 2, "end"], [-k, k + 6, "end"]];
      let label;
      for (const [dx, dy, anchor] of OFFSETS) {
        label = el("text", { x: cx + dx, y: cy + dy, "text-anchor": anchor, class: `point-label${r.layer > 1 ? " later" : ""}` }, g);
        const letter = el("tspan", {}, label);
        letter.textContent = r.id;
        if (r.layer === 1) {
          const value = el("tspan", { class: "point-value", dx: 6 }, label);
          value.textContent = `${r.timeMonths} months, ${gbp(r.cost)}`;
        } else {
          const note = el("tspan", { class: "layer-note", dx: 4 }, label);
          note.textContent = `layer ${r.layer}`;
        }
        if (clear(label.getBBox())) break;
        label.remove();
        label = null;
      }
      if (!label) console.error(`no clear label position for route ${r.id}`);
      else placed.push(label.getBBox());
    }
  }

  // ---------- Cards ----------
  function card(r) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `route-card layer-${r.layer}`;
    b.setAttribute("aria-pressed", String(r.id === selectedId));
    const comp = comparison(r);
    const lines = [];
    lines.push(`<span class="route-letter" aria-hidden="true"></span>`);
    lines.push(`<span class="route-name"></span>`);
    if (comp) lines.push(`<span class="route-margin"></span>`);
    lines.push(`<span class="route-figures"></span>`);
    if (economic) lines.push(`<span class="route-detail"></span>`);
    if (comp && comp.others.length) lines.push(`<span class="route-detail" data-others></span>`);
    if (r.layer > 1) lines.push(`<span class="route-detail">Layer ${r.layer}</span>`);
    b.innerHTML = lines.join("");
    b.querySelector(".route-letter").textContent = r.id;
    b.querySelector(".route-name").textContent = economic ? `Route ${r.id}: ${r.name}` : r.name;
    if (comp) b.querySelector(".route-margin").textContent = comp.text;
    b.querySelector(".route-figures").textContent = `Ready in ${r.timeMonths} months, ${gbp(r.cost)} ${economic ? "economic cost" : "direct spending"}`;
    if (economic) {
      const lost = r.economicMinor - r.directMinor;
      b.querySelector(".route-detail").textContent = `${gbp(r.directMinor)} fees${lost ? ` plus ${gbp(lost)} pay lost` : ", no pay lost"}. ${paymentPattern(r)}.`;
    }
    if (comp && comp.others.length) b.querySelector("[data-others]").textContent = `Also bettered by route ${comp.others.join(", ")}.`;
    return b;
  }

  function renderCards() {
    const best = document.querySelector("#cards-best");
    const other = document.querySelector("#cards-other");
    const byTime = (a, b) => a.timeMonths - b.timeMonths || a.cost - b.cost;
    routes.filter((r) => r.layer === 1).sort(byTime).forEach((r) => best.appendChild(card(r)));
    routes.filter((r) => r.layer > 1).sort((a, b) => a.layer - b.layer || byTime(a, b)).forEach((r) => other.appendChild(card(r)));
  }

  // ---------- Journey (TRACE-01 selected route) ----------
  const route = economic ? t.routes.find((r) => r.id === selectedId) : null;
  const startMonth = economic ? Number(t.planningStart.slice(5, 7)) - 1 : 0;
  const startYear = Number(t.planningStart.slice(0, 4));
  const readyIndex = route ? route.timeMonths : 0;

  function renderGantt() {
    const svg = document.querySelector("#gantt");
    if (!route) return;
    const W = 1200, LABEL = 250, COL = (W - LABEL - 40) / (t.horizonMonths + 1);
    const H = 236;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const pays = route.paymentsMinor.filter((x) => x > 0);
    const readyLabel = `1 ${fmt.monthName(startMonth + readyIndex)} ${startYear + Math.floor((startMonth + readyIndex) / 12)}`;
    svg.setAttribute("aria-label", `Route ${route.id} schedule: current job kept throughout at ${route.workHoursWhileActive} hours a week; evening course from ${fmt.longDate(route.start)} to ${fmt.longDate(route.finish)} at ${route.studyHours} hours a week; ${pays.length} payments, ${paymentPattern(route)}; assessed report at the end of the course; ready to apply from ${readyLabel} if the report passes.`);
    const defs = el("defs", {}, svg);
    const pat = el("pattern", { id: "hatch", width: 6, height: 6, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
    el("rect", { width: 6, height: 6, fill: "var(--surface-card)" }, pat);
    el("line", { x1: 0, y1: 0, x2: 0, y2: 6, stroke: "var(--text-on-reading-muted)", "stroke-width": 1.6 }, pat);
    const colX = (i) => LABEL + (i + 1) * COL; // column 0 is the month before the start
    // Month headers: the month before the start, then the horizon.
    text(svg, LABEL + COL / 2, 18, `${fmt.monthName(startMonth + 11, true)} ${startMonth === 0 ? startYear - 1 : startYear}`, "gantt-month", "middle");
    for (let i = 0; i < t.horizonMonths; i += 1) {
      text(svg, colX(i) + COL / 2, 18, `${fmt.monthName(startMonth + i, true)} ${startYear + Math.floor((startMonth + i) / 12)}`, "gantt-month", "middle");
      text(svg, colX(i) + COL / 2, 34, `month ${i + 1}`, "gantt-sub", "middle");
    }
    for (let i = -1; i <= t.horizonMonths; i += 1) el("line", { x1: colX(i), x2: colX(i), y1: 42, y2: H - 8, class: "gantt-grid" }, svg);

    const rows = [
      ["Current job", `${route.workHoursWhileActive} hours a week`],
      ["Evening course", `provider B, ${route.studyHours} hours a week`],
      ["Course payments", paymentPattern(route)],
      ["Assessment and readiness", "conditional"],
    ];
    rows.forEach(([a, b], k) => {
      text(svg, 0, 70 + k * 46, a, "gantt-label");
      text(svg, 0, 88 + k * 46, b, "gantt-sub");
    });
    // Work band: the whole horizon (kept throughout).
    el("rect", { x: colX(0) + 2, y: 58, width: colX(t.horizonMonths - 1) + COL - colX(0) - 4, height: 26, rx: 6, class: "band-work" }, svg);
    text(svg, colX(0) + 12, 76, `Take-home pay ${gbp(route.incomeMinor[0])} a month, unchanged`, "band-text");
    // Study band: actual dates.
    el("rect", { x: colX(0) + 2, y: 104, width: colX(route.timeMonths - 1) + COL - colX(0) - 4, height: 26, rx: 6, class: "band-study" }, svg);
    const study = text(svg, colX(0) + 12, 122, `${fmt.longDate(route.start)} to ${fmt.longDate(route.finish)}`, "band-text");
    study.setAttribute("paint-order", "stroke");
    study.setAttribute("stroke", "var(--surface-card)");
    study.setAttribute("stroke-width", "5");
    // Payments.
    route.paymentsMinor.forEach((p, i) => {
      if (!p) return;
      el("circle", { cx: colX(i) + COL / 2, cy: 162, r: 5, fill: "var(--surface-card)", stroke: "var(--text-on-reading)", "stroke-width": 1.6 }, svg);
      text(svg, colX(i) + COL / 2 + 10, 166, gbp(p), "band-text");
    });
    // Admission already accepted before the start.
    el("circle", { cx: LABEL + COL / 2, cy: 208, r: 5, fill: "var(--text-on-reading)" }, svg);
    text(svg, LABEL + COL / 2 + 10, 212, `Admission accepted ${fmt.longDate(t.admissionCompletedOn)}`, "band-text");
    // Gate at the end of the course, readiness at the next month boundary (TIME-1).
    const gx = colX(readyIndex);
    el("path", { d: `M${gx},${196} l10,10 l-10,10 l-10,-10 z`, class: "gate" }, svg);
    text(svg, gx - 16, 212, "Assessed report", "band-text", "end");
    el("line", { x1: gx, x2: gx, y1: 46, y2: 190, class: "ready-line" }, svg);
    text(svg, gx + 8, 196, `Ready to apply from 1 ${fmt.monthName(startMonth + readyIndex)}, if the report passes`, "ready-text");
  }

  function renderTimelineMobile() {
    const list = document.querySelector("#timeline-mobile");
    if (!route) return;
    const items = [
      [fmt.longDate(t.admissionCompletedOn), "Admission accepted"],
      [`${fmt.longDate(route.start)}`, `Evening course starts, ${route.studyHours} hours a week alongside ${route.workHoursWhileActive} hours of work`],
      [`${fmt.monthName(startMonth, true)} to ${fmt.monthName(startMonth + route.timeMonths - 1, true)}`, `Course payments, ${paymentPattern(route)}`],
      [`${fmt.longDate(route.finish)}`, "Course ends with an assessed report"],
      [`1 ${fmt.monthName(startMonth + readyIndex)} ${startYear}`, "Ready to apply, if the report passes"],
    ];
    for (const [when, what] of items) {
      const li = document.createElement("li");
      li.innerHTML = '<span class="when"></span><span class="what"></span>';
      li.querySelector(".when").textContent = when;
      li.querySelector(".what").textContent = what;
      list.appendChild(li);
    }
  }

  // ---------- Ledger: conservative prefunding (TIME-1), wages arrive late ----------
  function renderLedger() {
    const body = document.querySelector("#ledger-rows");
    if (!route) return;
    let cash = t.openingCashMinor;
    const rows = route.paymentsMinor.map((pay, i) => {
      const opening = cash;
      const lower = opening - pay - t.livingByMonthMinor[i];
      cash = lower + route.incomeMinor[i];
      return { i, opening, pay, living: t.livingByMonthMinor[i], lower, income: route.incomeMinor[i], closing: cash };
    });
    const min = Math.min(...rows.map((r) => r.lower));
    if (min !== t.print.minimumPrefundedCashMinor) console.error(`ledger minimum ${min} differs from print snapshot ${t.print.minimumPrefundedCashMinor}`);
    for (const r of rows) {
      const tr = document.createElement("tr");
      const cells = [`${fmt.monthName(startMonth + r.i)} ${startYear}`, gbp(r.opening), r.pay ? `−${gbp(r.pay)}` : "£0", `−${gbp(r.living)}`, gbp(r.lower), `+${gbp(r.income)}`, gbp(r.closing)];
      tr.innerHTML = cells.map((c, k) => (k === 0 ? `<th scope="row"></th>` : `<td${k === 4 && r.lower === min ? ' class="low"' : ""}></td>`)).join("");
      [...tr.children].forEach((cell, k) => (cell.textContent = cells[k]));
      body.appendChild(tr);
    }
    document.querySelector("#ledger-min").textContent = gbp(min);
  }

  if (route) document.querySelector("#hours-used").textContent = String(route.studyHours + route.workHoursWhileActive);

  // Dominated routes that lie exactly on the comparison line (for example an equal-time
  // tie with a better route) are named, so the line is never read as "all best".
  function onBoundary(r) {
    const f1 = routes.filter((q) => q.layer === 1).sort((a, b) => a.timeMonths - b.timeMonths);
    for (let i = 1; i < f1.length; i += 1) {
      const [a, b] = [f1[i - 1], f1[i]];
      if (r.cost === a.cost && r.timeMonths > a.timeMonths && r.timeMonths < b.timeMonths) return true;
      if (r.timeMonths === b.timeMonths && r.cost < a.cost && r.cost > b.cost) return true;
    }
    const last = f1[f1.length - 1];
    return r.cost === last.cost && r.timeMonths > last.timeMonths;
  }
  function renderTieNote() {
    const ties = routes.filter((r) => r.layer > 1 && onBoundary(r));
    const node = document.querySelector("#tie-note");
    if (!ties.length) return;
    node.textContent = ties.map((r) => {
      const c = routes.filter((p) => dominates(p, r)).sort((a, b) => a.cost - b.cost)[0];
      return `Route ${r.id} sits on the line at ${r.timeMonths} months, but route ${c.id} ${c.timeMonths === r.timeMonths ? "is as fast" : "is faster"} and costs ${gbp(r.cost - c.cost)} less, so ${r.id} is layer ${r.layer}.`;
    }).join(" ");
    node.hidden = false;
  }

  // Prose that states fixture numbers is generated here from the checked data.
  function renderDerivedText() {
    const set = (key, value) => { for (const n of document.querySelectorAll(`[data-derived="${key}"]`)) n.textContent = value; };
    const families = new Set(t.routes.map((r) => r.familyId)).size;
    const endMonth = startMonth + t.horizonMonths - 1;
    set("horizon-sentence", `${t.region.split(",")[0]}. Every route is compared over the same ${t.horizonMonths} months, ${fmt.monthName(startMonth)} to ${fmt.monthName(endMonth)} ${startYear + Math.floor(endMonth / 12)}.`);
    set("search-coverage", `Complete for this model: ${t.routes.length} schedules in ${families} route families`);
    set("directai-sentence", `Synthetic fixture DIRECTAI: ${F.directai.routes.length} routes to one target, with months and direct cost only.`);
    set("directai-count", `${F.directai.routes.length}, all feasible, one target (fixture DIRECTAI)`);
    set("basis-summary", economic
      ? `Economic cost over ${t.horizonMonths} months against ${gbp(t.baselineIncomeByMonthMinor[0])} a month take-home. Search complete: ${t.routes.length} schedules.`
      : `Direct spending only; pay lost while training isn't counted. ${F.directai.routes.length} routes from fixture DIRECTAI.`);
    if (route) document.querySelector("#journey-title").textContent = `Route ${route.id}: ${TRACE_NAMES[route.id].charAt(0).toLowerCase()}${TRACE_NAMES[route.id].slice(1)}`;
  }

  // Slider bounds come from the data, so every plotted route is inside the default view.
  function renderControls() {
    const xMax = Math.max(...routes.map((r) => r.timeMonths));
    const monthsMax = economic ? t.horizonMonths : Math.ceil(xMax / 2) * 2;
    const costMax = Math.ceil(Math.max(...routes.map((r) => r.cost)) / 100000) * 1000;
    for (const id of ["#time-range", "#time-number"]) {
      const n = document.querySelector(id);
      n.max = String(id === "#time-range" ? monthsMax : 24);
      n.value = String(monthsMax);
    }
    for (const n of document.querySelectorAll(".cost-range, .cost-number")) {
      if (n.classList.contains("cost-range")) n.max = String(costMax);
      n.value = String(costMax);
    }
  }

  renderDerivedText();
  renderControls();
  renderChart();
  renderTieNote();
  renderCards();
  renderGantt();
  renderTimelineMobile();
  renderLedger();
})();
