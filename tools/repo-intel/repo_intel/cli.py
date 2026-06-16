
"""
repo-intel CLI

A context engine that answers: "Where should I start auditing this repo?"
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from repo_intel.engine import ContextEngine
from repo_intel.modules import get_available_modules, get_module, get_module_categories
from repo_intel.server import start_server, update_scan_progress
from repo_intel.core.llm_triage import LLMTriageManager
from repo_intel.core.ai_threat_model import AIThreatModelGenerator


def run_auto_triage(output_dir, args):
    if not args.auto_triage:
        return

    # Load config from file if provided
    config = {}
    if args.triage_config:
        try:
            with open(args.triage_config, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[!] Error loading triage config: {e}")
            return

    # Override with CLI args
    if args.provider: config["provider"] = args.provider
    if args.api_key: config["api_key"] = args.api_key
    if args.model: config["model"] = args.model
    if args.prompt: config["prompt"] = args.prompt

    if not config.get("provider"):
        print("[!] Auto-triage requires --provider (or config file)")
        return
        
    try:
        manager = LLMTriageManager(output_dir, config)
        manager.run()
    except Exception as e:
        print(f"[!] Auto-triage failed: {e}")


def run_threat_model_generation(output_dir, args):
    if not args.generate_threat_model:
        return

    # Load config from file if provided
    config = {}
    if args.threat_model_config:
        try:
            with open(args.threat_model_config, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[!] Error loading threat model config: {e}")
            return

    # Override with CLI args
    if args.provider: config["provider"] = args.provider
    if args.api_key: config["api_key"] = args.api_key
    if args.model: config["model"] = args.model
    
    if not config.get("provider"):
        print("[!] Threat Model Generation requires --provider (or config file)")
        return

    try:
        generator = AIThreatModelGenerator(output_dir, config)
        generator.run()
    except Exception as e:
        print(f"[!] Threat Model Generation failed: {e}")


def list_modules():
    """List all available signal modules and categories."""
    modules = get_available_modules()
    categories = get_module_categories()
    
    print("\n" + "=" * 50)
    print("repo-intel: Available Signal Modules")
    print("=" * 50)
    
    print("\nCategories (Aliases):")
    for cat, mods in categories.items():
        print(f"  [{cat}]: {', '.join(mods)}")
    
    print("\nIndividual Modules:")
    for name, cls in modules.items():
        print(f"  [{name}]")
        print(f"  {cls.description}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="repo-intel: Where should I start reviewing this repo?",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  repo-intel https://github.com/lodash/lodash
  repo-intel --modules github_commits_analyse,github_issues_analyse --github-token TOKEN https://github.com/org/repo
  repo-intel --list-modules
  repo-intel --modules sources,extractors
        """
    )
    parser.add_argument("target", nargs="?", help="Repo URL to scan OR path to findings to view.")
    parser.add_argument("--target", dest="target_opt", help="Repo URL to scan (alternative to positional argument).")
    parser.add_argument("-o", "--output-dir", help="Output directory (default: findings/{repo}).", default=None)
    parser.add_argument("--modules", help="Comma-separated modules or categories to run (default: all). Use --list-modules to see options.", default="all")
    parser.add_argument("--list-modules", help="List available signal modules and exit.", action="store_true")
    parser.add_argument("--github-token", help="GitHub API token (required for github module).", default=None)
    parser.add_argument("--throttle", help="Delay in seconds between API calls.", type=float, default=None)
    parser.add_argument("--config", action="append", help="Module configuration in key=value format (e.g. --config commits_limit=5000).", default=[])
    parser.add_argument("--sarif-file", help="Path to specific SARIF file for sast_findings module.", default=None)
    parser.add_argument("--serve", help="Start local dashboard server.", action="store_true")
    
    # Auto-triage args
    parser.add_argument("--auto-triage", help="Run LLM-based auto-triage on findings.", action="store_true")
    parser.add_argument("--triage-config", help="Path to JSON config file for auto-triage (provider, key, model, prompt).", default=None)
    
    # Threat Model args
    parser.add_argument("--generate-threat-model", help="Generate an AI-based threat model from findings and docs.", action="store_true")
    parser.add_argument("--threat-model-config", help="Path to JSON config file for threat model generation.", default=None)

    # Shared LLM args
    parser.add_argument("--provider", help="LLM provider (openai, gemini, ollama).", default=None)
    parser.add_argument("--api-key", help="API key for the LLM provider.", default=None)
    parser.add_argument("--model", help="LLM model name.", default=None)
    parser.add_argument("--prompt", help="Custom prompt template.", default=None)
    parser.add_argument("--force", help="Force re-scan even if findings exist.", action="store_true")

    args = parser.parse_args()
    
    # Handle --list-modules
    if args.list_modules:
        list_modules()
        return
    
    # Determine target
    target = args.target_opt or args.target
    
    # Require target
    if not target:
        parser.error("target (URL or path) is required")
        
    # Check for View Mode (serving existing findings)
    if os.path.isdir(target) and os.path.exists(os.path.join(target, "context.json")):
        print(f"[*] Viewing findings from {target}")
        if args.auto_triage:
            run_auto_triage(target, args)
        
        if args.generate_threat_model:
            run_threat_model_generation(target, args)

        start_server(target)
        return
    
    print()
    print("=" * 60)
    print("  repo-intel")
    print("  \"signal-driven miner for security code review.\"")
    print("=" * 60)
    print()
    
    # Create the context engine
    engine = ContextEngine(target, output_dir=args.output_dir)
    
    # Check for existing findings to skip re-scan
    context_path = os.path.join(engine.output_dir, "context.json")
    if os.path.exists(context_path) and not args.force:
        print(f"[*] Found existing findings at {engine.output_dir}")
        print("    Skipping scan. Use --force to re-scan.")
        
        if args.auto_triage:
            run_auto_triage(engine.output_dir, args)
            
        if args.generate_threat_model:
            run_threat_model_generation(engine.output_dir, args)

        if args.serve:
            build_frontend_if_needed()
            start_server(engine.output_dir)
            
        return
    
    # Configure engine
    config = {}
    if args.github_token:
        config["github_token"] = args.github_token
    if args.throttle:
        config["throttle"] = args.throttle
    if args.sarif_file:
        config["sarif_file"] = args.sarif_file
    
    # Parse generic config
    for cfg in args.config:
        if "=" in cfg:
            key, val = cfg.split("=", 1)
            # Try to convert to int/float if possible
            if val.isdigit():
                val = int(val)
            else:
                try:
                    val = float(val)
                except ValueError:
                    pass # Keep as string
            config[key] = val
            
    engine.set_config(**config)
    
    # Determine which modules to run
    available = get_available_modules()
    categories = get_module_categories()
    
    if args.modules == "all":
        modules_to_run = list(available.keys())
    else:
        raw_list = [m.strip() for m in args.modules.split(",")]
        modules_to_run = []
        for item in raw_list:
            if item in categories:
                modules_to_run.extend(categories[item])
            else:
                modules_to_run.append(item)
        
        # Deduplicate
        modules_to_run = list(set(modules_to_run))

    # Smart Selection Logic: Check dependencies
    # Since we returned early if in view mode, we are definitely scanning here.
    enricher_modules = set(categories.get("enrichers", []))
    producer_modules = set(categories.get("sources", []) + categories.get("extractors", []))
    
    selected_enrichers = [m for m in modules_to_run if m in enricher_modules]
    selected_producers = [m for m in modules_to_run if m in producer_modules]
    
    if selected_enrichers and not selected_producers:
        print("\n[!] Error: You selected only 'enrichers' (e.g. exploits).")
        print("    These modules require finding data from 'sources' or 'extractors' to work.")
        print("\n    Did you mean: --modules extractors,enrichers")
        print("    Or run with 'all' (default).")
        sys.exit(1)
    
    # Add modules to engine
    for module_name in modules_to_run:
        module_cls = get_module(module_name)
        if not module_cls:
            print(f"[!] Unknown module: {module_name}")
            continue
        
        # Skip github related modules if no token
        if module_name in ["github_issues_analyse", "github_prs_analyse", "github_releases_analyse"] and not args.github_token:
            print(f"[!] Skipping {module_name} module (requires --github-token)")
            continue
        
        try:
            module = module_cls(**config)
            engine.add_module(module)
        except Exception as e:
            print(f"[!] Error initializing {module_name}: {e}")
    
    # Run the engine with progress tracking
    def progress_callback(progress_data):
        """Callback to update scan progress and broadcast via server."""
        # Show progress on a new line to avoid conflicts with module output
        if progress_data['status'] == 'running':
            # Only show progress if we've moved to a new module or significant progress
            current_time = time.time()
            if not hasattr(progress_callback, 'last_module'):
                progress_callback.last_module = None
                progress_callback.last_time = 0
            
            if (progress_data['current_module'] != progress_callback.last_module or 
                current_time - progress_callback.last_time > 2):  # Show every 2 seconds max
                print(f"[{progress_data['progress_percent']:.1f}%] {progress_data['current_step']}")
                progress_callback.last_module = progress_data['current_module']
                progress_callback.last_time = current_time
        elif progress_data['status'] == 'completed':
            print(f"[*] Scan completed in {progress_data['elapsed_time']:.1f}s - {progress_data['findings_count']} findings")
        elif progress_data['status'] == 'error':
            print(f"[!] Scan failed: {progress_data['error_message']}")
        
        # Update server progress for real-time updates
        update_scan_progress(progress_data)
    
    context = engine.run(progress_callback=progress_callback)
    
    # Print summary
    print()
    print(f"Full results: {engine.output_dir}/context.json")
    print(f"Audit guide:  {engine.output_dir}/audit_start.md")
    print(f"Dashboard:    {engine.output_dir}/dashboard.html")
    print()
    
    if args.auto_triage:
        run_auto_triage(engine.output_dir, args)

    if args.generate_threat_model:
        run_threat_model_generation(engine.output_dir, args)

    if args.serve:
        build_frontend_if_needed()
        start_server(engine.output_dir)

def build_frontend_if_needed():
    """Builds the Svelte frontend if source is available."""
    # Logic: If we are in a source checkout (frontend dir exists), try to build.
    # This ensures the user sees the latest changes.
    frontend_dir = os.path.join(os.path.dirname(__file__), "dashboard", "frontend")
    dist_dir = os.path.join(os.path.dirname(__file__), "dashboard", "dist")
    
    if not os.path.exists(frontend_dir):
        return # Likely an installed package without source
        
    # Check if already built
    if os.path.exists(dist_dir) and os.path.exists(os.path.join(dist_dir, "index.html")):
        # Could check mtime here, but for now assume if dist exists, we are good.
        # User can delete dist to force rebuild.
        return

    # Check if npm is available
    if not shutil.which("npm"):
        if not os.path.exists(dist_dir):
            print("[!] Warning: Dashboard frontend source found but 'npm' is missing.")
            print("    The dashboard may not work if 'dist' is missing.")
        return

    print("[*] Building Dashboard Frontend...")
    try:
        # We assume dependencies are installed or user handles it. 
        # But for robustness, we could run 'npm install' if node_modules missing.
        if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
            print("    Installing dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, capture_output=False) # Show output
            
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, capture_output=False)
        print("    Build complete.")
    except Exception as e:
        print(f"    [!] Build failed: {e}")
        print("    Proceeding with existing assets if available.")

if __name__ == "__main__":
    main()
