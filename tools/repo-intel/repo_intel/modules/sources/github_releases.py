"""GitHub Releases Module - Scans GitHub release notes for security signals."""

"""
__Logic:__

- It connects to the GitHub API to scan Release notes and Tags.
- **Release Scanning:** Checks release titles and bodies for CVE IDs and security keywords.
- **Tag Scanning:** If releases are sparse, it scans git tag commit messages.
- **Signal Generation:** Flags releases that mention security fixes or vulnerabilities.
"""

import re
import os
import time
from github import Github, GithubException
from datetime import datetime

from repo_intel.modules.base import SignalModule, register_module
from repo_intel.core.patterns import load_patterns, match_patterns
from repo_intel.core.utils import get_patterns_dir

@register_module
class GithubReleasesAnalyseModule(SignalModule):
    """Scans GitHub release notes (and tags) for security-related signals."""
    
    name = "github_releases_analyse"
    description = "Analyzes GitHub release notes and tag messages for CVEs and security keywords"

    def get_scores(self):
        """
        Default scores.
        Note: These scores are overridden for security pattern matches:
        - High Precision: confidence=8, research=8
        - Low Precision: confidence=4, research=4
        """
        return {
            "confidence_score": 10,
            "research_value": 1,
            "impact_score": 1
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
            print(f"      [GithubReleasesAnalyse] Token verified as user: {user.login}")
        except Exception as e:
            print(f"      [GithubReleasesAnalyse] Token verification failed: {e}")
            print(f"      [GithubReleasesAnalyse] Module will run in anonymous/limited mode or fail.")
            self.github = None
            self.api_token = None

    def collect(self, repo_url, repo_name, **kwargs):
        """Collect security signals from GitHub releases and tags."""
        if not self.api_token:
            print("      Skipping github_releases_analyse (no github_token provided)")
            return []
        
        findings = []
        try:
            repo = self.github.get_repo(repo_name)
            patterns = load_patterns(get_patterns_dir())
            
            # Use configured limit or default to 50
            limit = kwargs.get("releases_limit", 50)
            if isinstance(limit, str) and limit.lower() == "all":
                limit_count = None
            else:
                limit_count = int(limit)
                if limit_count <= 0: limit_count = None
            
            print(f"      [GithubReleasesAnalyse] Fetching releases for {repo_name}...")
            releases = repo.get_releases()
            
            scanned_tags = set()
            count = 0
            
            # 1. Scan Releases
            for release in releases:
                if limit_count is not None and count >= limit_count:
                    break
                
                count += 1
                scanned_tags.add(release.tag_name)
                release_findings = self._analyze_release(release, patterns)
                findings.extend(release_findings)
                
                # Simple throttling
                if self.throttle > 0:
                    time.sleep(self.throttle)
                    
            print(f"      [GithubReleasesAnalyse] Scanned {count} releases.")
            
            # 2. Scan Tags (if limit not reached)
            # This covers repositories that use Tags instead of Releases (e.g. Lodash)
            if limit_count is None or count < limit_count:
                print(f"      [GithubReleasesAnalyse] Fetching tags for {repo_name}...")
                tags = repo.get_tags()
                tag_count = 0
                
                for tag in tags:
                    if limit_count is not None and count >= limit_count:
                        break
                    
                    if tag.name in scanned_tags:
                        continue
                        
                    count += 1
                    tag_count += 1
                    
                    # Scan tag commit message
                    try:
                        # tag.commit is a Commit object, tag.commit.commit is the GitCommit object with message
                        message = tag.commit.commit.message
                        tag_findings = self._analyze_tag(tag, message, patterns)
                        findings.extend(tag_findings)
                    except Exception:
                        pass # Skip tags where commit message can't be retrieved
                        
                    if self.throttle > 0:
                        time.sleep(self.throttle)
                        
                if tag_count > 0:
                    print(f"      [GithubReleasesAnalyse] Scanned {tag_count} additional tags.")
            
            print(f"      [GithubReleasesAnalyse] Total scanned: {count}. Found {len(findings)} signals.")
            
        except GithubException as e:
            if e.status == 404:
                print(f"      [GithubReleasesAnalyse] Repo not found or no access: {repo_name}")
            else:
                print(f"      [GithubReleasesAnalyse] Error scanning releases/tags: {e}")
        except Exception as e:
            print(f"      [GithubReleasesAnalyse] Unexpected error: {e}")
            
        # Enrich CVEs
        if findings:
            print(f"      [GithubReleasesAnalyse] Enriching findings...")
            self._enrich_cves(findings)

        return findings
    
    def _analyze_release(self, release, patterns):
        """Analyze a single release for security signals."""
        findings = []
        text_content = f"{release.title}\n\n{release.body}"
        published_at = release.published_at.isoformat() if release.published_at else "Unknown"
        
        # Match security patterns (including CVEs)
        pattern_matches = match_patterns(text_content, patterns, "en")
        for match in pattern_matches:
            match_val = match.get('value')
            category = match.get('category')
            
            if category == "cve":
                # CVE Finding
                desc = f"CVE reference found in release {release.tag_name}: {release.title}"
                findings.append(self._make_finding(
                    signal_type="cve",
                    title=match_val.upper(),
                    description=desc,
                    metadata={
                        "cve_id": match_val.upper(),
                        "release_tag": release.tag_name,
                        "release_title": release.title,
                        "published_at": published_at,
                        "author": release.author.login if release.author else None,
                        "url": release.html_url
                    }
                ))
                continue

            desc = f"Security keyword '{match_val}' in release {release.tag_name}"
            
            overrides = {}
            precision = match.get("precision_bucket")
            if precision == "high_precision":
                overrides = {"confidence_score": 8, "research_value": 8}
            elif precision == "low_precision":
                overrides = {"confidence_score": 4, "research_value": 4}
            
            findings.append(self._make_finding(
                signal_type="security_keyword",
                title=f"Release Keyword: {match_val}",
                description=desc,
                metadata={
                    "keyword": match_val,
                    "category": category or "unknown",
                    "release_tag": release.tag_name,
                    "release_title": release.title,
                    "published_at": published_at,
                    "url": release.html_url
                },
                **overrides
            ))
            
        return findings

    def _analyze_tag(self, tag, message, patterns):
        """Analyze a single tag commit message for security signals."""
        findings = []
        text_content = message or ""
        
        # Try to get date from tag commit
        try:
            date = tag.commit.commit.author.date.isoformat()
        except:
            date = "Unknown"
        
        # Match security patterns (including CVEs)
        pattern_matches = match_patterns(text_content, patterns, "en")
        for match in pattern_matches:
            match_val = match.get('value')
            category = match.get('category')
            
            if category == "cve":
                # CVE Finding
                desc = f"CVE reference found in tag {tag.name}: {message[:100]}..."
                findings.append(self._make_finding(
                    signal_type="cve",
                    title=match_val.upper(),
                    description=desc,
                    metadata={
                        "cve_id": match_val.upper(),
                        "release_tag": tag.name,
                        "release_title": f"Tag: {tag.name}",
                        "published_at": date,
                        "author": None,
                        "url": f"https://github.com/TODO" # We don't have easy URL here without repo context, but can construct it if needed
                    }
                ))
                continue

            desc = f"Security keyword '{match_val}' in tag {tag.name}"
            
            overrides = {}
            precision = match.get("precision_bucket")
            if precision == "high_precision":
                overrides = {"confidence_score": 8, "research_value": 8}
            elif precision == "low_precision":
                overrides = {"confidence_score": 4, "research_value": 4}
            
            findings.append(self._make_finding(
                signal_type="security_keyword",
                title=f"Tag Keyword: {match_val}",
                description=desc,
                metadata={
                    "keyword": match_val,
                    "category": category or "unknown",
                    "release_tag": tag.name,
                    "release_title": f"Tag: {tag.name}",
                    "published_at": date,
                    "url": None
                },
                **overrides
            ))
            
        return findings
