// EYC Racing App — Service Worker
// Caches the app for offline use after first load.
// Bump the version string whenever you push a new version of the HTML.

const CACHE_NAME = 'eyc-racing-v1';

const FILES_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './eyc_flag.png'
];

// Install: cache all core files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(FILES_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate: remove old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch: serve from cache, fall back to network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request);
    })
  );
});
