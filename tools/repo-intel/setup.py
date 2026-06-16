
from setuptools import setup, find_packages

setup(
    name="repo-intel",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "repo_intel": ["rules/semgrep/*.yml", "patterns/**/*.txt", "dashboard/template.html"],
    },
    entry_points={
        "console_scripts": [
            "repo-intel = repo_intel.cli:main",
        ],
    },
)
