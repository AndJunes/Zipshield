# Zipshield frontend

Angular 22 SPA — standalone components, zoneless change detection and signals —
styled with Tailwind CSS v4. It talks to the FastAPI backend described in
[`../backend/README.md`](../backend/README.md).

## Setup

```bash
pnpm install
pnpm start        # http://localhost:4200
```

The API base URL comes from `src/environments/environment*.ts`
(`http://localhost:8000` by default) and is injected through the
`API_BASE_URL` token in `src/app/core/services/api-config.ts`.

The login screen shows chips for every seeded demo account (see the root
README), so you can try each role without typing credentials.

## Structure

```
src/app/
├── core/        auth (JWT interceptor, guards), API config, shared services
└── features/    one folder per domain: dashboard, clients, agents,
                 supervisors, policies, claims — each with a list page
                 (xxx-details/) and a detail page (xxx-detail/)
```

## Tests and build

```bash
npx ng test --watch=false   # Vitest, jsdom
npx ng build                # production build in dist/frontend
```
