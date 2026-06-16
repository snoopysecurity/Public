"""Unreleased Fix Detector Module - Identifies unreleased security fixes."""

"""
__Logic:__

- It identifies all CVEs found in commit messages.
- It uses `git tag --contains <commit_hash>` to check if the commit is included in any release.
- __If Unreleased:__ It flags the finding as a __CRITICAL__ "Half-Day Risk" (`⚠️ Unreleased Fix`).
- __If Released:__ It downgrades the finding to __INFO__ and identifies the *first* release that included the fix (`✅ Fixed CVE`).
"""

import requests
from git import Repo, GitCommandError
from repo_intel.modules.base import SignalModule, register_module
from repo_intel.core.utils import parse_repo_name

@register_module
class UnreleasedFixDetectorModule(SignalModule):
    """
    Analyzes CVE findings from commits to determine if they have been released.
    
    Categorizes findings into:
    1. Unreleased (Half-Day Risk) -> Critical
    2. Released (Fixed) -> Info
    """
    
    name = "unreleased_fix_detector"
    description = "Checks if security fixes in commits have been included in a release"

    def get_scores(self):
        return {
            "confidence_score": 10,
            "research_value": 10,
            "impact_score": 9
        }
    
    def collect(self, repo_url, repo_name, **kwargs):
        # This module is an enrichment module only, it doesn't collect raw signals
        return []
    
    def _check_remote_release_status(self, repo_url, commit_hash, github_token):
        """
        Check if a commit is released using GitHub scraping (fallback for shallow clones).
        Returns: True if released (tags found), False if unreleased (no tags), None if unknown/error.
        """
        if not github_token:
            return None
            
        try:
            repo_name = parse_repo_name(repo_url)
            if not repo_name: return None
            
            # Use the branch_commits endpoint which lists tags for a commit in the UI
            url = f"https://github.com/{repo_name}/branch_commits/{commit_hash}"
            headers = {"Authorization": f"token {github_token}"}
            
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                # Look for the tag list indicator
                if 'ul class="branches-tag-list' in resp.text:
                    return True # Tags found -> Released
                else:
                    return False # No tags found -> Unreleased
            
        except Exception as e:
            print(f"      [UnreleasedFixDetector] Remote check failed: {e}")
            
        return None

    def can_enrich(self, findings):
        # We can enrich if there are any CVE or high-precision security keyword findings from commits
        return any(
            (f.get("signal_type") == "cve" or (
                f.get("signal_type") == "security_keyword" and 
                f.get("confidence") == "high"
            )) and 
            f.get("source_module") == "github_commits_analyse"
            for f in findings
        )
        
    def enrich(self, findings, repo_path=None, **kwargs):
        if not repo_path:
            return findings
        
        github_token = kwargs.get("github_token")
        repo_url = kwargs.get("repo_url")
            
        try:
            repo = Repo(repo_path)
            # Check if shallow
            is_shallow = repo.git.rev_parse("--is-shallow-repository") == "true"
        except Exception as e:
            print(f"      [UnreleasedFixDetector] Error opening repo: {e}")
            return findings

        print(f"      [UnreleasedFixDetector] Checking release status of CVE commits...")
        if is_shallow:
            print("      [UnreleasedFixDetector] Repo is shallow. Will attempt remote fallback for tag checks.")
        
        updates_count = 0
        
        for finding in findings:
            # Filter for CVEs or High Confidence Keywords found in commits
            signal_type = finding.get("signal_type")
            is_cve = signal_type == "cve"
            is_keyword = signal_type == "security_keyword" and finding.get("confidence") == "high"

            if ((is_cve or is_keyword) and 
                finding.get("source_module") == "github_commits_analyse"):
                
                # Skip blacklisted findings (don't upgrade them to critical)
                if finding.get("severity") == "info" or "[BLACKLIST MATCH]" in finding.get("title", ""):
                    continue

                metadata = finding.get("metadata", {})
                commit_hash = metadata.get("commit_hash")
                
                if not commit_hash:
                    continue
                
                tags = []
                is_released = False
                
                try:
                    # 1. Local Check
                    tags_output = repo.git.tag(contains=commit_hash, sort="v:refname")
                    tags = [t.strip() for t in tags_output.split('\n') if t.strip()]
                    if tags:
                        is_released = True
                    
                    # 2. Remote Fallback (if local says unreleased but might be shallow)
                    if not is_released and (is_shallow or not tags):
                         remote_status = self._check_remote_release_status(repo_url, commit_hash, github_token)
                         if remote_status is True:
                             is_released = True
                             tags = ["Remote-Tag-Confirmed"] # Placeholder since we didn't fetch names
                         elif remote_status is False:
                             # Confirmed unreleased by remote
                             is_released = False
                         # If None, stick with local result (which is Unreleased) or skip?
                         # Sticking with local result logic (Unreleased) maintains existing behavior but risks FP.
                         # But if remote check failed (no token), we can't do better.
                    
                    ref_name = finding.get('metadata', {}).get('cve_id', finding.get('title', 'Unknown'))
                    
                    if not is_released:
                        # Case A: Unreleased -> High Risk
                        finding["title"] = f"⚠️ Unreleased Fix: {ref_name}"
                        finding["description"] = (
                            f"UNRELEASED FIX: This security fix (commit {commit_hash[:7]}) "
                            f"has NOT been included in any release yet."
                        )
                        
                        metadata["is_unreleased_fix"] = True
                        metadata["status"] = "unreleased"
                        
                        updates_count += 1
                        # Change source module to ensure it appears in its own tab in the dashboard
                        finding["source_module"] = self.name
                        
                        # Apply static scoring from this module
                        scores = self.get_scores()
                        finding["severity"] = "critical"
                        finding["confidence"] = "high"
                        finding["confidence_score"] = scores["confidence_score"] / 10.0
                        finding["research_value"] = scores["research_value"] / 10.0
                        finding["severity_score"] = scores["impact_score"] / 10.0
                    else:
                        # Case B: Released -> Fixed
                        # Leave as original module finding (Medium)
                        earliest_tag = tags[0]
                        metadata["is_unreleased_fix"] = False
                        metadata["status"] = "released"
                        metadata["fixed_in_release"] = earliest_tag
                        metadata["all_containing_releases"] = tags[:5] 
                        
                        finding["title"] = f"✅ Fixed: {ref_name}"
                        finding["description"] = (
                            f"Fixed in release {earliest_tag}. "
                            f"(Commit {commit_hash[:7]} is included in {len(tags)} releases)"
                        )
                    
                except GitCommandError as e:
                    pass
                except Exception as e:
                    print(f"      [UnreleasedFixDetector] Error checking commit {commit_hash}: {e}")
                    
        print(f"      [UnreleasedFixDetector] Updated {updates_count} CVE findings with release status.")
        return findings
