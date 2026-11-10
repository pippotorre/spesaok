/* spesaok – service worker. VERSION cambia a ogni build. */
const VERSION = "__VER__";
const SHELL = `spesaok-shell-${VERSION}`, DATA = "spesaok-data", FONTS = "spesaok-fonts";
const ASSETS = ["./", "index.html", "style.css?v=__VER__", "app.js?v=__VER__", "negozi.json", "manifest.webmanifest",
  "icons/favicon.svg", "icons/favicon-64.png", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];

self.addEventListener("install", e => {
  e.waitUntil(Promise.all([
    caches.open(SHELL).then(c => c.addAll(ASSETS)),
    caches.open(DATA).then(c => c.add("offerte.json")).catch(() => {})
  ]).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("spesaok-shell-") && k !== SHELL).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin && url.pathname.endsWith("/offerte.json")) {
    // Dati: prima la rete (con timeout), poi la copia salvata
    e.respondWith((async () => {
      const cache = await caches.open(DATA);
      try {
        const res = await Promise.race([fetch(req, {cache:"no-cache"}), new Promise((_, rej) => setTimeout(rej, 5000))]);
        if (res.ok) cache.put("offerte.json", res.clone());
        return res;
      } catch (err) {
        return (await cache.match("offerte.json")) || Response.error();
      }
    })());
    return;
  }
  if (url.host.endsWith("fonts.googleapis.com") || url.host.endsWith("fonts.gstatic.com")) {
    e.respondWith(caches.open(FONTS).then(async c => (await c.match(req)) || fetch(req).then(r => { c.put(req, r.clone()); return r; })));
    return;
  }
  if (url.origin === location.origin) {
    e.respondWith(caches.match(req, {ignoreSearch: req.mode === "navigate"}).then(r => r || fetch(req).catch(() => caches.match("index.html"))));
  }
});
