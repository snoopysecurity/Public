import os
import json
from repo_intel.core.utils import calculate_finding_id
from repo_intel.core.llm_providers import create_provider

class LLMTriageManager:
    DEFAULT_PROMPT = """You are an expert Application Security Engineer.
Your goal is to triage static analysis findings to identify those that relate to **real security risks** or **meaningful security improvements**.
We want to keep findings that are valuable for further security study and insight, while filtering out noise.

Review the following finding:

=== Finding Details ===
Signal: $title
Description: $description
File: $file
Line: $line

=== Code Snippet ===
$snippet

=== Additional Context ===
$metadata

=== Analysis Instructions ===
1. Analyze the snippet and details.
2. Determine if this finding is a **True Positive (TP)** or **False Positive (FP)** based on the following criteria:
   - **TP (Keep)**: It is a real vulnerability, a risky coding practice, or a valid security improvement (e.g., defense-in-depth). It is worth a human's time to review.
   - **FP (Discard)**: It is obviously safe (sanitized), unreachable, irrelevant (e.g., distinct test logic with no security implication), or a misunderstanding of the tool.
3. Be concise but insightful.

Respond with strictly valid JSON:
{"status": "TP" or "FP", "reason": "concise explanation of the security value or why it is noise"}
"""

    def __init__(self, findings_dir, config):
        self.findings_dir = findings_dir
        self.config = config
        self.provider = self._init_provider()
        self.prompt_template = config.get("prompt", self.DEFAULT_PROMPT)

    def _init_provider(self):
        return create_provider(self.config.get("provider"), self.config)

    def run(self):
        context_path = os.path.join(self.findings_dir, "context.json")
        triage_path = os.path.join(self.findings_dir, "triage.json")
        
        if not os.path.exists(context_path):
            print("[!] context.json not found")
            return
            
        with open(context_path, "r") as f:
            context = json.load(f)
            
        triage_data = {}
        if os.path.exists(triage_path):
            try:
                with open(triage_path, "r") as f:
                    triage_data = json.load(f)
            except: pass
            
        findings = context.get("findings", [])
        print(f"[*] Starting auto-triage for {len(findings)} findings...")
        print(f"[*] Using provider: {self.config.get('provider')} | Model: {self.provider.model}")
        
        self.stats = {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0}
        count = 0
        
        try:
            for finding in findings:
                fid = calculate_finding_id(finding)
                
                # Skip if already triaged (unless we want to force? assume skip for now)
                if fid in triage_data and triage_data[fid] != "UNTRIAGED":
                    continue
                    
                # Prepare data
                meta = finding.get("metadata", {})
                file_path = meta.get("file", "unknown")
                line = meta.get("line", "unknown")
                snippet = meta.get("snippet")
                
                # If no snippet, try to read file
                if not snippet and file_path != "unknown":
                    snippet = self._read_snippet(file_path, line)
                    
                finding_data = {
                    "title": finding.get("title", ""),
                    "description": finding.get("description", ""),
                    "file": file_path,
                    "line": line,
                    "snippet": snippet or "No snippet available.",
                    "body": meta.get("body", ""),
                    "metadata": json.dumps(meta, indent=2)
                }
                
                try:
                    print(f"    Triaging: {finding.get('title')[:50]}...")
                    result, usage = self.provider.generate(finding_data, self.prompt_template, json_mode=True)
                    
                    # Update stats
                    self.stats["requests"] += 1
                    self.stats["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    self.stats["completion_tokens"] += usage.get("completion_tokens", 0)
                    
                    status = result.get("status", "").upper()
                    reason = result.get("reason", "")
                    
                    if status in ["TP", "FP"]:
                        triage_data[fid] = status
                        count += 1
                        
                        # Incremental save
                        try:
                            with open(triage_path, "w") as f:
                                json.dump(triage_data, f, indent=2)
                        except: pass
                    else:
                        print(f"    [!] Invalid status from LLM: {status}")
                        
                except Exception as e:
                    print(f"    [!] Error triaging finding: {e}")
                    
            # Final save
            with open(triage_path, "w") as f:
                json.dump(triage_data, f, indent=2)
                
            print(f"[*] Auto-triage complete. Updated {count} findings.")
            
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user.")
        finally:
            self._print_stats()

    def _print_stats(self):
        print("\n--- Triage Session Stats ---")
        print(f"Requests made: {self.stats['requests']}")
        print(f"Tokens used: Prompt={self.stats['prompt_tokens']}, Completion={self.stats['completion_tokens']}")
        print(f"Total tokens: {self.stats['prompt_tokens'] + self.stats['completion_tokens']}")

    def _read_snippet(self, file_path, line):
        try:
            full_path = os.path.join(self.findings_dir, "source", file_path)
            if not os.path.exists(full_path):
                return None
                
            if not (line and isinstance(line, int) and line > 0):
                return None
                
            start = max(0, line - 5)
            end = line + 5
            snippet_lines = []
            
            with open(full_path, "r", errors="ignore") as f:
                for i, file_line in enumerate(f):
                    if i >= start:
                        snippet_lines.append(file_line)
                    if i >= end:
                        break
            
            return "".join(snippet_lines) if snippet_lines else None
        except:
            return None
