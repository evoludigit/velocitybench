---

# **[Pattern] Progressive Web Apps (PWAs) Reference Guide**

---

## **Overview**
Progressive Web Apps (PWAs) combine the best of web and native apps by leveraging modern web capabilities like offline functionality, push notifications, and platform integration. PWAs provide a seamless, app-like experience without requiring app store distribution or complex installations. This pattern reference outlines key architectural patterns for building PWAs, including service worker strategies, caching mechanisms, offline-first design, and progressive enhancement techniques. It ensures performance, reliability, and user engagement while adhering to web standards.

---

## **Key Concepts & Implementation Details**

### **1. Service Worker Architecture**
A core component of PWAs, the **service worker** acts as a proxy between the browser and network, enabling offline capabilities, caching strategies, and background sync. Implementations must consider:

- **Service Worker Lifecycle**: Registration, installation (and cache population), and activation phases.
- **Cache Strategies**:
  - **Network-First**: Prioritizes live data; caches as a fallback.
  - **Cache-First**: Serves stale data first; updates only on next request (ideal for static assets).
  - **Stale-While-Revalidate**: Returns cached data immediately while refreshing in the background.
  - **Network-Later**: Delays requests until offline to save bandwidth (e.g., downloads).
- **Fallback Strategies**: Graceful degradation when offline (e.g., showing cached content or a custom "offline mode" UI).

**Example Workflow**:
```javascript
// Cache static assets (e.g., HTML, CSS, JS)
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('pwa-cache-v1')
      .then(cache => cache.addAll([
        '/index.html',
        '/styles/main.css',
        '/scripts/app.js'
      ]))
  );
});

// Fetch logic with fallback to cache
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
```

---

### **2. Offline-First Design**
PWAs assume connectivity may fail. Key practices:
- **Critical CSS/JS**: Inline or preload essential styles/script to render above-the-fold content even when offline.
- **Data Persistence**: Use `IndexedDB` or `localStorage` for user data (e.g., forms, local edits).
- **Service Worker Updates**: Implement versioning (e.g., `cache-name` with timestamps) to force updates when new assets are added.

**Example: IndexedDB for Offline Data**
```javascript
// Initialize DB
const request = indexedDB.open('pwa-db', 1);
request.onupgradeneeded = (event) => {
  const db = event.target.result;
  if (!db.objectStoreNames.contains('userData')) {
    db.createObjectStore('userData');
  }
};

// Store data
db.transaction('userData', 'readwrite')
  .objectStore('userData')
  .put({ key: 'value', timestamp: Date.now() });
```

---

### **3. Progressive Enhancement**
Build for the lowest common denominator (basic HTML/CSS/JS) and enhance where possible:
- **Base Experience**: Functional without JavaScript (e.g., semantic HTML, ARIA labels).
- **Progressive Features**: Add interactivity (e.g., lazy-loaded images, web components) after initial load.
- **Feature Detection**: Use libraries like [Modernizr](https://modernizr.com/) or native APIs to enable/disable features dynamically.

**Example: Feature Detection**
```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('Service Worker registered'))
    .catch(err => console.error('Registration failed:', err));
}
```

---

### **4. Web App Manifest**
A JSON file (`manifest.json`) defines how the PWA appears in the OS (e.g., splash screen, theme colors, display mode). Required fields:
| Key               | Description                                                                 | Example Value                          |
|-------------------|-----------------------------------------------------------------------------|----------------------------------------|
| `name`            | App name displayed in the OS.                                               | `"My Awesome PWA"`                     |
| `short_name`      | Shortened name for the home screen.                                          | `"MyPWA"`                              |
| `start_url`       | URL the app launches to.                                                     | `"/"`                                  |
| `display`         | How the app displays (e.g., `standalone`, `fullscreen`, `minimal-ui`).       | `"standalone"`                         |
| `background_color`| Background color for the splash screen.                                      | `"#ffffff"`                            |
| `theme_color`     | Themes the browser/OS UI (e.g., address bar).                                | `"#000000"`                            |
| `icons`           | Array of icon assets (sizes: 48x48px to 512x512px).                         | `{ "src": "icon-192x192.png", "sizes": "192x192", "type": "image/png" }` |
| `scope`           | Canonical URL for offline access.                                            | `"/"`                                  |

**Example Manifest**:
```json
{
  "name": "My Progressive Web App",
  "short_name": "MyPWA",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    { "src": "icon-192x192.png", "sizes": "192x192", "type": "image/png" }
  ]
}
```

---

### **5. Push Notifications & Background Sync**
- **Push Notifications**: Use the [Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API) for async updates.
  - Requires a **Web Push Certificate** (generated via Cloudflare, Firebase, or similar).
  - Example:
    ```javascript
    const subscription = await navigator.serviceWorker.ready.then(registration =>
      registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(p256dh)
      })
    );
    ```
- **Background Sync**: Retry failed requests when connectivity resumes (e.g., uploading drafts).
  - Example:
    ```javascript
    navigator.serviceWorker.ready.then(registration =>
      registration.sync.register('pwa-sync-tag')
    );
    ```

---

### **6. Performance Optimization**
| Technique               | Description                                                                 | Tools to Use                          |
|-------------------------|-----------------------------------------------------------------------------|----------------------------------------|
| **Lazy Loading**        | Defer non-critical resources (e.g., images, scripts).                     | `<img loading="lazy">`, `IntersectionObserver` |
| **Code Splitting**      | Split bundle into chunks (e.g., React.lazy, dynamic `import()`).           | Webpack, Rollup                         |
| **Critical CSS**        | Inline above-the-fold CSS to reduce render-blocking.                       | [PurgeCSS](https://purgecss.com/)       |
| **Reduced Motion**      | Respect `prefers-reduced-motion` media query for accessibility.             | CSS `@media (prefers-reduced-motion)`   |
| **Web Vitals**          | Monitor Core Web Vitals (LCP, FID, CLS) for performance.                   | Lighthouse, Chrome DevTools            |

---

## **Schema Reference**
Below is a reference table for PWA configuration objects and APIs.

| **Category**       | **Object/API**               | **Purpose**                                                                 | **Key Properties/Methods**                          |
|--------------------|------------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| **Service Worker** | `navigator.serviceWorker`    | Register/install service workers.                                           | `register()`, `ready`, `controllers`               |
| **Caching**        | `Caches`                     | Manage cache storage (open, match, add).                                    | `open()`, `match()`, `add()`, `delete()`            |
| **IndexedDB**      | `indexedDB`                  | Store structured data offline.                                               | `open()`, `transaction`, `ObjectStore`             |
| **Push API**       | `PushManager`                | Handle push notifications.                                                   | `subscribe()`, `unsubscribe()`, `getSubscription()` |
| **Sync API**       | `SyncManager`                | Synchronize data when online.                                                | `register()`, `getRegistration()`                  |
| **Manifest**       | `manifest.json`              | Define app metadata (icons, display mode).                                   | `name`, `start_url`, `display`, `icons`            |
| **Web Push**       | `PushSubscription`           | Store push subscription data.                                               | `endpoint`, `keys` (auth, p256dh)                 |

---

## **Query Examples**

### **1. Registering a Service Worker**
```javascript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('Registered:', reg.scope))
      .catch(err => console.error('Registration failed:', err));
  });
}
```

### **2. Fetching with Cache Fallback**
```javascript
// In your service worker (sw.js)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
```

### **3. Storing Data in IndexedDB**
```javascript
// Client-side storage
async function saveData(data) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('pwa-db', 1);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('userData')) {
        db.createObjectStore('userData');
      }
    };
    request.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction('userData', 'readwrite');
      const store = transaction.objectStore('userData');
      const request = store.put(data, 'user-data-key');
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    };
    request.onerror = (event) => reject(event.target.error);
  });
}
```

### **4. Handling Push Notifications**
```javascript
// Client-side subscription
async function requestPermission() {
  const permission = await Notification.requestPermission();
  if (permission === 'granted') {
    const subscription = await navigator.serviceWorker.ready.then(registration =>
      registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(p256dh)
      })
    );
    console.log('Subscription:', subscription);
  }
}
```

---

## **Related Patterns**

| **Pattern**                          | **Description**                                                                 | **When to Use**                                  |
|--------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Offline-First Design](https://web.dev/progressive-web-apps/)** | Build apps that work without constant connectivity.                       | Critical mobile/app scenarios.                   |
| **[Service Worker Caching Strategies](https://developers.google.com/web/fundamentals/primers/service-workers/caching-strategies)** | Define how assets are cached (network-first, cache-first, etc.).      | Static sites, hybrid apps.                      |
| **[Web App Manifest](https://web.dev/add-manifest/)**             | Configures app-like behavior (icons, theme, display mode).                   | Creating app-like experiences.                  |
| **[Background Sync API](https://developers.google.com/web/updates/2015/03/background-sync)** | Retry failed requests when connectivity resumes.                          | Forms, uploads, or data synchronization.         |
| **[Web Components](https://developer.mozilla.org/en-US/docs/Web/Web_Components)** | Reusable custom elements/styles (e.g., `<my-element>`).                     | Modular, reusable UI components.                |
| **[Lazy Loading](https://web.dev/lazy-loading/)**                  | Defer loading of non-critical resources.                                    | Performance-critical pages.                     |
| **[Reduced Motion](https://web.dev/articles/respect-reduced-motion/)** | Respect user preferences for reduced motion.                                | Accessibility compliance.                       |
| **[Web Push Notifications](https://web.dev/push-notifications/)**   | Send async updates to users.                                                 | Engagement, reminders, or alerts.                |

---

## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| Service worker not registering      | Check browser support (`'serviceWorker' in navigator`).                     |
| Cached content stale                | Update cache version (e.g., `cache-name` with timestamp).                   |
| IndexedDB not persisting            | Verify permissions and transaction handling.                                |
| Push notifications failing          | Validate subscription endpoint/keys; test with [Web Push Simulator](https://web-push-codelab.glitch.me/). |
| App not installing (PWA)            | Ensure `manifest.json` is valid and linked (`<link rel="manifest" href="/manifest.json">`). |
| Performance issues                  | Audit with [Lighthouse](https://developer.chrome.com/docs/lighthouse/overview/) or [WebPageTest](https://www.webpagetest.org/). |

---
**Note**: PWAs require HTTPS (or `localhost` for development). Test across browsers (Chrome, Firefox, Edge) for compatibility.