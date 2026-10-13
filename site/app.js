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
      [`${m.heldout.significant} מתוך ${m.heldout.pairs}`, `השוואות בין קנטונים שנבנו מבחירות ${m.trainFirst}–${m.trainLast} בלבד מובהקות גם בבחירות ${m.testYear}`],
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
      ["החלוקה", "כל רשות מיוצגת באחוזי ההצבעה לכל רשימה שנכנסה לכנסת, בכל מערכת בחירות בנפרד. אלגוריתם לזיהוי קהילות ברשת (Louvain) מאחד רשויות שכנות שמצביעות באופן דומה לחמישה קנטונים. ברשת יש גם קישורים בין רשויות שאינן גובלות: בין רשויות שבהן אותו גוש מקבל יותר מ־70% מהקולות, ובין רשויות שאין להן שכנות בנתונים לרשויות הדומות להן ביותר. לכן רוב הקנטונים אינם רצף אחד במפה: בעיקר הקנטון הערבי והערים החרדיות, וגם כמה רשויות בודדות, כמו קריית שמונה ובית ג׳ן, שמשויכות לקנטון רחוק."],
      ["הבדיקה", `המפה יציבה: כשמריצים את השיטה על כל מערכת בחירות לבד, ${m.towns_never_moved} מתוך ${m.towns} הרשויות נשארות באותו קנטון (בחירות ${m.testYear} שונות יותר מכולן). וקנטונים שנבנו מבחירות ${m.trainFirst}–${m.trainLast} בלבד נבדלים זה מזה באופן מובהק סטטיסטית גם בבחירות ${m.testYear}, ב־${m.heldout.significant} מתוך ${m.heldout.pairs} ההשוואות.`],
    ],
    caveat: "הדמיון בין רשויות מחושב לפי רשימות בודדות; הגושים (ימין, חרדים, מרכז, שמאל, ערבים) רק מתארים את הקנטונים ומוסיפים קישורים ברשת. שמות הקנטונים נקבעו לפי הרשויות הבולטות בהם והגוש הגדול בהם. זהו ניתוח נתונים, לא הצעה מדינית.",
    footer: (l) => [
      "פרויקט M.Sc. במדעי המחשב, אוניברסיטת בר־אילן · אדיר אלמקייס · בהנחיית ד״ר אורן גליקמן",
      `<a href="${l.app}" target="_blank" rel="noopener">אפליקציית המחקר</a> · <a href="${l.report}" target="_blank" rel="noopener">הדוח המלא (PDF)</a> · <a href="${l.repo}" target="_blank" rel="noopener">הקוד והנתונים</a>`,
      "מקורות: תוצאות הבחירות לכנסת לפי רשות מקומית; גבולות רשויות: הלשכה המרכזית לסטטיסטיקה והמנהל האזרחי; מפת רקע: OpenFreeMap ו־OpenStreetMap.",
    ],
    voteIn: (label) => `ההצבעה בבחירות ${label}`,
    cantonsInElection: (label) => `הקנטונים בבחירות ${label}`,
    statusTown: (name) => `נבחרה רשות: ${name}`,
    statusCanton: (name) => `נבחר קנטון: ${name}`,
    mapFailed: "המפה לא נטענה. נסו לרענן את הדף; הנתונים שלמטה זמינים בכל מקרה.",
    dataFailed: "נתוני המפה לא נטענו. נסו לרענן את הדף.",
    zoomIn: "הגדלה",
    zoomOut: "הקטנה",
    attribution: "קרדיטים",
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
      [`${m.heldout.significant} of ${m.heldout.pairs}`, `comparisons between cantons built from the ${m.trainFirst}–${m.trainLast} elections only are significant in ${m.testYear} too`],
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
      ["The division", "Each municipality is described by the vote share of every list that won seats, in each election separately. A network community-detection algorithm (Louvain) groups neighbouring municipalities that vote alike into five cantons. The network also links municipalities that share no border: those where the same bloc wins over 70% of the vote, and municipalities with no neighbour in the data to their most similar ones. So most cantons are not single pieces on the map: mainly the Arab canton and the Haredi cities, and a few single towns, such as Kiryat Shmona and Beit Jann, that belong to a distant canton."],
      ["The checks", `The map is stable: when the method is run on each election alone, ${m.towns_never_moved} of ${m.towns} municipalities stay in the same canton (${m.testYear} differs most). Cantons built from the ${m.trainFirst}–${m.trainLast} elections only still differ significantly in ${m.testYear}, in ${m.heldout.significant} of ${m.heldout.pairs} comparisons.`],
    ],
    caveat: "Similarity between municipalities is computed from individual lists; blocs (Right, Haredi, Center, Left, Arab) only describe the cantons and add links in the network. Canton names come from their best-known municipalities and their largest bloc. This is a data analysis, not a policy proposal.",
    footer: (l) => [
      "M.Sc. project in Computer Science, Bar-Ilan University · Adir Elmakais · Advisor: Dr. Oren Glickman",
      `<a href="${l.app}" target="_blank" rel="noopener">Research app</a> · <a href="${l.report}" target="_blank" rel="noopener">Full report (PDF)</a> · <a href="${l.repo}" target="_blank" rel="noopener">Code and data</a>`,
      "Sources: Knesset election results by local authority; municipal boundaries: Central Bureau of Statistics and the Civil Administration; basemap: OpenFreeMap and OpenStreetMap.",
    ],
    voteIn: (label) => `Vote in the ${label} election`,
    cantonsInElection: (label) => `Cantons in the ${label} election`,
    statusTown: (name) => `Selected municipality: ${name}`,
    statusCanton: (name) => `Selected canton: ${name}`,
    mapFailed: "The map could not load. Try reloading the page; the data below is still available.",
    dataFailed: "The map data could not load. Try reloading the page.",
    zoomIn: "Zoom in",
    zoomOut: "Zoom out",
    attribution: "Credits",
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
// Canton of a town in the current view: the main map, or one election on its own
const cantonOf = (p) => (state.election === "all" ? p.canton : p[`e${state.election}`]);
const cantonIds = () => [...new Set(data.towns.features.map((f) => cantonOf(f.properties)))].sort((a, b) => a - b);
const membersOf = (id) => data.towns.features.filter((f) => cantonOf(f.properties) === id)
  .sort((a, b) => b.properties.voters - a.properties.voters);

// The canton as shown: the report's figures for the main map; for one election, computed from
// that election's vote in the canton's towns (weighted by their average number of valid votes)
function cantonView(id) {
  const base = data.cantons.get(id);
  if (state.election === "all" && base) return base;
  const members = membersOf(id);
  const voters = members.reduce((sum, f) => sum + f.properties.voters, 0);
  const blocs = BLOC_COLORS.map((_, i) => members.reduce(
    (sum, f) => sum + f.properties.votes[state.election][i] * f.properties.voters, 0) / (voters || 1));
  return {
    id,
    he: base ? base.he : TEXT.he.noCounterpart,
    en: base ? base.en : TEXT.en.noCounterpart,
    color: base ? base.color : NO_COUNTERPART_COLOR,
    towns: members.length,
    voters,
    blocs,
    largest: members.slice(0, 5).map((f) => ({ he: f.properties.he, en: f.properties.en })),
  };
}

const localeStrings = () => ({
  "CooperativeGesturesHandler.WindowsHelpText": t().cooperativeDesktop,
  "CooperativeGesturesHandler.MacHelpText": t().cooperativeMac,
  "CooperativeGesturesHandler.MobileHelpText": t().cooperative,
  "NavigationControl.ZoomIn": t().zoomIn,
  "NavigationControl.ZoomOut": t().zoomOut,
  "AttributionControl.ToggleAttribution": t().attribution,
});

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
    locale: localeStrings(),
  });
  placeControls();

  // If the basemap style never loads, draw the cantons on a plain background. Later errors
  // (a failed tile while panning) must not replace the style, or the cantons would vanish.
  let styleLoaded = false;
  let fellBack = false;
  map.on("style.load", () => {
    styleLoaded = true;
    addLayers();
  });
  map.on("error", () => {
    if (styleLoaded || fellBack) return;
    fellBack = true;
    map.setStyle(FALLBACK_STYLE, { diff: false });
  });

  popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 8 });
  map.on("mousemove", "towns-fill", (e) => {
    const f = e.features[0];
    setHover(f.id);
    map.getCanvas().style.cursor = "pointer";
    const p = f.properties;
    const c = data.cantons.get(Number(cantonOf(p)));
    popup.setLngLat(e.lngLat)
      .setHTML(`<div dir="${t().dir}"><b>${escapeHtml(townName(data.byName.get(p.he).properties))}</b><br>${escapeHtml(c ? cantonName(c) : t().noCounterpart)}</div>`)
      .addTo(map);
  });
  map.on("mouseleave", "towns-fill", () => {
    setHover(null);
    map.getCanvas().style.cursor = "";
    popup.remove();
  });
  map.on("click", "towns-fill", (e) => selectTown(e.features[0].properties.he, { fly: false, focus: false }));
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
  const ids = cantonIds();
  const items = ids.map((id) => {
    const c = cantonView(id);
    return `<button type="button" data-canton="${id}" aria-pressed="${state.canton === id}"><span class="swatch" style="background:${c.color}"></span>${escapeHtml(cantonName(c))}</button>`;
  });
  if (state.election !== "all") {
    items.push(`<span class="legend-item"><span class="swatch moved"></span>${escapeHtml(t().legendMoved)}</span>`);
  }
  $("#legend").innerHTML = items.join("");
  const note = $("#election-note");
  note.hidden = state.election === "all";
  if (!note.hidden) note.textContent = t().electionNote(electionLabel(state.election));
}

function cantonCard(c, { clickable }) {
  const largest = c.largest.map((x) => (state.lang === "he" ? x.he : x.en)).join(", ");
  const title = clickable
    ? `<button type="button" class="card-link" data-canton="${c.id}">${escapeHtml(cantonName(c))}</button>`
    : `<span tabindex="-1" data-focus>${escapeHtml(cantonName(c))}</span>`;
  const voteLine = state.election === "all" ? "" : `<p class="sub" style="margin:-6px 0 6px">${escapeHtml(t().voteIn(electionLabel(state.election)))}</p>`;
  return `<article class="card canton-card${state.canton === c.id ? " selected" : ""}"${clickable ? ` data-canton="${c.id}"` : ""}>
    <h3><span class="dot" style="background:${c.color}"></span>${title}</h3>
    <p class="sub">${fmt(c.towns)} ${t().towns} · ${fmt(c.voters)} ${t().votesAvg}</p>
    ${voteLine}${blocBar(c.blocs)}${blocKey(c.blocs)}
    <p class="towns-list">${t().largest}: ${escapeHtml(largest)}</p>
  </article>`;
}

function renderPanel() {
  const panel = $("#panel");
  if (state.town) {
    panel.innerHTML = townCard(data.byName.get(state.town));
  } else if (state.canton !== null && cantonIds().includes(state.canton)) {
    const members = membersOf(state.canton);
    panel.innerHTML = `<button type="button" class="back" data-back>${t().back}</button>
      ${cantonCard(cantonView(state.canton), { clickable: false })}
      <div class="card"><h3>${escapeHtml(t().allTowns(members.length))}</h3>
      <p class="towns-list">${members.map((f) => `<a href="#" data-town="${escapeHtml(f.properties.he)}">${escapeHtml(townName(f.properties))}</a>`).join(" · ")}</p></div>`;
  } else {
    const title = state.election === "all" ? t().cantonsTitle : t().cantonsInElection(electionLabel(state.election));
    panel.innerHTML = `<div><h2 tabindex="-1" data-focus style="margin:0 0 2px;font-size:1.2rem">${escapeHtml(title)}</h2>
      <p class="sub" style="margin:0 0 6px;color:var(--ink-soft)">${t().cantonsHint}</p></div>
      ${cantonIds().map((id) => cantonCard(cantonView(id), { clickable: true })).join("")}`;
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
    const label = `${data.meta.elections[k].short}: ${name}`;
    return `<div><div class="chip${id !== p.canton ? " moved" : ""}" style="background:${color}" role="img" aria-label="${escapeHtml(label)}" title="${escapeHtml(name)}"></div>${escapeHtml(data.meta.elections[k].short)}</div>`;
  }).join("");
  const rows = keys.map((k) => `<tr><td>${escapeHtml(electionLabel(k))}</td>${p.votes[k].map((v) => `<td>${v.toFixed(0)}</td>`).join("")}</tr>`).join("");
  const other = state.lang === "he" ? p.en : p.he;
  return `<button type="button" class="back" data-back>${t().back}</button>
    <div class="card">
      <h3 tabindex="-1" data-focus>${escapeHtml(townName(p))}</h3>
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

function render({ focus = false } = {}) {
  renderLegend();
  renderPanel();
  applyMapState();
  syncUrl();
  const status = state.town ? t().statusTown(townName(data.byName.get(state.town).properties))
    : state.canton !== null ? t().statusCanton(cantonName(cantonView(state.canton))) : "";
  $("#status").textContent = status;
  // Keep keyboard users in place: move focus to the panel's new heading
  if (focus) $("#panel [data-focus]")?.focus({ preventScroll: true });
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

function selectTown(name, { fly = true, focus = true } = {}) {
  const f = data.byName.get(name);
  if (!f) return;
  state.town = name;
  state.canton = null;
  if (fly && map) map.fitBounds(f.bbox, { padding: 80, maxZoom: 11, duration: 700 });
  render({ focus });
}

function selectCanton(id) {
  state.town = null;
  state.canton = state.canton === id ? null : id;
  if (state.canton !== null && map) map.fitBounds(unionBbox(membersOf(id)), { padding: 40, duration: 700 });
  render({ focus: true });
}

function resetSelection() {
  state.town = null;
  state.canton = null;
  render({ focus: true });
}

// Ignore case, spaces, hyphens, apostrophes, Hebrew geresh/gershayim and full spelling (קריית = קרית)
const normalize = (s) => s.toLowerCase().replace(/['"`’׳״()\-–־.\s]/g, "").replace(/יי/g, "י").replace(/וו/g, "ו");

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
  if (e && Object.hasOwn(data.meta.elections, e)) state.election = e;
  const town = params.get("town");
  if (town && data.byName.has(town)) state.town = town;
  const canton = Number(params.get("canton"));
  if (!state.town && params.has("canton") && cantonIds().includes(canton)) state.canton = canton;
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(location.href);
    toast(t().copied);
  } catch {
    window.prompt(t().share, location.href);
  }
}

// Copy the WebGL canvas right after drawing it, before the browser clears its buffer.
// Waits for tiles still loading, so an early click does not export an empty map.
async function captureMap() {
  if (!map.loaded()) {
    // Wait for tiles still loading, but never hang the download on a stuck tile
    await Promise.race([new Promise((resolve) => map.once("idle", resolve)), new Promise((resolve) => setTimeout(resolve, 4000))]);
  }
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
    return copyNow();
  }
  return new Promise((resolve) => {
    map.once("render", () => resolve(copyNow()));
    map.triggerRepaint();
  });
}

// Split text at " · " into lines no wider than maxWidth (the credit line is long on phones)
function wrapCredit(ctx, text, maxWidth) {
  const lines = [];
  for (const part of text.split(" · ")) {
    const last = lines[lines.length - 1];
    if (last !== undefined && ctx.measureText(`${last} · ${part}`).width <= maxWidth) lines[lines.length - 1] = `${last} · ${part}`;
    else lines.push(part);
  }
  return lines;
}

async function downloadMap() {
  if (!map) return;
  try {
    await document.fonts.ready;
    const src = await captureMap();
    const dpr = src.width / map.getCanvas().clientWidth;
    const W = src.width;
    const head = Math.round(70 * dpr);
    const out = document.createElement("canvas");
    out.width = W;
    let ctx = out.getContext("2d");
    const creditFont = `400 ${11 * dpr}px Heebo, Arial, sans-serif`;
    ctx.font = creditFont;
    const credit = wrapCredit(ctx, `${t().footer(data.meta.links)[0]} · © OpenStreetMap`, W - 36 * dpr);
    const lineGap = 15 * dpr;
    out.height = src.height + head + Math.round(10 * dpr + credit.length * lineGap); // resets the context state
    ctx = out.getContext("2d");
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
    ctx.font = creditFont;
    ctx.fillStyle = "#64748b";
    credit.forEach((line, i) => ctx.fillText(line, x0, head + src.height + 4 * dpr + (i + 1) * lineGap - 3 * dpr));

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
    if (map) {
      Object.assign(map._locale || {}, localeStrings()); // MapLibre keeps UI strings here
      if (map.cooperativeGestures.isEnabled()) {
        map.cooperativeGestures.disable();
        map.cooperativeGestures.enable();
      }
    }
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
  let lastGo = { value: null, at: 0 };
  const go = () => {
    // Enter fires keydown and then change: handle the same query once
    if (search.value === lastGo.value && Date.now() - lastGo.at < 800) return;
    lastGo = { value: search.value, at: Date.now() };
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
    console.error(err);
    $("#panel").innerHTML = `<div class="card">${escapeHtml(TEXT.he.dataFailed)}<br><span dir="ltr">${escapeHtml(TEXT.en.dataFailed)}</span></div>`;
    return;
  }
  readUrl();
  renderStatic();
  bindEvents();
  if (typeof maplibregl === "undefined") {
    // The map library did not load (blocked or offline): keep the cards, search and text working
    $("#map").innerHTML = `<p class="map-failed">${escapeHtml(t().mapFailed)}</p>`;
    render();
    return;
  }
  // Hebrew and Arabic basemap labels need the RTL shaping plugin; without it they still show, unshaped
  Promise.resolve().then(() => maplibregl.setRTLTextPlugin(RTL_PLUGIN, true)).catch(() => {});
  initMap();
  render();
  // Fit once the container has its final size (the map is created before layout settles)
  map.once("load", () => {
    map.resize();
    const box = state.town ? data.byName.get(state.town).bbox
      : unionBbox(state.canton === null ? data.towns.features : membersOf(state.canton));
    map.fitBounds(box, { padding: state.town ? 80 : 24, maxZoom: 11, duration: 0 });
  });
}

main();
