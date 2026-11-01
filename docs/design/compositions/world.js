// The living world's design reference: one place and one state per page
// (world.html?place=you|roles|skills|options|routes|plan&state=...; &key=open opens the key to
// the lights on a narrow screen). The world is drawn still, as SVG, in Horizon's geometry: the
// app's apps/web/src/lib/world/geometry.ts holds the same resting views and the same rule for
// standing the place in the part of the window its panels leave clear. Every word, figure and
// control is in the DOM over it. Values from fixtures/ come from data.js FIXTURES (checked by
// tools/check-fixture-data.mjs); everything else is invented for design review and says so on
// the page. When the page is laid out it leaves window.__worldCheck (every light, gate and trail
// as drawn) for tools/screenshots.mjs.
(() => {
  const { FIXTURES: F, DESIGN_LISTINGS: L } = window.CAREERWRIGHT;
  const T = F.trace01;
  const params = new URLSearchParams(location.search);
  const PLACES = ["you", "roles", "skills", "options", "routes", "plan"];
  const place = PLACES.includes(params.get("place")) ? params.get("place") : "you";
  const state = params.get("state") ?? "default";
  const keyOpen = params.get("key") === "open";
  const LABEL = { you: "You", roles: "Roles", skills: "Skills", options: "Options", routes: "Routes", plan: "Plan" };

  // ---------- Words and numbers ----------
  const money = (minor) => {
    const pounds = minor / 100;
    return `£${pounds.toLocaleString("en-GB", { minimumFractionDigits: Number.isInteger(pounds) ? 0 : 2, maximumFractionDigits: 2 })}`;
  };
  const day = (iso) => new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const count = (n, one, many) => `${n} ${n === 1 ? one : many}`;

  // The product's glyphs (apps/web/src/components/Glyph.tsx), drawn in the same 24-unit style.
  // `support`, `said` and `setAside` are new here: each meaning has its own glyph, so the support
  // panel never borrows "not known yet", "set aside" never borrows "not built yet" and "you said
  // so" never borrows "complete" (the app adds them with the slices that show them).
  const S = 'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';
  const GLYPH = {
    mark: `<circle cx="9" cy="15" r="5.2" ${S}/><path d="M12.6 11.3C14.6 8.6 16 7.3 18.4 6.2" ${S}/><circle cx="19.6" cy="5.6" r="1.9" ${S}/>`,
    unknown: `<circle cx="12" cy="12" r="9" ${S}/><path d="M9.6 9.6a2.5 2.5 0 1 1 3.6 2.2c-.8.4-1.2.9-1.2 1.7v.4" ${S}/><circle cx="12" cy="16.9" r="1" fill="currentColor"/>`,
    conditional: `<path d="M12 3.2L20.8 12 12 20.8 3.2 12z" ${S}/><circle cx="12" cy="12" r="2" fill="currentColor"/>`,
    stale: `<circle cx="12" cy="12" r="9" ${S}/><path d="M12 7v5.2l3.4 2" ${S}/>`,
    error: `<path d="M12 3.5L21.5 20h-19z" ${S}/><path d="M12 9.5v5" ${S}/><circle cx="12" cy="17.3" r="1.1" fill="currentColor"/>`,
    synthetic: `<path d="M9.5 3.5h5M10.5 3.5v5.8L5.6 17.8a2 2 0 0 0 1.7 3h9.4a2 2 0 0 0 1.7-3l-4.9-8.5V3.5" ${S}/><path d="M7.8 14.5h8.4" ${S}/>`,
    blocked: `<circle cx="12" cy="12" r="9" ${S}/><path d="M7.5 12h9" ${S}/>`,
    complete: `<circle cx="12" cy="12" r="9" ${S}/><path d="M7.8 12.4l2.8 2.8 5.6-6" ${S}/>`,
    said: `<path d="M4.5 6.5a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v7.5a2 2 0 0 1-2 2H11l-4.2 3.3V16h-.3a2 2 0 0 1-2-2z" ${S}/>`,
    support: `<circle cx="12" cy="12" r="8.5" ${S}/><circle cx="12" cy="12" r="3.8" ${S}/><path d="M6 6l3.3 3.3M18 6l-3.3 3.3M6 18l3.3-3.3M18 18l-3.3-3.3" ${S}/>`,
    setAside: `<path d="M4 15.5v3h16v-3" ${S}/><path d="M12 4.5v9M8.5 10l3.5 3.5 3.5-3.5" ${S}/>`,
    pause: `<circle cx="12" cy="12" r="9" ${S}/><path d="M10 8.5v7M14 8.5v7" ${S}/>`,
    sound: `<path d="M4.5 9.5h3.2L12 5.5v13l-4.3-4H4.5z" ${S}/><path d="M15.5 9a4.2 4.2 0 0 1 0 6M18 6.5a7.8 7.8 0 0 1 0 11" ${S}/>`,
    menu: `<path d="M4 7h16M4 12h16M4 17h10" ${S}/>`,
    live: `<circle cx="12" cy="12" r="3.2" fill="currentColor"/><circle cx="12" cy="12" r="7.5" ${S}/>`,
    // Deciding on a proposed change: a plain tick (never "complete"'s circled one) and a turn back.
    accept: `<path d="M5.5 12.8l4.2 4.2 8.8-9.6" ${S}/>`,
    undo: `<path d="M9 7.5L5 11.5l4 4M5.5 11.5h8.5a4.5 4.5 0 0 1 0 9H11" ${S}/>`,
    expand: `<path d="M7 14.5l5-5 5 5" ${S}/>`,
    collapse: `<path d="M7 9.5l5 5 5-5" ${S}/>`,
  };
  const glyph = (name) => `<svg viewBox="0 0 24 24" class="glyph" aria-hidden="true" focusable="false">${GLYPH[name]}</svg>`;

  // ---------- Horizon's geometry (mirrors apps/web/src/lib/world/geometry.ts) ----------
  const vp = { w: window.innerWidth, h: window.innerHeight };
  const phone = vp.w <= 760;
  const kx = Math.min(1, vp.w / vp.h / 1.6);
  const ORIGIN = [0, 0.04, 1.7];
  const HORIZON_Z = 17;
  /** Where the view rests at each place before the panels are measured (fractions of the window). */
  function restingView(id) {
    const right = phone ? 0.5 : 0.7;
    const { w, h } = vp;
    switch (id) {
      case "you":
        return { x: 0, z: 0.25, eye: 0.62, horizon: h * 0.36, centre: w * right, focal: h * 0.6 };
      case "roles":
        return { x: 0, z: -1, eye: 1, horizon: h * 0.4, centre: w * (phone ? 0.5 : 0.62), focal: h };
      case "skills":
        return { x: 0, z: -1.6, eye: 2.6, horizon: h * 0.2, centre: w * (phone ? 0.5 : 0.64), focal: h * 0.62 };
      case "options":
        return { x: 0, z: -2.2, eye: 3.6, horizon: h * 0.18, centre: w * (phone ? 0.5 : 0.64), focal: h * 0.62 };
      case "routes":
        return { x: 0, z: -2.6, eye: 3.2, horizon: h * 0.2, centre: w * (phone ? 0.5 : 0.66), focal: h * 0.72 };
      default:
        return { x: 0, z: -1.2, eye: 1.8, horizon: h * 0.26, centre: w * (phone ? 0.5 : 0.64), focal: h * 0.62 };
    }
  }
  const MIN_CLEAR = 240;
  const MIN_BAND = 128; // the app's geometry.ts: room for the names above and below, and a little plain
  // A You view with a decision waiting, below 968 px: the slim band (world.css), whose world
  // shows the person and the target, no more (Task W2E, the audit's F7).
  const slimBand = place === "you" && ["review", "saved", "known", "suggestions"].includes(state) && vp.w < 968;
  const ROOM_ABOVE = 56;
  const ROOM_BELOW = 48;
  /**
   * The resting view, stood in the part of the window the panels leave clear (as the app does):
   * moved across only where its usual place would be too near the panel beside it, and fitted
   * between the bars above and the panels below, smaller only if it must be.
   */
  function placeView(id, clear) {
    const view = restingView(id);
    if (clear === undefined) return view;
    if (clear.backdrop) return { ...view, centre: (clear.left + clear.right) / 2 };
    const near = view.centre < clear.left + MIN_CLEAR / 2 || view.centre > clear.right - MIN_CLEAR / 2;
    const span = ((view.eye - ORIGIN[1]) * view.focal) / (ORIGIN[2] - view.z);
    const room = clear.bottom - clear.top - ROOM_ABOVE - ROOM_BELOW;
    const scale = span > room ? room / span : 1;
    const highest = clear.top + ROOM_ABOVE;
    const lowest = clear.bottom - ROOM_BELOW - span * scale;
    return {
      ...view,
      centre: near ? (clear.left + clear.right) / 2 : view.centre,
      focal: view.focal * scale,
      horizon: Math.min(Math.max(view.horizon, highest), lowest),
    };
  }
  const box = (e) => {
    const r = e.getBoundingClientRect();
    return { x: r.left, y: r.top, w: r.width, h: r.height };
  };
  /** The part of the window the panels leave clear: beside them on a wide screen, above them otherwise. */
  function clearArea() {
    let top = 0;
    let left = 0;
    let right = vp.w;
    // The rail down the left edge, and the bars stacked along the top (a phone's top bar, then the strip).
    const bars = [...document.querySelectorAll(".strip, .topbar, .rail")].map(box).filter((b) => b.w > 0).sort((a, b) => a.y - b.y);
    for (const bar of bars) {
      if (bar.x <= 1 && bar.h >= vp.h * 0.9) left = Math.max(left, bar.x + bar.w);
      else if (bar.y <= top + 1) top = Math.max(top, bar.y + bar.h);
    }
    const panels = [...document.querySelectorAll(".panel")].map(box).filter((b) => b.w > 0);
    let sideLeft = left;
    let sideRight = right;
    for (const p of panels) {
      if (p.x + p.w / 2 < vp.w / 2) sideLeft = Math.max(sideLeft, p.x + p.w);
      else sideRight = Math.min(sideRight, p.x);
    }
    if (sideRight - sideLeft >= MIN_CLEAR) return { left: sideLeft, right: sideRight, top, bottom: vp.h };
    // Otherwise the taller of the bands above and below the panels.
    const above = { left, right, top, bottom: Math.min(vp.h, ...panels.map((p) => p.y)) };
    const below = { left, right, top: Math.max(top, ...panels.map((p) => p.y + p.h)), bottom: vp.h };
    const band = above.bottom - above.top >= below.bottom - below.top ? above : below;
    if (band.bottom - band.top >= MIN_BAND) return band;
    // No room anywhere: the world is a backdrop, standing behind the panels (as on a phone), so
    // no light peeks out beside them where its name has no room (Task W2C, a tall You console
    // on a tablet).
    return { left: Math.min(...panels.map((p) => p.x)), right: Math.max(...panels.map((p) => p.x + p.w)), top, bottom: vp.h, backdrop: true };
  }
  function seeded(seed) {
    let h = 2166136261;
    for (let i = 0; i < seed.length; i++) h = Math.imul(h ^ seed.charCodeAt(i), 16777619);
    return () => {
      h = Math.imul(h ^ (h >>> 15), 2246822507);
      h = Math.imul(h ^ (h >>> 13), 3266489909);
      h ^= h >>> 16;
      return (h >>> 0) / 4294967296;
    };
  }
  function cubic(a, b, c, d, steps) {
    const out = [];
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const u = 1 - t;
      out.push([0, 1, 2].map((k) => u * u * u * a[k] + 3 * u * u * t * b[k] + 3 * u * t * t * c[k] + t * t * t * d[k]));
    }
    return out;
  }
  const lift = (pts, from, to) => pts.map((p, i) => [p[0], from[1] + (to[1] - from[1]) * (i / (pts.length - 1)) ** 4, p[2]]);
  function sweep(from, to, seed, bend = null) {
    const rand = seeded(seed);
    const dz = to[2] - from[2];
    const sway = bend ?? (rand() - 0.5) * 1.1;
    return lift(cubic(from, [from[0] + (to[0] - from[0]) * 0.15 + sway, 0.02, from[2] + dz * 0.42], [to[0] - sway * 0.4, 0.02, from[2] + dz * 0.8], to, 56), from, to);
  }
  const destinationAt = (j, n) => [(j - (n - 1) / 2) * Math.min(6.5, 22 / Math.max(1, n)) * kx, 0.25, HORIZON_Z];
  const skillAt = (i, n) => {
    const rad = ((n > 1 ? -55 + (110 * i) / (n - 1) : 0) * Math.PI) / 180;
    return [ORIGIN[0] + Math.sin(rad) * 2.05 * 1.15 * kx, 0.02, ORIGIN[2] + Math.cos(rad) * 2.05];
  };

  // ---------- What each place shows (its states, before it is drawn) ----------
  // Destinations: P01's target (fixture) and, at Roles, suggested places (invented examples).
  const target = { id: "target", title: T.targetTitle, kind: "destination" };
  const SUGGESTED = ["Records manager", "Data steward", "Statistician", "Business analyst"].map((title) => ({ id: title, title, kind: "suggested" }));
  // D-M10: three chosen targets with long names (P01's, and two invented), as plan section 5 asks.
  const LONG = ["Senior data governance and information quality manager", "Clinical data standards and interoperability specialist"].map((title) => ({ id: title, title, kind: "destination" }));
  const SKILLS = [
    { id: "s1", label: "Check data for errors", state: "said" },
    { id: "s2", label: "Explain findings clearly", state: "said" },
    { id: "s3", label: "Keep accurate records", state: "usual" },
    { id: "s4", label: "Work to deadlines", state: "usual" },
    { id: "s5", label: "Use spreadsheets", state: "usual" },
  ];
  const STRETCHES = [
    { name: "Check data for errors", state: state === "unknown" ? "shadow" : "said" },
    { name: "Query related tables", state: state === "unknown" ? "shadow" : "usual" },
    { name: "Validate keys and missing values", state: "shadow" },
    { name: "Write reproducible checks", state: "shadow" },
    { name: "Pass the assessed report", state: "shadow", gate: true },
  ];
  const lit = !(place === "you" && state === "not-built");
  const roles = place === "roles" && state !== "not-built";
  const destinations = roles
    ? state === "three-targets"
      ? [target, ...LONG]
      : [...SUGGESTED, target]
    : [target];
  destinations.sort((a, b) => a.title.localeCompare(b.title));
  destinations.forEach((d, j) => {
    d.p = destinationAt(j, destinations.length);
  });
  const goal = target.p;
  const revelation = roles && state !== "three-targets" ? "Statistician" : null;

  // Openings for the chosen destination, by area (invented listings): each count says how many
  // sources answered for it and when. In the stale state the job board didn't answer today:
  // today's counts cover the sources that did, and the kept counts the search of two days ago,
  // when every source answered.
  const sources = L.totals.sourcesChecked;
  const AREAS = L.areas.map((a) => {
    const all = L.jobs.filter((j) => L.companies.find((c) => c.id === j.company)?.area === a.id).length;
    const shown = state === "unknown" && a.id === "leeds" ? 0 : all;
    const stale = state === "stale" && a.id !== "remote";
    const answered = state === "stale" && !stale ? sources - 1 : sources;
    const words = shown === 0 ? `${a.label}: none found in the ${sources} sources checked` : `${a.label}: ${count(shown, "opening", "openings")}, ${answered} sources, ${stale ? "2 days ago" : "today"}`;
    return { id: a.id, shown, stale, words };
  });

  // The ground between the person and the destination: a long S across the plain, so that its
  // stretches spread across the clear part of the window wherever the view stands.
  const ground = lift(cubic(ORIGIN, [3.2 * kx, 0.02, 6.5], [-3.2 * kx, 0.02, 11.5], goal, 96), ORIGIN, goal);

  // ---------- Drawing the still world ----------
  const BLUE = [64, 140, 255];
  const VIOLET = [158, 107, 255];
  const journey = (h) => {
    const t = Math.min(1, Math.max(0, h)) ** 2 * (3 - 2 * Math.min(1, Math.max(0, h)));
    return `rgb(${BLUE.map((b, i) => Math.round(b + (VIOLET[i] - b) * t)).join(",")})`;
  };
  const f = (n) => n.toFixed(1);
  const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  /** The world at this place and state, as drawn from `view`: lights, trails, gates and names. */
  function build(view) {
    const project = (p) => {
      const d = p[2] - view.z;
      if (d < 0.05) return { x: -1e5, y: -1e5, scale: 0, visible: false };
      const scale = view.focal / d;
      return { x: view.centre + (p[0] - view.x) * scale, y: view.horizon + (view.eye - p[1]) * scale, scale, visible: true };
    };
    const world = { project, trails: [], lights: [], gates: [], marks: [], labels: [], legend: new Set() };
    const label = (id, anchor, name, kind, extra = {}) => world.labels.push({ id, anchor, name, kind, ...extra });
    const light = (id, p, kind, name, extra = {}) => world.lights.push({ id, p, kind, name, ...extra });

    light("origin", ORIGIN, lit ? "origin" : "waiting", "origin");
    label("origin", ORIGIN, "You", "origin", { side: "below" });
    for (const d of destinations) {
      light(`destination:${d.id}`, d.p, d.kind, `destination:${d.id}`, { selected: roles && d.id === "target", revelation: d.id === revelation });
      label(`destination:${d.id}`, d.p, d.title, d.kind, { side: "above", selected: roles && d.id === "target" });
      world.legend.add(d.kind);
    }

    if (place === "you" && !slimBand) {
      SKILLS.forEach((s, i) => {
        const p = skillAt(i, SKILLS.length);
        const a = ORIGIN;
        world.trails.push({ points: lift(cubic(a, [a[0] + (p[0] - a[0]) * 0.2, 0.02, a[2] + (p[2] - a[2]) * 0.45], [a[0] + (p[0] - a[0]) * 0.75, 0.02, a[2] + (p[2] - a[2]) * 0.8], p, 24), a, p), state: s.state, width: [0.016, 0.013], hue: [0, 0.3] });
        light(`skill:${s.id}`, p, s.state, `skill:${s.id}`);
        label(`skill:${s.id}`, p, s.label, "skill", { side: "above", state: s.state });
        world.legend.add(s.state);
      });
    }

    if (place === "you" || place === "roles") {
      for (const d of destinations) world.trails.push({ points: sweep(ORIGIN, d.p, `shadow:${d.id}`), state: "shadow", width: [0.011, 0.05], hue: [0.1, 1] });
      world.legend.add("shadow");
    }

    if (roles && !phone) {
      // Openings around the chosen destination only, grouped by area (VIS-1's hierarchy), each
      // area's count with its coverage and date (AREAS). On a phone the areas would stand a few
      // pixels apart, too close to name apart, so the sheet lists them instead.
      // They stand just in front of it, clear of its ring, and under it as Roles sees it: a nearer
      // light is spread wider by perspective, so their across is drawn in to match.
      const front = goal[2] - 5.5;
      const roleZ = restingView("roles").z;
      const under = goal[0] * ((front - roleZ) / (goal[2] - roleZ));
      const rand = seeded("openings");
      const names = AREAS.map((area, k) => {
        const centre = [under + (k - 1) * 0.5 * kx, 0.03, front];
        const id = `area:${area.id}`;
        for (let i = 0; i < area.shown; i++) {
          const p = [centre[0] + (rand() - 0.5) * 0.32 * kx, 0.03, centre[2] + (rand() - 0.5) * 0.7];
          world.marks.push({ kind: "opening", p, stale: area.stale });
          light(`${id}:${i}`, p, area.stale ? "stale-opening" : "opening", id);
        }
        if (area.shown === 0) {
          world.marks.push({ kind: "area", p: centre, empty: true });
          light(id, centre, "none-found", id);
        }
        world.legend.add(area.shown === 0 ? "none-found" : area.stale ? "stale-opening" : "opening");
        return [id, centre, area.words];
      });
      // The areas stand close together, so their names step down from the rightmost, each
      // starting just left of its own lights: the line from each area further left passes the
      // names already placed, never through them.
      for (const [id, centre, words] of names.reverse()) label(id, centre, words, "area", { side: "below", align: "start" });
    }

    if (place === "skills" || place === "options" || place === "plan") {
      // The ground, stretch by stretch. Its states come from readiness (the Skills chapter,
      // Sprint 4); here they are examples. Stretches are cut at equal lengths on screen, so each
      // has room for its words (where a stretch begins or ends means nothing, VIS-1).
      const screen = ground.map(project);
      const along = [0];
      for (let i = 1; i < screen.length; i++) along.push(along[i - 1] + Math.hypot(screen[i].x - screen[i - 1].x, screen[i].y - screen[i - 1].y));
      const total = along[along.length - 1];
      const cut = (k) => (k <= 0 ? 0 : k >= STRETCHES.length ? ground.length - 1 : along.findIndex((a) => a >= (total * k) / STRETCHES.length));
      const plan = place === "plan";
      STRETCHES.forEach((stretch, k) => {
        const from = cut(k);
        const to = cut(k + 1);
        const mid = ground[Math.floor((from + to) / 2)];
        const sid = `stretch:${k}`;
        world.trails.push({ points: ground.slice(from, to + 1), state: plan ? "chosen" : stretch.state, width: [0.02, 0.05], hue: [k / STRETCHES.length, (k + 1) / STRETCHES.length] });
        if (stretch.gate && place !== "options") {
          // The gate stands where the last stretch begins, clear of the destination's light.
          const g = ground[from];
          world.gates.push({ id: "gate", p: g, name: "gate" });
          label("gate", g, "Ready if you pass the assessed report", "gate", { side: "right" });
          world.legend.add("gate");
        } else if (place === "skills") {
          label(sid, mid, stretch.name, "stretch", { side: k % 2 ? "left" : "right", state: stretch.state });
        }
        if (!plan) world.legend.add(`stretch-${stretch.state}`);
        if (place === "options" && (stretch.state === "shadow" || stretch.gate)) {
          // A bridge across a dark stretch: placed (lit) or still to find (none drawn, words say so).
          const bridged = state !== "unknown" && (k === 2 || stretch.gate);
          if (bridged) {
            const a = ground[from];
            const b = ground[to];
            const top = [(a[0] + b[0]) / 2, 0.7, (a[2] + b[2]) / 2];
            world.trails.push({ points: cubic(a, top, top, b, 24), state: "bridge", width: [0.03, 0.04], hue: [0.4, 0.8] });
            label(`bridge:${k}`, top, k === 2 ? "Bridge: part-time course" : "Bridge: assessed report, with the course", "bridge", { side: k % 2 ? "left" : "right" });
            world.legend.add("bridge");
          } else {
            label(sid, mid, `${stretch.name}: no bridge yet`, "stretch", { side: k % 2 ? "left" : "right", state: "shadow" });
          }
        }
      });
      if (plan) {
        // The chosen path made solid, with the next move glowing at its start.
        const next = ground[cut(0.35)];
        world.marks.push({ kind: "next", p: next });
        light("next", next, "next", "next");
        label("next", next, "Next: start the course", "next", { side: "right" });
        world.legend.add("chosen");
        world.legend.add("next");
      }
    }

    // Not built yet (as the app shows Routes in every workspace, Task W2E): no route is drawn,
    // because none has been worked out.
    if (place === "routes" && state !== "not-built") {
      // Whole journeys from the person to the destination: TRACE-01's five routes. Where each
      // runs is layout only; the instrument beside it carries time and cost exactly.
      const failed = state === "failed";
      const bends = { A: -5, B: -2, C: 1, D: 4, E: 7 };
      for (const route of T.routes) {
        const selected = route.id === T.selectedRoute && !failed;
        const pts = sweep(ORIGIN, goal, `route:${route.id}`, bends[route.id] * kx);
        world.trails.push({ points: pts, state: selected ? "chosen" : failed ? "stale" : "route", width: [0.02, 0.05], hue: [0.1, 1] });
        label(`route:${route.id}`, pts[Math.floor(pts.length * 0.55)], `Route ${route.id}`, "route", { side: "above", selected });
        if (selected) {
          // The gate on the selected route, where it is clear of both lights.
          const at = Math.floor(pts.length * 0.4);
          world.gates.push({ id: "gate", p: pts[at], name: "gate" });
          label("gate", pts[at], "Ready if you pass the assessed report", "gate", { side: "left" });
        }
      }
      world.legend.add(failed ? "stale" : "looking");
      if (!failed) {
        world.legend.add("route");
        world.legend.add("gate");
      }
    }
    return world;
  }

  function drawWorld(world, view) {
    const { project } = world;
    const opacity = {
      usual: Number(token("--trail-opacity-usual")),
      shadow: Number(token("--trail-opacity-shadow")),
      stale: Number(token("--trail-opacity-stale")),
    };
    const at = (y) => Math.min(1, Math.max(0, y / vp.h)).toFixed(3);
    const hy = view.horizon;
    const rand = seeded("stars");
    const parts = [];
    parts.push(`<defs>
      <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#010309"/><stop offset="${at(hy - 90)}" stop-color="#050a1a"/><stop offset="${at(hy)}" stop-color="#1C2552"/><stop offset="${at(hy + 18)}" stop-color="#0a1230"/><stop offset="${at(hy + 160)}" stop-color="#050916"/><stop offset="1" stop-color="#03050B"/></linearGradient>
      <radialGradient id="aurora" cx="0.55" cy="1" r="0.8"><stop offset="0" stop-color="#9E6BFF" stop-opacity="0.22"/><stop offset="0.5" stop-color="#408CFF" stop-opacity="0.08"/><stop offset="1" stop-color="#408CFF" stop-opacity="0"/></radialGradient>
      <radialGradient id="halo-person"><stop offset="0" stop-color="#9cc4ff" stop-opacity="0.9"/><stop offset="0.35" stop-color="#5f8fe0" stop-opacity="0.35"/><stop offset="1" stop-color="#5f8fe0" stop-opacity="0"/></radialGradient>
      <radialGradient id="halo-destination"><stop offset="0" stop-color="#FF9433" stop-opacity="0.9"/><stop offset="0.4" stop-color="#FF9433" stop-opacity="0.3"/><stop offset="1" stop-color="#FF9433" stop-opacity="0"/></radialGradient>
      <radialGradient id="pool"><stop offset="0" stop-color="#2a4a9a" stop-opacity="0.55"/><stop offset="1" stop-color="#2a4a9a" stop-opacity="0"/></radialGradient>
      <filter id="bloom" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
    </defs>`);
    parts.push(`<rect width="${vp.w}" height="${vp.h}" fill="url(#sky)"/>`);
    parts.push(`<rect y="${f(hy - vp.h * 0.32)}" width="${vp.w}" height="${f(vp.h * 0.32)}" fill="url(#aurora)"/>`);
    for (let i = 0; i < 80; i++) {
      const x = rand() * vp.w;
      const y = rand() * Math.max(0, hy - 60);
      parts.push(`<circle cx="${f(x)}" cy="${f(y)}" r="${(0.6 + rand()).toFixed(2)}" fill="#EDF5FF" opacity="${(0.2 + rand() * 0.5).toFixed(2)}"/>`);
    }
    const o = project(ORIGIN);
    parts.push(`<ellipse cx="${f(o.x)}" cy="${f(o.y)}" rx="${f(vp.w * 0.32)}" ry="${f(vp.h * 0.16)}" fill="url(#pool)" opacity="${lit ? 1 : 0.4}"/>`);
    const glow = [];
    const lines = [];
    world.trails.forEach((trail, n) => {
      const pts = trail.points.map(project).filter((p) => p.visible);
      if (pts.length < 2) return;
      const first = pts[0];
      const last = pts[pts.length - 1];
      // Each declared state at its measured strength (contrast-pairs.json composites it as drawn):
      // usual, shadow and stale at their tokens; said, chosen, bridges and whole routes in full.
      // Only said, chosen and bridges glow brightly; a whole route glows as quietly as a usual one.
      let stroke;
      let strength = 1;
      if (trail.state === "chosen") stroke = "#45F7D4";
      else if (trail.state === "shadow") {
        stroke = "#6F7EA3";
        strength = opacity.shadow;
      } else if (trail.state === "stale") {
        stroke = "#D6CBAE";
        strength = opacity.stale;
      } else {
        parts.push(`<defs><linearGradient id="t${n}" gradientUnits="userSpaceOnUse" x1="${f(first.x)}" y1="${f(first.y)}" x2="${f(last.x)}" y2="${f(last.y)}"><stop offset="0" stop-color="${journey(trail.hue[0])}"/><stop offset="1" stop-color="${journey(trail.hue[1])}"/></linearGradient></defs>`);
        stroke = `url(#t${n})`;
        strength = trail.state === "usual" ? opacity.usual : 1;
      }
      for (let i = 0; i < pts.length - 1; i += 6) {
        const part = pts.slice(i, Math.min(pts.length, i + 7));
        const mid = part[Math.floor(part.length / 2)];
        const u = (i + 3) / Math.max(1, pts.length - 1);
        const w = Math.max(1, (trail.width[0] + (trail.width[1] - trail.width[0]) * Math.min(1, u)) * mid.scale);
        const d = `M${part.map((p) => `${f(p.x)} ${f(p.y)}`).join("L")}`;
        lines.push(`<path d="${d}" stroke="${stroke}" stroke-width="${f(w)}" stroke-opacity="${strength}" fill="none" stroke-linecap="round"/>`);
        const bright = trail.state === "said" || trail.state === "chosen" || trail.state === "bridge";
        glow.push(`<path d="${d}" stroke="${stroke}" stroke-width="${f(w * 4 + 4)}" stroke-opacity="${bright ? 0.3 : trail.state === "shadow" || trail.state === "stale" ? 0.07 : 0.12}" fill="none" stroke-linecap="round"/>`);
      }
    });
    parts.push(`<g filter="url(#bloom)">${glow.join("")}</g><g>${lines.join("")}</g>`);
    // Lights.
    if (o.visible) {
      const r = Math.max(2.6, 0.034 * o.scale);
      parts.push(`<circle cx="${f(o.x)}" cy="${f(o.y)}" r="${f(r * (lit ? 9 : 5))}" fill="url(#halo-person)" opacity="${lit ? 0.85 : 0.35}"/>`);
      parts.push(`<circle cx="${f(o.x)}" cy="${f(o.y)}" r="${f(r * (lit ? 1 : 0.5))}" fill="#EDF5FF"/>`);
    }
    for (const l of world.lights) {
      const p = project(l.p);
      if (!p.visible) continue;
      if (l.kind === "said" || l.kind === "usual") {
        const r = Math.max(2.6, 0.026 * p.scale);
        parts.push(
          l.kind === "said"
            ? `<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 3)}" fill="url(#halo-person)" opacity="0.7"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r)}" fill="#cfe0ff"/>`
            : `<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 0.85)}" fill="none" stroke="${journey(0.3)}" stroke-width="${f(Math.max(1.4, r * 0.32))}"/>`,
        );
      } else if (l.kind === "destination" || l.kind === "suggested") {
        const r = Math.max(2.6, 0.22 * p.scale);
        if (l.kind === "suggested") {
          parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 2.4)}" fill="url(#halo-destination)" opacity="0.45"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 0.85)}" fill="none" stroke="#FF9433" stroke-width="2"/>`);
        } else {
          parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 4)}" fill="url(#halo-destination)"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r)}" fill="#FFD2A1"/>`);
          if (l.selected) parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 2.3)}" fill="none" stroke="#45F7D4" stroke-width="2"/>`);
        }
      }
    }
    for (const m of world.marks) {
      const p = project(m.p);
      if (!p.visible) continue;
      if (m.kind === "opening") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="2.2" fill="${m.stale ? "#D6CBAE" : "#EDF5FF"}" opacity="${m.stale ? opacity.stale : 1}"/>`);
      if (m.kind === "area") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="9" fill="none" stroke="#6F7EA3" stroke-width="1.5" stroke-opacity="${opacity.shadow}"/>`);
      if (m.kind === "next") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="9" fill="none" stroke="#45F7D4" stroke-width="2.5"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="16" fill="none" stroke="#45F7D4" stroke-width="1" opacity="0.5"/>`);
    }
    for (const g of world.gates) {
      const p = project(g.p);
      const s = 7;
      parts.push(`<rect x="${f(p.x - s)}" y="${f(p.y - s)}" width="${f(s * 2)}" height="${f(s * 2)}" fill="#03050B" stroke="#F2F6FF" stroke-width="2" transform="rotate(45 ${f(p.x)} ${f(p.y)})"/>`);
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${vp.w} ${vp.h}" aria-hidden="true" focusable="false">${parts.join("")}</svg>`;
  }

  // ---------- The exact layer: shell and the place's panel ----------
  const synthetic = `<span class="synthetic">${glyph("synthetic")}Synthetic demo</span>`;
  // Pause shows the person's own choice; distress stills the world on its own and says so: in the
  // strip, or on a phone in the top bar, where it adds no row (the other copy is not displayed).
  const stillStatus = state === "distress" ? `<span class="status world-status" data-tone="neutral" role="status">${glyph("support")}<span>Still while support is shown</span></span>` : "";
  const controls = `
    <button type="button" class="toggle" aria-pressed="false">${glyph("pause")}<span class="label">Hold the world still</span><span class="switch" aria-hidden="true"></span></button>
    ${stillStatus}
    <button type="button" class="toggle" aria-pressed="false">${glyph("sound")}<span class="label">Sound</span><span class="switch" aria-hidden="true"></span></button>
    <button type="button" class="toggle account" aria-label="Account and settings">${glyph("menu")}</button>`;
  const rail = `
    <nav class="rail" aria-label="Chapters">
      <a class="wordmark" href="index.html"><svg viewBox="0 0 24 24" aria-hidden="true">${GLYPH.mark}</svg><span>Careerwright</span></a>
      <ol>${PLACES.map((id) => `<li><a href="world.html?place=${id}" data-progress="${id === "you" ? "visited" : "todo"}"${id === place ? ' aria-current="page"' : ""}><span class="landmark" aria-hidden="true"></span>${LABEL[id]}${id === "you" ? "" : `<span class="later"><span class="sr-only">,</span> not built yet</span>`}${id === place ? "" : `<span class="sr-only">, ${id === "you" ? "visited" : "not started"}</span>`}</a></li>`).join("")}</ol>
    </nav>`;
  // The person's targets, as the app's strip names them: P01's, and the two long invented ones.
  const targetTitles = [...F.p01.targetTitles, ...(state === "three-targets" ? LONG.map((d) => d.title) : [])];
  const strip = `
    <header class="strip">
      <span class="synthetic-slot">${synthetic}</span>
      <span class="optional-phone">Target <strong>${esc(targetTitles.join(", "))}</strong></span>
      <span class="optional">Work area <strong>${esc(F.p01.cities.join(", "))}</strong></span>
      <span class="strip-end">
        <span>Answers saved</span>
        ${/* Live updates that work say nothing; only a state that isn't live is shown. */ ""}
        <span class="sr-only" role="status"></span>
        ${controls}
      </span>
    </header>`;
  const topbar = `<div class="topbar"><button type="button" class="toggle" aria-label="${LABEL[place]}, open chapter menu">${glyph("menu")}<strong>${LABEL[place]}</strong></button>${stillStatus}${synthetic}</div>`;

  // A place not built yet: the honest state, where it is, why it is empty and the one action;
  // what it will hold is one step away.
  const notBuilt = (where, why, holds) => `
    <section class="panel low" aria-labelledby="title">
      <p class="kicker" data-tone="unknown">${glyph("blocked")}Not built yet</p>
      <h1 id="title" class="title">${LABEL[place]}</h1>
      <p class="where">${where}</p>
      <p class="small muted">${why}</p>
      <div class="row"><a class="btn btn-secondary" href="world.html?place=you">Review what we know</a></div>
      <details class="more"><summary>More about this place</summary><p class="small muted">${holds}</p></details>
    </section>`;

  const NOT_BUILT = {
    roles: ["The horizon: places you could head for.", "Role research isn't ready yet, so no listings have been searched.", "Roles you could head for, and openings for them in your work areas, with the sources checked."],
    skills: ["The ground between you and a destination.", "Skills checking isn't ready yet, so nothing has been assessed or marked missing.", "What each target needs, what you have shown, and what is still not known."],
    options: ["Bridges across the dark stretches: courses, work routes and funding.", "Option research isn't ready yet, so no courses or funding have been searched.", "Courses, work routes and funding for each gap, with their dates and costs."],
    routes: ["Whole journeys from you to a destination, compared on time and cost.", "Route search isn't ready yet, so no route has been worked out.", "Every way to a destination, with how long it takes and what it costs."],
    plan: ["The path you choose, made solid, with your next move glowing at its start.", "Plan selection isn't ready yet, so no plan has been made.", "The route you choose, as a dated plan with one next step."],
  };

  // The plain names for TRACE-01's two costs; DIRECTAI's direct spending keeps its own words.
  const TOTAL_COST = "Total cost, including pay you'd give up";
  const PAID_OUT = "What you'd pay out";

  function instrument(failed) {
    // Time (months) across, TRACE-01's total cost up: its routes, layers told apart without colour.
    const W = 520;
    const H = 252;
    const pad = { l: 56, r: 24, t: 32, b: 52 };
    const maxT = 6;
    const maxC = 600000;
    const x = (t) => pad.l + (t / maxT) * (W - pad.l - pad.r);
    const y = (c) => H - pad.b - (c / maxC) * (H - pad.t - pad.b);
    const layer = (id) => T.fronts.findIndex((front) => front.includes(id)) + 1;
    const labelled = [];
    const marks = T.routes.map((r) => {
      const l = layer(r.id);
      const sel = r.id === T.selectedRoute && !failed;
      const cx = x(r.timeMonths);
      const cy = y(r.economicMinor);
      // A letter goes right of its mark, or left where a mark at the same time sits close by.
      const crowded = labelled.some((o) => o.cx === cx && Math.abs(o.cy - cy) < 22);
      labelled.push({ cx, cy });
      const shape = l === 1 ? `fill="none" stroke="#F2F6FF" stroke-width="2"` : l === 2 ? `fill="#9AA6C2"` : `fill="none" stroke="#9AA6C2" stroke-width="2"`;
      return `<circle cx="${cx}" cy="${cy}" r="7" ${shape}/>${sel ? `<circle cx="${cx}" cy="${cy}" r="12" fill="none" stroke="#45F7D4" stroke-width="2"/>` : ""}<text class="mark-label" x="${crowded ? cx - 16 : cx + 16}" y="${cy + 4}" text-anchor="${crowded ? "end" : "start"}">${r.id}</text>`;
    });
    const ticks = [0, 2, 4, 6].map((t) => `<text x="${x(t)}" y="${H - 30}" text-anchor="middle">${t}</text>`).join("");
    const cticks = [0, 200000, 400000, 600000].map((c) => `<text x="${pad.l - 8}" y="${y(c) + 4}" text-anchor="end">${money(c)}</text>`).join("");
    const axis = `<text class="axis-name" x="0" y="12">${esc(TOTAL_COST)}</text><text class="axis-name" x="${(pad.l + W - pad.r) / 2}" y="${H - 8}" text-anchor="middle">Months to ready</text>`;
    return `<figure class="instrument"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Months to ready and total cost, including pay you'd give up, of routes A to E">${axis}${ticks}${cticks}${marks.join("")}</svg></figure>`;
  }

  const route = (id) => T.routes.find((r) => r.id === id);
  const B = route(T.selectedRoute);
  const unpaid = L.jobs.filter((j) => j.pay.kind === "unknown").length;

  function panel() {
    if (state === "not-built" && NOT_BUILT[place]) return notBuilt(...NOT_BUILT[place]);
    if (place === "you") {
      if (state === "distress") {
        return `
          <section class="panel panel-wide" aria-labelledby="title">
            <h1 id="title" class="title">You</h1>
            <p class="answer">Synthetic: I've been feeling hopeless about work lately.</p>
            <p>Thank you for telling me. We can take this slowly. Would a smaller next step help, like naming one thing you've enjoyed doing?</p>
            <section class="alert support" data-tone="neutral" aria-labelledby="support">
              ${glyph("support")}
              <div class="list">
                <h2 id="support" class="small"><strong>Support is here, any time</strong></h2>
                <p class="small">If anything you mentioned is about how you are feeling, people trained to help are available. Your message was sent as usual.</p>
                <ul class="list">
                  <li><span><strong>Emergency services</strong>: call 999 or go to A&amp;E if your life is at risk now</span></li>
                  <li><span><strong>NHS 111</strong>: call 111 and choose the mental health option</span></li>
                  <li><span><strong>Samaritans</strong>: call 116 123, free, day or night</span></li>
                  <li><span><strong>Shout</strong>: text SHOUT to 85258, free, 24/7</span></li>
                </ul>
              </div>
            </section>
          </section>`;
      }
      // The console's three views, as tabs (SW.4: one idea per view; the suggestions on a tab of
      // their own). Each tab leads to its view's page here.
      const view = state === "known" ? "known" : state === "suggestions" ? "suggestions" : "conversation";
      const VIEWS = [["conversation", "Conversation", "default"], ["known", "What we know", "known"], ["suggestions", "Suggestions", "suggestions"]];
      const tabs = `
        <div class="tabs" role="tablist" aria-label="You">${VIEWS.map(([id, label, page]) => `<a role="tab" id="tab-${id}" href="world.html?place=you&amp;state=${page}" aria-selected="${id === view}"${id === view ? ' aria-controls="view"' : ' tabindex="-1"'}>${label}</a>`).join("")}</div>`;
      const field = (primary) => `
          <p class="field" aria-hidden="true">Reply in your own words</p>
          <div class="row"><button type="button" class="btn ${primary ? "btn-primary" : "btn-secondary"}">Send</button></div>`;
      // A limit says what it means wherever it is shown (session 2: "what do these mean??").
      const SPEND = "The most you'd spend on the whole change, all added up: course fees, exams, equipment and the like. Pay you'd give up while you train isn't part of it.";
      const MONTHLY = "The most you could pay out in any one month. A route with a bigger payment in some month doesn't fit, even if its total does.";
      const asked = `
          <p class="answer">Synthetic: I could do 5 hours a week, and spend up to £600.</p>
          <p class="reply">${glyph("mark")}<span>Demo interviewer (synthetic): I noted 2 things for you to review.</span></p>`;
      const atConsole = (body) => `
        <section class="panel console" aria-labelledby="title"${slimBand ? ' data-band="slim"' : ""}>
          <h1 id="title" class="title">You</h1>${tabs}
          <div class="view" role="tabpanel" id="view" aria-labelledby="tab-${view}">${body}</div>
        </section>`;
      if (state === "review") {
        // A reply's proposals: accept and confirm in leaf green (on a faint leaf tint once
        // chosen), the one bright action is saving them, Send waits, and the next question waits
        // until they are decided (one decision at a time).
        return atConsole(`
          ${asked}
          <section class="tray" aria-labelledby="tray">
            <h2 id="tray" class="small"><strong>To review: 2 changes from your last message</strong></h2>
            <div class="proposal">
              <p class="small muted">You said</p>
              <p><strong>Weekly study hours: 5 hours a week</strong></p>
              <div class="row"><button type="button" class="btn btn-accept" aria-pressed="false">${glyph("accept")}Confirm<span class="sr-only"> weekly study hours as a limit</span></button><button type="button" class="btn btn-secondary">Edit</button><button type="button" class="link">Skip</button><button type="button" class="link">Source</button></div>
            </div>
            <div class="proposal" data-basis="inferred">
              <p class="small muted">Careerwright's reading, not a fact until you accept it</p>
              <p><strong>Total spending limit: £600</strong></p>
              <p class="small muted">${SPEND}</p>
              <div class="row"><button type="button" class="btn btn-accept" aria-pressed="true">${glyph("accept")}Confirm<span class="sr-only"> total spending limit as a limit</span></button><button type="button" class="btn btn-secondary">Edit</button><button type="button" class="link">Skip</button><button type="button" class="link">Source</button></div>
            </div>
            <div class="row"><button type="button" class="btn btn-primary">Save 1 to What we know</button><button type="button" class="link">Keep none</button></div>
          </section>
          ${field(false)}`);
      }
      if (state === "saved") {
        // The decision made: what it did, where it was made, with Undo in orchid.
        return atConsole(`
          ${asked}
          <section class="notice" aria-labelledby="saved"><h2 id="saved" class="small"><strong>Saved to What we know</strong></h2>
            <button type="button" class="btn btn-undo">${glyph("undo")}Undo the last save</button>
          </section>
          <p class="question">About how many hours a week could you give to learning?</p>
          ${field(true)}`);
      }
      if (state === "known") {
        // The view's action first, under its heading, so a phone shows it in the first screen
        // however many answers there are (Task W2E fix round 1); the answers follow.
        return atConsole(`
          <h2 class="sentence">What we know</h2>
          <div class="row"><button type="button" class="btn btn-secondary">Edit answers directly</button></div>
          <dl class="known-facts">
            <div><dt>Target roles</dt><dd>${esc(F.p01.targetTitles.join(", "))}</dd></div>
            <div><dt>Work areas</dt><dd>${esc(F.p01.cities.join(", "))}</dd></div>
            <div><dt>Total spending limit<span class="explained">${SPEND}</span></dt><dd class="tnum">${money(F.p01.directSpendCapMinor)}</dd></div>
            <div><dt>Monthly payment limit<span class="explained">${MONTHLY}</span></dt><dd class="tnum">${money(F.p01.monthlyPaymentCapMinor)}</dd></div>
          </dl>
          <p class="small muted">Not asked yet: current role, weekly study hours, lowest pay you'd accept.</p>
          <details class="more"><summary>The early sketch for your target</summary><p class="small muted">Early sketch, not a checked route: the skills ESCO lists for data quality analyst work, and every step not resolved yet.</p></details>`);
      }
      if (state === "suggestions") {
        // A real slate's shape (design review I3: never only the attractive fixture): the slate
        // for the role "data analyst" (Task W2B's evaluation, case DSC-10: its six titles and its
        // notes' words; the counts and the lines in the open card are examples). The view's
        // controls and count line, the notes one step away, one suggestion open with its choice
        // right after its title, edged as the selection, its "Make this a target" the view's one
        // bright action; the rest titles to scan.
        const groups = [
          ["Close to what you do now", [["Data scientist", "Mathematicians, actuaries and statisticians"], ["Data quality specialist", "Database and network professionals"]]],
          ["Builds on skills you could carry over", [["Chief data officer", "Information and communications technology service managers"], ["Knowledge engineer", "Software and applications developers and analysts"], ["Big data archive librarian", "Librarians, archivists and curators"]]],
          ["Something different", [["Data entry clerk", "Keyboard operators"]]],
        ];
        const NOTES = [
          "Careerwright found 47 other occupations in ESCO that share 3 or more essential skills with “data analyst”, and keeps the 30 with the largest share of essential skills in common.",
          "Careerwright chose these from 31 occupations that match your answers closely. It aims for at least 60, but doesn't add weaker matches to get there.",
        ];
        const card = ([title, kind], i) =>
          i === 0
            ? `<article class="suggestion" data-open="true" aria-labelledby="s-0">
                <h4 id="s-0"><button type="button" aria-expanded="true" aria-disabled="true">${esc(title)}${glyph("expand")}</button></h4>
                <p class="small muted">Kind of work: ${esc(kind)}</p>
                <div class="row"><button type="button" class="btn btn-primary">Make this a target</button><button type="button" class="link">Not for me</button><button type="button" class="link">Exclude this kind of work</button><button type="button" class="link">Source</button></div>
                <p class="small">Data scientists find and interpret rich data sources, manage large amounts of data, merge data sources and ensure the consistency of data sets, and create visualisations to help understand data…</p>
                <p class="small"><strong>Why this could suit you</strong></p>
                <ul class="bullets"><li>Your current role: “data analyst”. ESCO lists 12 of the same essential skills for both, so Careerwright joined them by those skills.</li></ul>
                <p class="small"><strong>What might not suit you</strong></p>
                <ul class="bullets"><li>ESCO lists 24 essential skills, not yet compared with your experience, including: build recommender systems, collect ICT data, deliver visual presentation of data.</li><li>Entry requirements aren't researched yet.</li></ul>
                <p class="small"><strong>Try it before committing</strong></p>
                <ul class="bullets"><li>Talk to someone who does this work about a typical week (an informational interview).</li></ul>
                <p class="small muted">Pay, demand and listings in your work areas aren't researched yet.</p>
              </article>`
            : `<article class="suggestion" data-open="false" aria-labelledby="s-${i}"><h4 id="s-${i}"><button type="button" aria-expanded="false">${esc(title)}${glyph("collapse")}</button></h4><p class="small muted">Kind of work: ${esc(kind)}</p></article>`;
        let n = 0;
        return atConsole(`
          <h2 class="sentence">Directions to explore</h2>
          <p class="small muted">Occupations from ESCO, found from your own answers. Ideas to test, not a judgement of fit: no score or percentage.</p>
          <div class="segmented" role="group" aria-label="Which directions to show">${["Balanced", "Closer to what I do", "Less familiar", "Broader", "More depth"].map((e, i) => `<button type="button" class="btn btn-secondary" aria-pressed="${i === 0}">${e}</button>`).join("")}</div>
          <p class="small muted">6 of up to 6, from 31 occupations found by 1 search of ESCO. 17 more were found but not kept.</p>
          <details class="notes"><summary>How Careerwright searched (${NOTES.length} notes)</summary><ul class="bullets">${NOTES.map((t) => `<li>${esc(t)}</li>`).join("")}</ul></details>
          ${groups.map(([heading, items], g) => `<section class="group" aria-labelledby="g-${g}"><h3 id="g-${g}" class="group-title">${esc(heading)}</h3>${items.map((item) => card(item, n++)).join("")}</section>`).join("")}
          <p class="small muted">The slate for “data analyst”, from Careerwright's evaluation: its titles and notes; the counts and the open card's lines are examples for design review.</p>`);
      }
      const failed = state === "failed";
      return atConsole(`
          <p class="question">What do you do now, or what did you do last?</p>
          <p class="answer"${failed ? ' data-failed="true"' : ""}>Synthetic: I check customer records for a housing association.${failed ? `<br><span class="status" data-tone="error">${glyph("error")}Not processed</span>` : ""}</p>
          ${failed ? `<div class="alert" data-tone="error" role="alert">${glyph("error")}<div><p><strong>Careerwright's reply didn't arrive</strong></p><p class="small muted">Your message is kept. Nothing about you changed.</p></div></div>` : `<p>Records officers usually need these skills. Pick any you've used, and it lights up.</p>`}
          <p class="field" aria-hidden="true">Tell me more…</p>
          <div class="row"><button type="button" class="btn btn-primary">${failed ? "Try again" : "Send"}</button></div>`);
    }
    if (place === "roles") {
      const stale = state === "stale";
      const unknown = state === "unknown";
      // On a phone the openings are listed here, by area, rather than drawn (see build).
      const openings = AREAS.map((a) => a.words).join("; ");
      if (state === "three-targets") {
        return `
          <section class="panel low panel-roles" aria-labelledby="title">
            <h1 id="title" class="title">Roles</h1>
            <p class="where">Three places you chose to head for.</p>
            <p class="small muted">${phone ? `Openings for the one you're looking at, data quality analyst: ${openings}.` : "Openings are shown around the one you're looking at: data quality analyst."} Not job offers.</p>
            <div class="row"><button type="button" class="btn btn-primary">Look at another</button></div>
          </section>`;
      }
      return `
        <section class="panel low panel-roles" aria-labelledby="title">
          <h1 id="title" class="title">Roles</h1>
          <p class="small">ESCO lists 6 of the same essential skills for data quality analysts and statisticians.</p>
          <p class="small muted">Joined by skills, not job titles. A place you could head for. Not a job offer.</p>
          ${phone ? `<p class="small muted">Openings for ${esc(T.targetTitle.toLowerCase())}: ${openings}.</p>` : ""}
          ${stale ? `<div class="alert" data-tone="stale">${glyph("stale")}<div><p><strong>Last checked 2 days ago</strong></p><p class="small muted">The job board didn't answer today. Its openings are kept from 2 days ago and may have closed.</p></div></div>` : ""}
          ${unknown ? `<div class="alert" data-tone="unknown">${glyph("unknown")}<div><p><strong>Leeds: none found in the ${L.totals.sourcesChecked} sources checked</strong></p><p class="small muted">Not "no jobs": only these sources were searched. Pay not stated on ${count(unpaid, "opening", "openings")}.</p></div></div>` : ""}
          <div class="row"><button type="button" class="btn btn-primary">Keep statistician in view</button><button type="button" class="link">Why?</button></div>
        </section>`;
    }
    if (place === "skills") {
      const unknown = state === "unknown";
      return `
        <section class="panel low" aria-labelledby="title">
          <h1 id="title" class="title">Skills</h1>
          <p class="where">The ground between you and ${esc(T.targetTitle.toLowerCase())}.</p>
          <ul class="list">
            <li>${glyph(unknown ? "unknown" : "said")}<span>Check data for errors</span><span class="small muted">${unknown ? "Not known yet" : "You said so"}</span></li>
            <li>${glyph("unknown")}<span>Query related tables</span><span class="small muted">${unknown ? "Not known yet" : "ESCO lists it for this kind of work, not confirmed yet"}</span></li>
            <li>${glyph("unknown")}<span>Validate keys and missing values</span><span class="small muted">Not known yet</span></li>
            <li>${glyph("conditional")}<span>Pass the assessed report</span><span class="small muted">A gate</span></li>
          </ul>
          <p class="status" data-tone="neutral">${glyph("conditional")}Ready if you pass the assessed report</p>
          <div class="row"><button type="button" class="btn btn-primary">Tell me about a skill</button></div>
        </section>`;
    }
    if (place === "options") {
      const unknown = state === "unknown";
      return `
        <section class="panel low" aria-labelledby="title">
          <h1 id="title" class="title">Options</h1>
          <p class="where">Bridges across the dark stretches.</p>
          ${unknown ? `<div class="alert" data-tone="unknown">${glyph("unknown")}<div><p><strong>No bridge found yet</strong></p><p class="small muted">Nothing searched covers "Validate keys and missing values". That doesn't mean there are none.</p></div></div>` : `
          <ul class="list">
            <li data-selected="true">${glyph("complete")}<span>Part-time course, ${B.timeMonths} months, ${B.studyHours} hours a week</span><span class="tnum">${money(B.directMinor)}</span></li>
            <li>${glyph("setAside")}<span>Full-time course, ${route("A").timeMonths} months, ${route("A").studyHours} hours a week</span><span class="small muted">Set aside</span></li>
          </ul>`}
          <div class="row"><button type="button" class="btn btn-primary">${unknown ? "Look for a course" : "Use this course"}</button></div>
        </section>`;
    }
    if (place === "routes") {
      const failed = state === "failed";
      return `
        <section class="panel panel-wide" aria-labelledby="title">
          <h1 id="title" class="title">Routes</h1>
          ${failed ? `<div class="alert" data-tone="error" role="alert">${glyph("error")}<div><p><strong>The route search failed</strong></p><p class="small muted">Your last comparison is kept below. It may be out of date.</p></div></div>` : ""}
          ${failed ? `<p class="status" data-tone="stale">${glyph("stale")}Kept from your last search</p>` : ""}
          ${instrument(failed)}
          <dl class="facts">
            <dt>Route ${B.id}: ready in</dt><dd>${B.timeMonths} months, from ${day(B.start)}</dd>
            <dt>${TOTAL_COST}</dt><dd>${money(B.economicMinor)}</dd>
            <dt>${PAID_OUT}</dt><dd>${money(B.directMinor)}</dd>
            <dt>Lowest cash point</dt><dd>${money(T.print.minimumPrefundedCashMinor)}</dd>
          </dl>
          <p class="status" data-tone="neutral">${glyph("conditional")}Ready if you pass the assessed report</p>
          <div class="row"><button type="button" class="btn btn-primary">${failed ? "Search again" : `Choose route ${B.id}`}</button></div>
        </section>`;
    }
    return `
      <section class="panel low" aria-labelledby="title">
        <h1 id="title" class="title">Plan</h1>
        <p class="where">Route ${B.id}, made solid.</p>
        <p class="sentence">Next: start the part-time course on ${day(B.start)}.</p>
        <dl class="facts">
          <dt>Each month, for ${B.paymentsMinor.filter((p) => p > 0).length} months</dt><dd>${money(B.paymentsMinor[0])}</dd>
          <dt>Study</dt><dd>${B.studyHours} hours a week</dd>
          <dt>Ready</dt><dd>by ${day(B.finish)}, if you pass the assessed report</dd>
        </dl>
        <div class="row"><button type="button" class="btn btn-primary">Mark it started</button></div>
      </section>`;
  }

  // The key to the lights: each kind drawn here, with its mark drawn as the world draws it.
  const KEY = {
    destination: ["disc-destination", "Warm lights: places you chose to head for"],
    suggested: ["ring-destination", "Warm rings: places suggested to you"],
    said: ["disc-said", "Bright: you said you've done it"],
    usual: ["ring-usual", "Faint ring: ESCO lists it for this kind of work, not confirmed yet"],
    shadow: ["line-shadow", "Grey: not known yet"],
    "stretch-said": ["line-said", "Bright: a skill you said you have"],
    "stretch-usual": ["line-usual", "Fainter: ESCO lists it for this kind of work, not confirmed yet"],
    "stretch-shadow": ["line-shadow", "Grey: not known yet"],
    next: ["ring-next", "Teal ring: your next step"],
    opening: ["dot-opening", "Small lights: openings, by area"],
    "stale-opening": ["dot-stale", "Sand: openings kept from an earlier search"],
    "none-found": ["ring-none", "Grey ring: none found in the sources checked"],
    gate: ["gate", "Gate: a condition, in words beside it"],
    bridge: ["line-bridge", "Bright arc: a bridge you placed"],
    route: ["line-route", "Blue to violet: a whole route"],
    looking: ["line-chosen", "Teal: the route you're looking at"],
    chosen: ["line-chosen", "Teal: the path you chose"],
    stale: ["line-stale", "Sand: kept from your last search, may be out of date"],
  };
  const ORDER = ["destination", "suggested", "said", "usual", "shadow", "stretch-said", "stretch-usual", "stretch-shadow", "opening", "stale-opening", "none-found", "gate", "bridge", "route", "looking", "chosen", "next", "stale"];

  // ---------- Assemble ----------
  document.title = `${LABEL[place]}, ${state} · Careerwright world reference`;
  document.body.innerHTML = `
    <div class="world" data-distress="${state === "distress"}"></div>
    <aside class="world-words" aria-label="Your world"><ul></ul></aside>
    <details class="legend"><summary>What the lights mean</summary><ul></ul></details>
    <div class="shell">
      ${rail}
      ${topbar}
      ${strip}
      <main class="work" id="main">${panel()}</main>
    </div>`;

  /** Lays the world out once the fonts are in: the view, the drawing, the names and the key. */
  function layout() {
    const clear = clearArea();
    const view = placeView(place, clear);
    const world = build(view);
    const { project } = world;
    document.querySelector(".world").innerHTML = drawWorld(world, view);

    const legend = document.querySelector(".legend");
    // Open on a wide screen where the world beside the panels has room for it (as the app).
    legend.open = vp.w > 1100 && clear !== undefined && !clear.backdrop && clear.right - clear.left >= 360;
    legend.querySelector("ul").innerHTML = ORDER.filter((k) => world.legend.has(k))
      .map((k) => `<li data-kind="${k}"><span class="key key-${KEY[k][0]}" aria-hidden="true"></span>${KEY[k][1]}</li>`)
      .join("");

    const covers = [...document.querySelectorAll(".panel, .strip, .rail, .topbar")].map(box).filter((r) => r.w > 0);
    const inside = (b, pad = 8) => b.x >= pad && b.y >= pad && b.x + b.w <= vp.w - pad && b.y + b.h <= vp.h - pad;
    const meets = (a, b, pad) => a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;
    const holds = (b, p) => p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h;
    // Every light's centre and every gate stays uncovered: names step round them.
    const centres = world.lights
      .map((l) => ({ name: l.name, p: project(l.p) }))
      .filter(({ p }) => p.visible)
      .map(({ name, p }) => ({ name, x: p.x - 4, y: p.y - 4, w: 8, h: 8 }));
    const gates = world.gates.map((g) => ({ name: g.name, p: project(g.p) })).map(({ name, p }) => ({ name, x: p.x - 10, y: p.y - 10, w: 20, h: 20 }));
    // In view: inside the window and not under a panel.
    const inView = (p) => p.visible && holds({ x: 0, y: 0, w: vp.w, h: vp.h }, p) && !covers.some((c) => holds(c, p));

    // The key: open on a wide screen with room, bottom right; otherwise "What the lights mean",
    // closed, at the right of the clear part of the window, above any panel, or else just below
    // the bars along the top; failing those, at its left. It takes the first of those spots from
    // which every light can still be named (below), and names stay clear of it. It explains
    // every light but the person's, the gates and the trails, so it shows only while one of them
    // is in view.
    legend.style.visibility = "hidden";
    const size = box(legend);
    const explained = [...world.lights.filter((l) => l.name !== "origin").map((l) => l.p), ...world.gates.map((g) => g.p), ...world.trails.flatMap((t) => t.points)];
    let barsBottom = 0;
    for (const c of [...covers].sort((a, b) => a.y - b.y)) if (c.y <= barsBottom + 1 && !(c.x <= 1 && c.h >= vp.h * 0.9)) barsBottom = Math.max(barsBottom, c.y + c.h);
    const corners = [vp.h - 24, ...covers.filter((c) => c.y > 1).map((c) => c.y - 12)].sort((a, b) => b - a).concat(barsBottom + 12 + size.h);
    const margin = phone ? 16 : 24;
    const railEdge = Math.max(0, ...covers.filter((c) => c.x <= 1 && c.h >= vp.h * 0.9).map((c) => c.x + c.w));
    const keySpots = explained.some((p) => inView(project(p)))
      ? [vp.w - margin - size.w, railEdge + margin]
          .flatMap((x) => corners.map((bottom) => ({ x, y: bottom - size.h, w: size.w, h: size.h })))
          .filter((b) => inside(b, 4) && !covers.some((c) => meets(b, c, 0)) && !centres.some((c) => meets(b, c, 0)) && !gates.some((g) => meets(b, g, 0)))
      : [];

    // Names beside their lights, clear of the panels, the key, the lights, the lines already drawn
    // and each other. A name whose light is out of view or under a panel is hidden from sight; it
    // stays in the list. Every name is measured first, then placed, then written.
    const host = document.querySelector(".world-words ul");
    const PRIORITY = { origin: 0, destination: 1, suggested: 1, gate: 2, next: 2, route: 3, area: 4, bridge: 4, stretch: 5, skill: 6 };
    const items = world.labels
      .sort((a, b) => PRIORITY[a.kind] - PRIORITY[b.kind])
      .map((l) => {
        const li = document.createElement("li");
        li.className = "world-label";
        li.dataset.kind = l.kind;
        li.dataset.for = l.id;
        if (l.selected) li.dataset.selected = "true";
        li.innerHTML = `<span class="name">${esc(l.name)}</span>`;
        if (l.state === "usual") li.innerHTML += `<span class="caption">ESCO lists it for this kind of work, not confirmed yet</span>`;
        if (l.state === "said") li.innerHTML += `<span class="caption">you said so</span>`;
        if (l.state === "shadow" && !l.name.includes("no bridge")) li.innerHTML += `<span class="caption">not known yet</span>`;
        host.append(li);
        return { l, li, p: project(l.anchor) };
      });
    for (const item of items) {
      item.w = item.li.offsetWidth;
      item.h = item.li.offsetHeight;
    }
    // A name further than this from its light is joined to it by a line, stopping short of it.
    const LEADER_FROM = 20;
    const LEADER_CLEAR = 8;
    const GAP = 14;
    const flip = { above: "below", below: "above", left: "right", right: "left" };

    /** Each name's spot (or null) and the line back to its light (or null), placing in `order`. */
    function placeNames(order, keySpot) {
      const placed = keySpot ? [keySpot] : [];
      const lines = [];
      const spots = new Map();
      for (const item of order) {
        const { l, p, w, h } = item;
        // Centred on its light, or slid along its row (inside the window, still over its light).
        const across = (x) => Math.min(Math.max(x, 8), vp.w - 8 - w);
        const row = (side, n, x) => {
          const out = GAP + n * (h + 6);
          return { x: across(x), y: side === "above" ? p.y - out - h : p.y + out, w, h };
        };
        const beside = (side) => ({ x: side === "left" ? p.x - GAP - w : p.x + GAP, y: p.y - h / 2, w, h });
        // Its own side first, then rows further out (with a line back), then the other side. Along
        // a row it is centred, then slid either way while it still reaches over its light, as far
        // as its light standing at its very end. A name that starts at its light tries beginning
        // just left of it on every row first.
        const ROWS = [0, 1, 2, 3, 4, 5, 6, 7];
        const rows = (side, xs = [p.x - w / 2, p.x - w + 16, p.x - 16, p.x - w + 8, p.x - 8]) => ROWS.flatMap((n) => xs.map((x) => row(side, n, x)));
        const tries =
          l.side === "left" || l.side === "right"
            ? [beside(l.side), beside(flip[l.side]), ...rows("above"), ...rows("below")]
            : [...(l.align === "start" ? rows(l.side, [p.x - 8]) : []), ...rows(l.side), ...rows(flip[l.side])];
        // The line from a light to its name never passes under a panel (a name never hops one),
        // and the line a name draws never crosses another light, gate or name, or the key: a line
        // joins a name to its own light only.
        const leader = (b) => ({ x: p.x, y: Math.min(p.y, b.y + b.h), w: 1, h: Math.abs(Math.max(p.y, b.y) - Math.min(p.y, b.y + b.h)) });
        const gapTo = (b) => (b.y + b.h <= p.y ? p.y - (b.y + b.h) : b.y - p.y);
        const lineTo = (b) => (gapTo(b) > LEADER_FROM && b.x <= p.x && p.x <= b.x + b.w ? leader(b) : null);
        const clearLine = (line) => line === null || (!placed.some((o) => meets(line, o, 0)) && !centres.some((c) => c.name !== l.id && meets(line, c, 0)) && !gates.some((g) => g.name !== l.id && meets(line, g, 0)));
        const spot = inView(p)
          ? tries.find((b) => inside(b) && !covers.some((c) => meets(b, c, 0) || meets(leader(b), c, 0)) && !placed.some((o) => meets(b, o, 4)) && !lines.some((line) => meets(b, line, 0)) && !centres.some((c) => meets(b, c, 0)) && !gates.some((g) => meets(b, g, 2)) && clearLine(lineTo(b)))
          : undefined;
        if (spot === undefined) {
          spots.set(item, null);
          continue;
        }
        const line = lineTo(spot);
        placed.push(spot);
        if (line !== null) lines.push(line);
        spots.set(item, { spot, line, gap: gapTo(spot) });
      }
      return spots;
    }

    // A name left without a spot while its light is in view chooses first next time, so the
    // hardest names choose first. The placing kept leaves the fewest lights and gates unnamed,
    // then the fewest other names (a route's or a stretch's) out of sight.
    const named = new Set([...world.lights, ...world.gates].map((l) => l.name));
    const unnamed = (spots) => items.filter((item) => spots.get(item) === null && inView(item.p));
    const score = (spots) => {
      const left = unnamed(spots);
      return left.filter((item) => named.has(item.l.id)).length * 1000 + left.length;
    };
    function placeAll(keySpot) {
      let order = items;
      let latest = placeNames(order, keySpot);
      let best = latest;
      for (let attempt = 0; attempt < 6 && unnamed(latest).length > 0; attempt++) {
        const left = unnamed(latest).sort((a, b) => Number(named.has(b.l.id)) - Number(named.has(a.l.id)));
        order = [...left, ...order.filter((item) => !left.includes(item))];
        latest = placeNames(order, keySpot);
        if (score(latest) < score(best)) best = latest;
      }
      return best;
    }
    let keySpot;
    let best;
    for (const spot of keySpots) {
      const spots = placeAll(spot);
      if (best === undefined || score(spots) < score(best)) {
        keySpot = spot;
        best = spots;
      }
      if (score(best) < 1000) break;
    }
    best ??= placeAll(undefined);
    if (keySpot) {
      legend.style.right = `${vp.w - keySpot.x - keySpot.w}px`;
      legend.style.bottom = `${vp.h - keySpot.y - keySpot.h}px`;
      legend.style.visibility = "visible";
    }
    for (const item of items) {
      const { li, p, w } = item;
      const placing = best.get(item);
      if (placing === null) {
        li.className = "sr-only";
        continue;
      }
      const { spot, line, gap } = placing;
      li.style.left = `${spot.x + w / 2}px`;
      li.style.top = `${spot.y}px`;
      if (line !== null) {
        li.dataset.leader = spot.y + spot.h <= p.y ? "above" : "below";
        li.style.setProperty("--leader", `${Math.round(gap - LEADER_CLEAR)}px`);
        li.style.setProperty("--leader-x", `${Math.round(p.x - spot.x)}px`);
      }
    }

    // For tools/screenshots.mjs: every light, gate and trail as drawn, to check independently.
    window.__worldCheck = {
      // No room beside or above the panels: the world stands behind them (a band under MIN_BAND).
      backdrop: Boolean(clear?.backdrop),
      lights: world.lights.map((l) => ({ id: l.id, kind: l.kind, name: l.name, revelation: Boolean(l.revelation), ...project(l.p) })),
      gates: world.gates.map((g) => ({ id: g.id, name: g.name, ...project(g.p), r: 10 })),
      trails: world.trails.map((t) => t.points.map(project)),
    };
    // Opened as a person would open it: over the world, from where it was placed closed.
    if (keyOpen) legend.open = true;
    window.__worldReady = true;
  }
  document.fonts.ready.then(layout);
})();
