// Shared behaviour for the static compositions. No framework and no build: open any page
// from disk. `?state=default|unknown|failure` selects the state; elements carry
// data-show="<states>" and are hidden (removed from the accessibility tree) otherwise.
// Markup is built only from constants authored in this file; fixture values are written
// with textContent. Numbers in page prose come from data.js through data-gbp / data-value
// so tools/check-fixture-data.mjs covers them.
(function () {
  const STATES = ["default", "unknown", "failure"];
  const requested = new URLSearchParams(location.search).get("state");
  const state = STATES.includes(requested) ? requested : "default";
  document.documentElement.dataset.state = state;

  const CHAPTERS = [
    ["you", "You", "conversation.html"],
    ["roles", "Roles", "opportunity-map.html"],
    ["skills", "Skills", null],
    ["options", "Options", null],
    ["routes", "Routes", "route-comparison.html"],
    ["plan", "Plan", null],
  ];

  const GLYPHS = {
    mark: '<circle cx="9" cy="15" r="5.2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12.6 11.3C14.6 8.6 16 7.3 18.4 6.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="19.6" cy="5.6" r="1.9" fill="none" stroke="currentColor" stroke-width="1.6"/>',
    complete: '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M7.8 12.4l2.8 2.8 5.6-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    conditional: '<path d="M12 3.2L20.8 12 12 20.8 3.2 12z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="12" cy="12" r="2" fill="currentColor"/>',
    stale: '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 7v5.2l3.4 2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    error: '<path d="M12 3.5L21.5 20h-19z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M12 9.5v5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="17.3" r="1.1" fill="currentColor"/>',
    unknown: '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9.6 9.6a2.5 2.5 0 1 1 3.6 2.2c-.8.4-1.2.9-1.2 1.7v.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><circle cx="12" cy="16.9" r="1" fill="currentColor"/>',
    synthetic: '<path d="M9.5 3.5h5M10.5 3.5v5.8L5.6 17.8a2 2 0 0 0 1.7 3h9.4a2 2 0 0 0 1.7-3l-4.9-8.5V3.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M7.8 14.5h8.4" stroke="currentColor" stroke-width="1.7"/>',
    source: '<path d="M7 3.5h7l4 4v13H7z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M14 3.5v4h4M9.5 12h6M9.5 15.5h6" fill="none" stroke="currentColor" stroke-width="1.7"/>',
    close: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
    pause: '<path d="M9 6.5v11M15 6.5v11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    expand: '<path d="M7 14.5l5-5 5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    star: '<path d="M12 4l2.4 5 5.3.6-3.9 3.7 1 5.3L12 16l-4.8 2.6 1-5.3L4.3 9.6l5.3-.6z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
  };

  function glyph(name, label) {
    const a11y = label ? `role="img" aria-label="${label}"` : 'aria-hidden="true" focusable="false"';
    return `<svg viewBox="0 0 24 24" ${a11y}>${GLYPHS[name]}</svg>`;
  }

  function applyState() {
    // The attribute, not the .hidden property: SVG elements have no .hidden property.
    for (const el of document.querySelectorAll("[data-show]")) {
      el.toggleAttribute("hidden", !el.dataset.show.split(/\s+/).includes(state));
    }
  }

  function renderRail() {
    const rail = document.querySelector("[data-rail]");
    if (!rail) return;
    const current = document.body.dataset.chapter;
    const done = (document.body.dataset.done || "").split(/\s+/);
    const items = CHAPTERS.map(([id, label, href]) => {
      const progress = done.includes(id) ? "done" : id === current ? "current" : "todo";
      const currentAttr = id === current ? ' aria-current="page"' : "";
      const status = progress === "done" ? '<span class="visually-hidden">, decisions recorded</span>' : "";
      return `<li><a class="rail-chapter" data-progress="${progress}" href="${href || "#"}"${currentAttr}><span class="landmark" aria-hidden="true"></span>${label}${status}</a></li>`;
    }).join("");
    rail.innerHTML = `<a class="rail-mark" href="index.html">${glyph("mark")}<span>Nessa</span></a><nav aria-label="Chapters"><ul class="rail-chapters">${items}</ul></nav>`;
  }

  function renderTopbar() {
    const bar = document.querySelector("[data-topbar]");
    if (!bar) return;
    const current = CHAPTERS.find(([id]) => id === document.body.dataset.chapter);
    bar.innerHTML = `<button class="chapter-menu" type="button" aria-haspopup="true" aria-expanded="false">${glyph("menu")}<span>${current[1]}</span><span class="visually-hidden">, open chapter menu</span></button><span class="synthetic-label">${glyph("synthetic")}Synthetic demo</span>`;
  }

  // The glyph goes first; the remaining content is wrapped in one span so that long
  // status text wraps instead of overflowing its flex container.
  function fillGlyphs() {
    for (const el of document.querySelectorAll("[data-glyph]")) {
      if (el.childNodes.length) {
        const span = document.createElement("span");
        span.className = "glyph-text";
        span.append(...el.childNodes);
        el.append(span);
      }
      el.insertAdjacentHTML("afterbegin", glyph(el.dataset.glyph, el.dataset.glyphLabel));
    }
  }

  // GBP from integer minor units. Whole pounds print without pence; the exponent is
  // fixed at 2 for GBP here, never assumed for other currencies.
  function gbp(minor, { signed = false } = {}) {
    const negative = minor < 0;
    const abs = Math.abs(minor);
    const pounds = Math.floor(abs / 100);
    const pence = abs % 100;
    const body = pounds.toLocaleString("en-GB") + (pence ? "." + String(pence).padStart(2, "0") : "");
    return (negative ? "−" : signed ? "+" : "") + "£" + body;
  }

  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  function longDate(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return `${d} ${MONTHS[m - 1]} ${y}`;
  }
  function monthName(index, short = false) {
    const name = MONTHS[index % 12];
    return short ? name.slice(0, 3) : name;
  }

  function fixtureValue(path) {
    const value = path.split(".").reduce((node, key) => (node == null ? undefined : node[key]), window.NESSA.FIXTURES);
    if (value === undefined) throw new Error(`no fixture value at ${path}`);
    return value;
  }

  function bindFixtureValues() {
    for (const el of document.querySelectorAll("[data-gbp]")) el.textContent = gbp(fixtureValue(el.dataset.gbp));
    for (const el of document.querySelectorAll("[data-value]")) el.textContent = String(fixtureValue(el.dataset.value));
  }

  window.NESSA = window.NESSA || {};
  Object.assign(window.NESSA, { state, glyph, fixtureValue, fmt: { gbp, longDate, monthName } });

  renderRail();
  renderTopbar();
  fillGlyphs();
  bindFixtureValues();
  applyState();
})();
