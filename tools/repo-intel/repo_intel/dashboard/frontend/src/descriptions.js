export const descriptions = {
    // Overview
    dashboard: "This dashboard provides a high-level summary of the security posture of the repository. It includes key metrics such as total findings, triage status, research value distribution, and top hotspots requiring attention.",
    
    // Sources
    github_prs_analyse: "Analyzes GitHub Pull Requests to identify security risks, sensitive data exposure, and high-risk code changes using pattern matching and heuristics.",
    github_issues_analyse: "Scans GitHub Issues for discussions related to security vulnerabilities, bugs, and sensitive information, detecting potential leaks or disclosed weaknesses.",
    github_commits_analyse: "Examines commit history and messages to detect high-risk changes, secret leaks, and security-relevant modifications that might not be visible in current code.",
    contributors: "Analyzes contributor activity to identify potential insider threats, unusual contribution patterns, or lack of oversight in critical areas.",
    github_labels: "Uses GitHub labels to categorize and prioritize findings based on existing repository metadata, helping to identify pre-classified security issues.",
    github_releases_analyse: "Monitors GitHub Releases for security patches, unreleased fixes, and changelog analysis to detect disclosed but unpatched vulnerabilities.",
    tech_stack_analysis: "Identifies technologies, frameworks, and libraries used in the repository to contextualize security risks and attack surface.",
    
    // Extractors
    dependency_analysis: "Scans dependencies for known vulnerabilities and outdated packages using available manifest files and advisory databases.",
    sast_findings: "Aggregates findings from Static Application Security Testing (SAST) tools to provide a unified view of code vulnerabilities.",
    semgrep_file_analysis: "Performs deep file analysis using Semgrep to detect complex code patterns and security flaws directly in the source code.",
    unreleased_fix_detector: "Detects security fixes that have been committed but not yet included in a formal release, indicating potential 1-day vulnerabilities.",
    
    // Enrichers
    exploits: "Correlates findings with known exploits (e.g., CISA KEV, Trickest) to prioritize vulnerabilities with active exploitation potential.",
    
    // Fallback/Others if needed
    semgrep: "Performs deep file analysis using Semgrep to detect complex code patterns and security flaws.",
    unknown: "No description available for this module."
};
