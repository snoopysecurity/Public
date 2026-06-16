"""Tests for ContextEngine functionality"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from repo_intel.engine import ContextEngine, Finding, AuditContext


@pytest.mark.unit
class TestFinding:
    """Test Finding class"""

    def test_finding_creation(self):
        """Test finding creation and to_dict conversion"""
        finding = Finding(
            signal_type="cve",
            title="CVE-2024-1234",
            description="Test vulnerability",
            source_module="test_module",
            severity="high",
            confidence="medium",
            metadata={"cve_id": "CVE-2024-1234", "files": ["test.py"]}
        )
        
        result = finding.to_dict()
        
        assert result["signal_type"] == "cve"
        assert result["title"] == "CVE-2024-1234"
        assert result["severity"] == "high"
        assert result["confidence"] == "medium"
        assert result["metadata"]["cve_id"] == "CVE-2024-1234"
        assert "timestamp" in result

    def test_finding_defaults(self):
        """Test finding default values"""
        finding = Finding(
            signal_type="test",
            title="Test",
            description="Test description",
            source_module="test"
        )
        
        assert finding.severity == "medium"
        assert finding.confidence == "medium"
        assert finding.metadata == {}
        assert finding.timestamp is not None


@pytest.mark.unit
class TestAuditContext:
    """Test AuditContext class"""

    def test_audit_context_creation(self):
        """Test audit context creation"""
        context = AuditContext("test/repo")
        
        assert context.repo == "test/repo"
        assert context.findings == []
        assert context.hotspots == []
        assert context.summary == {}
        assert context.modules_run == []
        assert context.scan_date is not None

    def test_add_finding(self):
        """Test adding findings to context"""
        context = AuditContext("test/repo")
        finding = Finding("test", "Test", "Test", "test")
        
        context.add_finding(finding)
        
        assert len(context.findings) == 1
        assert context.findings[0] == finding

    def test_add_findings(self):
        """Test adding multiple findings"""
        context = AuditContext("test/repo")
        findings = [
            Finding("test1", "Test1", "Test1", "test"),
            Finding("test2", "Test2", "Test2", "test")
        ]
        
        context.add_findings(findings)
        
        assert len(context.findings) == 2

    def test_to_dict(self):
        """Test context serialization"""
        context = AuditContext("test/repo")
        context.modules_run = ["test_module"]
        context.summary = {"total": 1}
        context.hotspots = [{"type": "test"}]
        
        finding = Finding("test", "Test", "Test", "test")
        context.add_finding(finding)
        
        result = context.to_dict()
        
        assert result["repo"] == "test/repo"
        assert result["modules_run"] == ["test_module"]
        assert result["summary"]["total"] == 1
        assert len(result["findings"]) == 1
        assert "scan_date" in result


@pytest.mark.unit
class TestContextEngine:
    """Test ContextEngine class"""

    def test_engine_creation(self):
        """Test engine creation"""
        engine = ContextEngine("https://github.com/test/repo")
        
        assert engine.repo_url == "https://github.com/test/repo"
        assert engine.repo_name == "test/repo"
        assert engine.output_dir == "findings/test_repo"
        assert engine.modules == []
        assert isinstance(engine.context, AuditContext)

    def test_parse_repo_name(self):
        """Test repository name parsing"""
        engine = ContextEngine("https://github.com/user/repo")
        assert engine.repo_name == "user/repo"
        
        engine = ContextEngine("http://github.com/user/repo.git")
        assert engine.repo_name == "user/repo"

    def test_custom_output_dir(self):
        """Test custom output directory"""
        engine = ContextEngine("https://github.com/test/repo", output_dir="/tmp/test")
        assert engine.output_dir == "/tmp/test"

    def test_add_module(self):
        """Test adding modules to engine"""
        engine = ContextEngine("https://github.com/test/repo")
        mock_module = Mock()
        
        engine.add_module(mock_module)
        
        assert len(engine.modules) == 1
        assert engine.modules[0] == mock_module

    def test_set_config(self):
        """Test setting configuration"""
        engine = ContextEngine("https://github.com/test/repo")
        
        engine.set_config(github_token="test_token", throttle=1.0)
        
        assert engine.config["github_token"] == "test_token"
        assert engine.config["throttle"] == 1.0

    @patch('repo_intel.engine.Repo')
    def test_clone_repo(self, mock_repo):
        """Test repository cloning"""
        engine = ContextEngine("https://github.com/test/repo")
        
        # Test successful clone
        mock_repo.clone_from.return_value = None
        with patch('os.path.exists', return_value=False):
            result = engine._clone_repo()
            expected_path = os.path.join(engine.output_dir, "source")
            mock_repo.clone_from.assert_called_once_with(engine.repo_url, expected_path)
            assert result == expected_path

    @patch('repo_intel.engine.Repo')
    def test_clone_repo_cached(self, mock_repo):
        """Test using cached repository"""
        engine = ContextEngine("https://github.com/test/repo")
        
        with patch('os.path.exists', return_value=True):
            result = engine._clone_repo()
            expected_path = os.path.join(engine.output_dir, "source")
            mock_repo.clone_from.assert_not_called()
            assert result == expected_path

    def test_build_summary(self):
        """Test summary building"""
        engine = ContextEngine("https://github.com/test/repo")
        
        # Add test findings
        findings = [
            Finding("cve", "CVE-1", "Test", "module1", "high"),
            Finding("keyword", "password", "Test", "module2", "medium"),
            Finding("cve", "CVE-2", "Test", "module1", "critical")
        ]
        
        for finding in findings:
            engine.context.add_finding(finding)
        
        engine._build_summary()
        
        summary = engine.context.summary
        assert summary["total_findings"] == 3
        assert summary["by_type"]["cve"] == 2
        assert summary["by_type"]["keyword"] == 1
        assert summary["by_severity"]["high"] == 1
        assert summary["by_severity"]["critical"] == 1
        assert summary["by_severity"]["medium"] == 1

    def test_identify_hotspots(self):
        """Test hotspot identification"""
        engine = ContextEngine("https://github.com/test/repo")
        
        # Add test findings with various signals
        findings = [
            Finding("cve", "CVE-2024-1234", "Test", "module1", "critical",
                   metadata={"cve_id": "CVE-2024-1234", "files": ["app.py"]},
                   confidence_score=0.9, severity_score=0.9, research_value=0.9),
            Finding("security_keyword", "password", "Test", "module2", "medium",
                   metadata={"keyword": "password", "files": ["app.py"]},
                   confidence_score=0.7, severity_score=0.5, research_value=0.5),
            Finding("github_issue", "Security issue", "Test", "module3", "high",
                   metadata={"files": ["app.py"]},
                   confidence_score=0.8, severity_score=0.7, research_value=0.6),
            Finding("security_keyword", "sql", "Test", "module2", "medium",
                   metadata={"keyword": "sql", "files": ["database.py"]},
                   confidence_score=0.6, severity_score=0.5, research_value=0.5)
        ]
        
        for finding in findings:
            engine.context.add_finding(finding)
        
        # Calculate scores before identifying hotspots
        engine._aggregate_module_scores()
        engine._identify_hotspots()
        
        hotspots = engine.context.hotspots
        assert len(hotspots) > 0
        
        # Should have a CVE hotspot
        cve_hotspots = [h for h in hotspots if h["type"] == "cve"]
        assert len(cve_hotspots) > 0
        assert cve_hotspots[0]["identifier"] == "CVE-2024-1234"
        
        # Should have a file hotspot for app.py (multiple signals)
        file_hotspots = [h for h in hotspots if h["type"] == "file" and h["identifier"] == "app.py"]
        assert len(file_hotspots) > 0

    def test_score_findings(self):
        """Test finding scoring logic"""
        engine = ContextEngine("https://github.com/test/repo")
        
        # Add test findings with pre-set scores (as modules would provide)
        # 1. High Score: Conf=1.0, Impact=1.0, Research=1.0 -> 1.0 * (1.0+1.0)/2 = 1.0 (100)
        f1 = Finding("test", "Test 1", "Test", "module1")
        f1.confidence_score = 1.0
        f1.severity_score = 1.0
        f1.research_value = 1.0
        
        # 2. Low Score: Conf=0.2, Impact=0.2, Research=0.0 -> 0.2 * (0.0+0.2)/2 = 0.02 (2)
        f2 = Finding("test", "Test 2", "Test", "module2")
        f2.confidence_score = 0.2
        f2.severity_score = 0.2
        f2.research_value = 0.0

        engine.context.add_finding(f1)
        engine.context.add_finding(f2)
        
        engine._aggregate_module_scores()
        
        assert f1.priority_score == 100
        assert f1.severity == "critical" # >= 80 is critical (if using priority map) or based on research value?
        # In engine.py: finding["severity"] = self._map_research_value_to_severity(u)
        # f1: u=1.0 -> critical
        assert f1.severity == "critical"
        
        assert f2.priority_score == 2
        # f2: u=0.0 -> low
        assert f2.severity == "low"

    @patch('repo_intel.engine.Repo')
    def test_run_engine(self, mock_repo):
        """Test full engine run"""
        engine = ContextEngine("https://github.com/test/repo")
        
        # Mock module
        mock_module = Mock()
        mock_module.name = "test_module"
        mock_module.collect.return_value = [
            Finding("test", "Test finding", "Test", "test_module").to_dict()
        ]
        # Mock enrichment to avoid issues
        mock_module.can_enrich.return_value = False
        engine.add_module(mock_module)
        
        # Mock repo clone
        mock_repo.clone_from.return_value = None
        
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs'):
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = MagicMock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    context = engine.run()
                    
                    assert isinstance(context, AuditContext)
                    assert len(context.findings) == 1
                    assert "test_module" in context.modules_run

    def test_save_results(self):
        """Test result saving"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ContextEngine("https://github.com/test/repo", output_dir=tmpdir)
            
            # Add test data
            finding_dict = Finding("test", "Test", "Test", "test").to_dict()
            engine.context.add_finding(finding_dict)
            engine.context.modules_run = ["test"]
            engine.context.summary = {"total": 1}
            engine.context.hotspots = [{
                "type": "test", 
                "identifier": "test", 
                "priority": "high", 
                "reason": "Test reason", 
                "start_here": "Test action"
            }]
            
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                engine._save_results()
                
                # Should have opened context.json, audit_start.md, and dashboard.html
                assert mock_open.call_count >= 3

    def test_save_markdown_summary(self):
        """Test markdown summary generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ContextEngine("https://github.com/test/repo")
            
            # Add test data
            finding_dict = Finding("test", "Test", "Test", "test").to_dict()
            engine.context.add_finding(finding_dict)
            engine.context.modules_run = ["test"]
            engine.context.summary = {"total_findings": 1, "by_type": {"test": 1}}
            engine.context.hotspots = [
                {"type": "test", "identifier": "test", "priority": "high", 
                 "reason": "Test reason", "start_here": "Test action"}
            ]
            
            summary_path = os.path.join(tmpdir, "test.md")
            engine._save_markdown_summary(summary_path)
            
            with open(summary_path, 'r') as f:
                content = f.read()
            
            assert "Audit Starting Points" in content
            assert "test/repo" in content
            assert "Total signals found:** 1" in content
            assert "test" in content
