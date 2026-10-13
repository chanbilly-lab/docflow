# DocFlow review workspace

A responsive Traditional Chinese React/TypeScript demo. Uses the existing Vite
toolchain with no new runtime dependencies, remote fonts or external requests.

See [PUBLISHING.md](PUBLISHING.md) for the private online preview and update process.

## Run locally

With the repository's Node 22 tooling on PATH:

```sh
cd frontend
npm ci
npm run dev -- --port 5173
```

Open http://127.0.0.1:5173/. The development server binds only to loopback.

## Try the page

- Search by company, requester or case ID, and combine search with status filters.
- Open a case and switch between documents, checklist and activity.
- Claim/start a pending demo review. Approval requires four completed checks.
- Reject or request information with a nonblank reason; inspect the new history.
- Create a local draft or export the filtered list as explicitly marked demo JSON.
- Open the template viewer or use the help dialog to reset the demo.

All state lives in memory and resets on reload. Documents are synthetic metadata,
not files. Login, real uploads, production roles, backend APIs, notifications,
resubmission and template editing are not connected. The combined workspace is a
design preview, not an authorization boundary or proof of cloud acceptance.

## Checks

```sh
npm run format:check
npm run lint
npm test
npm run build
```

See `docs/verification/TASK-021-FRONTEND.md` at the repository root for the dated
browser verification and the separate TASK-021 cloud blocker.
