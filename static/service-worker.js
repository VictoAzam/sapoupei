const CACHE_NAME = "sapoupei-static-v8";
const STATIC_ASSETS = [
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/icons/app-icon.svg",
  "/static/manifest.json",
  "/static/vendor/bootstrap-5.3.3/bootstrap.min.css",
  "/static/vendor/bootstrap-5.3.3/bootstrap.bundle.min.js",
  "/static/vendor/bootstrap-icons-1.11.3/font/bootstrap-icons.min.css",
  "/static/vendor/bootstrap-icons-1.11.3/font/fonts/bootstrap-icons.woff2?dd67030699838ea613ee6dbda90effa6",
];

const NETWORK_FIRST_PATHS = [
  "/static/css/style.css",
  "/static/js/app.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const requestUrl = new URL(event.request.url);
  if (event.request.method !== "GET" || requestUrl.origin !== self.location.origin) return;
  if (!requestUrl.pathname.startsWith("/static/")) return;

  if (NETWORK_FIRST_PATHS.includes(requestUrl.pathname)) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match(event.request)),
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        }
        return response;
      });
    }),
  );
});