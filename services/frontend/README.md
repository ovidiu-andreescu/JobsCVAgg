
# JobsCVAgg Frontend (plug‑and‑play)

A tiny React + Vite + Tailwind app that talks to your existing services.

## Quick start
```bash
npm i
npm run dev
```
Then open the URL it prints. Go to **Settings** and point to your backends:
- User Management (FastAPI): `http://127.0.0.1:8000`
- Job Aggregator (Lambda/API GW): `http://127.0.0.1:9000` (or a full URL already containing `?q=...` etc.)
- Notifications (FastAPI): `http://127.0.0.1:5001`

> Demo login uses password `changeme123`. You can change that in `src/App.tsx`.

## Build
```bash
npm run build
npm run preview
```

## Drop‑in to an existing React app
- Copy `src/components/ui/*` and `src/App.tsx` into your app.
- Ensure you have Tailwind set up (or replace the classes with your own CSS).
- Install deps: `framer-motion`, `lucide-react`.
- Use `<App />` anywhere or split the cards (Search/Auth/Notify/Settings) as needed.
