# DevPulse AI architecture

## Implementation plan
1. Deep Sea design tokens and reusable UI, landing page and workspace.
2. Bounded static analysis, public GitHub snapshots, isolated scan history and triage.
3. Dependency intelligence, optional free-model explanations and ML training pipeline.
4. Security tests, production build, GitHub publication and Render verification.

## Reference lock
UI.md is authoritative: Deep Sea canvas, blue primary actions, teal highlights, 8/12px radii, 4px spacing, system theme with manual override. The supplied brief owns the code demo and repository workflow. Refero craft guidance contributes keyboard focus and semantic form states; its online library was unavailable. Code is the hero media: an actual editable sample with computed findings, not fabricated product metrics.

## Runtime
Next.js App Router exports a static frontend. FastAPI serves it and /api/v1 from one origin. Feature modules are under src/features; atoms, patterns and layout are separated as UI.md specifies. TanStack Query owns server data. SQLAlchemy stores session-owned scans and findings. PostgreSQL is supported via DATABASE_URL; SQLite is a local/ephemeral preview fallback. A bounded background executor supports one scan at a time on the small preview instance. Docker Compose provides PostgreSQL locally.

## API contract
GET /health; GET /capabilities; GET /scans; POST /scans {name,language,code,repository?}; GET /scans/{id}; PATCH /scans/{id}/findings/{finding_id} {status}; GET /scans/{id}/export?format=json|sarif; DELETE /scans; POST /explain {scan_id,finding_id,consent}; POST /ml/predict {code,language}. All under /api/v1. HttpOnly session cookies isolate data. Mutations require same-origin requests. No source is executed.

## Scope boundaries
Public repository scans pin a commit and read bounded blobs from GitHub. They do not claim full repository coverage. Private GitHub App OAuth, webhook/check publication, distributed Celery workers, transformer training on real data, and full historical commit comparison require additional provisioning/work and are not advertised as available. The preview stores no raw source after analysis. Findings can include bounded excerpts. Generative AI is opt-in, server-side, free-route only. ML is unavailable until a trained local artifact is supplied; no synthetic accuracy is displayed.
