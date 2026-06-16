"""SAST Findings Module - Generic SARIF file processor for static analysis tools."""

"""
__Logic:__

- It ingests Static Application Security Testing (SAST) results in SARIF format.
- **Auto-Discovery:** Recursively searches the repository for `.sarif` or `.sarif.json` files.
- **Parsing:** Extracts runs, results, rules, and locations from the SARIF data.
- **Mapping:** Converts SARIF severity levels to internal severity ratings.
- **Taint Analysis:** Extracts code flow information (taint traces) if available in the SARIF.
"""

import json
import os
import glob
from typing import List, Dict, Any, Optional
from repo_intel.modules.base import SignalModule, register_module

@register_module
class SastFindingsModule(SignalModule):
    """Processes SARIF files from various SAST tools (Semgrep, Snyk Code, CodeQL, etc.)."""
    
    name = "sast_findings"
    description = "Generic SARIF file processor for static analysis findings"

    def get_scores(self):
        return {
            "confidence_score": 9,
            "research_value": 9,
            "impact_score": 9
        }
    
    def collect(self, repo_url, repo_name, repo_path=None, sarif_file=None, **kwargs):
        findings = []
        if not repo_path:
            return findings
            
        # If a specific SARIF file is provided, use only that
        if sarif_file:
            print(f"    Using specified SARIF file: {sarif_file}")
            
            # If it's an absolute path, use it directly
            if os.path.isabs(sarif_file):
                sarif_file_path = sarif_file
            else:
                # For relative paths, first try current working directory, then repo_path
                current_dir_path = os.path.join(os.getcwd(), sarif_file)
                repo_relative_path = os.path.join(repo_path, sarif_file)
                
                if os.path.exists(current_dir_path):
                    sarif_file_path = current_dir_path
                    print(f"    Found SARIF file in current directory: {current_dir_path}")
                elif os.path.exists(repo_relative_path):
                    sarif_file_path = repo_relative_path
                    print(f"    Found SARIF file in repo directory: {repo_relative_path}")
                else:
                    print(f"    [!] SARIF file not found: {sarif_file}")
                    print(f"        Tried: {current_dir_path}")
                    print(f"        Tried: {repo_relative_path}")
                    return findings
                
            try:
                print(f"    Processing {os.path.basename(sarif_file_path)}...")
                with open(sarif_file_path, 'r', encoding='utf-8') as f:
                    sarif_data = json.load(f)
                
                # Check if SARIF findings reference files that exist in the current repo
                # If not, we need to handle this gracefully
                file_findings = self._process_sarif(sarif_data, sarif_file_path, repo_path)
                findings.extend(file_findings)
                print(f"      Extracted {len(file_findings)} findings")
                
                # If no files were found due to missing source files, try to extract repo info from SARIF
                if len(file_findings) == 0:
                    print(f"    [!] No findings extracted - source files may not match current repo")
                    print(f"    [!] Consider running with the original target repository")
                    print(f"    [!] Example: repo-intel --modules sast_findings --sarif-file {sarif_file} --target <original-repo-url>")
                
            except Exception as e:
                print(f"    [!] Error processing {os.path.basename(sarif_file_path)}: {e}")
                
            return findings
        
        # Otherwise, search for SARIF files automatically (existing behavior)
        print(f"    Searching for SARIF files in {repo_path}...")
        
        # Look for SARIF files recursively
        print(f"    Searching for *.sarif and *.sarif.json recursively...")
        sarif_files = []
        
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".sarif") or file.endswith(".sarif.json"):
                    sarif_files.append(os.path.join(root, file))
        
        # Unique files only
        sarif_files = list(set(sarif_files))
        
        if not sarif_files:
            print("    [!] No SARIF files found")
            return findings
            
        print(f"    Found {len(sarif_files)} SARIF file(s): {', '.join(os.path.basename(f) for f in sarif_files)}")
        
        for sarif_file in sarif_files:
            try:
                print(f"    Processing {os.path.basename(sarif_file)}...")
                with open(sarif_file, 'r', encoding='utf-8') as f:
                    sarif_data = json.load(f)
                
                file_findings = self._process_sarif(sarif_data, sarif_file, repo_path)
                findings.extend(file_findings)
                print(f"      Extracted {len(file_findings)} findings")
                
            except Exception as e:
                print(f"    [!] Error processing {os.path.basename(sarif_file)}: {e}")
                
        return findings
    
    def _process_sarif(self, sarif_data: Dict, sarif_file: str, repo_path: str) -> List[Dict]:
        """Process SARIF data and extract findings."""
        findings = []
        
        runs = sarif_data.get("runs", [])
        if not runs:
            print(f"      [!] No runs found in SARIF file")
            return findings
            
        for run_idx, run in enumerate(runs):
            tool_info = run.get("tool", {})
            tool_name = tool_info.get("driver", {}).get("name", "unknown")
            
            # Get results from this run
            results = run.get("results", [])
            if not results:
                continue
                
            print(f"      Processing {len(results)} results from {tool_name} (run {run_idx + 1})")
            
            # Get rule mappings for this run
            rules = {}
            if "tool" in run and "driver" in run["tool"]:
                rules_dict = run["tool"]["driver"].get("rules", [])
                for rule in rules_dict:
                    rule_id = rule.get("id")
                    if rule_id:
                        rules[rule_id] = rule
            
            for result in results:
                finding = self._convert_sarif_result(result, rules, tool_name, sarif_file, repo_path)
                if finding:
                    findings.append(finding)
        
        return findings
    
    def _convert_sarif_result(self, result: Dict, rules: Dict, tool_name: str, 
                            sarif_file: str, repo_path: str) -> Optional[Dict]:
        """Convert a SARIF result to the repo-intel finding format."""
        
        # Extract basic information
        rule_id = result.get("ruleId", "unknown")
        level = result.get("level", "note")
        message = result.get("message", {}).get("text", "No message")
        
        # Get rule information if available
        rule_info = rules.get(rule_id, {})
        rule_name = rule_info.get("name", rule_id)
        rule_description = rule_info.get("fullDescription", {}).get("text", "") or \
                          rule_info.get("shortDescription", {}).get("text", "") or \
                          rule_info.get("description", {}).get("text", "")
        
        # Extract file location
        locations = result.get("locations", [])
        if not locations:
            return None
            
        location = locations[0]
        physical_loc = location.get("physicalLocation", {})
        artifact_loc = physical_loc.get("artifactLocation", {})
        
        # Extract file path
        file_uri = artifact_loc.get("uri", "")
        if file_uri.startswith("file://"):
            file_path = file_uri[7:]
        else:
            file_path = file_uri
        
        # Make path relative to repo
        if os.path.isabs(file_path) and file_path.startswith(repo_path):
            rel_path = os.path.relpath(file_path, repo_path)
        else:
            rel_path = file_path
        
        # Check if the file exists in the repo - if not, still create the finding but note the issue
        full_file_path = os.path.join(repo_path, rel_path)
        if not os.path.exists(full_file_path):
            print(f"      [!] Source file not found: {rel_path}")
            # Don't return None - still create the finding, but we'll handle missing source in the frontend
        
        # Extract location details
        region = physical_loc.get("region", {})
        start_line = region.get("startLine", 1)
        end_line = region.get("endLine", start_line)
        start_column = region.get("startColumn", 1)
        end_column = region.get("endColumn", start_column)
        
        # Extract code snippet if available
        snippet_text = ""
        if "logicalLocations" in result:
            # Try to get snippet from logical locations
            logical_loc = result["logicalLocations"][0] if result["logicalLocations"] else {}
            snippet_text = logical_loc.get("fullyQualifiedName", "")
        
        # Build metadata
        metadata = {
            "file": rel_path,
            "files": [rel_path],
            "line": start_line,
            "end_line": end_line,
            "start_column": start_column,
            "end_column": end_column,
            "rule_id": rule_id,
            "rule_name": rule_name,
            "tool": tool_name,
            "sarif_file": os.path.basename(sarif_file),
            "level": level,
            "snippet": snippet_text
        }
        
        # Add flag if source file is missing
        if not os.path.exists(full_file_path):
            metadata["source_file_missing"] = True
        
        # Extract taint flow data if present
        has_taint_flow = False
        if "codeFlows" in result:
            taint_flows = self._extract_taint_flows(result["codeFlows"], repo_path)
            if taint_flows:
                metadata["taint_flows"] = taint_flows
                has_taint_flow = True
        
        # Add additional rule metadata if available
        if rule_info:
            if "help" in rule_info:
                metadata["help_text"] = rule_info["help"].get("text", "")
            if "properties" in rule_info:
                metadata.update(rule_info["properties"])
            if "defaultConfiguration" in rule_info:
                config = rule_info["defaultConfiguration"]
                if "level" in config:
                    metadata["default_level"] = config["level"]
        
        # Add CWE/OWASP information if available
        if "properties" in result:
            props = result["properties"]
            if "cwe" in props:
                metadata["cwe"] = props["cwe"]
            if "owasp" in props:
                metadata["owasp"] = props["owasp"]
            if "tags" in props:
                metadata["tags"] = props["tags"]
        
        # Build description
        description_parts = []
        if rule_description:
            description_parts.append(f"Rule: {rule_description}")
        if message:
            description_parts.append(f"Message: {message}")
        if tool_name != "unknown":
            description_parts.append(f"Tool: {tool_name}")
            
        description = "\n".join(description_parts)
        
        # Create the finding
        return self._make_finding(
            signal_type="sast_finding",
            title=f"{rule_name}: {message}"[:100],
            description=description,
            metadata=metadata
        )
    
    def _extract_taint_flows(self, code_flows: List[Dict], repo_path: str) -> List[Dict]:
        """Extract taint flow information from SARIF codeFlows."""
        flows = []
        
        for flow_idx, code_flow in enumerate(code_flows):
            thread_flows = code_flow.get("threadFlows", [])
            
            for thread_idx, thread_flow in enumerate(thread_flows):
                locations = thread_flow.get("locations", [])
                
                if not locations:
                    continue
                
                flow_steps = []
                
                for step_idx, location in enumerate(locations):
                    loc_data = location.get("location", {})
                    physical_loc = loc_data.get("physicalLocation", {})
                    artifact_loc = physical_loc.get("artifactLocation", {})
                    region = physical_loc.get("region", {})
                    
                    # Extract file path
                    file_uri = artifact_loc.get("uri", "")
                    if file_uri.startswith("file://"):
                        file_path = file_uri[7:]
                    else:
                        file_path = file_uri
                    
                    # Make path relative to repo
                    if os.path.isabs(file_path) and file_path.startswith(repo_path):
                        rel_path = os.path.relpath(file_path, repo_path)
                    else:
                        rel_path = file_path
                    
                    # Extract location details
                    step = {
                        "step_id": loc_data.get("id", step_idx),
                        "file": rel_path,
                        "line": region.get("startLine", 1),
                        "end_line": region.get("endLine", region.get("startLine", 1)),
                        "column": region.get("startColumn"),
                        "end_column": region.get("endColumn"),
                        "step_index": step_idx
                    }
                    
                    # Add step message if available
                    if "message" in loc_data:
                        step["message"] = loc_data["message"].get("text", "")
                    
                    # Add step kind/importance if available
                    if "kinds" in loc_data:
                        step["kinds"] = loc_data["kinds"]
                    
                    flow_steps.append(step)
                
                if flow_steps:
                    flows.append({
                        "flow_id": flow_idx,
                        "thread_id": thread_idx,
                        "steps": flow_steps,
                        "step_count": len(flow_steps)
                    })
        
        return flows
