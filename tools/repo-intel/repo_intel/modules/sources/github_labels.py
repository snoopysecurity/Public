"""GitHub Labels Module - Collects signals from GitHub issues/PRs based on labels."""

import time
from github import Github, GithubException
from repo_intel.modules.base import SignalModule, register_module

SECURITY_LABELS = [
    "security",
    "sec",
    "sec-bug",
    "security-bug",
    "security-fix",
    "security-issue",
    "security-review",
    "security-audit",
    "vulnerability",
    "vuln",
    "cve",
    "advisory",
    "psirt",
    "security-advisory",
    "responsible-disclosure"
]

@register_module
class GithubLabelsAnalyseModule(SignalModule):
    """Collects security signals from GitHub labels."""
    
    name = "github_labels_analyse"
    description = "Scans GitHub issues and PRs for specific security labels"

    def get_scores(self):
        return {
            "confidence_score": 8,
            "research_value": 5,
            "impact_score": 4
        }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_token = kwargs.get("github_token")
        self.github = Github(self.api_token) if self.api_token else None
        self.throttle = kwargs.get("throttle", 0)
        
        if self.github:
            self._verify_token()
            
    def _verify_token(self):
        """Verify the GitHub token is valid."""
        try:
            user = self.github.get_user()
            print(f"      [GithubLabelsAnalyse] Token verified as user: {user.login}")
        except Exception as e:
            print(f"      [GithubLabelsAnalyse] Token verification failed: {e}")
            print(f"      [GithubLabelsAnalyse] Module will run in anonymous/limited mode or fail.")
            self.github = None
            self.api_token = None

    def collect(self, repo_url, repo_name, **kwargs):
        """Collect security signals from GitHub labels."""
        if not self.api_token:
            print("      Skipping (no github_token provided)")
            return []
        
        findings = []
        seen_ids = set()
        
        print(f"      [GithubLabelsAnalyse] Searching {len(SECURITY_LABELS)} security labels...")
        
        for label in SECURITY_LABELS:
            new_findings = self._search_label(repo_name, label)
            
            # Deduplicate
            for finding in new_findings:
                unique_id = finding['metadata'].get('url')
                if unique_id and unique_id not in seen_ids:
                    seen_ids.add(unique_id)
                    findings.append(finding)
            
            # Default sleep to avoid secondary rate limits
            sleep_time = max(2.0, self.throttle)
            time.sleep(sleep_time)
        
        # Enrich CVEs if any found (handled by base class if implemented, or we can reuse logic)
        # For now, we return the findings. 
        # Note: If we want to enrich CVEs similar to other modules, we can call self._enrich_cves(findings)
        # checking if any title/body has CVEs. The base class has _enrich_cves but we need to ensure
        # the findings have 'cve' signal_type if we want that specific enrichment path, 
        # or we can rely on generic enrichment.
        # Actually, let's just return findings for now as the main goal is label detection.

        return findings
    
    def _search_label(self, repo_name, label):
        """Search for issues/PRs with a specific label."""
        findings = []
        try:
            query = f"repo:{repo_name} label:\"{label}\""
            issues = self.github.search_issues(query)
            
            count = 0
            for issue in issues:
                if count >= 10:  # Limit per label to avoid spam
                    break
                count += 1
                
                opened_at = issue.created_at.isoformat() if issue.created_at else "Unknown"
                status = issue.state
                
                # Check if it's a PR or Issue
                is_pr = issue.pull_request is not None
                item_type = "PR" if is_pr else "Issue"

                desc = f"{item_type} found with label '{label}': {issue.title}"
                
                findings.append(self._make_finding(
                    signal_type="security_label",
                    title=f"Security Label '{label}': {issue.title}",
                    description=desc,
                    metadata={
                        "label": label,
                        "labels": [l.name for l in issue.labels],
                        "url": issue.html_url,
                        "state": status,
                        "number": issue.number,
                        "created_at": issue.created_at.isoformat() if issue.created_at else None,
                        "author": issue.user.login if issue.user else None,
                        "type": item_type
                    }
                ))
        except GithubException as e:
            if e.status == 403 or e.status == 429:
                print(f"      [GithubLabelsAnalyse] Rate limit exceeded (403/429). Pausing for 60s...")
                time.sleep(60)
            elif e.status == 404:
                # Label might not exist in repo, which is fine
                pass
            else:
                print(f"      [GithubLabelsAnalyse] Error searching label '{label}': {e}")
        except Exception as e:
            print(f"      [GithubLabelsAnalyse] Unexpected error: {e}")
        
        return findings
