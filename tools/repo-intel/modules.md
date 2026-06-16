# Module Reference

This document details the logic and operation of each signal module in `repo-intel`.

## Core Philosophy
Modules are designed to be **single-purpose signal collectors**. They do not make final prioritization decisions; instead, they provide evidence (signals) to the central Context Engine, which calculates Audit Priority based on Confidence, Research Value, and Impact.

## Global Capabilities

### Global Blacklist (Content)
All signal modules automatically check findings against a global content blacklist (`repo_intel/patterns/blacklist.txt`).
-   **Effect**: If a finding's title or description contains a blacklisted term (case-insensitive), its severity is forced to **Info** and scores are downgraded.
-   **Use Case**: Reducing noise from known test tools, legacy systems, or false positives.

### Filepath Blacklist (Context)
Findings are checked against a filepath blacklist (`repo_intel/patterns/filepath_blacklist.txt`).
-   **Effect**: If a finding's file path matches a blacklisted pattern (e.g., `test/`, `spec/`), its severity is forced to **Info** and scores are downgraded.
-   **Use Case**: Automatically deprioritizing findings in tests, documentation, or vendor directories.

---

## Source Modules
*Miners that collect metadata and history.*

### `github_commits_analyse`
**Purpose**: Scans git commit history for security-relevant changes.
**Logic**:
1.  Iterates through git commit history (default: last 1000 commits).
2.  **CVE Detection**: Regex searches commit messages for `CVE-YYYY-NNNN` patterns.
3.  **Keyword Matching**: Scans messages against a library of security patterns (e.g., "XSS", "Buffer Overflow").
4.  **Revert Detection**: Flags commits that revert security fixes (High Signal).
5.  **Partial Fix Analysis**: Flags commit messages using words like "mitigate", "workaround", "temporary" (High Signal).
**Signals**: `cve`, `security_keyword`, `revert_security_fix`, `partial_security_fix`

### `github_issues`
**Purpose**: Identifies security discussions in the issue tracker.
**Logic**:
1.  Connects to GitHub API.
2.  Searches repository issues using high-value security keywords.
3.  **Deep Search**: Analyzes Issue Title, Body, **and Comments**.
4.  **CVE Extraction**: Regex searches for CVE IDs.
**Signals**: `github_issue`, `cve`, `security_keyword`

### `github_labels_analyse`
**Purpose**: Scans for issues/PRs tagged with security labels.
**Logic**:
1.  Searches for a predefined list of labels (e.g., `security`, `vuln`, `cve`, `psirt`, `responsible-disclosure`).
2.  Deduplicates findings (ignores if same item found via multiple labels).
**Signals**: `security_label`

### `github_prs`
**Purpose**: Identifies security-related Pull Requests.
**Logic**:
1.  Similar to `github_issues`, but targets PRs.
2.  Useful for finding "silent fixes" or ongoing security work.
**Signals**: `github_pr`, `cve`

### `github_releases`
**Purpose**: Analyzes release notes for security disclosures.
**Logic**:
1.  Scans GitHub Releases (titles/bodies) for CVEs and security keywords.
2.  **Tag Scanning**: If releases are sparse, scans annotated git tags.
**Signals**: `cve`, `security_keyword`

### `contributors`
**Purpose**: Provides context on ownership, churn, and knowledge silos.
**Logic**:
1.  Parses `git log` to build contributor statistics per file.
2.  **High Churn**: Sensitive files with >50 commits.
3.  **Knowledge Silo (Bus Factor)**: Critical files modified by only one author.
4.  **Drive-by Pattern**: Sensitive files where most contributors have <2 commits.
5.  **Orphan Code**: Files where the primary author hasn't been active in >6 months.
6.  **Permission Anomaly**: Contributors touching sensitive files who typically work outside sensitive areas.
7.  **Recent Complex Churn**: Files with >10 commits and >500 lines changed in the last 30 days.
**Signals**: `high_churn_hotspot`, `knowledge_silo`, `drive_by_contributors`, `orphan_code`, `anomaly_contributor`, `recent_complex_churn`

### `tech_stack`
**Purpose**: Identifies the technology stack.
**Logic**:
1.  **Primary**: Runs `npx @specfy/stack-analyser` for deep analysis of the project structure.
2.  **Fallback**: Checks file heuristics (e.g., `package.json`, `requirements.txt`) if `npx` is unavailable.
**Signals**: `tech_stack_analysis`

---

## Extractor Modules
*Scanners that actively inspect code or artifacts.*

### `dependency_analysis`
**Purpose**: Detects known vulnerabilities in project dependencies.
**Logic**:
1.  **Primary**: Runs `osv-scanner` on lockfiles (`package-lock.json`, etc.) for precise version matching.
2.  **Fallback**: Manually parses manifest files (`package.json`) if scanner fails (Low Confidence).
3.  **Reachability**: Grep-searches for usage of vulnerable packages in source code.
**Signals**: `vulnerable_dependency`

### `sast_findings`
**Purpose**: Ingests results from external Static Analysis tools.
**Logic**:
1.  Recursively searches for `.sarif` files.
2.  Parses SARIF data, normalizes severity, and extracts code snippets.
**Signals**: `sast_finding`

### `semgrep_file_analysis`
**Purpose**: Runs lightweight static analysis using Semgrep.
**Logic**:
1.  Executes `semgrep scan --config=auto --json` on the codebase.
2.  Parses JSON output into findings.
**Signals**: `semgrep_finding`

### `semgrep_code_intel`
**Purpose**: Detects interesting application features and functional areas (Intelligence Focus).
**Logic**:
1.  Executes `semgrep` using local rules in `repo_intel/rules/semgrep/`.
2.  Identifies patterns for:
    *   **Authentication**: Login, registration, password verification.
    *   **Cryptography**: Hashing, encryption, signing.
    *   **Payment**: Stripe, PayPal, billing logic.
    *   **PII**: Emails, SSNs, phone numbers.
    *   **Admin**: Admin panels, privileged roles.
    *   **Messaging**: Email, SMS, Slack integrations.
    *   **Files**: File uploads, S3 usage.
    *   **Web**: API route definitions.
3.  Assigns High Research Value but Low Impact (Info severity) to prioritize understanding over risk.
**Signals**: `feature_detected`

### `unreleased_fix_detector`
**Purpose**: Detects "Half-Day" vulnerabilities (fixed in code but not yet released).
**Logic**:
1.  Identifies all commits associated with CVE findings.
2.  Checks if the fix commit is included in any git tag (`git tag --contains`).
3.  **Unreleased**: If no tags contain the commit -> **Critical Risk**.
**Signals**: Updates `cve` metadata.

---

## Enricher Modules
*Post-processing modules that add external intelligence.*

### `exploits`
**Purpose**: Adds real-world exploit context to CVE findings.
**Logic**:
1.  **CISA KEV**: Checks CISA Known Exploited Vulnerabilities catalog.
2.  **EPSS**: Fetches Exploit Prediction Scoring System probability.
3.  **PoC Check**: Checks for Proof-of-Concept code (Trickest/GitHub).
**Signals**: `exploit_intelligence`, updates `cve` metadata.

### `enrichment`
**Purpose**: Base logic for NVD/CVE enrichment.
**Logic**:
1.  Fetches CVSS scores and descriptions from NVD for any CVEs found by other modules.
**Signals**: Updates `cve` metadata.
