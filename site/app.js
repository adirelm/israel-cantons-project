"use strict";

// Public map page: five political cantons of Israel. Data comes from site/data/,
// written by scripts/build_site_data.py from the research pipeline's results.

const BLOC_COLORS = ["#3b82f6", "#6b7280", "#a855f7", "#ef4444", "#22c55e"]; // right, haredi, center, left, arab
const NO_COUNTERPART_COLOR = "#f59e0b";
const MOVED_COLOR = "#dc2626";
const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const FALLBACK_STYLE = { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": "#eef2f6" } }] };
// Country, territory and region names are hidden on the basemap; city names stay
const HIDDEN_BASEMAP_LABELS = ["label_country_1", "label_country_2", "label_country_3", "label_state", "label_other"];
const RTL_PLUGIN = "https://unpkg.com/@mapbox/mapbox-gl-rtl-text@0.2.3/mapbox-gl-rtl-text.min.js";

const TEXT = {
  he: {
    dir: "rtl", locale: "he-IL", other: "English",
    brand: "ישראל בקנטונים",
    research: "למחקר המלא",
    title: "ישראל בחמישה קנטונים",
    lead: (m) => `מה יקרה אם נחלק את ישראל לאזורים לפי הדרך שבה הם מצביעים? חילקנו ${m.towns} רשויות מקומיות, כולל הרשויות הישראליות ביהודה ושומרון, לחמישה קנטונים: קבוצות של רשויות שמצביעות באופן דומה. החלוקה נשענת על אחוזי ההצבעה לכל רשימה בחמש מערכות הבחירות שבין ${m.first} ל־${m.last}.`,
    facts: (m) => [
      [m.towns, "רשויות מקומיות"],
      ["5", `מערכות בחירות, ${m.first}–${m.last}`],
      [`${m.towns_never_moved} מתוך ${m.towns}`, "רשויות נשארות באותו קנטון כשמחלקים כל מערכת בחירות לבד"],
      [`${m.heldout.significant} מתוך ${m.heldout.pairs}`, `השוואות בין קנטונים מובהקות גם בבחירות ${m.testYear}, שלא שימשו לבניית המפה`],
    ],
    searchLabel: "חיפוש רשות",
    searchPlaceholder: "חפשו עיר, מועצה מקומית או אזורית…",
    notFound: "לא נמצאה רשות בשם הזה",
    electionsLabel: "מערכת בחירות",
    allElections: (m) => `כל הבחירות (${m.first}–${m.last})`,
    mapLabel: "מפת הקנטונים",
    share: "העתקת קישור",
    copied: "הקישור הועתק",
    download: "הורדת המפה",
    downloadFailed: "לא הצלחנו ליצור תמונה. נסו שוב.",
    electionNote: (label) => `אותה שיטה הורצה על בחירות ${label} בלבד. רשויות שהקנטון שלהן שונה מהמפה הראשית מסומנות באדום.`,
    legendMoved: "קנטון שונה מהמפה הראשית",
    noCounterpart: "קנטון ללא מקבילה במפה הראשית",
    cantonsTitle: "חמשת הקנטונים",
    cantonsHint: "לחצו על קנטון או על רשות במפה, או חפשו רשות.",
    towns: "רשויות",
    votesAvg: "קולות כשרים בממוצע",
    largest: "הגדולות",
    back: "→ כל הקנטונים",
    canton: "קנטון",
    townVsCanton: "הצבעה לפי גוש, ממוצע חמש מערכות הבחירות",
    thisTown: "הרשות",
    thisCanton: "הקנטון",
    perElection: "הקנטון בכל מערכת בחירות",
    stayed: "באותו קנטון בכל חמש מערכות הבחירות.",
    movedCount: (n) => `שויכה לקנטון אחר ב־${n} מתוך חמש מערכות הבחירות.`,
    votesTable: "אחוז הקולות לפי גוש",
    election: "בחירות",
    allTowns: (n) => `כל ${n} הרשויות`,
    blocs: ["ימין", "חרדים", "מרכז", "שמאל", "ערבים"],
    howTitle: "איך זה עובד",
    steps: (m) => [
      ["הנתונים", `תוצאות הבחירות לכנסת בכל רשות מקומית בחמש מערכות הבחירות ${m.first}–${m.last}, וגבולות הרשויות מהלשכה המרכזית לסטטיסטיקה ומהמנהל האזרחי.`],
      ["החלוקה", "כל רשות מיוצגת באחוזי ההצבעה לכל רשימה שנכנסה לכנסת, בכל מערכת בחירות בנפרד. אלגוריתם לזיהוי קהילות ברשת (Louvain) מאחד רשויות שכנות שמצביעות באופן דומה לחמישה קנטונים. רשויות שבהן אותו גוש מקבל יותר מ־70% מהקולות מקושרות זו לזו גם כשאינן גובלות, ולכן רוב הקנטונים אינם רצף אחד במפה: בעיקר הקנטון הערבי והערים החרדיות, וגם כמה רשויות בודדות, כמו קריית שמונה, שמשויכות לקנטון רחוק."],
      ["הבדיקה", `המפה כמעט לא זזה כשמריצים את השיטה על כל מערכת בחירות לבד: ${m.towns_never_moved} מתוך ${m.towns} הרשויות נשארות במקומן. וקנטונים שנבנו מבחירות ${m.trainFirst}–${m.trainLast} בלבד נבדלים זה מזה באופן מובהק סטטיסטית גם בבחירות ${m.testYear}, ב־${m.heldout.significant} מתוך ${m.heldout.pairs} ההשוואות.`],
    ],
    caveat: "הגושים (ימין, חרדים, מרכז, שמאל, ערבים) משמשים לתיאור הקנטונים ולקישור בין רשויות שבהן גוש אחד דומיננטי, לא לסיווג המפלגות לפני החלוקה. שמות הקנטונים נקבעו לפי הרשויות הבולטות בהם והגוש הגדול בהם. זהו ניתוח נתונים, לא הצעה מדינית.",
    footer: (l) => [
      "פרויקט M.Sc. במדעי המחשב, אוניברסיטת בר־אילן · אדיר אלמקייס · בהנחיית ד״ר אורן גליקמן",
      `<a href="${l.app}" target="_blank" rel="noopener">אפליקציית המחקר</a> · <a href="${l.report}" target="_blank" rel="noopener">הדוח המלא (PDF)</a> · <a href="${l.repo}" target="_blank" rel="noopener">הקוד והנתונים</a>`,
      "מקורות: תוצאות הבחירות לכנסת לפי רשות מקומית; גבולות רשויות: הלשכה המרכזית לסטטיסטיקה והמנהל האזרחי; מפת רקע: OpenFreeMap ו־OpenStreetMap.",
    ],
    imageTitle: "ישראל בחמישה קנטונים",
    imageSub: (label) => `קנטונים לפי דפוסי הצבעה · ${label}`,
    cooperative: "השתמשו בשתי אצבעות כדי להזיז את המפה",
    cooperativeDesktop: "השתמשו ב־Ctrl + גלילה כדי להגדיל את המפה",
    cooperativeMac: "השתמשו ב־⌘ + גלילה כדי להגדיל את המפה",
  },
  en: {
    dir: "ltr", locale: "en-US", other: "עברית",
    brand: "Israel in Cantons",
    research: "Full research",
    title: "Israel in five cantons",
    lead: (m) => `What if Israel were divided by the way its towns vote? We grouped ${m.towns} local authorities, including the Israeli authorities in Judea and Samaria, into five cantons: groups of municipalities that vote alike. The division rests on each list's share of the vote in the five elections from ${m.first} to ${m.last}.`,
    facts: (m) => [
      [m.towns, "local authorities"],
      ["5", `Knesset elections, ${m.first}–${m.last}`],
      [`${m.towns_never_moved} of ${m.towns}`, "authorities stay in the same canton when each election is divided on its own"],
      [`${m.heldout.significant} of ${m.heldout.pairs}`, `comparisons between cantons are significant in ${m.testYear} too, an election the map was not built from`],
    ],
    searchLabel: "Find a municipality",
    searchPlaceholder: "Search a city, local or regional council…",
    notFound: "No municipality by that name",
    electionsLabel: "Election",
    allElections: (m) => `All elections (${m.first}–${m.last})`,
    mapLabel: "Canton map",
    share: "Copy link",
    copied: "Link copied",
    download: "Download map",
    downloadFailed: "Could not create the image. Please try again.",
    electionNote: (label) => `The same method run on the ${label} election alone. Municipalities whose canton differs from the main map are outlined in red.`,
    legendMoved: "Different canton from the main map",
    noCounterpart: "Canton with no counterpart in the main map",
    cantonsTitle: "The five cantons",
    cantonsHint: "Click a canton or a municipality on the map, or search for one.",
    towns: "municipalities",
    votesAvg: "valid votes on average",
    largest: "Largest",
    back: "← All cantons",
    canton: "Canton",
    townVsCanton: "Vote by bloc, average of five elections",
    thisTown: "Municipality",
    thisCanton: "Canton",
    perElection: "Canton in each election",
    stayed: "In the same canton in all five elections.",
    movedCount: (n) => `In a different canton in ${n} of the five elections.`,
    votesTable: "Share of the vote by bloc",
    election: "Election",
    allTowns: (n) => `All ${n} municipalities`,
    blocs: ["Right", "Haredi", "Center", "Left", "Arab"],
    howTitle: "How it works",
    steps: (m) => [
      ["The data", `Knesset election results for every local authority in the five elections from ${m.first} to ${m.last}, and municipal boundaries from the Central Bureau of Statistics and the Civil Administration.`],
      ["The division", "Each municipality is described by the vote share of every list that won seats, in each election separately. A network community-detection algorithm (Louvain) groups neighbouring municipalities that vote alike into five cantons. Municipalities where one bloc wins over 70% of the vote are linked to each other even when they share no border, so most cantons are not single pieces on the map: mainly the Arab canton and the Haredi cities, and a few single towns, such as Kiryat Shmona, that belong to a distant canton."],
      ["The checks", `The map barely moves when the method is run on each election alone: ${m.towns_never_moved} of ${m.towns} municipalities stay put. Cantons built from the ${m.trainFirst}–${m.trainLast} elections only still differ significantly in ${m.testYear}, in ${m.heldout.significant} of ${m.heldout.pairs} comparisons.`],
    ],
    caveat: "Blocs (Right, Haredi, Center, Left, Arab) describe the cantons and link municipalities dominated by one bloc; parties are not grouped before the division. Canton names come from their best-known municipalities and their largest bloc. This is a data analysis, not a policy proposal.",
    footer: (l) => [
      "M.Sc. project in Computer Science, Bar-Ilan University · Adir Elmakais · Advisor: Dr. Oren Glickman",
      `<a href="${l.app}" target="_blank" rel="noopener">Research app</a> · <a href="${l.report}" target="_blank" rel="noopener">Full report (PDF)</a> · <a href="${l.repo}" target="_blank" rel="noopener">Code and data</a>`,
      "Sources: Knesset election results by local authority; municipal boundaries: Central Bureau of Statistics and the Civil Administration; basemap: OpenFreeMap and OpenStreetMap.",
    ],
    imageTitle: "Israel in five cantons",
    imageSub: (label) => `Cantons by voting pattern · ${label}`,
    cooperative: "Use two fingers to move the map",
    cooperativeDesktop: "Use Ctrl + scroll to zoom the map",
    cooperativeMac: "Use ⌘ + scroll to zoom the map",
  },
};

const state = { lang: "he", election: "all", canton: null, town: null };
let data = null; // { towns, cantons, meta, byName, search }
let map = null;
let hovered = null;
let popup = null;
let controls = [];

const $ = (sel) => document.querySelector(sel);
const t = () => TEXT[state.lang];
const fmt = (n) => new Intl.NumberFormat(t().locale).format(Math.round(n));
const year = (label) => label.en.split(" ").pop();
const townName = (p) => (state.lang === "he" ? p.he : p.en);
const cantonName = (c) => (state.lang === "he" ? c.he : c.en);
const electionKeys = () => Object.keys(data.meta.elections);
const electionLabel = (k) => data.meta.elections[k][state.lang];

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

function metaForText() {
  const m = data.meta;
  const keys = electionKeys();
  const train = m.heldout.train.map(String);
  return {
    ...m,
    first: year(m.elections[keys[0]]),
    last: year(m.elections[keys[keys.length - 1]]),
    trainFirst: year(m.elections[train[0]]),
    trainLast: year(m.elections[train[train.length - 1]]),
    testYear: year(m.elections[String(m.heldout.test)]),
  };
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

async function loadData() {
  const [towns, cantons, meta] = await Promise.all(
    ["data/towns.geojson", "data/cantons.json", "data/meta.json"].map((u) => fetch(u).then((r) => {
      if (!r.ok) throw new Error(`${u}: ${r.status}`);
      return r.json();
    })),
  );
  const keys = Object.keys(meta.elections);
  const byName = new Map();
  for (const f of towns.features) {
    const p = f.properties;
    for (const k of keys) {
      p[`e${k}`] = p.elections[k];
      p[`m${k}`] = p.elections[k] !== p.canton ? 1 : 0;
    }
    f.bbox = bboxOf(f.geometry.coordinates);
    byName.set(p.he, f);
  }
  return { towns, cantons: new Map(cantons.map((c) => [c.id, c])), meta, byName };
}

function bboxOf(coords) {
  const box = [Infinity, Infinity, -Infinity, -Infinity];
  (function walk(c) {
    if (typeof c[0] === "number") {
      box[0] = Math.min(box[0], c[0]); box[1] = Math.min(box[1], c[1]);
      box[2] = Math.max(box[2], c[0]); box[3] = Math.max(box[3], c[1]);
    } else c.forEach(walk);
  })(coords);
  return box;
}

function unionBbox(features) {
  return features.reduce((b, f) => [Math.min(b[0], f.bbox[0]), Math.min(b[1], f.bbox[1]),
    Math.max(b[2], f.bbox[2]), Math.max(b[3], f.bbox[3])], [Infinity, Infinity, -Infinity, -Infinity]);
}

// ---------------------------------------------------------------------------
// Map
// ---------------------------------------------------------------------------

const cantonProp = () => (state.election === "all" ? ["get", "canton"] : ["get", `e${state.election}`]);

function colorExpression() {
  const expr = ["match", cantonProp()];
  for (const c of data.cantons.values()) expr.push(c.id, c.color);
  expr.push(NO_COUNTERPART_COLOR);
  return expr;
}

function opacityExpression() {
  const hover = ["boolean", ["feature-state", "hover"], false];
  if (state.canton === null) return ["case", hover, 0.92, 0.74];
  return ["case", ["==", cantonProp(), state.canton], ["case", hover, 0.95, 0.85], 0.14];
}

function initMap() {
  const isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
  map = new maplibregl.Map({
    container: "map",
    style: BASEMAP_STYLE,
    bounds: unionBbox(data.towns.features),
    fitBoundsOptions: { padding: 24 },
    attributionControl: false,
    cooperativeGestures: true,
    locale: {
      "CooperativeGesturesHandler.WindowsHelpText": t().cooperativeDesktop,
      "CooperativeGesturesHandler.MacHelpText": t().cooperativeMac,
      "CooperativeGesturesHandler.MobileHelpText": t().cooperative,
    },
  });
  placeControls();

  let fellBack = false;
  map.on("error", (e) => {
    // Basemap unavailable: keep the cantons on a plain background
    if (!fellBack && !map.isStyleLoaded() && String(e?.error?.message || "").length) {
      fellBack = true;
      map.setStyle(FALLBACK_STYLE);
    }
  });
  map.on("style.load", addLayers);

  popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8 });
  map.on("mousemove", "towns-fill", (e) => {
    const f = e.features[0];
    setHover(f.id);
    map.getCanvas().style.cursor = "pointer";
    const p = f.properties;
    const c = data.cantons.get(Number(state.election === "all" ? p.canton : p[`e${state.election}`]));
    popup.setLngLat(e.lngLat)
      .setHTML(`<div dir="${t().dir}"><b>${escapeHtml(townName(data.byName.get(p.he).properties))}</b><br>${escapeHtml(c ? cantonName(c) : t().noCounterpart)}</div>`)
      .addTo(map);
  });
  map.on("mouseleave", "towns-fill", () => {
    setHover(null);
    map.getCanvas().style.cursor = "";
    popup.remove();
  });
  map.on("click", "towns-fill", (e) => selectTown(e.features[0].properties.he, { fly: false }));
}

// Zoom buttons and attribution sit on the side away from the legend and the action buttons
function placeControls() {
  if (!map) return;
  controls.forEach((c) => map.removeControl(c));
  const end = state.lang === "he" ? "left" : "right";
  controls = [new maplibregl.NavigationControl({ showCompass: false }), new maplibregl.AttributionControl({ compact: true })];
  map.addControl(controls[0], `top-${end}`);
  map.addControl(controls[1], `bottom-${end}`);
}

function addLayers() {
  if (map.getSource("towns")) return;
  HIDDEN_BASEMAP_LABELS.filter((id) => map.getLayer(id)).forEach((id) => map.setLayoutProperty(id, "visibility", "none"));
  map.addSource("towns", { type: "geojson", data: data.towns, promoteId: "he" });
  const firstLabel = (map.getStyle().layers || []).find((l) => l.type === "symbol")?.id;
  map.addLayer({ id: "towns-fill", type: "fill", source: "towns",
    paint: { "fill-color": colorExpression(), "fill-opacity": opacityExpression() } }, firstLabel);
  map.addLayer({ id: "towns-line", type: "line", source: "towns",
    paint: { "line-color": "#ffffff", "line-width": ["interpolate", ["linear"], ["zoom"], 6, 0.2, 10, 1], "line-opacity": 0.8 } }, firstLabel);
  map.addLayer({ id: "towns-moved", type: "line", source: "towns", filter: ["==", ["get", "m21"], 2],
    paint: { "line-color": MOVED_COLOR, "line-width": 1.8 } }, firstLabel);
  map.addLayer({ id: "towns-focus", type: "line", source: "towns", filter: ["==", ["get", "he"], ""],
    paint: { "line-color": "#0f172a", "line-width": 1.6 } });
  map.addLayer({ id: "towns-selected", type: "line", source: "towns", filter: ["==", ["get", "he"], ""],
    paint: { "line-color": "#0f172a", "line-width": 3 } });
  applyMapState();
}

function setHover(id) {
  if (hovered !== null) map.setFeatureState({ source: "towns", id: hovered }, { hover: false });
  hovered = id;
  if (id !== null) map.setFeatureState({ source: "towns", id }, { hover: true });
}

function applyMapState() {
  if (!map || !map.getLayer("towns-fill")) return;
  map.setPaintProperty("towns-fill", "fill-color", colorExpression());
  map.setPaintProperty("towns-fill", "fill-opacity", opacityExpression());
  map.setFilter("towns-moved", state.election === "all" ? ["==", ["get", "m21"], 2] : ["==", ["get", `m${state.election}`], 1]);
  map.setFilter("towns-selected", ["==", ["get", "he"], state.town || ""]);
  // Outline the selected canton's towns so small ones (the Haredi cities) stand out
  map.setFilter("towns-focus", state.canton === null ? ["==", ["get", "he"], ""] : ["==", cantonProp(), state.canton]);
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function blocBar(shares) {
  const segs = shares.map((v, i) => `<span style="width:${Math.max(0, v)}%;background:${BLOC_COLORS[i]}" title="${escapeHtml(t().blocs[i])} ${v.toFixed(1)}%"></span>`).join("");
  return `<div class="bar" role="img" aria-label="${escapeHtml(shares.map((v, i) => `${t().blocs[i]} ${v.toFixed(0)}%`).join(", "))}">${segs}</div>`;
}

function blocKey(shares) {
  return `<div class="bloc-key">${shares.map((v, i) => `<span><i style="background:${BLOC_COLORS[i]}"></i>${escapeHtml(t().blocs[i])} ${v.toFixed(0)}%</span>`).join("")}</div>`;
}

function renderStatic() {
  const m = metaForText();
  document.documentElement.lang = state.lang;
  document.documentElement.dir = t().dir;
  document.title = t().title;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t()[el.dataset.i18n]; });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t()[el.dataset.i18nPlaceholder]; });
  document.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t()[el.dataset.i18nAria]); });
  $("#lang-toggle").textContent = t().other;
  $("#link-app").href = data.meta.links.app;
  $("#lead").textContent = t().lead(m);
  $("#facts").innerHTML = t().facts(m).map(([n, s]) => `<li><b>${escapeHtml(n)}</b><span>${escapeHtml(s)}</span></li>`).join("");
  $("#steps").innerHTML = t().steps(m).map(([h, s]) => `<li><b>${escapeHtml(h)}</b>${escapeHtml(s)}</li>`).join("");
  $("#caveat").textContent = t().caveat;
  $("#footer").innerHTML = `<div class="inner">${t().footer(data.meta.links).map((x) => `<div>${x}</div>`).join("")}</div>`;

  const options = [];
  for (const f of data.towns.features) {
    const p = f.properties;
    options.push(p.he, p.en);
    if (p.alt) options.push(p.alt);
  }
  $("#town-names").innerHTML = [...new Set(options)].sort((a, b) => a.localeCompare(b, t().locale))
    .map((o) => `<option value="${escapeHtml(o)}"></option>`).join("");

  const buttons = [["all", t().allElections(m)], ...electionKeys().map((k) => [k, electionLabel(k)])];
  $("#elections").innerHTML = buttons.map(([k, label]) =>
    `<button type="button" data-election="${k}" aria-pressed="${state.election === k}">${escapeHtml(label)}</button>`).join("");
}

function renderLegend() {
  const ids = new Set(data.towns.features.map((f) => (state.election === "all" ? f.properties.canton : f.properties[`e${state.election}`])));
  const items = [...data.cantons.values()].filter((c) => ids.has(c.id)).map((c) =>
    `<button type="button" data-canton="${c.id}" aria-pressed="${state.canton === c.id}"><span class="swatch" style="background:${c.color}"></span>${escapeHtml(cantonName(c))}</button>`);
  if ([...ids].some((id) => !data.cantons.has(id))) {
    items.push(`<button type="button" disabled><span class="swatch" style="background:${NO_COUNTERPART_COLOR}"></span>${escapeHtml(t().noCounterpart)}</button>`);
  }
  if (state.election !== "all") {
    items.push(`<button type="button" disabled><span class="swatch moved"></span>${escapeHtml(t().legendMoved)}</button>`);
  }
  $("#legend").innerHTML = items.join("");
  const note = $("#election-note");
  note.hidden = state.election === "all";
  if (!note.hidden) note.textContent = t().electionNote(electionLabel(state.election));
}

function cantonCard(c, { clickable }) {
  const tag = clickable ? "button" : "div";
  const largest = c.largest.map((x) => (state.lang === "he" ? x.he : x.en)).join(", ");
  return `<${tag} ${clickable ? `type="button" data-canton="${c.id}"` : ""} class="card canton-card${state.canton === c.id ? " selected" : ""}">
    <h3><span class="dot" style="background:${c.color}"></span>${escapeHtml(cantonName(c))}</h3>
    <p class="sub">${fmt(c.towns)} ${t().towns} · ${fmt(c.voters)} ${t().votesAvg}</p>
    ${blocBar(c.blocs)}${blocKey(c.blocs)}
    <p class="towns-list">${t().largest}: ${escapeHtml(largest)}</p>
  </${tag}>`;
}

function renderPanel() {
  const panel = $("#panel");
  if (state.town) {
    panel.innerHTML = townCard(data.byName.get(state.town));
  } else if (state.canton !== null && data.cantons.has(state.canton)) {
    const c = data.cantons.get(state.canton);
    const members = data.towns.features.filter((f) => f.properties.canton === c.id)
      .sort((a, b) => b.properties.voters - a.properties.voters);
    panel.innerHTML = `<button type="button" class="back" data-back>${t().back}</button>
      ${cantonCard(c, { clickable: false })}
      <div class="card"><h3>${escapeHtml(t().allTowns(members.length))}</h3>
      <p class="towns-list">${members.map((f) => `<a href="#" data-town="${escapeHtml(f.properties.he)}">${escapeHtml(townName(f.properties))}</a>`).join(" · ")}</p></div>`;
  } else {
    panel.innerHTML = `<div><h2 style="margin:0 0 2px;font-size:1.2rem">${t().cantonsTitle}</h2>
      <p class="sub" style="margin:0 0 6px;color:var(--ink-soft)">${t().cantonsHint}</p></div>
      ${[...data.cantons.values()].map((c) => cantonCard(c, { clickable: true })).join("")}`;
  }
}

function townCard(f) {
  const p = f.properties;
  const c = data.cantons.get(p.canton);
  const keys = electionKeys();
  const moved = keys.filter((k) => p.elections[k] !== p.canton).length;
  const chips = keys.map((k) => {
    const id = p.elections[k];
    const color = data.cantons.get(id)?.color || NO_COUNTERPART_COLOR;
    const name = data.cantons.has(id) ? cantonName(data.cantons.get(id)) : t().noCounterpart;
    return `<div><div class="chip${id !== p.canton ? " moved" : ""}" style="background:${color}" title="${escapeHtml(name)}"></div>${escapeHtml(data.meta.elections[k].short)}</div>`;
  }).join("");
  const rows = keys.map((k) => `<tr><td>${escapeHtml(electionLabel(k))}</td>${p.votes[k].map((v) => `<td>${v.toFixed(0)}</td>`).join("")}</tr>`).join("");
  const other = state.lang === "he" ? p.en : p.he;
  return `<button type="button" class="back" data-back>${t().back}</button>
    <div class="card">
      <h3>${escapeHtml(townName(p))}</h3>
      <p class="sub">${escapeHtml(other)} · ${fmt(p.voters)} ${t().votesAvg}</p>
      <p class="sub" style="color:var(--ink)"><span class="dot" style="background:${c.color};vertical-align:-2px"></span> ${t().canton}: <b>${escapeHtml(cantonName(c))}</b></p>
      <p class="sub" style="margin-bottom:4px">${t().townVsCanton}</p>
      <div class="bar-label"><span>${t().thisTown}</span></div>${blocBar(p.blocs)}
      <div class="bar-label"><span>${t().thisCanton}</span></div>${blocBar(c.blocs)}
      ${blocKey(p.blocs)}
    </div>
    <div class="card">
      <h3>${t().perElection}</h3>
      <div class="timeline">${chips}</div>
      <p class="sub" style="margin:6px 0 0">${moved ? t().movedCount(moved) : t().stayed}</p>
      <table class="votes"><caption class="visually-hidden">${t().votesTable}</caption>
        <thead><tr><th>${t().election}</th>${t().blocs.map((b) => `<th>${escapeHtml(b)}</th>`).join("")}</tr></thead>
        <tbody>${rows}</tbody></table>
    </div>`;
}

function render() {
  renderLegend();
  renderPanel();
  applyMapState();
  syncUrl();
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

function selectTown(name, { fly = true } = {}) {
  const f = data.byName.get(name);
  if (!f) return;
  state.town = name;
  state.canton = null;
  if (fly) map.fitBounds(f.bbox, { padding: 80, maxZoom: 11, duration: 700 });
  render();
}

function selectCanton(id) {
  state.town = null;
  state.canton = state.canton === id ? null : id;
  if (state.canton !== null) {
    const members = data.towns.features.filter((f) => f.properties.canton === id);
    map.fitBounds(unionBbox(members), { padding: 40, duration: 700 });
  }
  render();
}

function resetSelection() {
  state.town = null;
  state.canton = null;
  render();
}

// Ignore case, spaces, hyphens, apostrophes, Hebrew geresh/gershayim and full spelling (קריית = קרית)
const normalize = (s) => s.toLowerCase().replace(/['"`’׳״()\-–.\s]/g, "").replace(/יי/g, "י").replace(/וו/g, "ו");

function findTown(query) {
  const q = normalize(query);
  if (!q) return null;
  const names = (f) => [f.properties.he, f.properties.en, f.properties.alt].filter(Boolean).map(normalize);
  const all = data.towns.features;
  return all.find((f) => names(f).includes(q))
    || all.filter((f) => names(f).some((n) => n.includes(q))).sort((a, b) => b.properties.voters - a.properties.voters)[0]
    || null;
}

function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.hidden = true; }, 2200);
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.lang !== "he") params.set("lang", state.lang);
  if (state.election !== "all") params.set("e", state.election);
  if (state.town) params.set("town", state.town);
  else if (state.canton !== null) params.set("canton", String(state.canton));
  const qs = params.toString();
  history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
}

function readUrl() {
  const params = new URLSearchParams(location.search);
  if (params.get("lang") === "en") state.lang = "en";
  const e = params.get("e");
  if (e && data.meta.elections[e]) state.election = e;
  const town = params.get("town");
  if (town && data.byName.has(town)) state.town = town;
  const canton = Number(params.get("canton"));
  if (!state.town && params.has("canton") && data.cantons.has(canton)) state.canton = canton;
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(location.href);
    toast(t().copied);
  } catch {
    window.prompt(t().share, location.href);
  }
}

// Copy the WebGL canvas right after drawing it, before the browser clears its buffer
function captureMap() {
  const copyNow = () => {
    const live = map.getCanvas();
    const copy = document.createElement("canvas");
    copy.width = live.width;
    copy.height = live.height;
    copy.getContext("2d").drawImage(live, 0, 0);
    return copy;
  };
  if (typeof map.redraw === "function") {
    map.redraw(); // synchronous draw, so the buffer is still intact below
    return Promise.resolve(copyNow());
  }
  return new Promise((resolve) => {
    map.once("render", () => resolve(copyNow()));
    map.triggerRepaint();
  });
}

async function downloadMap() {
  try {
    await document.fonts.ready;
    const src = await captureMap();
    const dpr = src.width / map.getCanvas().clientWidth;
    const W = src.width;
    const head = Math.round(70 * dpr);
    const foot = Math.round(30 * dpr);
    const out = document.createElement("canvas");
    out.width = W;
    out.height = src.height + head + foot;
    const ctx = out.getContext("2d");
    const rtl = state.lang === "he";
    const x0 = rtl ? W - 18 * dpr : 18 * dpr;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, out.width, out.height);
    ctx.drawImage(src, 0, head);
    ctx.direction = rtl ? "rtl" : "ltr";
    ctx.textAlign = rtl ? "right" : "left";
    ctx.fillStyle = "#0f172a";
    ctx.font = `800 ${24 * dpr}px Heebo, Arial, sans-serif`;
    ctx.fillText(t().imageTitle, x0, 34 * dpr);
    ctx.font = `400 ${14 * dpr}px Heebo, Arial, sans-serif`;
    ctx.fillStyle = "#475569";
    const label = state.election === "all" ? t().allElections(metaForText()) : electionLabel(state.election);
    ctx.fillText(t().imageSub(label), x0, 56 * dpr);

    const ids = new Set(data.towns.features.map((f) => (state.election === "all" ? f.properties.canton : f.properties[`e${state.election}`])));
    const entries = [...data.cantons.values()].filter((c) => ids.has(c.id)).map((c) => [c.color, cantonName(c)]);
    if ([...ids].some((id) => !data.cantons.has(id))) entries.push([NO_COUNTERPART_COLOR, t().noCounterpart]);
    if (state.election !== "all") entries.push([null, t().legendMoved]);
    ctx.font = `500 ${13 * dpr}px Heebo, Arial, sans-serif`;
    const lineH = 20 * dpr;
    const boxW = Math.max(...entries.map(([, n]) => ctx.measureText(n).width)) + 44 * dpr;
    const boxH = entries.length * lineH + 14 * dpr;
    const bx = rtl ? W - boxW - 12 * dpr : 12 * dpr;
    const by = head + src.height - boxH - 12 * dpr;
    ctx.fillStyle = "rgba(255,255,255,0.94)";
    ctx.fillRect(bx, by, boxW, boxH);
    entries.forEach(([color, name], i) => {
      const y = by + 10 * dpr + i * lineH;
      const sx = rtl ? bx + boxW - 24 * dpr : bx + 10 * dpr;
      if (color) {
        ctx.fillStyle = color;
        ctx.fillRect(sx, y + 2 * dpr, 14 * dpr, 14 * dpr);
      } else {
        ctx.strokeStyle = MOVED_COLOR;
        ctx.lineWidth = 2 * dpr;
        ctx.strokeRect(sx + dpr, y + 3 * dpr, 12 * dpr, 12 * dpr);
      }
      ctx.fillStyle = "#0f172a";
      ctx.fillText(name, rtl ? sx - 8 * dpr : sx + 22 * dpr, y + 14 * dpr);
    });
    ctx.font = `400 ${11 * dpr}px Heebo, Arial, sans-serif`;
    ctx.fillStyle = "#64748b";
    ctx.fillText(`${t().footer(data.meta.links)[0]} · © OpenStreetMap`, x0, out.height - 11 * dpr);

    out.toBlob((blob) => {
      if (!blob) { toast(t().downloadFailed); return; }
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `israel-cantons-${state.election}-${state.lang}.png`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    }, "image/png");
  } catch (err) {
    console.error(err);
    toast(t().downloadFailed);
  }
}

function bindEvents() {
  $("#lang-toggle").addEventListener("click", () => {
    state.lang = state.lang === "he" ? "en" : "he";
    renderStatic();
    placeControls();
    render();
  });
  $("#elections").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-election]");
    if (!b) return;
    state.election = b.dataset.election;
    state.canton = null;
    document.querySelectorAll("#elections button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    render();
  });
  const onCanton = (e) => {
    const b = e.target.closest("[data-canton]");
    if (b && !b.disabled) selectCanton(Number(b.dataset.canton));
  };
  $("#legend").addEventListener("click", onCanton);
  $("#panel").addEventListener("click", (e) => {
    if (e.target.closest("[data-back]")) { resetSelection(); return; }
    const a = e.target.closest("[data-town]");
    if (a) { e.preventDefault(); selectTown(a.dataset.town); return; }
    onCanton(e);
  });
  const search = $("#search");
  const go = () => {
    const f = findTown(search.value);
    if (f) { selectTown(f.properties.he); search.blur(); } else if (search.value.trim()) toast(t().notFound);
  };
  search.addEventListener("change", go);
  search.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
  $("#btn-share").addEventListener("click", copyLink);
  $("#btn-download").addEventListener("click", downloadMap);
}

async function main() {
  try {
    data = await loadData();
  } catch (err) {
    $("#panel").innerHTML = `<div class="card">Could not load the map data. ${escapeHtml(err.message)}</div>`;
    return;
  }
  readUrl();
  renderStatic();
  // Hebrew and Arabic basemap labels need the RTL shaping plugin; without it they still show, unshaped
  Promise.resolve().then(() => maplibregl.setRTLTextPlugin(RTL_PLUGIN, true)).catch(() => {});
  initMap();
  bindEvents();
  render();
  // Fit once the container has its final size (the map is created before layout settles)
  map.once("load", () => {
    map.resize();
    const members = state.canton === null ? data.towns.features
      : data.towns.features.filter((f) => f.properties.canton === state.canton);
    const box = state.town ? data.byName.get(state.town).bbox : unionBbox(members);
    map.fitBounds(box, { padding: state.town ? 80 : 24, maxZoom: 11, duration: 0 });
  });
}

main();
