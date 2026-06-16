# Auto-import all modules to trigger registration
from repo_intel.modules.sources import github_commits_analyse
from repo_intel.modules.sources import github_issues
from repo_intel.modules.sources import github_releases
from repo_intel.modules.sources import github_prs
from repo_intel.modules.sources import github_labels
from repo_intel.modules.sources import tech_stack
from repo_intel.modules.sources import contributors

from repo_intel.modules.extractors import semgrep_file_analysis
from repo_intel.modules.extractors import semgrep_code_intel
from repo_intel.modules.extractors import dependency_analysis
from repo_intel.modules.extractors import sast_findings
from repo_intel.modules.extractors import unreleased_fix_detector

from repo_intel.modules.enrichers import exploits

from repo_intel.modules.base import (
    SignalModule,
    register_module,
    get_available_modules,
    get_module,
)

# Define Module Categories
MODULE_CATEGORIES = {
    "sources": [
        "github_commits_analyse", 
        "github_issues_analyse", 
        "github_prs_analyse", 
        "github_releases_analyse", 
        "github_labels_analyse",
        "contributors", 
        "tech_stack_analysis"
    ],
    "extractors": [
        "sast_findings", 
        "semgrep_file_analysis", 
        "semgrep_code_intel",
        "dependency_analysis", 
        "unreleased_fix_detector"
    ],
    "enrichers": [
        "exploits"
    ]
}

def get_module_categories():
    return MODULE_CATEGORIES.copy()
