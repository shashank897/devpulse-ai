# Security model and limitations

Source is never executed. The service does not clone repositories, run hooks, install repository dependencies, or invoke subprocesses on source. GitHub requests target the fixed api.github.com origin without credentials or redirect following; only public sources are accessible. Blob reads are limited to 20 eligible files, 100 KB per file, and 1 MB per scan. No archive extraction occurs.

Browser sessions use unpredictable 256-bit cookies, HttpOnly, SameSite=Strict and Secure in production. The database stores a hash of the cookie. Every scan/read/export/update is scoped to that hash. This is anonymous session isolation, not a full account authentication system. Cross-origin mutations are rejected. The runtime is designed for a single process; use a proper shared queue/rate limiter before scaling to multiple workers.

Findings include bounded source evidence; credential-shaped literal evidence is redacted. The redactor cannot detect every secret. Raw source is discarded after analysis. The public preview is not suitable for confidential repositories. Excerpts are deleted with scan history. SQLite is ephemeral on the free host; PostgreSQL is supported for durable deployments.

Cloud AI is opt-in, server-side, and constrained to free routes. Only generic rule metadata is sent, not excerpts. Results are suggestions and never automatically applied. Model artifacts are deployment-controlled; joblib must never deserialize user uploads.

No analyzer provides a security guarantee. Pattern rules have false positives and blind spots. Python query lookup is not scope-aware taint analysis. ML signals are not confirmed vulnerabilities. Please report vulnerabilities privately to the repository owner instead of posting credentials in public issues.
