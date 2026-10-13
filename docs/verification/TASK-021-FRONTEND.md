# TASK-021 frontend workspace - 2026-09-29

User explicitly extended this continuation with a frontend page design request.
Local frontend implementation is complete; overall TASK-021 remains BLOCKED by
the independently documented Lambda concurrency prerequisite and unfinished live
acceptance. No new AWS deployment, quota request, email or AWS mutation in this work.
The user subsequently authorized frontend GitHub publication and an online preview;
the static Site publication is independent of AWS acceptance.

## Delivered page

Traditional Chinese document-review workspace: forest-green navigation, warm
neutral surfaces, sage highlights, a document illustration made with CSS/SVG,
case summary cards and a case list/detail split layout. Responsive navigation
and stacked details adapt to mobile. Small text is at least 11px; controls have
visible keyboard focus, accessible names and native modal focus containment.

Working local interactions: search/status filters, empty state, case selection,
document-information/checklist/activity views, pending-review claim/start,
four-check approval gate, reason-required reject/request-information dialogs,
immutable activity append, create-draft form, filtered JSON export, read-only
template viewer and reset. On narrow screens opening a row scrolls/focuses details.
Transient status feedback clears after six seconds; decision errors stay in-dialog.

## Explicit boundary

Eight synthetic cases run only in React memory. Reload resets changes. Company
display names and IDs are design fixtures, not new API fields. No remote fonts,
network API, login, real file upload/download, email or backend authorization is
represented as integrated. The document dialog explicitly says no actual PDF is
present. Demonstration labels remain visible. Cloud acceptance is NOT RUN here.
No architecture, dependency, backend, API/event contract or IAM changes.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Frontend Prettier check | PASS | Existing npm script, all files formatted. |
| Frontend ESLint | PASS | Existing npm script with zero warnings. |
| Vitest | PASS | Six tests: shell/demo boundary, combined search, required checks, reasons for both non-approval outcomes, immutable history and terminal-decision rejection. |
| TypeScript / Vite production build | PASS | Existing npm build script. |
| Desktop/mobile Edge interaction pass | PASS | Headless installed Edge with bundled Playwright; 1440px and 390px viewports, plus 320px overflow check. Search/empty/reset, check-gated approval/history, request-information reason, mobile detail focus, whitespace rejection guard, rejection history, create, JSON export, Escape, reset/reload; no page errors, external requests or mobile page overflow. |
| Visual inspection | PASS | Desktop/mobile screenshots viewed; final readability and mobile focus refinements verified. |
| Backend/Terraform/cloud suites | NOT RUN | Frontend-only scope; existing dated backend/cloud evidence is unchanged. |
| Private static Site deployment | PASS | Deployment succeeded; live URL and source snapshot are recorded in frontend/PUBLISHING.md. |

Frontend-only GitHub publication is explicitly authorized independently of TASK-021.
Use the repository commit and remote branch as publication evidence; this is not a
TASK-021 completion commit. Earlier cloud-session changes remain outside its scope.

Private browser check and screenshots: ignored `build/task-021/frontend-browser-check.cjs`,
`frontend-desktop.png` and `frontend-mobile.png` in that directory. The built-in
browser automation process failed twice; verification used installed headless Edge.
No new browser/testing package was added to the repository.

## Exact files changed in this continuation

- frontend/src/App.tsx
- frontend/src/demo.ts
- frontend/src/styles.css
- frontend/index.html
- frontend/tests/App.test.tsx
- frontend/README.md
- PROJECT_STATUS.md
- docs/tasks.md
- docs/CHANGELOG.md
- docs/TECHNICAL_DESIGN.md
- docs/verification/TASK-021-FRONTEND.md

Next: TASK-021 cloud quota/configuration resolution and separately reviewed live
acceptance; later connect this UI to production authentication and API contracts.
TASK-022 remains TODO. No live behavior is inferred from the frontend demo.
