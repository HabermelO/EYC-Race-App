// EYC Racing App — Service Worker
// Strategy: Network-First, fallback to Cache.
// The app always tries the network first. If online and a new version
// exists on GitHub, it downloads and caches it automatically.
// If offline, it serves the last cached version instantly.
//
// HOW TO PUSH UPDATES TO ALL USERS:
// Bump the version number below (e.g. v3 -> v4) every time you push
// a new version of index.html to GitHub.
// The browser will detect the changed sw.js, install the new worker,
// and wipe the old cache — users get the update on next open.

const CACHE_VERSION = 'eyc-racing-v16';

const FILES_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './eyc_flag.png'
];

// Install: pre-cache all core files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => {
      return cache.addAll(FILES_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate: delete any old version caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_VERSION)
          .map(key => {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          })
      )
    )
  );
  self.clients.claim();
});

// Fetch: Network-First strategy
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  // Weather API: network only, never cache
  if (event.request.url.includes('open-meteo.com')) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(networkResponse => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_VERSION).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request).then(cached => {
          if (cached) return cached;
          if (event.request.headers.get('accept') &&
              event.request.headers.get('accept').includes('text/html')) {
            return caches.match('./index.html');
          }
        });
      })
  );
});
