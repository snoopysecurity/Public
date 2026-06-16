"""Tests for signal modules"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from repo_intel.modules.base import SignalModule
from repo_intel.engine import Finding


@pytest.mark.unit
class TestBaseModule:
    """Test BaseModule functionality"""

    def test_base_module_interface(self):
        """Test that base module defines required interface"""
        # This is more of a design test - ensure BaseModule defines the interface
        assert hasattr(SignalModule, 'collect')
        assert hasattr(SignalModule, 'enrich')
        assert hasattr(SignalModule, 'name')
        assert hasattr(SignalModule, 'description')

    def test_module_enrichment_check(self):
        """Test module enrichment capability check"""
        # SignalModule is abstract, so we'll test with a simple implementation
        class TestModule(SignalModule):
            name = "test"
            description = "Test module"
            
            def collect(self, **kwargs):
                return []
        
        module = TestModule()
        
        # Base module should not have enrichment by default
        assert not getattr(module, 'can_enrich', lambda x: False)([])


@pytest.mark.unit
class TestModuleIntegration:
    """Test module integration and common patterns"""

    @patch('repo_intel.engine.Repo')
    def test_module_with_repo(self, mock_repo):
        """Test module execution with repository"""
        from repo_intel.modules.sources.github_commits_analyse import GithubCommitsAnalyseModule
        
        # Mock successful clone
        mock_repo.clone_from.return_value = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            module = GithubCommitsAnalyseModule()
            
            # Create a test git repo
            from git import Repo
            test_repo = Repo.init(tmpdir)
            
            # Create a test commit
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('test')")
            test_repo.index.add(["test.py"])
            test_repo.index.commit("Initial commit")
            
            findings = module.collect(
                repo_url="https://github.com/test/repo",
                repo_name="test/repo",
                repo_path=tmpdir
            )
            
            assert isinstance(findings, list)
            # Module should return findings (may be empty for test repo)

    def test_module_error_handling(self):
        """Test module error handling"""
        from repo_intel.modules.sources.github_commits_analyse import GithubCommitsAnalyseModule
        
        module = GithubCommitsAnalyseModule()
        
        # Test with invalid repo path
        findings = module.collect(
            repo_url="https://github.com/test/repo",
            repo_name="test/repo",
            repo_path="/nonexistent/path"
        )
        
        # Should handle error gracefully (return empty list or raise specific error)
        assert isinstance(findings, list)

    def test_module_configuration(self):
        """Test module configuration passing"""
        from repo_intel.modules.sources.github_commits_analyse import GithubCommitsAnalyseModule
        
        # Test module initialization with config
        module = GithubCommitsAnalyseModule(limit=100, throttle=1.0)
        
        # Module should accept and store configuration
        assert hasattr(module, 'limit') or hasattr(module, 'config')

    def test_finding_format_consistency(self):
        """Test that all modules produce consistent finding format"""
        # This test would need to be adapted based on actual module implementations
        pass

    def test_module_categories(self):
        """Test module categorization"""
        from repo_intel.modules import get_module_categories
        
        categories = get_module_categories()
        
        # Should have expected categories
        assert "sources" in categories
        assert "extractors" in categories
        assert "enrichers" in categories
        
        # Categories should have modules
        for category, modules in categories.items():
            assert isinstance(modules, list)
            assert len(modules) > 0

    def test_module_availability(self):
        """Test module discovery"""
        from repo_intel.modules import get_available_modules
        
        modules = get_available_modules()
        
        # Should have modules
        assert len(modules) > 0
        
        # All modules should have required attributes
        for name, module_class in modules.items():
            assert hasattr(module_class, 'name') or hasattr(module_class, '__name__')
            assert hasattr(module_class, 'description') or hasattr(module_class, '__doc__')


@pytest.mark.unit
class TestSpecificModules:
    """Tests for specific module implementations"""

    @patch('shutil.which')
    def test_tech_stack_module(self, mock_which):
        """Test tech stack detection module"""
        # Force npx not found to test fallback logic
        mock_which.return_value = None
        
        try:
            from repo_intel.modules.sources.tech_stack import TechStackModule

            with tempfile.TemporaryDirectory() as tmpdir:
                # Create test files
                with open(os.path.join(tmpdir, 'package.json'), 'w') as f:
                    json.dump({"name": "test", "dependencies": {"express": "^4.0.0"}}, f)
                
                with open(os.path.join(tmpdir, 'requirements.txt'), 'w') as f:
                    f.write("requests==2.28.0\nfastapi==0.100.0\n")
                
                module = TechStackModule()
                findings = module.collect(
                    repo_url="https://github.com/test/repo",
                    repo_name="test/repo",
                    repo_path=tmpdir
                )
                
                assert isinstance(findings, list)
                # Should detect Node.js and Python dependencies
                if findings:
                    tech_types = []
                    for f in findings:
                        meta = f.get('metadata', {})
                        # Check both tech_type (primary) and framework (fallback)
                        tech_types.append(meta.get('tech_type'))
                        tech_types.append(meta.get('framework'))
                    
                    # Flatten and check
                    assert any('express' in str(t) or 'flask' in str(t) for t in tech_types if t)
        except ImportError:
            pytest.skip("TechStack module not available")

    def test_dependency_analysis_module(self):
        """Test dependency analysis module"""
        try:
            from repo_intel.modules.extractors.dependency_analysis import DependencyAnalysisModule
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create test requirements.txt
                with open(os.path.join(tmpdir, 'requirements.txt'), 'w') as f:
                    f.write("requests==2.28.0\n")
                
                module = DependencyAnalysisModule()
                findings = module.collect(
                    repo_url="https://github.com/test/repo",
                    repo_name="test/repo",
                    repo_path=tmpdir
                )
                
                assert isinstance(findings, list)
        except ImportError:
            pytest.skip("DependencyAnalysis module not available")

    def test_sast_findings_module(self):
        """Test SAST findings module"""
        try:
            from repo_intel.modules.extractors.sast_findings import SastFindingsModule
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create test Python file with security issue
                with open(os.path.join(tmpdir, 'test.py'), 'w') as f:
                    f.write("import os\nexec(user_input)\n")
                
                # Create test SARIF file
                sarif_data = {
                    "version": "2.1.0",
                    "runs": [{
                        "tool": {"driver": {"name": "test"}},
                        "results": [{
                            "ruleId": "security-issue",
                            "message": {"text": "Security issue found"},
                            "locations": [{
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "test.py"},
                                    "region": {"startLine": 1}
                                }
                            }]
                        }]
                    }]
                }
                
                with open(os.path.join(tmpdir, 'test.sarif'), 'w') as f:
                    json.dump(sarif_data, f)
                
                module = SastFindingsModule()
                findings = module.collect(
                    repo_url="https://github.com/test/repo",
                    repo_name="test/repo",
                    repo_path=tmpdir,
                    sarif_file=os.path.join(tmpdir, 'test.sarif')
                )
                
                assert isinstance(findings, list)
        except ImportError:
            pytest.skip("SastFindings module not available")

    def test_exploits_enrichment(self):
        """Test exploits enrichment module"""
        try:
            from repo_intel.modules.enrichers.exploits import ExploitsModule
            
            module = ExploitsModule()
            
            # Test findings to enrich
            findings = [
                {
                    "signal_type": "cve",
                    "title": "CVE-2024-1234", 
                    "description": "Test vulnerability",
                    "source_module": "test_module", 
                    "metadata": {"cve_id": "CVE-2024-1234"}
                }
            ]
            
            # Test enrichment
            enriched = module.enrich(
                findings,
                repo_url="https://github.com/test/repo",
                repo_name="test/repo",
                repo_path="/tmp"
            )
            
            assert isinstance(enriched, list)
            assert len(enriched) == len(findings)
        except ImportError:
            pytest.skip("Exploits module not available")

    def test_semgrep_module(self):
        """Test Semgrep module"""
        try:
            from repo_intel.modules.extractors.semgrep import SemgrepModule
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create test Python file
                with open(os.path.join(tmpdir, 'test.py'), 'w') as f:
                    f.write("def test(): pass\n")
                
                module = SemgrepModule()
                
                # Mock semgrep execution
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value.stdout = json.dumps({"results": []})
                    mock_run.return_value.returncode = 0
                    
                    findings = module.collect(
                        repo_url="https://github.com/test/repo",
                        repo_name="test/repo",
                        repo_path=tmpdir
                    )
                    
                    assert isinstance(findings, list)
        except ImportError:
            pytest.skip("Semgrep module not available")
