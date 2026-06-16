
import pytest
from unittest.mock import MagicMock, patch
from repo_intel.modules.extractors.unreleased_fix_detector import UnreleasedFixDetectorModule

class TestUnreleasedFixDetector:
    
    def test_can_enrich(self):
        module = UnreleasedFixDetectorModule()
        
        # Test 1: CVE from github_commits_analyse -> True
        findings_cve = [{
            "signal_type": "cve", 
            "source_module": "github_commits_analyse"
        }]
        assert module.can_enrich(findings_cve) is True

        # Test 2: Security Keyword (High Confidence) -> True
        findings_keyword_high = [{
            "signal_type": "security_keyword", 
            "confidence": "high",
            "source_module": "github_commits_analyse"
        }]
        assert module.can_enrich(findings_keyword_high) is True
        
        # Test 3: Security Keyword (Low Confidence) -> False
        findings_keyword_low = [{
            "signal_type": "security_keyword", 
            "confidence": "low",
            "source_module": "github_commits_analyse"
        }]
        assert module.can_enrich(findings_keyword_low) is False

        # Test 4: Other module -> False
        findings_other = [{
            "signal_type": "cve", 
            "source_module": "other_module"
        }]
        assert module.can_enrich(findings_other) is False

    @patch('repo_intel.modules.extractors.unreleased_fix_detector.Repo')
    def test_enrich_logic(self, mock_repo_cls):
        module = UnreleasedFixDetectorModule()
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        
        # Setup findings
        findings = [
            {
                "signal_type": "cve",
                "source_module": "github_commits_analyse",
                "title": "CVE-2023-1234",
                "metadata": {"commit_hash": "aaa111", "cve_id": "CVE-2023-1234"}
            },
            {
                "signal_type": "security_keyword",
                "confidence": "high",
                "source_module": "github_commits_analyse",
                "title": "RCE Fix",
                "metadata": {"commit_hash": "bbb222"}
            },
             {
                "signal_type": "security_keyword",
                "confidence": "low",
                "source_module": "github_commits_analyse",
                "title": "TODO fix",
                "metadata": {"commit_hash": "ccc333"}
            }
        ]
        
        # Mock git.tag behavior
        def git_tag_side_effect(contains=None, sort=None):
            if contains == "aaa111": # Released
                return "v1.0.0\nv1.1.0"
            if contains == "bbb222": # Unreleased
                return ""
            return ""
            
        mock_repo.git.tag.side_effect = git_tag_side_effect
        
        # Run enrich
        enriched = module.enrich(findings, repo_path="/tmp/test")
        
        # Check Finding 1 (CVE Released)
        # Severity is not changed for released findings in the new static model
        assert "✅ Fixed: CVE-2023-1234" in enriched[0]["title"]
        assert enriched[0]["metadata"]["status"] == "released"
        
        # Check Finding 2 (Keyword Unreleased)
        assert enriched[1]["severity"] == "critical"
        assert "⚠️ Unreleased Fix: RCE Fix" in enriched[1]["title"]
        assert enriched[1]["metadata"]["status"] == "unreleased"
        
        # Check Finding 3 (Low confidence - should be untouched)
        assert "severity" not in enriched[2]
