
import pytest
from unittest.mock import MagicMock
from repo_intel.modules.base import SignalModule

class MockModule(SignalModule):
    name = "mock_module"
    def get_scores(self):
        return {
            "confidence_score": 9,
            "impact_score": 9,
            "research_value": 9
        }
    def collect(self, **kwargs): return []

class TestContextBlacklist:
    def test_context_downgrade(self):
        module = MockModule()
        
        # Test 1: Normal file -> High Severity (from module)
        finding_normal = module._make_finding(
            "test_signal", "Title", "Desc",
            metadata={"file": "src/main.py"}
        )
        # Base module sets severity to "medium" by default, Engine upgrades it later.
        assert finding_normal["severity"] == "medium"
        assert finding_normal["severity_score"] == 0.9
        
        # Test 2: Test file -> Info Severity (Context Downgrade)
        # using 'test/' which is in the blacklist
        finding_test = module._make_finding(
            "test_signal", "Title", "Desc",
            metadata={"file": "test/test_main.py"}
        )
        assert finding_test["severity"] == "info"
        assert finding_test["severity_score"] == 0.1
        
        # Check reason string
        reason = finding_test["metadata"].get("module_confidence_reason", "")
        assert "Filepath blacklist" in reason
        assert "test/" in reason
        
        # Test 3: Doc file -> Info Severity
        finding_doc = module._make_finding(
            "test_signal", "Title", "Desc",
            metadata={"files": ["docs/api.md"]}
        )
        assert finding_doc["severity"] == "info"
        assert finding_doc["severity_score"] == 0.1
