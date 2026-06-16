"""Semgrep Code Intel Module - Scans codebase for features using local Semgrep rules."""

import os
import json
import shutil
import subprocess
from repo_intel.modules.base import SignalModule, register_module

@register_module
class SemgrepCodeIntelModule(SignalModule):
    """Scans the codebase using Semgrep with local feature-extraction rules."""
    
    name = "semgrep_code_intel"
    description = "Scans code for features (Auth, Crypto, API) using local Semgrep rules"

    def get_scores(self):
        return {
            "confidence_score": 8,
            "research_value": 9,
            "impact_score": 2  # Features are not vulnerabilities
        }
    
    def collect(self, repo_url, repo_name, repo_path=None, **kwargs):
        """Run semgrep scan using local rules."""
        findings = []
        
        if not repo_path:
            return findings

        if not shutil.which("semgrep"):
            print(f"    [!] 'semgrep' command not found. Skipping Code Intel analysis.")
            return findings
        
        # Locate local rules directory
        # This file is in modules/extractors/
        # Rules are in rules/semgrep/
        # Path: ../../rules/semgrep
        script_dir = os.path.dirname(os.path.realpath(__file__))
        rules_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "rules", "semgrep"))
        
        if not os.path.exists(rules_dir):
            print(f"    [!] Local Semgrep rules not found at {rules_dir}")
            return findings

        print(f"    Running Semgrep Feature Scan on {repo_path} using rules in {rules_dir}...")
        
        try:
            cmd = [
                "semgrep", 
                "scan", 
                f"--config={rules_dir}", 
                "--json", 
                "-q",
                repo_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0 and result.stderr:
                 if "error" in result.stderr.lower() and not result.stdout:
                    print(f"    [!] Semgrep error: {result.stderr.strip()}")
                    return findings

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                return findings
                
            results = data.get("results", [])
            print(f"    Semgrep found {len(results)} features.")
            
            for result in results:
                finding = self._convert_semgrep_result(result, repo_path)
                if finding:
                    findings.append(finding)
                    
        except Exception as e:
            print(f"    [!] Error running semgrep code intel: {e}")
            
        return findings

    def _convert_semgrep_result(self, result, repo_path):
        """Convert a Semgrep JSON result to a Finding."""
        path = result.get("path", "")
        check_id = result.get("check_id", "unknown")
        
        try:
            abs_path = os.path.abspath(path)
            abs_repo = os.path.abspath(repo_path)
            rel = os.path.relpath(abs_path, abs_repo)
            
            if not rel.startswith(".."):
                rel_path = rel
            else:
                rel_path = path
        except Exception:
            rel_path = path
            
        extra = result.get("extra", {})
        message = extra.get("message", "")
        
        start = result.get("start", {})
        end = result.get("end", {})
        line = start.get("line", 1)
        
        snippet = extra.get("lines", "")
        
        # Extract categories from metadata if present
        meta = extra.get("metadata", {})
        category = meta.get("category", "feature")
        subcategory = meta.get("subcategory", "")
        
        metadata = {
            "file": rel_path,
            "files": [rel_path],
            "line": line,
            "end_line": end.get("line", line),
            "col": start.get("col", 1),
            "check_id": check_id,
            "snippet": snippet.strip(),
            "tool": "semgrep-code-intel",
            "category": category,
            "subcategory": subcategory
        }
            
        description = f"{message}\n\nRule: {check_id}"
        
        return self._make_finding(
            signal_type="feature_detected",
            title=f"Feature: {message}"[:100],
            description=description,
            metadata=metadata
        )
