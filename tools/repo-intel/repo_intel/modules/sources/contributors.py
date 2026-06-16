"""Contributor Analysis Module."""
"""
__Logic:__

- __Git Log Analysis__: Uses `git log` via subprocess for efficient data collection (authors, dates, commit counts per file).
- __High Contributor Density__: Identifies sensitive files (e.g., matching `auth`, `security`) with >10 unique contributors.
- __Drive-by Contributor Pattern__: Detects files where a high percentage (>50%) of contributors have made ≤2 commits.
- __Knowledge Silos (Bus Factor)__: Flags sensitive files with only a single historical contributor.
- __Orphan Code__: Identifies files where the primary author (most commits) hasn't been active in the repository for over 6 months.
- __Permission & Privilege Anomalies__: Flags contributors who touch sensitive files but have very little history in sensitive areas compared to their total contributions.
- __High Churn Hotspots__: Identifies sensitive files with high commit activity (>50 commits).
- __recent_complex_churn__: Reports if File has __>10 commits__ AND __>500 lines changed__ in the last 30 days.
"""
import time
import re
import os
import subprocess
from collections import defaultdict
from git import Repo
from repo_intel.modules.base import SignalModule, register_module

@register_module
class ContributorModule(SignalModule):
    """Analyzes git history for contributor patterns, churn, and security risks."""
    
    name = "contributors"
    description = "Identifies ownership risks, knowledge silos, and anomalies in contribution patterns as supporting context."

    def get_scores(self):
        return {
            "confidence_score": 2,
            "research_value": 1,
            "impact_score": 1
        }
    
    # Sensitive file patterns (heuristic)
    SENSITIVE_PATTERN = re.compile(
        r"(auth|security|crypto|secret|token|key|pwd|password|login|policy|permission|rbac|iam|access|middleware|session|audit|admin|user|account)", 
        re.IGNORECASE
    )

    def collect(self, repo_url, repo_name, repo_path=None, **kwargs):
        findings = []
        if not repo_path:
            return findings
            
        try:
            repo = Repo(repo_path)
            
            # --- Data Structures ---
            # file_path -> { authors: {email: count}, commits: int, last_modified: int, recent_commits: int, recent_complexity: int, recent_authors_set: set }
            file_stats = defaultdict(lambda: {
                "authors": defaultdict(int),
                "commits": 0,
                "last_modified": 0,
                "recent_commits": 0,
                "recent_complexity": 0,
                "recent_authors_set": set()
            })
            
            # Global author stats
            author_last_seen = {} # email -> timestamp
            author_total_commits = defaultdict(int) # email -> count
            author_sensitive_commits = defaultdict(int) # email -> count
            
            # --- Parse Git Log ---
            # Format: LOG_ENTRY_START|email|timestamp
            # Followed by list of files with stats (numstat)
            # Uses git log for performance on large repos
            # Stream output using subprocess to avoid Memory Error on large repos
            try:
                cmd = ["git", "-C", repo_path, "log", "--no-merges", "--numstat", "--format=LOG_ENTRY_START|%ae|%ct"]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors="replace", bufsize=1)
            except Exception as e:
                print(f"Error running git log: {e}")
                return []

            current_author = None
            current_ts = 0
            
            now = time.time()
            thirty_days_ago = now - (30 * 24 * 60 * 60)
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith("LOG_ENTRY_START|"):
                    parts = line.split("|")
                    if len(parts) >= 3:
                        current_author = parts[1].strip()
                        try:
                            current_ts = int(parts[2])
                        except ValueError:
                            current_ts = 0
                        
                        # Update global last seen
                        if current_author not in author_last_seen:
                            author_last_seen[current_author] = current_ts
                        else:
                            author_last_seen[current_author] = max(author_last_seen[current_author], current_ts)
                            
                        author_total_commits[current_author] += 1
                else:
                    # File stat line: added deleted path
                    # Using split() handles tabs and spaces, but we expect tabs for separation of numbers
                    # git log --numstat separates with tabs
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        added_str = parts[0].strip()
                        deleted_str = parts[1].strip()
                        fpath = parts[2].strip()
                        
                        # Handle binary files or errors
                        added = 0
                        deleted = 0
                        if added_str != '-':
                            try:
                                added = int(added_str)
                            except ValueError:
                                pass
                        if deleted_str != '-':
                            try:
                                deleted = int(deleted_str)
                            except ValueError:
                                pass
                        
                        complexity = added + deleted

                        # Update file stats
                        stats = file_stats[fpath]
                        stats["authors"][current_author] += 1
                        stats["commits"] += 1
                        stats["last_modified"] = max(stats["last_modified"], current_ts)
                        
                        # Recent stats
                        if current_ts > thirty_days_ago:
                            stats["recent_commits"] += 1
                            stats["recent_complexity"] += complexity
                            stats["recent_authors_set"].add(current_author)
                        
                        # Update global sensitive stats
                        if self.SENSITIVE_PATTERN.search(fpath):
                            author_sensitive_commits[current_author] += 1
            
            process.stdout.close()
            process.wait()

            # --- Analysis ---
            six_months = 180 * 24 * 60 * 60
            
            for fpath, stats in file_stats.items():
                # Skip if file no longer exists (optional, but reduces noise from deleted files)
                full_path = os.path.join(repo_path, fpath)
                if not os.path.exists(full_path):
                    continue

                is_sensitive = bool(self.SENSITIVE_PATTERN.search(fpath))
                unique_authors = len(stats["authors"])
                total_commits = stats["commits"]
                
                # 1. High Contributor Density
                if is_sensitive and unique_authors > 10:
                    findings.append(self._make_finding(
                        signal_type="high_contributor_density",
                        title=f"High Contributor Density: {fpath}",
                        description=f"Sensitive file modified by {unique_authors} different authors (>10). High risk of inconsistent security assumptions.",
                        metadata={
                            "file": fpath,
                            "contributor_count": unique_authors,
                            "commit_count": total_commits
                        }
                    ))
                
                # 2. Drive-by Contributor Pattern
                drive_by_authors = sum(1 for count in stats["authors"].values() if count <= 2)
                drive_by_ratio = drive_by_authors / unique_authors if unique_authors > 0 else 0
                
                if unique_authors >= 5 and drive_by_ratio > 0.5:
                    findings.append(self._make_finding(
                        signal_type="drive_by_contributors",
                        title=f"Drive-by Contributor Risk: {fpath}",
                        description=f"{drive_by_authors} out of {unique_authors} contributors ({int(drive_by_ratio*100)}%) made fewer than 3 commits to this file.",
                        metadata={
                            "file": fpath,
                            "drive_by_count": drive_by_authors,
                            "total_authors": unique_authors
                        }
                    ))

                # 3. Knowledge Silos (Bus Factor)
                if is_sensitive and unique_authors == 1:
                    findings.append(self._make_finding(
                        signal_type="knowledge_silo",
                        title=f"Knowledge Silo: {fpath}",
                        description="Critical security file has only one historical contributor.",
                        metadata={
                            "file": fpath,
                            "author": list(stats["authors"].keys())[0]
                        }
                    ))

                # 4. Orphan Code
                if stats["authors"]:
                    primary_author = max(stats["authors"], key=stats["authors"].get)
                    last_seen = author_last_seen.get(primary_author, 0)
                    
                    if (now - last_seen) > six_months:
                        findings.append(self._make_finding(
                            signal_type="orphan_code",
                            title=f"Orphaned Code: {fpath}",
                            description=f"Primary author ({primary_author}) has not been active in the repo for >6 months.",
                            metadata={
                                "file": fpath,
                                "primary_author": primary_author,
                                "last_active_date": time.ctime(last_seen)
                            }
                        ))

                # 5. Permission/Privilege Anomaly
                if is_sensitive:
                    for author in stats["authors"]:
                        if author_total_commits[author] > 20 and author_sensitive_commits[author] < 5:
                            findings.append(self._make_finding(
                                signal_type="anomaly_contributor",
                                title=f"Unusual Contributor: {fpath}",
                                description=f"Contributor {author} typically works outside sensitive areas.",
                                metadata={
                                    "file": fpath,
                                    "author": author,
                                    "total_commits": author_total_commits[author],
                                    "sensitive_commits": author_sensitive_commits[author]
                                }
                            ))
                            break 

                # 6. High Churn Hotspot (Total History)
                if is_sensitive and total_commits > 50:
                     findings.append(self._make_finding(
                        signal_type="high_churn_hotspot",
                        title=f"High Churn Hotspot: {fpath}",
                        description=f"Sensitive file with high activity ({total_commits} commits).",
                        metadata={
                            "file": fpath,
                            "commit_count": total_commits
                        }
                    ))
                
                # 7. Recent Complex Churn (Last 30 Days)
                # Logic: > 10 commits AND > 500 lines changed
                if stats["recent_commits"] > 10 and stats["recent_complexity"] > 500:
                    findings.append(self._make_finding(
                        signal_type="recent_complex_churn",
                        title=f"Recent Complex Churn: {fpath}",
                        description=f"File has high churn ({stats['recent_commits']} commits) and high complexity ({stats['recent_complexity']} lines changed) in the last 30 days.",
                        metadata={
                            "file": fpath,
                            "recent_commits": stats["recent_commits"],
                            "recent_complexity": stats["recent_complexity"]
                        }
                    ))

                # 8. Temporal Churn (High Recent Contributors)
                recent_unique_authors = len(stats["recent_authors_set"])
                if recent_unique_authors >= 5: # Threshold: 5+ distinct authors in 30 days
                    findings.append(self._make_finding(
                        signal_type="temporal_churn",
                        title=f"High Recent Contributor Flux: {fpath}",
                        description=f"File modified by {recent_unique_authors} distinct authors in the last 30 days. High risk of context loss.",
                        metadata={
                            "file": fpath,
                            "recent_author_count": recent_unique_authors,
                            "total_commits_recent": stats["recent_commits"]
                        }
                    ))

        except Exception as e:
            print(f"    Error in contributor analysis: {e}")
            
        return findings
