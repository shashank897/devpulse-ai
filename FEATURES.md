# DevPulse AI features

DevPulse AI is an evidence-first code-analysis preview. It combines a responsive product site with a working analysis workspace. The interface distinguishes deterministic static-analysis findings from optional AI guidance and experimental machine-learning predictions.

## Product site

- Responsive landing page that explains the analysis workflow, privacy boundaries, and supported languages.
- Light and dark themes based on the supplied Deep Sea design system, including blue and teal colors, keyboard focus styles, and reduced-motion support.
- Interactive Python example that demonstrates detection of dynamically constructed SQL, highlights the affected line, explains the risk, and previews parameterized SQL.
- Clearly labels the demonstration as a sample, separate from an actual repository scan.

## Code analysis

- Scan a pasted code snippet, load a local source file up to 100 KB, or scan a public GitHub repository. File language is detected from its extension; source can be reviewed before submission.
- Python analysis uses the abstract syntax tree to look for dynamic code execution, unsafe pickle deserialization, shell command execution, dynamically constructed SQL, and insecure temporary-file patterns.
- JavaScript and TypeScript checks identify selected dynamic execution and unsafe HTML-sink patterns.
- C and C++ checks identify selected unbounded memory-operation patterns.
- Credential-shaped literals generate a finding with the source evidence redacted.
- Findings show a rule ID, severity, file path, line number, bounded evidence, an explanation, and suggested remediation.
- Syntax errors and partial repository scans are reported as warnings instead of being presented as a clean result.
- Offers separate, opt-in Python security and performance previews in the snippet editor. The security preview parameterizes narrowly matched SQLite f-strings; the performance preview suggests `enumerate` for a simple indexed loop. Both display the current and suggested code side by side and require an explicit apply action. Unsupported cases get no automatic edit; previews are not executed or stored, and performance edits must be benchmarked.

These rules are deliberately limited. Pattern checks can produce false positives or miss problems; they do not provide a security guarantee.

## Public GitHub scans

- Accepts a public GitHub repository name or URL.
- Reads a read-only snapshot at a pinned commit; the commit appears with scan results.
- Identifies supported source files while excluding common generated and vendor directories.
- Limits each scan to 20 source files or Python notebook cells, 100 KB per source, and 1 MB total. Reads a bounded public archive without GitHub REST rate limits. Coverage notices explain skipped content.
- Does not run source code, install project dependencies, or access private repositories.

## Analysis workspace

- Shows the risk signal, analyzed files and lines, open findings, and high-severity findings for a completed scan.
- Presents file metrics such as language, line count, Python function count, limited Python branch complexity, and finding count.
- Combines search with severity (including critical), review status and file filters. Sorts by severity or source location. Summary counters open the relevant actionable findings.
- Opens findings at their pinned GitHub commit; notebook findings link to the notebook without inventing a source line.
- Makes coverage notices visible beside the review summary; a clean result is scoped to the inspected source.
- Lets reviewers mark findings as open, confirmed, false positive, or resolved.
- Searches and filters scan history, opens saved results, rescans public repositories, and retries failed repository imports.
- Compares a repository scan with its previous completed scan, using shared files/cells and rule/evidence matching. Shows newly reported, repeated and no-longer-reported findings. This is a bounded comparison, not verification of fixes.
- Supports JSON and SARIF 2.1.0 report exports plus CSV export of the current filtered findings, with spreadsheet formula prefixes escaped.
- Supports confirmed deletion of an individual completed/failed scan or the session’s entire history. Active scans cannot be deleted, and other sessions cannot access or delete a scan.

The risk signal is a simple weighted sum of static findings, capped at 100. It is a prioritization aid, not a calibrated probability or proof that code is safe.

## Optional explanations and ML pipeline

- Finding explanations require explicit consent. If configured, only the generic rule name and guidance are sent to OpenRouter; source excerpts are excluded.
- Uses the OpenRouter free route by default and allows only explicitly configured free model routes. Falls back to built-in rule guidance if a key or free-model capacity is unavailable.
- Includes TF-IDF pipelines for logistic regression, Random Forest and Extra Trees, with duplicate checks, project-separated evaluation and recorded metrics.
- Runs the trained Extra Trees v3 C/C++ classifier in Files & ML. Its measured QEMU ROC-AUC is 0.5620; scores are uncalibrated experimental signals. Full comparisons are in ML_REPORT.md.

## Privacy and deployment

- Uses an anonymous HTTP-only browser session cookie and scopes scan records to that session.
- Keeps raw source out of persistent scan records; findings can retain bounded source excerpts, with credential-shaped evidence redacted.
- Uses FastAPI for the API, Next.js static export for the interface, and SQLAlchemy with PostgreSQL support.
- Runs as a single Docker web service on Render with PostgreSQL storage in an isolated DevPulse schema shared with the CareerLens database. History access requires the session cookie; retention depends on the hosting plan.
- Includes local PostgreSQL Docker Compose configuration, example environment variables, and a GitHub Actions workflow for frontend and backend checks.

## Not available in this preview

- GitHub App installation, OAuth sign-in, and private repository access.
- Webhooks, automated pull-request reviews, or publishing GitHub Checks.
- Dependency vulnerability/advisory scanning.
- Transformer fine-tuning or a validated production model registry.
- Distributed background workers or Redis queues.
- Full historical commit comparison, repository-wide dependency inventory, and verified test coverage.

## Simplified in this update

Removed the chart comparing unrelated scans, unavailable-check rows on the overview, and the unconfigured private-GitHub row in Settings. Renamed Code DNA to Files & ML and corrected outdated storage/ML descriptions. The existing theme and low idle CPU behavior are retained; no animation library or background polling loop was added.
