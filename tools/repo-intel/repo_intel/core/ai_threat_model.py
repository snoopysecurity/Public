import os
import json
from repo_intel.core.utils import calculate_finding_id
from repo_intel.core.llm_providers import create_provider

class AIThreatModelGenerator:
    DEFAULT_PROMPT = """You are a Principal Security Architect.
Your task is to generate a Threat Model and a prioritized Security Audit Plan for a software project, based on its documentation and initial automated security findings.

=== Project Documentation ===
$documentation

=== Confirmed Security Findings ===
$findings

=== Instructions ===
Analyze the provided documentation and findings to understand the application's purpose, architecture, and risk profile.
Generate a response in Markdown format with the following sections:

## 1. Architecture & Data Flow
- **Overview**: High-level summary of what the application does.
- **Components**: Key components (frontend, backend, databases, queues, etc.).
- **Data Flow**: How data moves through the system (especially sensitive data).
- **Trust Boundaries**: Where are the edges of trust? (e.g., Internet vs Internal, User vs Admin).

## 2. Threat Landscape (STRIDE Analysis)
Identify top threats using the STRIDE model (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).
- Focus on threats specific to this application's business logic and architecture.

## 3. Risk Assessment
- **Critical Assets**: What needs most protection?
- **Known Weaknesses**: Summarize the impact of the confirmed security findings provided above.

## 4. Audit Plan & Recommendations
- **High Priority Areas**: Which components or code paths require manual code review?
- **Specific Test Cases**: List concrete security test cases to verify (e.g., "Attempt SQLi on login parameter", "Check for IDOR on user profile").
- **Strategic Fixes**: Systemic improvements (e.g., "Implement centralized auth", "Enable CSP").

Be specific to the provided context. Avoid generic security advice that applies to every application.
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
        source_dir = os.path.join(self.findings_dir, "source")
        output_path = os.path.join(self.findings_dir, "threat_model_plan.md")
        
        if not os.path.exists(context_path):
            print("[!] context.json not found")
            return

        print(f"[*] Generating AI Threat Model for {self.findings_dir}...")
        
        # 1. Gather TP Findings
        tp_findings = self._get_tp_findings(context_path, triage_path)
        print(f"[*] Found {len(tp_findings)} TP findings.")

        # 2. Gather Documentation
        docs_text = self._gather_documentation(source_dir)
        print(f"[*] Gathered {len(docs_text)} characters of documentation.")

        # 3. Construct Data
        findings_text = self._format_findings(tp_findings)
        
        data = {
            "documentation": docs_text,
            "findings": findings_text
        }
        
        # 4. Generate
        try:
            print(f"[*] Sending to LLM ({self.config.get('provider')})...")
            result, usage = self.provider.generate(data, self.prompt_template, json_mode=False)
            
            # 5. Save
            with open(output_path, "w") as f:
                f.write(result)
                
            print(f"[+] Threat model saved to: {output_path}")
            print(f"    Tokens used: {usage.get('total_tokens', 'unknown')}")
            
        except Exception as e:
            print(f"[!] Error generating threat model: {e}")

    def _get_tp_findings(self, context_path, triage_path):
        with open(context_path, "r") as f:
            context = json.load(f)
        
        all_findings = context.get("findings", [])
        
        triage_data = {}
        if os.path.exists(triage_path):
            try:
                with open(triage_path, "r") as f:
                    triage_data = json.load(f)
            except: pass
            
        tp_findings = []
        for finding in all_findings:
            fid = calculate_finding_id(finding)
            status = triage_data.get(fid)
            
            # If explicit TP, include
            if status == "TP":
                tp_findings.append(finding)
            # If no triage data exists at all, maybe we want to be permissive?
            # User said "look at all TP findings", so strict is better.
            
        return tp_findings

    def _gather_documentation(self, source_dir):
        if not os.path.exists(source_dir):
            return "No source code available."
            
        docs = []
        # Walk and find .md files
        for root, dirs, files in os.walk(source_dir):
            # Ignore common vendor/dist directories
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "vendor", "dist", "build", "venv", ".venv"]]
            
            for file in files:
                if file.lower().endswith(".md"):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, source_dir)
                    try:
                        with open(path, "r", errors="ignore") as f:
                            content = f.read(10000) # Limit per file
                            docs.append(f"--- File: {rel_path} ---\n{content}\n")
                    except: pass
        
        full_docs = "\n".join(docs)
        if len(full_docs) > 50000: # Global limit
             full_docs = full_docs[:50000] + "\n... (truncated)"
             
        return full_docs if full_docs else "No markdown documentation found."

    def _format_findings(self, findings):
        if not findings:
            return "No confirmed findings."
            
        lines = []
        for f in findings:
            meta = f.get('metadata', {})
            lines.append(f"- [{f.get('signal_type')}] {f.get('title')}")
            lines.append(f"  Description: {f.get('description')}")
            lines.append(f"  File: {meta.get('file', 'unknown')}")
            if meta.get('cwe'):
                 lines.append(f"  CWE: {meta.get('cwe')}")
            if meta.get('owasp'):
                 lines.append(f"  OWASP: {meta.get('owasp')}")
            lines.append("")
        return "\n".join(lines)
