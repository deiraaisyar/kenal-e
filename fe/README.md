# Kenal-E web

Four pages follow mockup v2: Home, Result, Cek Laci, Catalog. Category details, sorting, drop-off locations, and app information appear in panels. React + TypeScript + Vite; Plus Jakarta Sans is served locally; Lucide icons and SVG illustrations. The logo comes from the user's original asset.

```bash
cd fe
npm ci
npm run dev
```

Vite forwards `/api` to `http://127.0.0.1:8000`. The backend must be started from the repository root. Open `http://localhost:5173`.

- Camera or gallery → resize to JPEG, max 1024 px → API → result.
- The example buttons use reference vectors without requesting new inference and are always labeled as examples.
- An unrecognized result stops before category/risk/price. It can be saved as a question for the maintainers.
- Cek Laci lives in IndexedDB via Zustand; categories can be corrected and items deleted. The report card counts all groups, including unrecognized ones, and is exported as PNG via html-to-image.
- Photos and Cek Laci sessions are not embedded in the service worker cache. The shell/font/catalog cache is available after a successful visit; analysis still needs a network connection. The offline catalog only works after being opened online in a PWA build, not on the dev server.
- The PWA has a manifest, icons, and a service worker. PWA installation/camera needs a secure context (localhost or HTTPS).
- Dataset photos that are not yet available are marked. The drop-off panel shows an illustrative map of the UNDIP area with sample points; directions are not yet active. Research prices come with scope, unit, source, and date; those that are not yet comparable stay without a number.
