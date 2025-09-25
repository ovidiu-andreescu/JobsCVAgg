
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

## Integration notes (JobsCVAgg UI)
- Configure bases in the **Settings** tab:
  - User Management (auth, /me): `/api` or full URL to API Gateway stage
  - Job Aggregator (search): `/agg` or full URL (expects query params: q, location, page, results_per_page)
  - Notifications: `/notif` or full URL (POST /notifications/send)
  - CV Handling: `/cv` or use `/api` for `/me/cv` endpoints depending on your deployment
  - Matcher: `/match` or full URL (GET /me/matches)

- Flow:
  1. **Register/Login** in Auth tab (demo password is `changeme123` unless you change it).
  2. Use **Search** to pull jobs from Aggregator.
  3. In **CV** tab, choose a PDF and click **Upload CV** (uses `/me/cv/presign` then S3 POST). Then **Refresh Status**.
  4. In **Matches** tab, click **Refresh** to fetch matches for the logged user.
  5. **Notify** tab allows sending a test message via Notifications service.
