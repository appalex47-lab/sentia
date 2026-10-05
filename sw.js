const CACHE_VERSION = "sentia-0.3.39";
const APP_CACHE = `${CACHE_VERSION}-app`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;
const APP_SHELL = [
  "./",
  "./index.html",
  "./css/styles.css",
  "./js/db.js",
  "./js/app.js",
  "./data/datos_procesados.json",
  "./browser-smoke.html",
  "./manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(APP_CACHE).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => !key.startsWith(CACHE_VERSION)).map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  const isAppAsset = url.origin === self.location.origin;
  if (!isAppAsset) return;

  event.respondWith((async () => {
    const cache = await caches.open(RUNTIME_CACHE);
    const cached = await cache.match(request);
    if (cached) return cached;

    try {
      const response = await fetch(request);
      if (response.ok) await cache.put(request, response.clone());
      return response;
    } catch (error) {
      const fallback = await caches.match(request);
      if (fallback) return fallback;
      if (request.mode === "navigate") return caches.match("./index.html");
      throw error;
    }
  })());
});
