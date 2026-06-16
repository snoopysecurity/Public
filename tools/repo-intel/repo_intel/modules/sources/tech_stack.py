"""Tech Stack Identifier Module."""

"""
__Logic:__

- It identifies the technology stack, frameworks, and dependencies of the repository.
- **Primary Analysis:** Uses `@specfy/stack-analyser` via `npx` for deep analysis of the project structure.
- **Fallback Analysis:** If `npx` is unavailable, uses file-existence heuristics (e.g., checking for `package.json`, `manage.py`, `pom.xml`) to identify common frameworks like React, Django, Flask, etc.
- **Signal Generation:** Produces informational findings detailing the detected languages, frameworks, and dependencies.
"""

import os
import json
import time
import shutil
import subprocess
import tempfile
from repo_intel.modules.base import SignalModule, register_module

@register_module
class TechStackModule(SignalModule):
    """Identifies frameworks and technologies using @specfy/stack-analyser."""
    
    name = "tech_stack_analysis"
    description = "Identifies technologies, frameworks, and dependencies"

    def get_scores(self):
        return {
            "confidence_score": 10,
            "research_value": 1,
            "impact_score": 1
        }
    
    def collect(self, repo_url, repo_name, repo_path=None, **kwargs):
        findings = []
        if not repo_path:
            return findings
            
        print(f"    Identifying tech stack using @specfy/stack-analyser...")
        
        # Check if npx is available
        if not shutil.which("npx"):
            print("      [!] npx not found. Please install Node.js/npx to use the full power of this module.")
            print("      [!] Falling back to basic file existence heuristics.")
            return self._collect_fallback(repo_path)
            
        try:
            # Create a temporary file for output (use relative path as stack-analyser seems to prepend CWD)
            output_file = f"stack_analysis_{int(time.time())}.json"
            
            # Run stack-analyser
            # Use -y to accept npx prompts
            cmd = ["npx", "-y", "@specfy/stack-analyser", repo_path, f"--output={output_file}"]
            
            # Run quietly
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                # Process the JSON data
                findings = self._process_stack_data(data, repo_path)
                
                # Cleanup
                os.unlink(output_file)
            else:
                print("      [!] stack-analyser produced no output.")
                return self._collect_fallback(repo_path)
                
        except subprocess.CalledProcessError as e:
            print(f"      [!] stack-analyser failed: {e}")
            if e.stderr: print(f"      [!] stderr: {e.stderr}")
            if e.stdout: print(f"      [!] stdout: {e.stdout}")
            return self._collect_fallback(repo_path)
        except Exception as e:
            print(f"      [!] Error running stack-analyser: {e}")
            return self._collect_fallback(repo_path)
            
        return findings

    def _process_stack_data(self, data, repo_path):
        """Recursively process the stack data components."""
        findings = []
        
        def traverse(component):
            # If component has significant techs or dependencies, create a finding
            if component.get("techs") or component.get("dependencies") or component.get("tech"):
                findings.append(self._create_finding_for_component(component, repo_path))
            
            # Recurse children
            for child in component.get("childs", []):
                traverse(child)
                
        traverse(data)
        return findings

    def _create_finding_for_component(self, component, repo_path):
        name = component.get("name", "Unknown")
        techs = component.get("techs", [])
        deps = component.get("dependencies", [])
        langs = component.get("languages", {})
        licenses = component.get("licenses", [])
        main_tech = component.get("tech")
        paths = component.get("path", [])
        
        # Determine target path relative to repo root
        target_path = "Repo Root"
        if paths:
            first_path = paths[0]
            if repo_path and first_path.startswith(repo_path):
                rel = os.path.relpath(first_path, repo_path)
                target_path = rel if rel != "." else "Repo Root"
            elif first_path.startswith("/"):
                 # Try to use basename if path is absolute but not in repo (e.g. docker mounts)
                 target_path = os.path.basename(first_path)
            else:
                target_path = first_path

        # Generate description
        desc_lines = []
        if main_tech:
            desc_lines.append(f"**Main Tech**: {main_tech}")
            
        if techs:
            desc_lines.append(f"**Technologies**: {', '.join(techs)}")
            
        if langs:
            # Sort languages by count descending
            sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)
            top_langs = [f"{l[0]}" for l in sorted_langs[:5]]
            desc_lines.append(f"**Languages**: {', '.join(top_langs)}")
            
        if licenses:
            desc_lines.append(f"**Licenses**: {', '.join(licenses)}")
        
        if deps:
            desc_lines.append(f"**Dependencies ({len(deps)})**:")
            for dep in deps[:10]:
                # Dep format: [ecosystem, name, version]
                if isinstance(dep, list) and len(dep) >= 2:
                    eco = f"[{dep[0]}] " if dep[0] else ""
                    desc_lines.append(f"- {eco}{dep[1]} ({dep[2] if len(dep)>2 else '?'})")
            if len(deps) > 10:
                desc_lines.append(f"- ... and {len(deps)-10} more")

        return self._make_finding(
            signal_type="tech_stack_analysis",
            title=f"Stack: {name}",
            description="\n".join(desc_lines),
            metadata={
                "component": name,
                "path": target_path,
                "techs": techs,
                "languages": langs,
                "licenses": licenses,
                "dependencies": deps,
                "raw_component": component
            }
        )

    def _collect_fallback(self, repo_path):
        """Original heuristic collection logic."""
        findings = []
        stack_signals = {
            "django": {"files": ["manage.py", "django-admin.py"], "content": ["from django", "import django"]},
            "flask": {"files": ["app.py", "wsgi.py"], "content": ["from flask", "import flask"]},
            "react": {"files": ["package.json"], "content": ["react", "react-dom"], "ext": [".jsx", ".tsx"]},
            "spring": {"files": ["pom.xml", "build.gradle"], "content": ["org.springframework"]},
            "express": {"files": ["package.json"], "content": ["express"]},
        }
        
        detected = set()
        
        # 1. File existence check
        for tech, rules in stack_signals.items():
            for f in rules.get("files", []):
                if os.path.exists(os.path.join(repo_path, f)):
                    if f == "package.json":
                        try:
                            with open(os.path.join(repo_path, f)) as pf:
                                content = pf.read()
                                if any(c in content for c in rules.get("content", [])):
                                    detected.add(tech)
                        except: pass
                    else:
                        detected.add(tech)
        
        # 2. Extension check
        for root, _, files in os.walk(repo_path):
            if root[len(repo_path):].count(os.sep) > 2:
                continue
            for file in files:
                for tech, rules in stack_signals.items():
                    if tech not in detected:
                         if any(file.endswith(ext) for ext in rules.get("ext", [])):
                             detected.add(tech)
        
        for tech in detected:
            related_files = []
            rules = stack_signals.get(tech, {})
            for f in rules.get("files", []):
                if os.path.exists(os.path.join(repo_path, f)):
                    related_files.append(f)
            
            findings.append(self._make_finding(
                signal_type="tech_stack_analysis",
                title=f"Detected {tech.title()} Framework",
                description=f"This appears to be a {tech.title()} application.",
                metadata={
                    "framework": tech,
                    "keyword": tech,
                    "files": related_files
                }
            ))
        return findings
