"""
repo-intel Context Engine

This is the core orchestration layer that answers:
"If I were going to spend a week auditing this repo, where should I start — and why?"

The engine:
1. Runs signal modules (commits, github issues, NVD, etc.)
2. Normalizes findings into a unified format
3. Scores and prioritizes areas of interest
4. Produces actionable audit starting points
"""

import os
import json
import shutil
import subprocess
import threading
import time
from datetime import datetime
from collections import defaultdict
from git import Repo
from repo_intel.core.utils import calculate_finding_id


class Finding:
    """Normalized finding from any signal source."""
    
    def __init__(self, signal_type, title, description, source_module, 
                 severity="medium", confidence="medium", metadata=None,
                 research_value=0.0, confidence_score=0.0, severity_score=0.0):
        self.signal_type = signal_type  # cve, security_keyword, issue, pr, etc.
        self.title = title
        self.description = description
        self.source_module = source_module
        self.severity = severity  # critical, high, medium, low, info
        self.confidence = confidence  # high, medium, low
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
        
        # Scoring Fields
        self.research_value = research_value
        self.confidence_score = confidence_score
        self.severity_score = severity_score
        
        # Legacy/Calculated
        self.priority_score = 0
        self.impact_score = severity_score
        
        self.confidence_reason = None
        self.impact_reason = None
        self.priority_reason = None
    
    def to_dict(self):
        return {
            "signal_type": self.signal_type,
            "title": self.title,
            "description": self.description,
            "source_module": self.source_module,
            "severity": self.severity,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            # Scoring Fields
            "research_value": self.research_value,
            "confidence_score": self.confidence_score,
            "severity_score": self.severity_score,
            "priority_score": self.priority_score,
            # Legacy/Compat
            "impact_score": self.impact_score,
            "confidence_reason": self.confidence_reason,
            "impact_reason": self.impact_reason,
            "priority_reason": self.priority_reason
        }


class ScanProgress:
    """Progress tracking for long-running scans."""
    
    def __init__(self, total_modules):
        self.total_modules = total_modules
        self.completed_modules = 0
        self.current_module = None
        self.current_step = ""
        self.findings_count = 0
        self.start_time = time.time()
        self.status = "running"  # running, completed, error
        self.error_message = None
        self.callbacks = []  # Progress update callbacks
        
    def update(self, module=None, step="", findings_added=0):
        if module:
            if self.current_module != module:
                self.completed_modules += 1
                self.current_module = module
        self.current_step = step
        self.findings_count += findings_added
        self._notify_callbacks()
        
    def complete(self, status="completed", error_message=None):
        self.status = status
        if error_message:
            self.error_message = error_message
        self._notify_callbacks()
        
    def add_callback(self, callback):
        """Add a callback function to receive progress updates."""
        self.callbacks.append(callback)
        
    def _notify_callbacks(self):
        progress_data = self.to_dict()
        for callback in self.callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                print(f"[!] Progress callback error: {e}")
                
    def to_dict(self):
        elapsed = time.time() - self.start_time
        return {
            "total_modules": self.total_modules,
            "completed_modules": self.completed_modules,
            "current_module": self.current_module,
            "current_step": self.current_step,
            "findings_count": self.findings_count,
            "progress_percent": (self.completed_modules / self.total_modules * 100) if self.total_modules > 0 else 0,
            "elapsed_time": elapsed,
            "status": self.status,
            "error_message": self.error_message
        }


class AuditContext:
    """Aggregated context for audit prioritization."""
    
    def __init__(self, repo_identifier):
        self.repo = repo_identifier
        self.findings = []
        self.hotspots = []  # Prioritized areas to investigate
        self.summary = {}
        self.modules_run = []
        self.scan_date = datetime.now().isoformat()
    
    def add_finding(self, finding):
        self.findings.append(finding)
    
    def add_findings(self, findings):
        self.findings.extend(findings)
    
    def to_dict(self):
        return {
            "repo": self.repo,
            "scan_date": self.scan_date,
            "modules_run": self.modules_run,
            "summary": self.summary,
            "hotspots": self.hotspots,
            "findings": [f.to_dict() if hasattr(f, 'to_dict') else f for f in self.findings]
        }


class ContextEngine:
    """
    The core engine that orchestrates signal modules and builds audit context.
    """
    
    def __init__(self, repo_url, output_dir=None):
        self.repo_url = repo_url
        self.repo_name = self._parse_repo_name(repo_url)
        self.output_dir = output_dir or os.path.join("findings", self.repo_name.replace("/", "_"))
        self.modules = []
        self.context = AuditContext(self.repo_name)
        self.config = {}
        self.repo_path_local = None # Stored after cloning
        self.progress = None  # ScanProgress instance
    
    def _parse_repo_name(self, repo_url):
        """Extract owner/repo from URL."""
        name = repo_url.replace("https://github.com/", "").replace("http://github.com/", "")
        if name.endswith(".git"):
            name = name[:-4]
        return name.strip("/")
    
    def add_module(self, module):
        """Add a signal module to the engine."""
        self.modules.append(module)
    
    def set_config(self, **kwargs):
        """Set configuration options passed to all modules."""
        self.config.update(kwargs)
    
    def run(self, module_names=None, progress_callback=None):
        """
        Run all (or specified) modules and build the audit context.
        """
        # Initialize progress tracking
        modules_to_run = [m for m in self.modules if not module_names or m.name in module_names]
        self.progress = ScanProgress(len(modules_to_run))
        if progress_callback:
            self.progress.add_callback(progress_callback)
            
        self.progress.update(step="Initializing scan")
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create raw_modules directory for individual module outputs
        raw_dir = os.path.join(self.output_dir, "raw_modules")
        os.makedirs(raw_dir, exist_ok=True)
        
        # Clone repository once for all modules (persist in output dir for viewer)
        self.progress.update(step="Cloning repository")
        self.repo_path_local = self._clone_repo()
        if not self.repo_path_local:
            self.progress.complete(status="error", error_message="Failed to clone repository")
            print("[!] Failed to clone repository. Aborting.")
            return self.context
            
        try:
            for module in modules_to_run:
                if module_names and module.name not in module_names:
                    continue
                
                self.progress.update(module=module.name, step=f"Running {module.name} module...")
                print(f"[*] Running {module.name} module...")
                
                try:
                    # Pass context to module
                    findings = module.collect(
                        repo_url=self.repo_url,
                        repo_name=self.repo_name,
                        repo_path=self.repo_path_local,
                        **self.config
                    )
                    
                    if findings:
                        self.context.add_findings(findings)
                        self.progress.update(findings_added=len(findings))
                        print(f"    Found {len(findings)} signals")
                        
                        # Save raw module output
                        raw_path = os.path.join(raw_dir, f"{module.name}.json")
                        with open(raw_path, "w") as f:
                            json.dump(findings, f, indent=2)
                        print(f"    Raw output: {raw_path}")
                    else:
                        print(f"    No signals found")
                    
                    self.context.modules_run.append(module.name)
                    
                except Exception as e:
                    error_msg = f"Error in {module.name}: {e}"
                    print(f"    {error_msg}")
                    self.progress.update(step=error_msg)
            
            # Run Enrichment
            if self.context.findings:
                self.progress.update(step="Running enrichment...")
                print(f"[*] Running enrichment...")
                for module in modules_to_run:
                    if module_names and module.name not in module_names:
                        continue
                    
                    # Skip if module has nothing to enrich
                    if hasattr(module, 'can_enrich') and not module.can_enrich(self.context.findings):
                        continue
                        
                    try:
                        self.progress.update(step=f"Enriching with {module.name}...")
                        print(f"    Enriching with {module.name}...")
                        self.context.findings = module.enrich(
                            self.context.findings,
                            repo_url=self.repo_url,
                            repo_name=self.repo_name,
                            repo_path=self.repo_path_local,
                            **self.config
                        )
                    except Exception as e:
                        error_msg = f"Error enriching with {module.name}: {e}"
                        print(f"    {error_msg}")
                        self.progress.update(step=error_msg)

            # Scoring / Post-processing
            self.progress.update(step="Calculating audit priority scores...")
            print(f"[*] Calculating Audit Priority scores (Module-based)...")
            # self._score_findings() # Central scoring disabled temporarily
            self._aggregate_module_scores()
            
            self.progress.update(step="Applying cross-signal reinforcement...")
            print(f"[*] Applying Cross-Signal Reinforcement...")
            self._apply_reinforcement()

            # Build summary and hotspots
            self.progress.update(step="Building summary and hotspots...")
            self._build_summary()
            self._identify_hotspots()
            
            # Save results
            self.progress.update(step="Saving results...")
            self._save_results()
            
            # Complete progress tracking
            self.progress.complete(status="completed")
            print(f"[*] Scan completed successfully!")
            
        except Exception as e:
            error_msg = f"Engine execution failed: {e}"
            print(f"[!] {error_msg}")
            if self.progress:
                self.progress.complete(status="error", error_message=error_msg)
            import traceback
            traceback.print_exc()
        
        return self.context
    
    def _aggregate_module_scores(self):
        """
        Calculates the final priority score based on module-provided metrics.
        Priority = Confidence * (Research Value + Impact) / 2
        """
        for finding in self.context.findings:
            f = finding if isinstance(finding, dict) else finding.__dict__
            
            u = f.get("research_value", 0.0)
            p = f.get("confidence_score", 0.0)
            i = f.get("severity_score", 0.0)
            
            # Formula: Confidence * (Research Value + Impact) / 2
            raw_priority = p * ((u + i) / 2)
            priority_score = int(raw_priority * 100)
            priority_score = min(priority_score, 100)
            
            reason = f"C:{p:.1f} × (R:{u:.1f} + I:{i:.1f})/2"
            
            if isinstance(finding, dict):
                finding["priority_score"] = priority_score
                finding["priority_reason"] = reason
                finding["impact_score"] = i
                
                # User requested Research Value to be the severity label
                finding["severity"] = self._map_research_value_to_severity(u)
            else:
                finding.priority_score = priority_score
                finding.priority_reason = reason
                finding.impact_score = i
                finding.severity = self._map_research_value_to_severity(u)

    def _apply_reinforcement(self):
        """Boost score if file has signals from multiple distinct modules."""
        by_file = defaultdict(set)
        
        # Map file -> set of module names
        for f in self.context.findings:
            finding = f if isinstance(f, dict) else f.to_dict()
            module = finding.get("source_module")
            files = finding.get("metadata", {}).get("files", [])
            if finding.get("metadata", {}).get("file"):
                files.append(finding["metadata"]["file"])
            
            for file_path in files:
                if isinstance(file_path, str):
                    by_file[file_path].add(module)
        
        # Apply boost
        for f in self.context.findings:
            finding = f if isinstance(f, dict) else f.__dict__ # Hack to access object or dict
            
            # Get files for this finding
            meta_files = []
            if isinstance(finding, dict):
                m = finding.get("metadata", {})
                if m.get("files"): meta_files.extend(m["files"])
                if m.get("file"): meta_files.append(m["file"])
                current_score = finding.get("priority_score", 0)
            else:
                m = finding.metadata
                if m.get("files"): meta_files.extend(m["files"])
                if m.get("file"): meta_files.append(m["file"])
                current_score = finding.priority_score

            # Check if any file associated with this finding has reinforcement
            boost = False
            for file_path in meta_files:
                if isinstance(file_path, str) and len(by_file[file_path]) > 1:
                    boost = True
                    break
            
            if boost:
                # Add 20 points, cap at 100
                new_score = min(current_score + 20, 100)
                
                if isinstance(finding, dict):
                    finding["priority_score"] = new_score
                    finding["priority_reason"] += " [🔥 Cross-Signal Boost]"
                    finding["severity"] = self._map_priority_to_severity(new_score)
                else:
                    finding.priority_score = new_score
                    finding.priority_reason += " [🔥 Cross-Signal Boost]"
                    finding.severity = self._map_priority_to_severity(new_score)

    def _map_research_value_to_severity(self, score):
        # Score is 0.0-1.0
        if score >= 0.9: return "critical"
        if score >= 0.7: return "high"
        if score >= 0.4: return "medium"
        return "low"

    def _map_priority_to_severity(self, score):
        # Legacy mapping, kept if needed for other logic
        if score >= 80: return "critical"
        if score >= 60: return "high"
        if score >= 30: return "medium"
        return "low"

    def _clone_repo(self):
        """Clone the repository to the output directory (persisted)."""
        repo_path = os.path.join(self.output_dir, "source")
        
        if os.path.exists(repo_path):
            print(f"[*] Repository already exists at {repo_path}, using cached version.")
            return repo_path
            
        try:
            print(f"[*] Cloning {self.repo_url} to {repo_path}...")
            Repo.clone_from(self.repo_url, repo_path)
            return repo_path
        except Exception as e:
            print(f"[!] Error cloning repo: {e}")
            return None
            
    def _build_summary(self):
        """Build summary statistics from findings."""
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        by_module = defaultdict(int)
        
        for f in self.context.findings:
            finding = f if isinstance(f, dict) else f.to_dict()
            by_type[finding.get("signal_type", "unknown")] += 1
            by_severity[finding.get("severity", "medium")] += 1
            by_module[finding.get("source_module", "unknown")] += 1
        
        self.context.summary = {
            "total_findings": len(self.context.findings),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "by_module": dict(by_module)
        }
    
    def _identify_hotspots(self):
        """
        Identify and prioritize areas to start auditing based on Audit Priority.
        """
        hotspots = []
        
        # Group findings by various dimensions
        by_file = defaultdict(list)
        by_cve = defaultdict(list)
        
        for f in self.context.findings:
            finding = f if isinstance(f, dict) else f.to_dict()
            metadata = finding.get("metadata", {})
            
            # Track CVEs
            if finding.get("signal_type") == "cve":
                cve_id = metadata.get("cve_id") or finding.get("title", "")
                by_cve[cve_id].append(finding)
            
            # Track files mentioned
            files = metadata.get("files", [])
            if metadata.get("file"):
                files.append(metadata.get("file"))
            
            for file_path in files:
                if isinstance(file_path, str):
                    by_file[file_path].append(finding)
        
        # Prioritize CVEs
        for cve_id, findings in sorted(by_cve.items(), key=lambda x: -len(x[1])):
            max_p = max(f.get("priority_score", 0) for f in findings)
            
            hotspots.append({
                "type": "cve",
                "identifier": cve_id,
                "reason": f"Known vulnerability with {len(findings)} related signals",
                "priority": self._map_priority_to_severity(max_p),
                "score": max_p,
                "signal_count": len(findings),
                "start_here": f"Search codebase for {cve_id} fix and related changes",
                "review_guide": self._generate_review_guide("cve", findings[0], len(findings))
            })
        
        # Prioritize files
        for file_path, findings in sorted(by_file.items(), key=lambda x: -len(x[1])):
            if len(findings) >= 1: 
                # Identify the highest priority finding in this file
                findings_sorted = sorted(findings, key=lambda x: -x.get("priority_score", 0))
                top_finding = findings_sorted[0]
                max_p = top_finding.get("priority_score", 0)
                
                # Only include hotspots with decent priority (e.g. > 20)
                if max_p < 20: continue

                # Build descriptive reason from the top finding
                reason = top_finding.get("priority_reason")
                if not reason:
                     reason = f"Contains {len(findings)} signals (Top: {top_finding.get('title')})"
                
                start_here = f"Review {file_path}"
                
                # Calculate Adjacency
                adjacency = self._compute_adjacency(file_path)

                hotspots.append({
                    "type": "file",
                    "identifier": file_path,
                    "reason": reason,
                    "priority": self._map_priority_to_severity(max_p),
                    "score": max_p,
                    "signal_count": len(findings),
                    "start_here": start_here,
                    "adjacency": adjacency,
                    "review_guide": self._generate_review_guide("file", top_finding, len(findings), file_path)
                })
        
        # Sort by Score (Audit Priority)
        hotspots.sort(key=lambda x: -x.get("score", 0))
        
        self.context.hotspots = hotspots[:20]  # Top 20 hotspots

    def _generate_review_guide(self, type, finding, count, file_path=None):
        """Generates 'Why am I looking here?' summary and questions."""
        
        # 1. Summary
        summary = f"This is a high-priority review target (Score: {finding.get('priority_score')}). "
        summary += f"It has {count} signals. "
        
        if finding.get("confidence_score", 0) > 0.7:
            summary += "Confidence is high due to strong indicators like " + (finding.get("confidence_reason") or "specific patterns") + ". "
        
        if finding.get("impact_score", 0) > 0.7:
            summary += "Impact is critical because it involves " + (finding.get("impact_reason") or "sensitive components") + ". "

        # 2. Questions
        questions = []
        stype = finding.get("signal_type")
        
        if stype == "cve" or finding.get("metadata", {}).get("cve_id"):
            questions.append("Was input validation added here, or only in the patched code path?")
            questions.append("Are there other call sites that bypass this fix?")
        
        if stype == "vulnerable_dependency":
             questions.append("Is this dependency actually used in production paths?")
             questions.append("Can we upgrade this dependency without breaking changes?")
        
        if "auth" in str(file_path).lower() or "login" in str(file_path).lower():
            questions.append("Does this auth logic handle edge cases (null tokens, expired sessions)?")
            questions.append("Is there a bypass for this check?")
            
        if not questions:
            questions.append("What is the security impact if this code fails?")
            questions.append("Is user input properly sanitized before use?")

        return {
            "summary": summary,
            "questions": questions
        }

    def _compute_adjacency(self, file_path):
        """Finds nearby files: Siblings and Imports."""
        if not self.repo_path_local:
            return {"siblings": [], "importers": []}
            
        full_path = os.path.join(self.repo_path_local, file_path)
        if not os.path.exists(full_path):
             return {"siblings": [], "importers": []}
             
        # 1. Siblings (Same Directory)
        siblings = []
        try:
            parent_dir = os.path.dirname(full_path)
            for f in os.listdir(parent_dir):
                if f == os.path.basename(file_path): continue
                if os.path.isfile(os.path.join(parent_dir, f)):
                    siblings.append(f)
        except Exception:
            pass
            
        # 2. Importers (Lightweight grep)
        importers = []
        try:
            fname = os.path.basename(file_path)
            # Remove extension
            fname_no_ext = os.path.splitext(fname)[0]
            
            # Grep for filename in repo
            # Limit to 5 matches
            cmd = [
                "grep", "-r", "-l", "-m", "5",
                "--exclude-dir=.git", 
                "--exclude-dir=node_modules",
                fname_no_ext,
                self.repo_path_local
            ]
            
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.stdout:
                lines = res.stdout.strip().splitlines()
                for line in lines:
                     # Make relative
                     rel = os.path.relpath(line, self.repo_path_local)
                     if rel != file_path:
                         importers.append(rel)
                         
        except Exception:
            pass

        return {
            "siblings": siblings[:5], # Limit noise
            "importers": importers[:5]
        }
    
    def _save_results(self):
        """Save context to output directory."""
        # Pre-calculate IDs for server performance
        for f in self.context.findings:
            if isinstance(f, dict):
                f["id"] = calculate_finding_id(f)
            # If it's an object, we assume it has no ID field or we can't set it easily without ensuring attr exists
            # But the dict conversion in to_dict handles it.
            # Let's rely on to_dict modifications if needed, or just set it if possible.
            elif hasattr(f, "__dict__"):
                # Calculate based on dict representation
                f.id = calculate_finding_id(f.to_dict())

        output_path = os.path.join(self.output_dir, "context.json")
        with open(output_path, "w") as f:
            json.dump(self.context.to_dict(), f, indent=2)
        print(f"\n[+] Results saved to {output_path}")
        
        # Also save a human-readable summary
        summary_path = os.path.join(self.output_dir, "audit_start.md")
        self._save_markdown_summary(summary_path)
        print(f"[+] Audit guide saved to {summary_path}")
        
        # Save dashboard
        self._save_dashboard()
    
    def _save_dashboard(self):
        """Generate the HTML dashboard."""
        try:
            # Load template
            template_path = os.path.join(os.path.dirname(__file__), "dashboard", "template.html")
            if not os.path.exists(template_path):
                print(f"[!] Dashboard template not found at {template_path}")
                return

            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            
            # Inject data
            json_data = json.dumps(self.context.to_dict(), ensure_ascii=False)
            # Escape closing script tags to prevent XSS/breaking HTML
            json_data = json_data.replace("</", "<\\/")
            html = template.replace("window.CONTEXT_DATA || {};", json_data)
            
            output_path = os.path.join(self.output_dir, "dashboard.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            print(f"[+] Dashboard saved to {output_path}")
            
        except Exception as e:
            print(f"[!] Error generating dashboard: {e}")

    def _save_markdown_summary(self, path):
        """Generate a human-readable audit starting guide."""
        lines = [
            f"# Audit Starting Points: {self.repo_name}",
            f"",
            f"*Generated: {self.context.scan_date}*",
            f"",
            f"## Summary",
            f"",
            f"- **Total signals found:** {self.context.summary.get('total_findings', 0)}",
            f"- **Modules run:** {', '.join(self.context.modules_run)}",
            f"",
        ]
        
        # Add breakdown
        by_type = self.context.summary.get("by_type", {})
        if by_type:
            lines.append("### Signal Breakdown")
            lines.append("")
            for signal_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
                lines.append(f"- {signal_type}: {count}")
            lines.append("")
        
        # Add hotspots
        if self.context.hotspots:
            lines.append("## Where to Start (Prioritized by Confidence × Impact)")
            lines.append("")
            for i, hotspot in enumerate(self.context.hotspots[:10], 1):
                priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(hotspot["priority"], "⚪")
                lines.append(f"### {i}. {priority_emoji} {hotspot['identifier']} (Score: {hotspot.get('score', 0)})")
                lines.append(f"")
                
                # Use Review Guide if available
                if hotspot.get("review_guide"):
                    rg = hotspot["review_guide"]
                    lines.append(f"**Why:** {rg['summary']}")
                    lines.append(f"")
                    if rg.get("questions"):
                        lines.append("**Suggested Questions:**")
                        for q in rg["questions"]:
                            lines.append(f"- {q}")
                        lines.append("")
                else:
                    lines.append(f"**Why:** {hotspot['reason']}")
                    lines.append(f"")
                
                # Adjacency
                adj = hotspot.get("adjacency")
                if adj and (adj.get("siblings") or adj.get("importers")):
                    lines.append("**Review Radius (Adjacent Files):**")
                    if adj.get("importers"):
                        lines.append(f"- *Referenced by:* {', '.join(adj['importers'][:3])}")
                    if adj.get("siblings"):
                        lines.append(f"- *Siblings:* {', '.join(adj['siblings'][:3])}")
                    lines.append("")

                lines.append(f"**Action:** {hotspot['start_here']}")
                lines.append(f"")
        
        with open(path, "w") as f:
            f.write("\n".join(lines))
