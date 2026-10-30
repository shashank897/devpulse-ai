# DevPulse AI features

DevPulse AI is an evidence-first code-analysis preview. It combines a responsive product site with a working analysis workspace. The interface distinguishes deterministic static-analysis findings from optional AI guidance and unavailable machine-learning predictions.

## Product site

- Responsive landing page that explains the analysis workflow, privacy boundaries, and supported languages.
- Light and dark themes based on the supplied Deep Sea design system, including blue and teal colors, keyboard focus styles, and reduced-motion support.
- Interactive Python example that demonstrates detection of dynamically constructed SQL, highlights the affected line, explains the risk, and previews parameterized SQL.
- Clearly labels the demonstration as a sample, separate from an actual repository scan.

## Code analysis

- Scan a pasted code snippet or a public GitHub repository.
- Python analysis uses the abstract syntax tree to look for dynamic code execution, unsafe pickle deserialization, shell command execution, dynamically constructed SQL, and insecure temporary-file patterns.
- JavaScript and TypeScript checks identify selected dynamic execution and unsafe HTML-sink patterns.
- C and C++ checks identify selected unbounded memory-operation patterns.
- Credential-shaped literals generate a finding with the source evidence redacted.
- Findings show a rule ID, severity, file path, line number, bounded evidence, an explanation, and suggested remediation.
- Syntax errors and partial repository scans are reported as warnings instead of being presented as a clean result.

These rules are deliberately limited. Pattern checks can produce false positives or miss problems; they do not provide a security guarantee.

## Public GitHub scans

- Accepts a public GitHub repository name or URL.
- Reads a read-only snapshot at a pinned commit; the commit appears with scan results.
- Identifies supported source files while excluding common generated and vendor directories.
- Limits each scan to 20 files, 100 KB per file, and 1 MB total. Reports when those limits or GitHub tree truncation make coverage partial.
- Does not run source code, install project dependencies, or access private repositories.

## Analysis workspace

- Shows the risk signal, analyzed files and lines, open findings, and high-severity findings for a completed scan.
- Presents file metrics such as language, line count, Python function count, limited Python branch complexity, and finding count.
- Provides a searchable finding table with severity filters.
- Lets reviewers mark findings as open, confirmed, false positive, or resolved.
- Shows recent scan history and compares rule-weighted signals when multiple scans exist. The chart does not imply that different repositories form a quality trend.
- Supports JSON and SARIF 2.1.0 report exports.
- Provides an explicit action to delete the current browser session’s scan history.

The risk signal is a simple weighted sum of static findings, capped at 100. It is a prioritization aid, not a calibrated probability or proof that code is safe.

## Optional explanations and ML pipeline

- Finding explanations require explicit consent. If configured, only the generic rule name and guidance are sent to OpenRouter; source excerpts are excluded.
- Uses the OpenRouter free route by default and allows only explicitly configured free model routes. Falls back to built-in rule guidance if a key or free-model capacity is unavailable.
- Includes a trainable TF-IDF and logistic-regression defect-classification pipeline for C/C++ data, with duplicate checks, project-disjoint evaluation, and common classification metrics.
- The ML prediction endpoint remains unavailable until a trusted model artifact is configured. No trained model, accuracy claim, or fabricated prediction is included.

## Privacy and deployment

- Uses an anonymous HTTP-only browser session cookie and scopes scan records to that session.
- Keeps raw source out of persistent scan records; findings can retain bounded source excerpts, with credential-shaped evidence redacted.
- Uses FastAPI for the API, Next.js static export for the interface, and SQLAlchemy with PostgreSQL support.
- Runs as a single Docker web service on Render. The current free preview uses ephemeral SQLite storage, so stored scan history can disappear when Render restarts or suspends the service.
- Includes local PostgreSQL Docker Compose configuration, example environment variables, and a GitHub Actions workflow for frontend and backend checks.

## Not available in this preview

- GitHub App installation, OAuth sign-in, and private repository access.
- Webhooks, automated pull-request reviews, or publishing GitHub Checks.
- Dependency vulnerability/advisory scanning.
- A production-trained model, transformer fine-tuning, or a validated model registry.
- Distributed background workers, Redis queues, or durable hosted PostgreSQL provisioned with this service.
- Full historical commit comparison, repository-wide dependency inventory, and verified test coverage.
