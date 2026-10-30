# Frontend reference and implementation

## Build target

User-supplied reference: [ScanRepo](https://www.scanrepo.dev/), inspected in a clean browser at desktop size on 2026-10-31. Preserve DevPulse's existing light/dark blue and teal theme, backend, analysis behavior and core tools. Implementation is original; reference assets and source code are not included.

Refero style searches were attempted, but the service returned `NO_SUBSCRIPTION`. Research therefore uses the supplied live reference, the existing DevPulse design system and the Refero skill's bundled motion guidance. The supplied URL provides a concrete target for direct implementation.

## Reference lock and decisions

| Decision | Source | Adaptation |
| --- | --- | --- |
| Repository input in the hero | ScanRepo landing page | Calls the existing scan API and opens the resulting scan in DevPulse's workspace. |
| Status strip, compact sticky navigation | ScanRepo header | Shows actual service capabilities and storage; includes DevPulse workspace navigation and theme toggle. |
| Canvas-based interactive ASCII artwork | ScanRepo's animated wireframe canvas | Original projected character shield with pointer tilt, orbital field and scanning highlight, drawn in existing primary/accent colors. |
| Pulsing status and blinking cursor | Observed `pulseDot` and `blinkCursor` effects | Native CSS with reduced-motion support. |
| Four counters and tabbed scan feed | ScanRepo landing page | Uses the current browser session's real results, capped by the API's 50-scan history. No global counts or public scan feed are invented. |
| Six detection cards | ScanRepo's detection section | Describes DevPulse's implemented rule families and notebook support. |
| FAQ and bottom action | ScanRepo question section and CLI strip | Expandable FAQ and links to actual workspace/export features. No unsupported CLI, IoC scanning or Bitbucket claims. |
| Colors, font roles, rounded controls | Existing `tokens.css`, user constraint | Existing blue/teal light and dark themes retained. No new color system or pixel font replaces the current theme. |
| Micro feedback and state transitions | Bundled Refero motion guide | Hover/press states, count-up on changed data, typed input suggestions, feed transitions, section reveals, modal/drawer entry and FAQ expansion. |
| Dashboard shell | Reference's compact horizontal navigation | Existing workspace tools now use horizontal tabs; findings, triage, explanations, ML, history, exports and settings retain their APIs. |

Canvas animation pauses when hidden or outside the viewport. Reduced-motion preference stops recurring motion and renders a static canvas. Source inspection and results are never delayed by a decorative scan timer. The API, model, database schema, limits and security policy are unchanged by this frontend work.

## Validation

Production build and TypeScript checks; browser review at desktop/mobile sizes in both themes; keyboard and reduced-motion checks; actual local API scans, URL validation, scan deep links, feed filters, navigation, notebook import, finding triage, exports and the existing experimental ML prediction. Review screenshots are generated locally rather than committed as product assets.

Completed browser checks: 360, 390, 768, 1024 and 1440 px widths; no horizontal page overflow; no page JavaScript errors. A public repository submission imported 20 notebook cells at the expected commit. The existing snippet dialog, finding confirmation, explanation request, SARIF export, ML prediction, mobile menu, filters, FAQ, keyboard shortcut and reduced-motion state all passed. Final visual review adjusted ML result spacing and kept all five workspace tabs visible on small screens. Production builds were run from a clean temporary source copy because OneDrive marked an old generated `.next` folder read-only; the committed application configuration did not change.
