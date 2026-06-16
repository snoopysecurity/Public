"""GitHub PRs Module - Collects signals from GitHub pull requests."""

"""
__Logic:__

- It connects to the GitHub API to search repository Pull Requests.
- **Keyword Search:** Searches PRs for security keywords (e.g., "security fix", "vulnerability").
- **CVE Extraction:** Identifies CVE IDs mentioned in PR titles or bodies.
- **Signal Generation:** Creates findings for security-relevant PRs.
- **Enrichment:** Can also enrich existing findings by finding related PRs.
"""

import os
import time
import re
from github import Github, GithubException
from repo_intel.core.patterns import load_patterns, match_patterns
from repo_intel.core.utils import get_patterns_dir, get_security_keywords, parse_repo_name, get_keyword_precision_map
from repo_intel.modules.base import SignalModule, register_module


@register_module
class GithubPrsAnalyseModule(SignalModule):
    """Collects security signals from GitHub pull requests."""
    
    name = "github_prs_analyse"
    description = "Scans GitHub PRs for security-related discussions"

    def get_scores(self):
        """
        Default scores.
        Note: These scores are overridden for security pattern matches:
        - High Precision: confidence=8, research=8
        - Low Precision: confidence=4, research=4
        """
        return {
            "confidence_score": 5,
            "research_value": 4,
            "impact_score": 3
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
            print(f"      [GithubPrsAnalyse] Token verified as user: {user.login}")
        except Exception as e:
            print(f"      [GithubPrsAnalyse] Token verification failed: {e}")
            print(f"      [GithubPrsAnalyse] Module will run in anonymous/limited mode or fail.")
            self.github = None
            self.api_token = None

    def collect(self, repo_url, repo_name, **kwargs):
        """Collect security signals from GitHub PRs."""
        if not self.api_token:
            print("      Skipping (no github_token provided)")
            return []
        
        findings = []
        patterns = load_patterns(get_patterns_dir())
        
        # Search for security-related PRs
        security_keywords = get_security_keywords(patterns)
        # Get precision map
        precision_map = get_keyword_precision_map(patterns)
        
        print(f"      [GithubPrsAnalyse] Searching {len(security_keywords)} security keywords...")
        
        prs_limit = kwargs.get("prs_limit", 1000)
        
        seen_ids = set()
        for keyword in security_keywords[:20]:  # Limit to avoid rate limits
            findings.extend(self._search_prs(repo_name, keyword, patterns, seen_ids, precision_map.get(keyword), limit=prs_limit))
            
            # Default sleep to avoid secondary rate limits
            sleep_time = max(2.0, self.throttle)
            time.sleep(sleep_time)
        
        # Enrich CVEs if any found
        if findings:
            print(f"      [GithubPrsAnalyse] Enriching findings...")
            self._enrich_cves(findings)

        return findings
    
    def _search_prs(self, repo_name, keyword, patterns, seen_ids=None, precision=None, limit=1000):
        """Search for security-related pull requests."""
        findings = []
        if seen_ids is None:
            seen_ids = set()
            
        try:
            query = f"{keyword} repo:{repo_name} is:pr"
            prs = self.github.search_issues(query)
            
            count = 0
            for pr in prs:
                if limit is not None and count >= limit:
                    break
                
                if pr.number in seen_ids:
                    continue
                seen_ids.add(pr.number)
                
                count += 1
                
                # Convert Issue to PullRequest to get detailed attributes
                status = pr.state
                merged_at = None
                
                if pr.pull_request:
                    try:
                        pr_details = pr.as_pull_request()
                        status = pr_details.state
                        if status == "closed" and pr_details.merged:
                            status = "merged"
                        merged_at = pr_details.merged_at.isoformat() if pr_details.merged_at else None
                    except Exception:
                        pass
                
                opened_at = pr.created_at.isoformat() if pr.created_at else "Unknown"
                
                # Fetch comments (limit to first 10 to conserve API calls)
                comments_text = ""
                try:
                    comments = pr.get_issue_comments()
                    # Iterate slightly to fetch first page
                    count_comments = 0
                    fetched_comments = []
                    for c in comments:
                        if count_comments >= 10: break
                        fetched_comments.append(c.body)
                        count_comments += 1
                    comments_text = "\n".join(fetched_comments)
                except Exception:
                    pass

                # Analyze content using patterns (including CVE regex)
                # Include labels and comments in analysis
                labels_text = ", ".join([l.name for l in pr.labels])
                text_content = f"{pr.title}\n{pr.body or ''}\nLabels: {labels_text}\nComments: {comments_text}"
                pattern_matches = match_patterns(text_content, patterns, "en")
                
                for match in pattern_matches:
                    match_val = match.get("value")
                    category = match.get("category")
                    
                    # Determine context
                    context_str = "PR"
                    if match_val in pr.title:
                        context_str = "PR Title"
                    elif pr.body and match_val in pr.body:
                        context_str = "PR Body"
                    elif match_val in labels_text:
                        context_str = "PR Label"
                    elif match_val in comments_text:
                        context_str = "PR Comment"

                    if category == "cve":
                        # CVE Finding
                        desc = f"CVE reference found in {context_str} #{pr.number}: {pr.title}"
                        findings.append(self._make_finding(
                            signal_type="cve",
                            title=match_val.upper(),
                            description=desc,
                            metadata={
                                "cve_id": match_val.upper(),
                                "context": context_str,
                                "pr_number": pr.number,
                                "pr_title": pr.title,
                                "url": pr.html_url,
                                "labels": [l.name for l in pr.labels],
                                "author": pr.user.login if pr.user else None,
                                "state": status,
                                "created_at": opened_at,
                                "merged_at": merged_at
                            }
                        ))
                    else:
                        # Security Keyword Finding
                        # We might find the searched keyword again here, which is fine.
                        desc = f"Security keyword '{match_val}' found in {context_str}: {pr.title}"
                        
                        overrides = {}
                        match_precision = match.get("precision_bucket")
                        if match_precision == "high_precision":
                            overrides = {"confidence_score": 8, "research_value": 8}
                        elif match_precision == "low_precision":
                            overrides = {"confidence_score": 4, "research_value": 4}
                            
                        findings.append(self._make_finding(
                            signal_type="security_keyword",
                            title=f"{context_str} mentioning {match_val}",
                            description=desc,
                            metadata={
                                "keyword": match_val,
                                "category": category,
                                "context": context_str,
                                "url": pr.html_url,
                                "state": status,
                                "number": pr.number,
                                "created_at": opened_at,
                                "merged_at": merged_at,
                                "labels": [l.name for l in pr.labels],
                                "author": pr.user.login if pr.user else None,
                                "body": pr.body
                            },
                            **overrides
                        ))

                desc = f"PR mentioning '{keyword}': {pr.title}"
                
                overrides = {}
                if precision == "high_precision":
                    overrides = {"confidence_score": 8, "research_value": 8}
                elif precision == "low_precision":
                    overrides = {"confidence_score": 4, "research_value": 4}
                
                findings.append(self._make_finding(
                    signal_type="github_pr",
                    title=pr.title,
                    description=desc,
                    metadata={
                        "keyword": keyword,
                        "url": pr.html_url,
                        "state": status,
                        "number": pr.number,
                        "created_at": pr.created_at.isoformat() if pr.created_at else None,
                        "merged_at": merged_at,
                        "labels": [l.name for l in pr.labels],
                        "author": pr.user.login if pr.user else None,
                        "body": pr.body
                    },
                    **overrides
                ))
        except GithubException as e:
            if e.status == 403 or e.status == 429:
                print(f"      [GithubPrsAnalyse] Rate limit exceeded (403/429). Pausing for 60s...")
                time.sleep(60)
            else:
                print(f"      [GithubPrsAnalyse] Error searching PRs for '{keyword}': {e}")
        except Exception as e:
            print(f"      [GithubPrsAnalyse] Unexpected error: {e}")
        
        return findings
    
    def can_enrich(self, findings):
        """Check if there are findings to enrich with GitHub data."""
        return any(
            f.get("signal_type") in ["security_keyword", "pattern"] or
            f.get("type") == "pattern"
            for f in findings
        )
        
    def enrich(self, findings, **kwargs):
        """Enriches findings with GitHub PRs."""
        repo_url = kwargs.get("repo_url")
        if not repo_url:
            print("Warning: repo_url not provided for GitHub enrichment")
            return findings
        repo_name = parse_repo_name(repo_url)
        
        unique_keywords = set()
        for finding in findings:
            if finding.get("type") == "pattern":
                unique_keywords.add(finding["value"])
        
        if not unique_keywords:
            return findings
        
        keyword_cache = {}
        print(f"      [GithubPrsAnalyse] Enriching {len(unique_keywords)} unique keywords...")
        
        for keyword in unique_keywords:
            keyword_cache[keyword] = []
            try:
                query = f"{keyword} repo:{repo_name} is:pr"
                prs = self.github.search_issues(query)
                count = 0
                for pr in prs:
                    if count >= 5: break
                    count += 1
                    
                    keyword_cache[keyword].append({
                        "url": pr.html_url,
                        "title": pr.title,
                        "state": pr.state,
                    })
                time.sleep(max(2.0, self.throttle))
            except Exception as e:
                print(f"Error searching PRs for '{keyword}': {e}")
        
        for finding in findings:
            if finding.get("type") == "pattern":
                keyword = finding["value"]
                if keyword in keyword_cache and keyword_cache[keyword]:
                    finding.setdefault("enrichment", {})["github_pull_requests"] = keyword_cache[keyword]
        
        return findings
