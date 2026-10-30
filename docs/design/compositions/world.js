// The living world's design reference: one place and one state per page
// (world.html?place=you|roles|skills|options|routes|plan&state=...). The world is drawn still,
// as SVG, in Horizon's geometry (the app's apps/web/src/lib/world/geometry.ts holds the same
// views); every word, figure and control is in the DOM over it. Values from fixtures/ come from
// data.js FIXTURES (checked by tools/check-fixture-data.mjs); everything else is invented for
// design review and says so on the page.
(() => {
  const { FIXTURES: F, DESIGN_LISTINGS: L } = window.CAREERWRIGHT;
  const T = F.trace01;
  const params = new URLSearchParams(location.search);
  const PLACES = ["you", "roles", "skills", "options", "routes", "plan"];
  const place = PLACES.includes(params.get("place")) ? params.get("place") : "you";
  const state = params.get("state") ?? "default";
  const LABEL = { you: "You", roles: "Roles", skills: "Skills", options: "Options", routes: "Routes", plan: "Plan" };

  // ---------- Words and numbers ----------
  const money = (minor) => {
    const pounds = minor / 100;
    return `£${pounds.toLocaleString("en-GB", { minimumFractionDigits: Number.isInteger(pounds) ? 0 : 2, maximumFractionDigits: 2 })}`;
  };
  const day = (iso) => new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // The product's glyphs (apps/web/src/components/Glyph.tsx), drawn in the same 24-unit style.
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
    pause: `<circle cx="12" cy="12" r="9" ${S}/><path d="M10 8.5v7M14 8.5v7" ${S}/>`,
    calm: `<path d="M3.5 9.5c2.8-2 5.7-2 8.5 0s5.7 2 8.5 0" ${S}/><path d="M3.5 15.5h17" ${S}/>`,
    sound: `<path d="M4.5 9.5h3.2L12 5.5v13l-4.3-4H4.5z" ${S}/><path d="M15.5 9a4.2 4.2 0 0 1 0 6M18 6.5a7.8 7.8 0 0 1 0 11" ${S}/>`,
    menu: `<path d="M4 7h16M4 12h16M4 17h10" ${S}/>`,
    live: `<circle cx="12" cy="12" r="3.2" fill="currentColor"/><circle cx="12" cy="12" r="7.5" ${S}/>`,
  };
  const glyph = (name) => `<svg viewBox="0 0 24 24" class="glyph" aria-hidden="true" focusable="false">${GLYPH[name]}</svg>`;

  // ---------- Horizon's geometry (mirrors apps/web/src/lib/world/geometry.ts) ----------
  const vp = { w: window.innerWidth, h: window.innerHeight };
  const phone = vp.w <= 760;
  const kx = Math.min(1, vp.w / vp.h / 1.6);
  const ORIGIN = [0, 0.04, 1.7];
  const HORIZON_Z = 17;
  const VIEWS = {
    you: { x: 0, z: 0.25, eye: 0.62, horizon: 0.36, centre: phone ? 0.5 : 0.7, focal: 0.6 },
    roles: { x: 0, z: -1, eye: 1, horizon: 0.4, centre: phone ? 0.5 : 0.62, focal: 1.0 },
    skills: { x: 0, z: -0.4, eye: 0.42, horizon: 0.3, centre: phone ? 0.5 : 0.64, focal: 0.8 },
    options: { x: 0, z: -1.2, eye: 2.4, horizon: 0.22, centre: phone ? 0.5 : 0.64, focal: 0.8 },
    routes: { x: 0, z: -2.6, eye: 3.2, horizon: 0.2, centre: phone ? 0.5 : 0.66, focal: 0.72 },
    plan: { x: 0, z: -0.6, eye: 0.9, horizon: 0.34, centre: phone ? 0.5 : 0.64, focal: 0.66 },
  };
  const v = VIEWS[place];
  const view = { ...v, horizon: v.horizon * vp.h, centre: v.centre * vp.w, focal: v.focal * vp.h };
  // On a phone the place's sheet covers the lower half: the world's focus rises above it.
  if (phone) view.horizon -= vp.h * 0.16;
  const project = (p) => {
    const d = p[2] - view.z;
    if (d < 0.05) return { x: -1e5, y: -1e5, scale: 0, visible: false };
    const scale = view.focal / d;
    return { x: view.centre + (p[0] - view.x) * scale, y: view.horizon + (view.eye - p[1]) * scale, scale, visible: true };
  };
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

  // ---------- What each place shows (the world's states) ----------
  // Destinations: P01's target (fixture) and, at Roles, suggested places (invented examples).
  const target = { id: "target", title: T.targetTitle, kind: "destination" };
  const SUGGESTED = ["Records manager", "Data steward", "Statistician", "Business analyst"].map((title) => ({ id: title, title, kind: "suggested" }));
  const SKILLS = [
    { id: "s1", label: "Check data for errors", state: "said" },
    { id: "s2", label: "Explain findings clearly", state: "said" },
    { id: "s3", label: "Keep accurate records", state: "usual" },
    { id: "s4", label: "Work to deadlines", state: "usual" },
    { id: "s5", label: "Use spreadsheets", state: "usual" },
  ];
  const lit = !(place === "you" && state === "not-built");
  const world = { lit, destinations: [], skills: [], trails: [], gates: [], marks: [], labels: [], legend: new Set() };
  const addLabel = (anchor, name, kind, extra = {}) => world.labels.push({ anchor, name, kind, ...extra });

  const destinations = place === "roles" && state !== "not-built" ? [...SUGGESTED, target].sort((a, b) => a.title.localeCompare(b.title)) : [target];
  destinations.forEach((d, j) => {
    d.p = destinationAt(j, destinations.length);
    world.destinations.push(d);
  });
  const goal = target.p;

  if (place === "you" || place === "skills") {
    SKILLS.forEach((s, i) => {
      const p = skillAt(i, SKILLS.length);
      world.skills.push({ ...s, p });
      world.trails.push({ points: lift(cubic(ORIGIN, [ORIGIN[0] + (p[0] - ORIGIN[0]) * 0.2, 0.02, ORIGIN[2] + (p[2] - ORIGIN[2]) * 0.45], [ORIGIN[0] + (p[0] - ORIGIN[0]) * 0.75, 0.02, ORIGIN[2] + (p[2] - ORIGIN[2]) * 0.8], p, 24), ORIGIN, p), state: s.state, width: [0.016, 0.013], hue: [0, 0.3] });
      world.legend.add(s.state);
    });
  }

  if (place === "you" || place === "roles") {
    for (const d of world.destinations) {
      world.trails.push({ points: sweep(ORIGIN, d.p, `shadow:${d.id}`), state: "shadow", width: [0.011, 0.05], hue: [0.1, 1] });
    }
    world.legend.add("shadow");
    world.legend.add("destination");
    if (place === "roles" && state !== "not-built") world.legend.add("suggested");
  }

  if (place === "roles" && state !== "not-built") {
    // Openings around the chosen destination, grouped by city (VIS-1's hierarchy).
    const areas = L.areas.map((a) => ({ ...a, count: L.jobs.filter((j) => L.companies.find((c) => c.id === j.company)?.area === a.id).length }));
    const rand = seeded("openings");
    areas.forEach((area, k) => {
      const centre = [goal[0] + (k - 1) * 2.6 * kx, 0.03, goal[2] - 3.2 + Math.abs(k - 1) * 0.6];
      const shown = state === "unknown" && area.id === "leeds" ? 0 : area.count;
      for (let i = 0; i < shown; i++) {
        const p = [centre[0] + (rand() - 0.5) * 1.6 * kx, 0.03, centre[2] + (rand() - 0.5) * 1.2];
        world.marks.push({ kind: "opening", p, stale: state === "stale" && area.id !== "remote" });
      }
      world.marks.push({ kind: "area", p: centre, empty: shown === 0 });
      const words = shown === 0 ? `${area.label}: none found in the ${L.totals.sourcesChecked} sources checked` : `${area.label}: ${shown} openings`;
      addLabel(centre, words, "area", { side: "below" });
    });
  }

  if (place === "skills" || place === "options" || place === "plan") {
    // The ground between the person and the destination, stretch by stretch. Its states come
    // from readiness (the Skills chapter, Sprint 4); here they are examples.
    const path = sweep(ORIGIN, goal, "ground", 0.6);
    const unknownAll = state === "unknown";
    const STRETCHES = [
      { name: "Check data for errors", state: unknownAll ? "shadow" : "said" },
      { name: "Query related tables", state: unknownAll ? "shadow" : "usual" },
      { name: "Validate keys and missing values", state: "shadow" },
      { name: "Write reproducible checks", state: "shadow" },
      { name: "Pass the assessed report", state: "shadow", gate: true },
    ];
    const per = Math.floor((path.length - 1) / STRETCHES.length);
    STRETCHES.forEach((stretch, k) => {
      const from = k * per;
      const to = k === STRETCHES.length - 1 ? path.length - 1 : (k + 1) * per;
      const chosen = place === "plan";
      world.trails.push({ points: path.slice(from, to + 1), state: chosen ? "chosen" : stretch.state, width: [0.02, 0.05], hue: [k / STRETCHES.length, (k + 1) / STRETCHES.length] });
      const mid = path[Math.floor((from + to) / 2)];
      if (stretch.gate && place !== "options") {
        world.gates.push({ p: path[from + 2] });
        addLabel(path[from + 2], "Ready if you pass the assessed report", "gate", { side: "above" });
      } else if (place === "skills") {
        addLabel(mid, stretch.name, "stretch", { side: k % 2 ? "above" : "below", state: stretch.state });
      }
      if (place === "options" && (stretch.state === "shadow" || stretch.gate)) {
        // A bridge across a dark stretch: placed (lit) or still to find (none drawn, words say so).
        const bridged = state !== "unknown" && (k === 2 || stretch.gate);
        if (bridged) {
          const a = path[from];
          const b = path[to];
          const top = [(a[0] + b[0]) / 2, 0.55, (a[2] + b[2]) / 2];
          world.trails.push({ points: cubic(a, top, top, b, 24), state: "bridge", width: [0.03, 0.04], hue: [0.4, 0.8] });
          addLabel(top, k === 2 ? "Bridge: part-time course" : "Bridge: assessed report, with the course", "bridge", { side: "above" });
        } else {
          addLabel(mid, `${stretch.name}: no bridge yet`, "stretch", { side: "below", state: "shadow" });
        }
      }
    });
    world.legend.add(place === "plan" ? "chosen" : "shadow");
    if (place !== "plan") world.legend.add("gate");
    world.legend.add("destination");
    if (place === "plan") {
      // Landmarks along the chosen path: one per month of route B (TRACE-01), the next move first.
      const months = T.routes.find((r) => r.id === T.selectedRoute).timeMonths;
      for (let m = 0; m <= months; m++) {
        const p = path[Math.min(path.length - 1, Math.round((m / months) * (path.length - 1)))];
        world.marks.push({ kind: m === 0 ? "next" : "landmark", p });
      }
      addLabel(path[2], "Next: start the course", "next", { side: "below" });
    }
  }

  if (place === "routes") {
    // Whole journeys from the person to the destination: TRACE-01's five routes. Where each
    // runs is layout only; the instrument beside it carries time and cost exactly.
    const bends = { A: -5, B: -2, C: 1, D: 4, E: 7 };
    for (const route of T.routes) {
      const selected = route.id === T.selectedRoute && state !== "failed";
      const pts = sweep(ORIGIN, goal, `route:${route.id}`, bends[route.id] * kx);
      world.trails.push({ points: pts, state: selected ? "chosen" : state === "failed" ? "stale" : "usual", width: [0.02, 0.05], hue: [0.1, 1] });
      addLabel(pts[Math.floor(pts.length * 0.55)], `Route ${route.id}`, "route", { side: "above", selected });
    }
    world.legend.add(state === "failed" ? "stale" : "chosen");
    world.legend.add("destination");
    if (state !== "failed") {
      world.gates.push({ p: sweep(ORIGIN, goal, "route:B", bends.B * kx)[40] });
      world.legend.add("gate");
    }
  }

  addLabel(ORIGIN, "You", "origin", { side: "below" });
  for (const d of world.destinations) {
    addLabel(d.p, d.title, d.kind === "suggested" ? "suggested" : "destination", { side: "above", selected: place === "roles" && d.id === "target" && state !== "not-built" });
  }

  // ---------- Drawing the still world ----------
  const BLUE = [64, 140, 255];
  const VIOLET = [158, 107, 255];
  const journey = (h) => {
    const t = Math.min(1, Math.max(0, h)) ** 2 * (3 - 2 * Math.min(1, Math.max(0, h)));
    return `rgb(${BLUE.map((b, i) => Math.round(b + (VIOLET[i] - b) * t)).join(",")})`;
  };
  const f = (n) => n.toFixed(1);
  function drawWorld() {
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
      let stroke;
      let opacity = 0.6;
      if (trail.state === "chosen") stroke = "#45F7D4";
      else if (trail.state === "shadow") {
        stroke = "#6F7EA3";
        opacity = 0.8;
      } else if (trail.state === "stale") {
        stroke = "#6F7EA3";
        opacity = 0.45;
      } else {
        parts.push(`<defs><linearGradient id="t${n}" gradientUnits="userSpaceOnUse" x1="${f(first.x)}" y1="${f(first.y)}" x2="${f(last.x)}" y2="${f(last.y)}"><stop offset="0" stop-color="${journey(trail.hue[0])}"/><stop offset="1" stop-color="${journey(trail.hue[1])}"/></linearGradient></defs>`);
        stroke = `url(#t${n})`;
        opacity = trail.state === "said" || trail.state === "bridge" ? 1 : 0.55;
      }
      for (let i = 0; i < pts.length - 1; i += 6) {
        const part = pts.slice(i, Math.min(pts.length, i + 7));
        const mid = part[Math.floor(part.length / 2)];
        const u = (i + 3) / Math.max(1, pts.length - 1);
        const w = Math.max(0.8, (trail.width[0] + (trail.width[1] - trail.width[0]) * Math.min(1, u)) * mid.scale);
        const d = `M${part.map((p) => `${f(p.x)} ${f(p.y)}`).join("L")}`;
        lines.push(`<path d="${d}" stroke="${stroke}" stroke-width="${f(w)}" stroke-opacity="${opacity}" fill="none" stroke-linecap="round"/>`);
        const bright = trail.state === "said" || trail.state === "chosen" || trail.state === "bridge";
        glow.push(`<path d="${d}" stroke="${stroke}" stroke-width="${f(w * 4 + 4)}" stroke-opacity="${bright ? 0.3 : trail.state === "shadow" ? 0.07 : 0.12}" fill="none" stroke-linecap="round"/>`);
      }
    });
    parts.push(`<g filter="url(#bloom)">${glow.join("")}</g><g>${lines.join("")}</g>`);
    // Lights.
    if (o.visible) {
      const r = Math.max(2.6, 0.034 * o.scale);
      parts.push(`<circle cx="${f(o.x)}" cy="${f(o.y)}" r="${f(r * (lit ? 9 : 5))}" fill="url(#halo-person)" opacity="${lit ? 0.85 : 0.35}"/>`);
      parts.push(`<circle cx="${f(o.x)}" cy="${f(o.y)}" r="${f(r * (lit ? 1 : 0.5))}" fill="#EDF5FF"/>`);
    }
    for (const s of world.skills) {
      const p = project(s.p);
      const r = Math.max(2.6, 0.026 * p.scale);
      parts.push(
        s.state === "said"
          ? `<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 3)}" fill="url(#halo-person)" opacity="0.7"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r)}" fill="#cfe0ff"/>`
          : `<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 0.85)}" fill="none" stroke="${journey(0.3)}" stroke-width="${f(Math.max(1.4, r * 0.32))}"/>`,
      );
      addLabel(s.p, s.label, "skill", { side: "above", state: s.state });
    }
    for (const d of world.destinations) {
      const p = project(d.p);
      const r = Math.max(2.6, 0.22 * p.scale);
      if (d.kind === "suggested") {
        parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 2.4)}" fill="url(#halo-destination)" opacity="0.45"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 0.85)}" fill="none" stroke="#FF9433" stroke-width="2"/>`);
      } else {
        parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 4)}" fill="url(#halo-destination)"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r)}" fill="#FFD2A1"/>`);
        if (place === "roles" && state !== "not-built") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r * 2.3)}" fill="none" stroke="#45F7D4" stroke-width="2"/>`);
      }
    }
    for (const m of world.marks) {
      const p = project(m.p);
      if (!p.visible) continue;
      if (m.kind === "opening") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="2.2" fill="${m.stale ? "#D6CBAE" : "#EDF5FF"}" opacity="${m.stale ? 0.55 : 0.75}"/>`);
      if (m.kind === "area") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="${m.empty ? 9 : 4}" fill="none" stroke="${m.empty ? "#6F7EA3" : "#C2CCE2"}" stroke-width="1.5" opacity="0.8"/>`);
      if (m.kind === "landmark") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="4" fill="none" stroke="#45F7D4" stroke-width="1.5"/>`);
      if (m.kind === "next") parts.push(`<circle cx="${f(p.x)}" cy="${f(p.y)}" r="9" fill="none" stroke="#45F7D4" stroke-width="2.5"/><circle cx="${f(p.x)}" cy="${f(p.y)}" r="16" fill="none" stroke="#45F7D4" stroke-width="1" opacity="0.5"/>`);
    }
    for (const g of world.gates) {
      const p = project(g.p);
      const s = Math.max(7, 0.12 * p.scale);
      parts.push(`<rect x="${f(p.x - s)}" y="${f(p.y - s)}" width="${f(s * 2)}" height="${f(s * 2)}" fill="#03050B" stroke="#F2F6FF" stroke-width="2" transform="rotate(45 ${f(p.x)} ${f(p.y)})"/>`);
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${vp.w} ${vp.h}" aria-hidden="true" focusable="false">${parts.join("")}</svg>`;
  }

  // ---------- The exact layer: shell and the place's panel ----------
  const synthetic = `<span class="synthetic">${glyph("synthetic")}Synthetic demo</span>`;
  const toggles = `
    <button type="button" class="toggle" aria-pressed="${state === "distress" ? "true" : "false"}">${glyph("pause")}<span class="label">Pause motion</span><span class="switch" aria-hidden="true"></span></button>
    <button type="button" class="toggle" aria-pressed="false">${glyph("calm")}<span class="label">Calm mode</span><span class="switch" aria-hidden="true"></span></button>
    <button type="button" class="toggle" aria-pressed="false">${glyph("sound")}<span class="label">Sound</span><span class="switch" aria-hidden="true"></span></button>`;
  const rail = `
    <nav class="rail" aria-label="Chapters">
      <a class="wordmark" href="index.html"><svg viewBox="0 0 24 24" aria-hidden="true">${GLYPH.mark}</svg><span>Careerwright</span></a>
      <ol>${PLACES.map((id) => `<li><a href="world.html?place=${id}" data-progress="${id === "you" ? "visited" : "todo"}"${id === place ? ' aria-current="page"' : ""}><span class="landmark" aria-hidden="true"></span>${LABEL[id]}${id === place ? "" : `<span class="sr-only">, ${id === "you" ? "visited" : "not started"}</span>`}</a></li>`).join("")}</ol>
    </nav>`;
  const strip = `
    <header class="strip">
      <span class="optional">${synthetic}</span>
      <span>Target <strong>${esc(F.p01.targetTitles.join(", "))}</strong></span>
      <span class="optional">Work area <strong>${esc(F.p01.cities.join(", "))}</strong></span>
      <span class="strip-end">
        <span class="optional">Saved, version 3</span>
        <span class="status" data-tone="neutral" role="status">${glyph("live")}Updates: Live</span>
        ${toggles}
      </span>
    </header>`;
  const topbar = `<div class="topbar"><button type="button" class="toggle" aria-label="${LABEL[place]}, open chapter menu">${glyph("menu")}<strong>${LABEL[place]}</strong></button>${synthetic}</div>`;

  const notBuilt = (where, purpose) => `
    <section class="panel low" aria-labelledby="title">
      <p class="kicker" data-tone="unknown">${glyph("blocked")}Not built yet</p>
      <h1 id="title" class="title">${LABEL[place]}</h1>
      <p class="where">${where}</p>
      <p class="small muted">${purpose}</p>
      <div class="row"><a class="btn btn-secondary" href="world.html?place=you">Review what we know</a></div>
    </section>`;

  const NOT_BUILT = {
    roles: ["The horizon: places you could head for.", "Role research isn't part of this build yet, so no listings have been searched."],
    skills: ["The ground between you and a destination.", "The skills matrix isn't part of this build yet. Nothing has been assessed, so nothing is marked missing."],
    options: ["Bridges across the dark stretches: courses, work routes and funding.", "Option research isn't part of this build yet. No courses or funding have been searched."],
    routes: ["Whole journeys from you to a destination, compared on time and cost.", "Careerwright's route search isn't part of this build yet, so no route has been computed."],
    plan: ["The path you choose, made solid, with your next move glowing at its start.", "Plan selection isn't part of this build yet, so no plan has been made."],
  };

  function instrument() {
    // Time (months) across, economic cost up: TRACE-01's routes, layers told apart without colour.
    const W = 520;
    const H = 236;
    const pad = { l: 56, r: 24, t: 16, b: 52 };
    const maxT = 6;
    const maxC = 600000;
    const x = (t) => pad.l + (t / maxT) * (W - pad.l - pad.r);
    const y = (c) => H - pad.b - (c / maxC) * (H - pad.t - pad.b);
    const layer = (id) => T.fronts.findIndex((front) => front.includes(id)) + 1;
    const labelled = [];
    const marks = T.routes.map((r) => {
      const l = layer(r.id);
      const sel = r.id === T.selectedRoute;
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
    return `<figure class="instrument"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Time and economic cost of routes A to E">${ticks}${cticks}<text x="${(pad.l + W - pad.r) / 2}" y="${H - 8}" text-anchor="middle">Months to ready</text>${marks.join("")}</svg></figure>`;
  }

  const route = (id) => T.routes.find((r) => r.id === id);
  const B = route(T.selectedRoute);

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
              ${glyph("unknown")}
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
            <p class="small muted">The world goes quiet while you read: no revelations, no celebrations.</p>
          </section>`;
      }
      const failed = state === "failed";
      return `
        <section class="panel" aria-labelledby="title">
          <h1 id="title" class="title">You</h1>
          <p class="question">What do you do now, or what did you do last?</p>
          <p class="answer"${failed ? ' data-failed="true"' : ""}>Synthetic: I check customer records for a housing association.${failed ? `<br><span class="status" data-tone="error">${glyph("error")}Not processed</span>` : ""}</p>
          ${failed ? `<div class="alert" data-tone="error" role="alert">${glyph("error")}<div><p><strong>Careerwright's reply didn't arrive</strong></p><p class="small muted">Your message is kept. Nothing about you changed.</p></div></div>` : `<p>Records officers usually need these skills. Pick any you've used, and it lights up.</p>`}
          <p class="field" aria-hidden="true">Tell me more…</p>
          <div class="row"><button type="button" class="btn btn-primary">${failed ? "Try again" : "Send"}</button></div>
        </section>`;
    }
    if (place === "roles") {
      const stale = state === "stale";
      const unknown = state === "unknown";
      return `
        <section class="panel low" aria-labelledby="title">
          <h1 id="title" class="title">Roles</h1>
          <p class="kicker">${glyph("synthetic")}An unexpected connection: an example</p>
          <p class="sentence">Data quality analysts and statisticians share 6 essential skills.</p>
          <p class="small muted">A field you didn't name, joined to yours by skills, not job titles. A place you could head for. Not a job offer.</p>
          ${stale ? `<div class="alert" data-tone="stale">${glyph("stale")}<div><p><strong>Last checked 2 days ago</strong></p><p class="small muted">The job board didn't answer today. Its openings are kept from 2 days ago and may have closed.</p></div></div>` : ""}
          ${unknown ? `<div class="alert" data-tone="unknown">${glyph("unknown")}<div><p><strong>Leeds: none found in the ${L.totals.sourcesChecked} sources checked</strong></p><p class="small muted">Not "no jobs": only these sources were searched. Pay not stated on 3 openings.</p></div></div>` : ""}
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
            <li>${glyph(unknown ? "unknown" : "complete")}<span>Check data for errors</span><span class="small muted">${unknown ? "Not known yet" : "You said so"}</span></li>
            <li>${glyph("unknown")}<span>Query related tables</span><span class="small muted">${unknown ? "Not known yet" : "Usual in your role, not confirmed yet"}</span></li>
            <li>${glyph("unknown")}<span>Validate keys and missing values</span><span class="small muted">Not known yet</span></li>
            <li>${glyph("conditional")}<span>Pass the assessed report</span><span class="small muted">A gate</span></li>
          </ul>
          <p class="status" data-tone="neutral">${glyph("conditional")}Ready if you pass the assessed report</p>
          <div class="row"><button type="button" class="btn btn-primary">Tell me about a stretch</button></div>
        </section>`;
    }
    if (place === "options") {
      const unknown = state === "unknown";
      return `
        <section class="panel low" aria-labelledby="title">
          <h1 id="title" class="title">Options</h1>
          <p class="where">Bridges across the dark stretches.</p>
          ${unknown ? `<div class="alert" data-tone="unknown">${glyph("unknown")}<div><p><strong>No bridge found yet</strong></p><p class="small muted">Nothing searched covers "Validate keys and missing values". That is not "none exist".</p></div></div>` : `
          <ul class="list">
            <li data-selected="true">${glyph("complete")}<span>Part-time course, ${B.timeMonths} months, ${B.studyHours} hours a week</span><span class="tnum">${money(B.directMinor)}</span></li>
            <li>${glyph("blocked")}<span>Full-time course, ${route("A").timeMonths} months, ${route("A").studyHours} hours a week</span><span class="small muted">Set aside</span></li>
          </ul>`}
          <div class="row"><button type="button" class="btn btn-primary">Place this bridge</button></div>
        </section>`;
    }
    if (place === "routes") {
      const failed = state === "failed";
      return `
        <section class="panel panel-wide" aria-labelledby="title">
          <h1 id="title" class="title">Routes</h1>
          ${failed ? `<div class="alert" data-tone="error" role="alert">${glyph("error")}<div><p><strong>The route search failed</strong></p><p class="small muted">The last comparison stays below, from version 14. It may be out of date.</p></div></div>` : ""}
          ${instrument()}
          <dl class="facts">
            <dt>Route ${B.id}: ready in</dt><dd>${B.timeMonths} months, from ${day(B.start)}</dd>
            <dt>Economic cost</dt><dd>${money(B.economicMinor)}</dd>
            <dt>Direct spending</dt><dd>${money(B.directMinor)}</dd>
            <dt>Lowest cash point</dt><dd>${money(T.print.minimumPrefundedCashMinor)}</dd>
          </dl>
          <p class="status" data-tone="neutral">${glyph("conditional")}Ready if you pass the assessed report</p>
          <div class="row"><button type="button" class="btn btn-primary">Choose route ${B.id}</button></div>
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

  const KEY = {
    destination: `<li><span class="key-destination" aria-hidden="true"></span>Warm lights: places you chose to head for</li>`,
    suggested: `<li><span class="key-ring" style="border-color:var(--light-destination);transform:rotate(45deg);border-radius:0" aria-hidden="true"></span>Warm rings: places suggested to you</li>`,
    said: `<li><span class="key-said" aria-hidden="true"></span>Bright: you said you've done it</li>`,
    usual: `<li><span class="key-ring" aria-hidden="true"></span>Faint ring: usual in your role, not confirmed yet</li>`,
    shadow: `<li><span class="key-shadow" aria-hidden="true"></span>Slate: not known yet</li>`,
    gate: `<li><span class="key-gate" aria-hidden="true"></span>Gate: a condition, in words beside it</li>`,
    chosen: `<li><span class="key-chosen" aria-hidden="true"></span>Sea-glass: the path you chose</li>`,
    stale: `<li><span class="key-shadow" style="opacity:0.6" aria-hidden="true"></span>Faded: from the last comparison</li>`,
  };

  // ---------- Assemble ----------
  document.title = `${LABEL[place]}, ${state} · Careerwright world reference`;
  document.body.innerHTML = `
    <div class="world" data-distress="${state === "distress"}">${drawWorld()}</div>
    <aside class="world-words" aria-label="Your world"><ul></ul></aside>
    <ul class="legend" aria-label="What the lights mean">${[...world.legend].map((k) => KEY[k]).join("")}</ul>
    <div class="shell">
      ${rail}
      ${topbar}
      ${strip}
      <main class="work" id="main">${panel()}</main>
    </div>`;

  // Words beside their lights, clear of the panels and of each other (as the app places them).
  const host = document.querySelector(".world-words ul");
  const covers = [...document.querySelectorAll(".panel, .strip, .rail, .topbar, .legend")].map((e) => e.getBoundingClientRect()).filter((r) => r.width > 0);
  const placed = [];
  const meets = (a, b, pad) => a.x < b.x + b.w + pad && b.x < a.x + a.w + pad && a.y < b.y + b.h + pad && b.y < a.y + a.h + pad;
  const box = (r) => ({ x: r.left, y: r.top, w: r.width, h: r.height });
  const ORDER = { origin: 0, destination: 1, gate: 2, next: 2, route: 3, area: 4, bridge: 4, suggested: 5, stretch: 6, skill: 7 };
  for (const label of world.labels.sort((a, b) => ORDER[a.kind] - ORDER[b.kind])) {
    const p = project(label.anchor);
    const li = document.createElement("li");
    li.className = "world-label";
    li.dataset.kind = label.kind;
    if (label.selected) li.dataset.selected = "true";
    li.innerHTML = `<span>${esc(label.name)}</span>`;
    if (label.state === "usual") li.innerHTML += `<span class="caption">usual in your role, not confirmed yet</span>`;
    if (label.state === "said") li.innerHTML += `<span class="caption">you said so</span>`;
    if (label.state === "shadow" && label.kind !== "stretch") li.innerHTML += `<span class="caption">not known yet</span>`;
    if (label.state === "shadow" && label.kind === "stretch" && !label.name.includes("no bridge")) li.innerHTML += `<span class="caption">not known yet</span>`;
    host.append(li);
    const w = li.offsetWidth;
    const h = li.offsetHeight;
    const other = label.side === "above" ? "below" : "above";
    const tries = [[label.side, 0], [label.side, 1], [other, 0], [other, 1]].map(([s, row]) => {
      const out = 14 + row * (h + 6);
      return { x: p.x - w / 2, y: s === "above" ? p.y - out - h : p.y + out, w, h };
    });
    const spot = p.visible
      ? tries.find((b) => b.x >= 8 && b.y >= 8 && b.x + b.w <= vp.w - 8 && b.y + b.h <= vp.h - 8 && !covers.some((c) => meets(b, box(c), 0)) && !placed.some((o) => meets(b, o, 4)))
      : undefined;
    if (spot) {
      placed.push(spot);
      li.style.left = `${spot.x + w / 2}px`;
      li.style.top = `${spot.y}px`;
    } else {
      li.className = "sr-only";
    }
  }
})();
