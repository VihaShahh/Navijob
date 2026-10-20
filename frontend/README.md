# NaviJob frontend

Next.js/React with self-hosted Manrope and the Sage & Forest design. Follow the
[root README](../README.md) for the isolated Django preview, fictional accounts,
checks and Chrome journey commands. Node.js 20.9+ runs the app; browser scripts
require Node.js 22+.

```bash
npm ci
npm run dev -- --hostname localhost --port 3100
npm run lint
npx tsc --noEmit
npm run build
```

Webpack is selected for development and builds because the local Turbopack run
failed package resolution. `/api/` requests use Django through a same-origin proxy;
endpoint trailing slashes are preserved. `BACKEND_URL` defaults to
`http://127.0.0.1:8100`. Authentication uses server sessions and CSRF cookies.
The legacy demo-auth module cannot grant backend access.

`/api/demo/jobs` exposes clearly labeled, read-only fictional JSON. Legacy waitlist
and visitor integrations are separate from the core job platform; optional Supabase
environment values are listed in `.env.example`. No service-role secret belongs in
browser-exposed environment variables.
