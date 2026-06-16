"""
Commits Module - Scans git commit history for security signals.

This module analyzes commit messages to find:
- CVE references
- Security-related keywords (vulnerability, exploit, patch, etc.)
- Silent fixes (security fixes without CVE mentions)
"""

"""
__Logic:__

- It scans the git commit history (default: last 1000 commits) for security signals.
- **CVE Detection:** Regex searches commit messages for CVE IDs (e.g., `CVE-2023-1234`).
- **Keyword Analysis:** Matches commit messages against a library of security patterns (e.g., "fix XSS", "vulnerability").
- **Metadata Extraction:** Captures commit hash, author, date, and changed files for each finding.
- **Enrichment:** Automatically triggers NVD enrichment for detected CVEs.
"""

import re
import os
import time
from datetime import datetime
from git import Repo
from langdetect import detect

from repo_intel.modules.base import SignalModule, register_module
from repo_intel.core.patterns import load_patterns, match_patterns
from repo_intel.core.utils import get_patterns_dir


@register_module
class GithubCommitsAnalyseModule(SignalModule):
    """Scans git commit history for security-relevant signals."""
    
    name = "github_commits_analyse"
    description = "Analyzes commit messages for CVEs, security keywords, and patterns"

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
    
    def collect(self, repo_url, repo_name, repo_path=None, **kwargs):
        """Scan commit history of the provided repo."""
        findings = []
        
        if not repo_path:
            print(f"    Skipping github_commits_analyse module (no repo_path provided)")
            return findings
        
        try:
            repo = Repo(repo_path)
            patterns = load_patterns(get_patterns_dir())
            
            # Use configured limit or default to 1000. <= 0 means all.
            limit = kwargs.get("commits_limit", 1000)
            if isinstance(limit, str) and limit.lower() == "all":
                max_commits = None
            else:
                max_commits = int(limit)
                if max_commits <= 0: max_commits = None
            
            print(f"    Scanning {'all' if max_commits is None else f'last {max_commits}'} commits...")
            
            count = 0
            for commit in repo.iter_commits(max_count=max_commits):
                count += 1
                if count % 100 == 0:
                    print(f"    Scanned {count} commits...", end='\r')
                    
                commit_findings = self._analyze_commit(commit, patterns)
                findings.extend(commit_findings)
            print(f"    Scanned {count} commits. Found {len(findings)} signals.")
            
        except Exception as e:
            print(f"    Error scanning commits: {e}")
            
        # Enrich CVEs
        print(f"    Enriching CVE findings...")
        self._enrich_cves(findings)
        
        return findings
    
    def _analyze_commit(self, commit, patterns):
        """Analyze a single commit for security signals."""
        findings = []
        message = commit.message
        
        # Skip language detection for performance (assume mostly English/code)
        lang = "en"
        
        # Get changed files
        try:
            changed_files = list(commit.stats.files.keys())
        except:
            changed_files = []
            
        authored_date = datetime.fromtimestamp(commit.authored_date).isoformat()
        committed_date = datetime.fromtimestamp(commit.committed_date).isoformat()
        
        # 1. Detect Reverts (High Signal)
        if message.lower().strip().startswith("revert"):
            # Check if it reverts a security fix
            if any(w in message.lower() for w in ["security", "vuln", "cve", "exploit", "patch"]):
                desc = f"Commit appears to revert a security fix: {message.strip()[:200]}"
                
                findings.append(self._make_finding(
                    signal_type="revert_security_fix",
                    title="Reverted Security Fix",
                    description=desc,
                    metadata={
                        "commit_hash": commit.hexsha,
                        "author": commit.author.name,
                        "date": authored_date,
                        "committed_date": committed_date,
                        "message": message.strip()[:500],
                        "files": changed_files[:20]
                    }
                ))

        # 2. Detect Partial Fix Language
        partial_terms = ["mitigate", "workaround", "temporary fix", "temp fix", "partial fix"]
        for term in partial_terms:
            if term in message.lower():
                desc = f"Commit message suggests a partial or temporary security fix: {message.strip()[:200]}"
                
                findings.append(self._make_finding(
                    signal_type="partial_security_fix",
                    title=f"Potential Partial Fix ({term})",
                    description=desc,
                    metadata={
                        "term": term,
                        "commit_hash": commit.hexsha,
                        "author": commit.author.name,
                        "date": authored_date,
                        "committed_date": committed_date,
                        "message": message.strip()[:500],
                        "files": changed_files[:20]
                    }
                ))

        # Match security patterns (including CVEs)
        pattern_matches = match_patterns(message, patterns, lang, exclude_categories=["todo"])
        for match in pattern_matches:
            match_val = match.get('value')
            category = match.get('category')
            
            if category == "cve":
                # CVE Finding
                desc = f"CVE reference found in commit: {message[:200]}"
                findings.append(self._make_finding(
                    signal_type="cve",
                    title=match_val.upper(),
                    description=desc,
                    metadata={
                        "cve_id": match_val.upper(),
                        "commit_hash": commit.hexsha,
                        "author": commit.author.name,
                        "date": authored_date,
                        "committed_date": committed_date,
                        "message": message.strip()[:500],
                        "files": changed_files[:20],
                        "stats": {
                            "insertions": commit.stats.total.get('insertions', 0),
                            "deletions": commit.stats.total.get('deletions', 0),
                            "files_changed": commit.stats.total.get('files', 0)
                        }
                    }
                ))
                continue

            # Standard Pattern Finding
            desc = f"Security keyword '{match_val}' in commit: {message[:200]}"
            
            overrides = {}
            precision = match.get("precision_bucket")
            if precision == "high_precision":
                overrides = {"confidence_score": 8, "research_value": 8}
            elif precision == "low_precision":
                overrides = {"confidence_score": 4, "research_value": 4}
            
            findings.append(self._make_finding(
                signal_type="security_keyword",
                title=f"Security Keyword: '{match_val}'"[:100],
                description=desc,
                metadata={
                    "keyword": match_val,
                    "category": category or "unknown",
                    "commit_hash": commit.hexsha,
                    "author": commit.author.name,
                    "date": authored_date,
                    "committed_date": committed_date,
                    "message": message.strip()[:500],
                    "files": changed_files[:20],
                    "language": lang
                },
                **overrides
            ))
        
        return findings
