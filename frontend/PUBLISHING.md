# Frontend preview publication

> Privacy note (2026-10-14): private account/resource identifiers and personal home paths have been redacted for the public-release candidate. Historical outcomes are unchanged; placeholders are not live targets.

Live preview: <PRIVATE_PREVIEW_URL_OMITTED>

Deployment verification: PASS (`succeeded`, 2026-09-29).

The source repository remains private: https://github.com/chanbilly-lab/docflow.
The preview is owner-private and requires the owner's ChatGPT sign-in. It contains
only synthetic in-memory data; reloading resets changes. No AWS backend is called.

## Site identity

- Project: `<PRIVATE_SITE_ID_OMITTED>`
- Source snapshot: `c21924626110a146eb521b1bcab673344d164573`
- Deployment: `<PRIVATE_SITE_ID_OMITTED>`
- Local isolated checkout: `build/task-021/site-preview/` (ignored)
- Manifest: `.openai/hosting.json` inside that checkout, with the project above
  and `static.directory` set to `dist`.

## Update procedure

1. Run frontend format/lint/tests/build and inspect the changed interactions.
2. Open the existing Site through the Sites workflow, reusing the project ID.
3. Synchronize the complete `frontend/dist/` output into the isolated checkout's
   `dist/`. Remove obsolete assets only inside that isolated static output.
4. Use the Sites skill's workflow to push the exact static snapshot and package
   its archive, then deploy privately and wait for `succeeded` with a URL.
5. Commit the frontend source and documentation to GitHub separately. Never
   publish unfinished TASK-021 backend changes as a completed task.

On this Windows host, put Git Bash and the repository's Node 22 on PATH. Set
`TAR_OPTIONS=--force-local` for the packaging process so a Windows drive path is
not interpreted as a remote tar location. Keep source credentials in memory and
the workflow's hidden stdin, never in arguments, Git, configuration or logs.

GitHub Pages activation returned HTTP 422 for the current private-repository
plan. Repository visibility and paid plans were not changed. There is no automatic
GitHub-to-Sites deployment job. This preview does not satisfy cloud acceptance.
