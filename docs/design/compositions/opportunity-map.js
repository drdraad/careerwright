// Renders the opportunity map, pay lens and listing list from DESIGN_LISTINGS (synthetic,
// design-only data) for the current state. Layout is deterministic: fixed anchors, fixed
// company angles, no force simulation (plan section 5: no continuous force motion).
(function () {
  const { DESIGN_LISTINGS: L, state, fmt } = window.CAREERWRIGHT;
  const AI = window.CAREERWRIGHT.FIXTURES.trace01.aiScore;

  const VIEWS = {
    default: { areas: ["manchester", "leeds", "remote"], jobs: null, selected: "j1", stale: [], empty: [] },
    unknown: { areas: ["manchester", "leeds"], jobs: ["j3", "j4", "j5"], selected: "j4", stale: [], empty: ["leeds"] },
    failure: { areas: ["manchester", "leeds", "remote"], jobs: null, selected: "j9", stale: ["j2", "j9", "j13", "j14"], empty: [] },
  };
  const view = VIEWS[state];
  const jobs = L.jobs.filter((j) => !view.jobs || view.jobs.includes(j.id));
  const company = Object.fromEntries(L.companies.map((c) => [c.id, c]));
  const area = Object.fromEntries(L.areas.map((a) => [a.id, a]));
  const selected = jobs.find((j) => j.id === view.selected);
  const INDUSTRY_NAMES = { finance: "Finance and insurance", health: "Health and care", retail: "Retail", technology: "Technology", public: "Public and third sector", other: "Other" };
  const INDUSTRY_TOKEN = { finance: "blue", health: "coral", retail: "amber", technology: "violet", public: "olive", other: "other" };
  const colour = (industry) => `var(--industry-${INDUSTRY_TOKEN[industry]})`;
  const SVG = "http://www.w3.org/2000/svg";
  const isStale = (job) => view.stale.includes(job.id);

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

  // One <text> per label, one <tspan> per line, so a label is a single box.
  function label(parent, x, y, lines, anchor) {
    const t = el("text", { x, y, "text-anchor": anchor }, parent);
    lines.forEach(([content, cls], k) => {
      const span = el("tspan", { x, dy: k === 0 ? 0 : 16, class: cls }, t);
      span.textContent = content;
    });
    return t;
  }

  function wrap(label, width) {
    if (label.length <= width) return [label];
    const words = label.split(" ");
    const lines = [""];
    for (const w of words) {
      const line = lines[lines.length - 1];
      if (line && (line + " " + w).length > width) lines.push(w);
      else lines[lines.length - 1] = line ? line + " " + w : w;
    }
    return lines;
  }

  function payText(pay) {
    if (pay.kind === "unknown") return "Pay not stated";
    const range = pay.min === pay.max ? `£${pay.min.toLocaleString("en-GB")}` : `£${pay.min.toLocaleString("en-GB")}–£${pay.max.toLocaleString("en-GB")}`;
    return pay.kind === "predicted" ? `${range}, estimated by the listing site` : `${range}, advertised`;
  }

  function aiText(job) {
    return job.ai === "range" ? `${AI.range[0]}–${AI.range[1]} of 10` : "Unscored";
  }

  function ageText(job) {
    if (isStale(job)) return "Last checked 2 days ago";
    return job.postedDays === 1 ? "Posted yesterday" : `Posted ${job.postedDays} days ago`;
  }

  function employerText(c) {
    return c.agency ? `${c.name} (agency; employer not disclosed)` : c.name;
  }

  // ---------- Map ----------
  const ANCHORS = { manchester: [290, 280], leeds: [595, 150], remote: [600, 440] };
  const ANGLES = {
    kestrel: -140, northmoor: -100, copperfield: 15, ashgrove: 130, tessellate: 180,
    hollinbrook: 180, ridings: -35, kirkgate: 25,
    fenwick: 195, lumen: 15,
  };
  const AREA_R = 46;
  const COMPANY_R = 122;
  const JOB_R = 48;
  const LABEL_R = 72;
  const rad = (d) => (d * Math.PI) / 180;
  const polar = ([x, y], r, deg) => [x + r * Math.cos(rad(deg)), y + r * Math.sin(rad(deg))];

  function curve(from, to, bend) {
    const mx = (from[0] + to[0]) / 2;
    const my = (from[1] + to[1]) / 2;
    const dx = to[0] - from[0];
    const dy = to[1] - from[1];
    return `M${from[0].toFixed(1)},${from[1].toFixed(1)} Q${(mx - dy * bend).toFixed(1)},${(my + dx * bend).toFixed(1)} ${to[0].toFixed(1)},${to[1].toFixed(1)}`;
  }

  function jobMark(g, [x, y], job) {
    const c = colour(company[job.company].industry);
    const r = 5.5;
    el("circle", { cx: x, cy: y, r: r + 6, class: "job-focus" }, g);
    el("circle", { cx: x, cy: y, r: r + 1, fill: "none", "data-mark": "" }, g);
    if (job.mode === "onsite") {
      el("circle", { cx: x, cy: y, r, fill: c, stroke: c, "stroke-width": 1.6, class: "job-mark" }, g);
    } else if (job.mode === "hybrid") {
      el("circle", { cx: x, cy: y, r, fill: "var(--surface-space)", stroke: c, "stroke-width": 1.6, class: "job-mark" }, g);
      el("path", { d: `M${x - r},${y} A${r},${r} 0 0 0 ${x + r},${y} Z`, fill: c }, g);
    } else {
      el("circle", { cx: x, cy: y, r, fill: "var(--surface-space)", stroke: c, "stroke-width": 2, class: "job-mark" }, g);
    }
  }

  function renderMap() {
    const svg = document.querySelector("#map-svg");
    const drawn = [];
    for (const areaId of view.areas) {
      const a = area[areaId];
      const anchor = ANCHORS[areaId];
      const companies = L.companies.filter((c) => c.area === areaId && jobs.some((j) => j.company === c.id));
      const areaJobs = jobs.filter((j) => company[j.company].area === areaId);
      for (const c of companies) {
        const pos = polar(anchor, COMPANY_R, ANGLES[c.id]);
        el("path", { d: curve(polar(anchor, AREA_R, ANGLES[c.id]), pos, 0.12), class: "branch", stroke: colour(c.industry) }, svg);
        const cJobs = areaJobs.filter((j) => j.company === c.id);
        cJobs.forEach((job, i) => {
          const spread = cJobs.length === 1 ? 0 : (i - (cJobs.length - 1) / 2) * 30;
          const p = polar(pos, JOB_R, ANGLES[c.id] + spread);
          el("path", { d: curve(pos, p, 0.18), class: "branch", stroke: colour(c.industry) }, svg);
          drawn.push({ job, p });
        });
        el("circle", { cx: pos[0], cy: pos[1], r: 7, fill: colour(c.industry), "data-mark": "" }, svg);
        // Labels sit radially beyond the job fan, so they never cross their own branches.
        const cos = Math.cos(rad(ANGLES[c.id]));
        const sin = Math.sin(rad(ANGLES[c.id]));
        const anchorText = cos > 0.35 ? "start" : cos < -0.35 ? "end" : "middle";
        const lines = wrap(c.name, 20);
        const [lx, ly0] = polar(pos, LABEL_R, ANGLES[c.id]);
        const block = (lines.length - 1) * 16;
        const ly = anchorText === "middle" ? (sin < 0 ? ly0 - block : ly0 + 10) : ly0 - block / 2 + 4;
        label(svg, lx, ly, lines.map((line) => [line, "company-label"]), anchorText);
      }
      // Area anchor: the open-circle motif holding the area's name and count, so no
      // branch ever crosses an area label. The region note is in the key below.
      el("circle", { cx: anchor[0], cy: anchor[1], r: AREA_R, class: `area-ring${view.empty.includes(areaId) ? " empty" : ""}`, "aria-hidden": "true" }, svg);
      if (areaId === "remote") el("circle", { cx: anchor[0], cy: anchor[1], r: AREA_R - 5, class: "area-ring-inner", "aria-hidden": "true" }, svg);
      const n = areaJobs.length;
      const empty = view.empty.includes(areaId);
      label(svg, anchor[0], anchor[1] - 2, [[a.label, "area-label"], [empty ? "none found" : `${n} listing${n === 1 ? "" : "s"}`, "area-count"]], "middle");
      if (empty) label(svg, anchor[0], anchor[1] + AREA_R + 22, [["No matching listings in the 4 sources checked", "area-note"]], "middle");
    }
    for (const { job, p } of drawn) {
      const c = company[job.company];
      const g = el("g", { class: `job${isStale(job) ? " stale" : ""}`, tabindex: "0", role: "button", "aria-pressed": String(job.id === view.selected), "aria-label": `${job.title}, ${employerText(c)}, ${payText(job.pay)}${isStale(job) ? ", last checked 2 days ago" : ""}` }, svg);
      jobMark(g, p, job);
      if (isStale(job)) el("circle", { cx: p[0], cy: p[1], r: 9, class: "stale-ring" }, g);
      if (job.id === view.selected) {
        el("circle", { cx: p[0], cy: p[1], r: 11, class: "selected-ring" }, g);
        el("circle", { cx: p[0], cy: p[1], r: 17, class: "selected-ring", opacity: 0.4 }, g);
      }
    }
  }

  function renderLegend() {
    const foot = document.querySelector("#map-legend");
    const present = [...new Set(jobs.map((j) => company[j.company].industry))];
    const order = ["finance", "health", "retail", "technology", "public", "other"].filter((k) => present.includes(k));
    const items = order.map((k) => `<span class="legend-item"><span class="industry-dot" style="background:${colour(k)}"></span>${INDUSTRY_NAMES[k]}</span>`).join("");
    const modes = '<span class="legend-item"><svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="currentColor"/></svg>On site</span><span class="legend-item"><svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M1.5 6A4.5 4.5 0 0 0 10.5 6Z" fill="currentColor"/></svg>Hybrid</span><span class="legend-item"><svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>Remote</span>';
    const areas = view.areas.map((id) => `${area[id].label}: ${area[id].note}`).join(". ");
    foot.innerHTML = `<span class="legend" aria-label="Industry">${items}</span><span class="legend" aria-label="Work mode">${modes}</span><span>${areas}.</span><span>Distance on the map is layout only, not travel time or a chance of an offer.</span>`;
  }

  // ---------- Pay and location lens ----------
  function renderLens() {
    const svg = document.querySelector("#lens-svg");
    const X0 = 150, X1 = 700, UNKNOWN_X = 790, MIN = 20000, MAX = 50000;
    const x = (v) => X0 + ((v - MIN) / (MAX - MIN)) * (X1 - X0);
    let y = 22;
    for (let v = MIN; v <= MAX; v += 5000) {
      el("line", { x1: x(v), x2: x(v), y1: 14, y2: 1000, stroke: "var(--line-space-hairline)" }, svg);
      text(svg, x(v), 10, `£${v / 1000}k`, "lens-axis", "middle");
    }
    text(svg, UNKNOWN_X, 10, "Pay not stated", "lens-axis", "middle");
    for (const areaId of view.areas) {
      const rowJobs = jobs.filter((j) => company[j.company].area === areaId);
      const known = rowJobs.filter((j) => j.pay.kind !== "unknown");
      const unknown = rowJobs.filter((j) => j.pay.kind === "unknown");
      const h = Math.max(30, known.length * 11 + 14);
      el("line", { x1: 0, x2: 860, y1: y + h, y2: y + h, stroke: "var(--line-space-hairline)" }, svg);
      text(svg, 0, y + 18, area[areaId].label, "lens-row-label");
      if (!rowJobs.length) text(svg, X0, y + 18, "No matching listings in the sources checked", "lens-axis");
      known.forEach((job, i) => {
        const yy = y + 12 + i * 11;
        const c = colour(company[job.company].industry);
        const sameCompany = selected && job.company === selected.company;
        // Dimmed bars stay at 3:1 or better against the lens (0.75 measured: lowest 3.86:1).
        const opacity = !selected || sameCompany ? 1 : 0.75;
        const width = job.id === view.selected ? 5 : sameCompany ? 4 : 3;
        if (job.pay.min === job.pay.max) {
          el("circle", { cx: x(job.pay.min), cy: yy, r: 3.5, fill: c, opacity }, svg);
        } else {
          if (job.pay.kind === "predicted") {
            // Estimated by the listing site: a hollow bar, not a dashed one.
            el("rect", { x: x(job.pay.min), y: yy - width / 2 - 1, width: x(job.pay.max) - x(job.pay.min), height: width + 2, rx: (width + 2) / 2, fill: "var(--surface-space-raised)", stroke: c, "stroke-width": 1.4, opacity }, svg);
          } else {
            el("line", { x1: x(job.pay.min), x2: x(job.pay.max), y1: yy, y2: yy, stroke: c, "stroke-width": width, "stroke-linecap": "round", opacity }, svg);
          }
        }
        if (job.id === view.selected) el("rect", { x: x(job.pay.min) - 6, y: yy - 6, width: x(job.pay.max) - x(job.pay.min) + 12, height: 12, rx: 6, fill: "none", stroke: "var(--selection-space)", "stroke-width": 1.5 }, svg);
      });
      unknown.forEach((job, i) => {
        const c = colour(company[job.company].industry);
        el("circle", { cx: UNKNOWN_X - 24 + i * 14, cy: y + 18, r: 4, fill: "none", stroke: c, "stroke-width": 1.6 }, svg);
        if (job.id === view.selected) el("circle", { cx: UNKNOWN_X - 24 + i * 14, cy: y + 18, r: 9, fill: "none", stroke: "var(--selection-space)", "stroke-width": 1.5 }, svg);
      });
      y += h + 8;
    }
    svg.setAttribute("viewBox", `0 0 860 ${y}`);
  }

  // ---------- List (desktop table and phone cards) ----------
  function renderList() {
    const tbody = document.querySelector("#listing-rows");
    const cards = document.querySelector("#listing-cards");
    for (const job of jobs) {
      const c = company[job.company];
      const tr = document.createElement("tr");
      tr.setAttribute("aria-selected", String(job.id === view.selected));
      const cells = [
        `<span class="listing-title"></span>`,
        `<span class="role-employer"><span class="industry-dot" style="background:${colour(c.industry)}"></span><span class="emp"></span></span>`,
        `<span class="where"></span>`,
        `<span class="pay tnum"></span>`,
        `<span class="tnum ai"></span>`,
        `<span class="age"></span>`,
      ];
      tr.innerHTML = cells.map((x) => `<td>${x}</td>`).join("");
      fill(tr, job, c);
      tbody.appendChild(tr);

      const card = document.createElement("article");
      card.className = "listing-card";
      if (job.id === view.selected) card.setAttribute("aria-current", "true");
      card.innerHTML = `<span class="listing-title"></span><span class="role-employer"><span class="industry-dot" style="background:${colour(c.industry)}"></span><span class="emp"></span></span><span class="listing-meta"><span class="where"></span><span class="pay tnum"></span><span>AI Resilience <span class="ai tnum"></span></span><span class="age"></span></span>`;
      fill(card, job, c);
      cards.appendChild(card);
    }
  }

  function fill(node, job, c) {
    node.querySelector(".listing-title").textContent = job.title;
    node.querySelector(".emp").textContent = employerText(c);
    node.querySelector(".where").textContent = c.area === "remote" ? "Remote, employed in England" : `${area[c.area].label}, ${job.mode === "onsite" ? "on site" : job.mode}`;
    node.querySelector(".pay").textContent = job.pay.kind === "unknown" ? "Pay not stated" : payText(job.pay).replace(", advertised", "").replace(", estimated by the listing site", " (estimated)");
    // Phone cards have no column header, so a published range carries its experimental
    // marker inline; an unscored role has no record to mark.
    node.querySelector(".ai").textContent = aiText(job) + (node.classList.contains("listing-card") && job.ai === "range" ? ", experimental" : "");
    const age = node.querySelector(".age");
    age.textContent = ageText(job);
    if (isStale(job)) age.className = "age status status-stale";
  }

  function renderCounts() {
    const found = jobs.reduce((n, j) => n + j.copies, 0);
    for (const node of document.querySelectorAll("[data-count='found']")) node.textContent = String(found);
    for (const node of document.querySelectorAll("[data-count='shown']")) node.textContent = String(jobs.length);
    for (const node of document.querySelectorAll("[data-count='duplicates']")) node.textContent = String(found - jobs.length);
    for (const node of document.querySelectorAll("[data-count='fresh']")) node.textContent = String(jobs.length - view.stale.length);
    for (const node of document.querySelectorAll("[data-count='stale']")) node.textContent = String(view.stale.length);
  }

  // Phones lead with the list (spec section 7); the toggle shows that.
  if (window.matchMedia("(max-width: 760px)").matches) {
    for (const b of document.querySelectorAll("[data-view]")) b.setAttribute("aria-pressed", String(b.dataset.view === "list"));
  }

  renderMap();
  renderLegend();
  renderLens();
  renderList();
  renderCounts();
})();
