"""Pytest configuration and fixtures"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_repo(temp_dir):
    """Create a sample repository structure for testing"""
    repo_path = os.path.join(temp_dir, "sample_repo")
    os.makedirs(repo_path)
    
    # Create sample files
    files = {
        "app.py": """
import os
import subprocess

def process_input(user_input):
    # Potential security issue
    os.system(f"echo {user_input}")
    return True

def main():
    pass
""",
        "config.json": json.dumps({
            "database": "sqlite:///app.db",
            "debug": True,
            "secret_key": "insecure-secret-key"
        }),
        "requirements.txt": "flask==2.0.0\nrequests==2.25.0\n",
        "package.json": json.dumps({
            "name": "test-app",
            "dependencies": {
                "express": "^4.0.0",
                "lodash": "^4.0.0"
            }
        }),
        "README.md": "# Test Repository\n\nThis is a test repository for security analysis."
    }
    
    for file_path, content in files.items():
        full_path = os.path.join(repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
    
    return repo_path


@pytest.fixture
def mock_module():
    """Create a mock module for testing"""
    module = Mock()
    module.name = "test_module"
    module.description = "Test module for unit testing"
    module.collect.return_value = []
    return module


@pytest.fixture
def mock_finding():
    """Create a mock finding for testing"""
    from repo_intel.engine import Finding
    
    return Finding(
        signal_type="test",
        title="Test Finding",
        description="This is a test finding",
        source_module="test_module",
        severity="medium",
        metadata={"test": True}
    )


@pytest.fixture
def sample_findings(mock_finding):
    """Create a list of sample findings"""
    from repo_intel.engine import Finding
    
    return [
        Finding("cve", "CVE-2024-1234", "Test vulnerability", "nvd_module", "critical",
               metadata={"cve_id": "CVE-2024-1234", "files": ["app.py"]}),
        Finding("security_keyword", "password", "Password handling", "pattern_module", "high",
               metadata={"files": ["config.json"], "keyword": "password"}),
        Finding("dependency", "flask", "Flask dependency", "deps_module", "medium",
               metadata={"tech_type": "python", "version": "2.0.0"}),
        mock_finding
    ]


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require network access)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add integration marker to integration tests
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)
