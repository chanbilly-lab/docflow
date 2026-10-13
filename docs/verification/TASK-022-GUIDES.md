# TASK-022 bilingual illustrated guide supplement

Date: 2026-09-29. Status: DONE (documentation only).

The owner requested Chinese/English documents explaining project purpose and
implemented functions with demonstration images. Delivered matching Markdown
guides and standalone HTML editions with all six PNGs embedded. No external
font, JavaScript or image fetch is required to read the HTML. Reference links
in HTML point to repository source and require internet access when followed.

## Evidence

- PASS: six screenshots captured through real local React demo interactions in
  headless Edge, viewport 1440 x 1100. See images/README.md for exact sequences.
- PASS: both HTML editions load all six images with positive natural dimensions;
  eight principal sections each; no horizontal overflow at 1280px or 390px.
- PASS: visual inspection of both HTML opening layouts and all six screenshots.
- PASS: all Markdown guide image/reference file targets exist.
- PASS: documentation whitespace validation with git diff --check.
- NOT RUN: full backend/frontend/Terraform suites, unnecessary for docs/images.
- NOT RUN: new AWS/browser integration acceptance. No deployment or AWS calls.

Used the existing bundled Playwright/marked tooling and installed Edge; no new
application dependencies. Temporary capture/render/check scripts remain in ignored
build/. Screenshots contain only fictional data. English captions explain the
original Chinese UI; no English product interface is claimed.

## Exact publication file manifest

New files:

- docs/portfolio/guide-zh.md
- docs/portfolio/guide-en.md
- docs/portfolio/DocFlow-中文介绍.html
- docs/portfolio/DocFlow-English-Guide.html
- docs/portfolio/images/README.md
- docs/portfolio/images/01-overview.png
- docs/portfolio/images/02-checklist.png
- docs/portfolio/images/03-approved-history.png
- docs/portfolio/images/04-request-information.png
- docs/portfolio/images/05-information-history.png
- docs/portfolio/images/06-create-case.png
- docs/verification/TASK-022-GUIDES.md

Updated files:

- README.md
- PROJECT_STATUS.md
- docs/tasks.md
- docs/CHANGELOG.md
- docs/portfolio/README.md
- docs/portfolio/cost.md (preceding verified cleanup update)
- docs/adr/029-retire-cloud-and-document-portfolio.md (preceding cleanup amendment)
- docs/verification/AWS-RETIREMENT.md (preceding actual cleanup evidence)

Unrelated unfinished code/infrastructure/acceptance helpers are excluded. TASK-021
remains BLOCKED. The documentation supplement does not certify full cloud
acceptance, production readiness, public-preview access or zero future AWS bills.
