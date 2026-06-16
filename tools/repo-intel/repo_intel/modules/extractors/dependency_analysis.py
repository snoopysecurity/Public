"""Dependency Analysis Module - Checks for vulnerable dependencies using osv-scanner with API fallback."""

"""
__Logic:__

- It scans the repository for vulnerable dependencies using `osv-scanner`.
- **Primary Method:** Executes `osv-scanner` recursively to find vulnerabilities in lockfiles and manifests.
- **Fallback Method:** If `osv-scanner` is missing or finds nothing, it manually parses manifests (`package.json`, `requirements.txt`) and queries the OSV API.
- It normalizes findings into "Vulnerable Dependency" signals with CVE IDs and severity ratings.
"""

import os
import json
import shutil
import subprocess
import requests
from typing import List, Dict, Any

from repo_intel.modules.base import SignalModule, register_module


@register_module
class DependencyAnalysisModule(SignalModule):
    """Scans dependency files and checks against OSV database using osv-scanner or direct API."""
    
    name = "dependency_analysis"
    description = "Checks project dependencies for known vulnerabilities using osv-scanner (with manifest fallback)"

    def get_scores(self):
        return {
            "confidence_score": 9,
            "research_value": 9,
            "impact_score": 9
        }
    
    def collect(self, repo_url: str, repo_name: str, repo_path: str = None, **kwargs) -> List[Dict[str, Any]]:
        """Scan dependencies using osv-scanner, falling back to direct API if needed."""
        findings = []
        
        if not repo_path:
            return findings

        # 1. Try osv-scanner if installed
        if shutil.which("osv-scanner"):
            print(f"    Scanning dependencies in {repo_path} using osv-scanner...")
            findings = self._run_osv_scanner(repo_path)
        else:
            print("    [!] osv-scanner not found. Falling back to direct manifest scanning.")
            # We don't add a "missing tool" finding anymore since we have a fallback,
            # but we could log it.

        # 2. If no findings from scanner (or scanner missing/failed), try fallback for manifests
        if not findings:
             print("    Checking for manifests (package.json, requirements.txt) for API fallback...")
             fallback_findings = self._scan_manifests_fallback(repo_path)
             if fallback_findings:
                 print(f"    Found {len(fallback_findings)} findings via fallback API.")
                 findings.extend(fallback_findings)

        # 3. Usage Check (Reachability Hints)
        # Check if the vulnerable package is actually imported/used in the code
        if findings and repo_path:
            print("    Checking for package usage in code (Reachability)...")
            for finding in findings:
                pkg = finding["metadata"].get("package")
                if pkg:
                    usage = self._check_usage(pkg, repo_path)
                    
                    if usage:
                        finding["description"] += "\n\n**Reachability:** Package name found in source code (higher risk)."
                        finding["metadata"]["usage_detected"] = True
                    else:
                        finding["description"] += "\n\n**Reachability:** Package name NOT found in source code (lower risk)."
                        finding["metadata"]["usage_detected"] = False

        return findings

    def _check_usage(self, pkg_name, repo_path):
        """Simple grep to see if package name appears in code."""
        try:
            # Grep for the package name, excluding common noise directories
            # -r recursive, -l list files only, -m 1 stop after 1 match
            cmd = [
                "grep", "-r", "-l", "-m", "1",
                "--exclude-dir=.git", 
                "--exclude-dir=node_modules",
                "--exclude-dir=venv",
                "--exclude-dir=__pycache__",
                pkg_name,
                repo_path
            ]
            
            # Run silently
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return result.returncode == 0 # 0 means found
        except Exception:
            return False

    def _run_osv_scanner(self, repo_path: str) -> List[Dict[str, Any]]:
        findings = []
        try:
            # Command: osv-scanner scan source -r --no-resolve --format json {repo_path}
            cmd = [
                "osv-scanner",
                "scan",
                "source",
                "-r",               # Recursive
                "--no-resolve",     # Skip transitive dependencies resolution
                "--format", "json", # JSON output
                repo_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False 
            )
            
            if not result.stdout:
                if result.stderr:
                    # Don't print full stderr if it's just "No package sources found" unless debug
                    if "No package sources found" not in result.stderr:
                        print(f"      osv-scanner error: {result.stderr}")
                return findings

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                return findings

            scan_results = data.get("results", [])
            for res in scan_results:
                source_path = res.get("source", {}).get("path", "unknown")
                if source_path.startswith(repo_path):
                    source_path = source_path[len(repo_path):].lstrip("/")
                
                packages = res.get("packages", [])
                for pkg_wrapper in packages:
                    pkg_info = pkg_wrapper.get("package", {})
                    pkg_name = pkg_info.get("name", "unknown")
                    pkg_version = pkg_info.get("version", "unknown")
                    ecosystem = pkg_info.get("ecosystem", "unknown")
                    
                    vulns = pkg_wrapper.get("vulnerabilities", [])
                    
                    for vuln in vulns:
                        vuln_id = vuln.get("id", "unknown")
                        summary = vuln.get("summary") or vuln.get("details", "No description")
                        summary = summary[:200] + "..." if len(summary) > 200 else summary
                        
                        aliases = vuln.get("aliases", [])
                        cve_id = next((a for a in aliases if a.startswith("CVE-")), None)
                        
                        title = f"Vulnerable {pkg_name} {pkg_version}"
                        if cve_id:
                            title += f" ({cve_id})"
                        
                        findings.append(self._make_finding(
                            signal_type="vulnerable_dependency",
                            title=title,
                            description=f"Found {vuln_id} in {pkg_name}@{pkg_version} ({ecosystem}): {summary}",
                            metadata={
                                "package": pkg_name,
                                "version": pkg_version,
                                "ecosystem": ecosystem,
                                "vuln_id": vuln_id,
                                "cve_id": cve_id,
                                "file": source_path,
                                "method": "osv_scanner",
                                "references": [ref.get("url") for ref in vuln.get("references", [])]
                            }
                        ))
        except Exception as e:
            print(f"      Error running osv-scanner: {e}")
            
        return findings

    def _scan_manifests_fallback(self, repo_path: str) -> List[Dict[str, Any]]:
        """Manually scan manifests if osv-scanner missed them."""
        findings = []
        queries = []
        
        # 1. Collect dependencies
        
        # Check package.json (npm)
        # Walk to find all package.json files since osv-scanner is recursive
        for root, dirs, files in os.walk(repo_path):
            if "node_modules" in dirs:
                dirs.remove("node_modules") # Skip node_modules
                
            if "package.json" in files:
                pkg_json_path = os.path.join(root, "package.json")
                rel_path = os.path.relpath(pkg_json_path, repo_path)
                try:
                    with open(pkg_json_path, "r") as f:
                        data = json.load(f)
                        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        for name, version in deps.items():
                            clean_ver = version.lstrip("^~>=<v")
                            if clean_ver and clean_ver[0].isdigit():
                                 queries.append({
                                    "package": {"name": name, "ecosystem": "npm"},
                                    "version": clean_ver,
                                    "source_file": rel_path
                                })
                except Exception:
                    pass

            # Check requirements.txt (PyPI)
            if "requirements.txt" in files:
                req_path = os.path.join(root, "requirements.txt")
                rel_path = os.path.relpath(req_path, repo_path)
                try:
                    with open(req_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "==" in line:
                                parts = line.split("==")
                                name = parts[0].strip()
                                version = parts[1].split()[0].strip()
                                queries.append({
                                    "package": {"name": name, "ecosystem": "PyPI"},
                                    "version": version,
                                    "source_file": rel_path
                                })
                except Exception:
                    pass

        if not queries:
            return findings

        # 2. Query OSV.dev
        # Group queries by chunk of 1000
        chunk_size = 1000
        for i in range(0, len(queries), chunk_size):
            chunk = queries[i:i + chunk_size]
            # Prepare payload - remove 'source_file' which is not part of API schema
            payload_queries = [{"package": q["package"], "version": q["version"]} for q in chunk]
            
            try:
                url = "https://api.osv.dev/v1/querybatch"
                response = requests.post(url, json={"queries": payload_queries}, timeout=30)
                response.raise_for_status()
                results = response.json().get("results", [])
                
                for idx, result in enumerate(results):
                    vulns = result.get("vulns", [])
                    if vulns:
                        pkg_ctx = chunk[idx]
                        pkg_name = pkg_ctx["package"]["name"]
                        pkg_ver = pkg_ctx["version"]
                        source_file = pkg_ctx["source_file"]
                        ecosystem = pkg_ctx["package"]["ecosystem"]
                        
                        for vuln in vulns:
                            cve_id = next((a for a in vuln.get("aliases", []) if a.startswith("CVE-")), None)
                            summary = vuln.get("summary") or vuln.get("details", "No description")
                            summary = summary[:200] + "..." if len(summary) > 200 else summary
                            vuln_id = vuln["id"]
                            
                            title = f"Vulnerable {pkg_name} {pkg_ver}"
                            if cve_id:
                                title += f" ({cve_id})"
                            title += " [Low Precision - Manifest Scan]"
                            
                            findings.append(self._make_finding(
                                signal_type="vulnerable_dependency",
                                title=title,
                                description=f"Found {vuln_id} in {pkg_name}@{pkg_ver} ({ecosystem}).\n\n**Note:** This finding is approximate (Low Precision) because it was detected by scanning `{os.path.basename(source_file)}` directly without a lockfile. The actual installed version may differ.\n\nSummary: {summary}",
                                metadata={
                                    "package": pkg_name,
                                    "version": pkg_ver,
                                    "ecosystem": ecosystem,
                                    "vuln_id": vuln_id,
                                    "cve_id": cve_id,
                                    "file": source_file,
                                    "method": "manifest_fallback"
                                }
                            ))
                            
            except Exception as e:
                print(f"      Error querying OSV API: {e}")
                
        return findings
