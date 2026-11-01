# Frontend reference and implementation

## Build target

User-supplied reference: [ScanRepo](https://www.scanrepo.dev/), inspected in a clean browser at desktop size on 2026-10-31. Preserve DevPulse's existing light/dark blue and teal theme, backend, analysis behavior and core tools. Implementation is original; reference assets and source code are not included.

Refero style searches were attempted, but the service returned `NO_SUBSCRIPTION`. Research therefore uses the supplied live reference, the existing DevPulse design system and the Refero skill's bundled motion guidance. The supplied URL provides a concrete target for direct implementation.

## Reference lock and decisions

| Decision | Source | Adaptation |
| --- | --- | --- |
| Repository input in the hero | ScanRepo landing page | Calls the existing scan API and opens the resulting scan in DevPulse's workspace. |
| Status strip, compact sticky navigation | ScanRepo header | Shows actual service capabilities and storage; includes DevPulse workspace navigation and theme toggle. |
| Text-first hero | User performance request | Removed the ASCII shield and its canvas, frame loop, pointer listeners and observers. Existing typography, spacing and theme remain. |
| Static status and cursor | User performance request, bundled motion guidance | No perpetual decorative animations; loading spinners still indicate actual work. |
| Four counters and tabbed scan feed | ScanRepo landing page | Uses the current browser session's real results, capped by the API's 50-scan history. No global counts or public scan feed are invented. |
| Six detection cards | ScanRepo's detection section | Describes DevPulse's implemented rule families and notebook support. |
| FAQ and bottom action | ScanRepo question section and CLI strip | Expandable FAQ and links to actual workspace/export features. No unsupported CLI, IoC scanning or Bitbucket claims. |
| Colors, font roles, rounded controls | Existing `tokens.css`, user constraint | Existing blue/teal light and dark themes retained. No new color system or pixel font replaces the current theme. |
| Micro feedback and state transitions | Bundled Refero motion guide | Short hover/press states, feed transitions, modal/drawer entry and FAQ expansion. Counters and input hints are static; sections appear without reveal observers. |
| Dashboard shell | Reference's compact horizontal navigation | Existing workspace tools now use horizontal tabs; findings, triage, explanations, ML, history, exports and settings retain their APIs. |

The page does not run decorative frame loops or typing timers. The sticky header uses an opaque theme surface instead of backdrop blur. A small SVG chart replaces Recharts; values are available by pointer, keyboard and an expandable table. Route prefetch is disabled on the shared navigation and landing page to avoid loading unvisited screens. Queries stay fresh for 30 seconds; explicit invalidation and active-scan polling still update results immediately. Source inspection and results are never delayed by a decorative scan timer. The API, model, database schema, limits and security policy are unchanged by this frontend work.

## Validation

Production build and TypeScript checks; browser review at desktop/mobile sizes in both themes; keyboard and reduced-motion checks; actual local API scans, URL validation, scan deep links, feed filters, navigation, notebook import, finding triage, exports and the existing experimental ML prediction. Review screenshots are generated locally rather than committed as product assets.

Completed browser checks: 360, 390, 768, 1024 and 1440 px widths; no horizontal page overflow; no page JavaScript errors. A public repository submission imported 20 notebook cells at the expected commit. The existing snippet dialog, finding confirmation, explanation request, SARIF export, ML prediction, mobile menu, filters, FAQ, keyboard shortcut and reduced-motion state all passed. Final visual review adjusted ML result spacing and kept all five workspace tabs visible on small screens. Production builds were run from a clean temporary source copy because OneDrive marked an old generated `.next` folder read-only; the committed application configuration did not change.

## Low-CPU optimization verification — 2026-10-31

Compared the previous production source (`cabe71c`) with this change using production builds, headless Chrome, a 1440 × 900 viewport, and CDP's 4× CPU slowdown. Each run used a fresh browser context, waited for the engine response and four seconds of settling, then measured ten seconds on the idle home page. Both versions were served by the same local FastAPI process, with no active scans. These are controlled main-thread measurements, not device-wide CPU percentages or network speed claims.

| Measurement | Before | After |
| --- | --- | --- |
| Idle main-thread task time, three runs | 7194.2 / 7152.0 / 6957.9 ms | 10.9 / 6.7 / 13.1 ms |
| Median idle task time | 7152.0 ms | 10.9 ms (99.8% lower) |
| Animation-frame callbacks in each idle window | 1169 / 1207 / 1197 | 0 / 0 / 0 |
| Timer callbacks in each idle window | 100 / 102 / 104 | 0 / 0 / 0 |
| Running idle CSS animations | 3 | 0 |
| Home JavaScript, decoded bytes | 533,325 | 529,012 |
| Workspace JavaScript, decoded bytes | 913,296 | 557,451 (39.0% lower) |

Workspace byte counts were captured from browser resource timings on a direct `/workspace/` visit in a fresh context, with identical empty API fixtures and three seconds of settling. The old route was served by Render; the new route used the local production build. Decoded sizes exclude transport compression and are not download-time measurements.

The production build and TypeScript check passed. Real local API workflows passed again: public GitHub import (20 notebook cells), snippet creation, scan selection, finding triage, explanations, SARIF export and ML prediction. The optimization-specific browser check used 4× CPU slowdown and verified a static hero/input, zero idle animations, the sample interaction, both themes at five viewport widths, and a 50-point chart with 0/100 endpoints, keyboard selection and its accessible values table. No page JavaScript errors or horizontal page overflow were observed. Loading feedback and active-scan polling remain available.

## Practical scanning update — 2026-11-01

User priority: practical scanning and clearer results. Preserve the existing blue/teal theme, compact header and low idle CPU use. Reference research: GitHub code-scanning alert filters and source evidence (https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning-alerts), SonarQube review summaries (https://www.sonarsource.com/resources/library/getting-started-with-sonarqube-cloud/), and Snyk remediation workflows (https://snyk.io/product/snyk-code/). These inform product patterns, not claims of equivalent analysis capabilities.

Decisions: replace unrelated-scan trend charts with same-repository comparisons; replace unimplemented-check rows with explicit inspected-source coverage; add actionable severity counts, combined filters and CSV exports; make saved scans navigable and retryable; load source files into the existing bounded snippet form. Keep consent, source redaction, session isolation, preview limits and the experimental ML tool. Rename Code DNA to Files & ML.

Validation: TypeScript/production build; helper checks for safe source URLs, multi-filter ordering, scoped comparisons including repeated evidence, and CSV escaping; API checks for deletion ownership, active-scan protection and failed-import metadata; browser flows for upload validation, scanning, triage, filters, exports, history, deletion, source links and rescan. Desktop/mobile visual checks cover both themes and 360/390/768/1440 px widths. No page errors or page-width overflow observed.
