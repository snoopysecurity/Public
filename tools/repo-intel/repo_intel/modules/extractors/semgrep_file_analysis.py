"""Semgrep Analysis Module - Scans codebase using Semgrep."""

"""
__Logic:__

- It executes the `semgrep` CLI tool directly on the codebase.
- **Configuration:** Uses Semgrep's "auto" configuration (or custom config if provided) to select rules.
- **Parsing:** Captures the JSON output from Semgrep.
- **Signal Generation:** Converts Semgrep results into standardized findings with rule IDs and code snippets.
"""

import os
import json
import shutil
import subprocess
from repo_intel.modules.base import SignalModule, register_module

@register_module
class SemgrepFileAnalysisModule(SignalModule):
    """Scans the codebase using the Semgrep CLI tool."""
    
    name = "semgrep_file_analysis"
    description = "Scans files for security issues using Semgrep (requires 'semgrep' installed)"

    def get_scores(self):
        return {
            "confidence_score": 9,
            "research_value": 9,
            "impact_score": 9
        }
    
    def collect(self, repo_url, repo_name, repo_path=None, **kwargs):
        """Run semgrep scan on the repository."""
        findings = []
        
        if not repo_path:
            print(f"    Skipping semgrep_file_analysis (no repo_path provided)")
            return findings

        # Check if semgrep is installed
        if not shutil.which("semgrep"):
            print(f"    [!] 'semgrep' command not found. Please install it (e.g., 'pip install semgrep').")
            print(f"    [!] Skipping Semgrep analysis.")
            return findings

        print(f"    Running Semgrep scan on {repo_path}...")
        
        try:
            # Run semgrep with auto config and JSON output
            # -q for quiet (no progress bar on stderr)
            # --config=auto uses default rules (r/all usually or security)
            # We can also use --config=p/security-audit if we want specific security focus
            # For now, auto is a good default.
            cmd = [
                "semgrep", 
                "scan", 
                "--config=auto", 
                "--json", 
                "-q",
                repo_path
            ]
            
            # Allow user to override config via --config semgrep_config=...
            if "semgrep_config" in kwargs:
                cmd[2] = f"--config={kwargs['semgrep_config']}"
                
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.returncode != 0 and result.stderr:
                # Semgrep returns 0 on success (findings or no findings), 
                # but might return non-zero on error. 
                # Note: Semgrep return codes can be configured to exit 1 on findings, 
                # but default is 0 unless --error flag is used.
                if "error" in result.stderr.lower() and not result.stdout:
                    print(f"    [!] Semgrep error: {result.stderr.strip()}")
                    return findings

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                print(f"    [!] Failed to parse Semgrep output")
                if result.stderr:
                    print(f"    Stderr: {result.stderr.strip()[:200]}...")
                return findings
                
            results = data.get("results", [])
            print(f"    Semgrep found {len(results)} issues.")
            
            for result in results:
                finding = self._convert_semgrep_result(result, repo_path)
                if finding:
                    findings.append(finding)
                    
        except Exception as e:
            print(f"    [!] Error running semgrep: {e}")
            
        return findings

    def _convert_semgrep_result(self, result, repo_path):
        """Convert a Semgrep JSON result to a Finding."""
        path = result.get("path", "")
        check_id = result.get("check_id", "unknown")
        
        # Make path relative to the repository root
        # Semgrep might return absolute paths or paths relative to CWD (which includes repo_path)
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
        
        # Extract location
        start = result.get("start", {})
        end = result.get("end", {})
        line = start.get("line", 1)
        
        # Extract snippet
        snippet = extra.get("lines", "")
        
        # Extract metadata
        metadata = {
            "file": rel_path,
            "files": [rel_path], # Used by aggregation logic
            "line": line,
            "end_line": end.get("line", line),
            "col": start.get("col", 1),
            "check_id": check_id,
            "snippet": snippet.strip(),
            "tool": "semgrep"
        }
        
        # Add security metadata
        meta = extra.get("metadata", {})
        if "cwe" in meta:
            metadata["cwe"] = meta["cwe"]
        if "owasp" in meta:
            metadata["owasp"] = meta["owasp"]
        if "references" in meta:
            metadata["references"] = meta["references"]
            
        # Build description
        description = f"{message}\n\nRule: {check_id}"
        if "cwe" in meta:
            cwe = meta["cwe"]
            if isinstance(cwe, list):
                cwe = ", ".join(cwe)
            description += f"\nCWE: {cwe}"
            
        return self._make_finding(
            signal_type="semgrep_finding",
            title=f"{check_id.split('.')[-1]}: {message}"[:100],
            description=description,
            metadata=metadata
        )
