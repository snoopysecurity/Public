"""Integration tests for repo-intel"""

import pytest
import tempfile
import os
import json
import subprocess
from unittest.mock import Mock, patch
from repo_intel.engine import ContextEngine, Finding, AuditContext
from repo_intel.cli import main


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.integration
    def test_full_scan_workflow(self):
        """Test complete scan workflow with mocked modules"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test repository structure
            repo_path = os.path.join(tmpdir, "test_repo")
            os.makedirs(repo_path)
            
            # Create test files
            with open(os.path.join(repo_path, "app.py"), "w") as f:
                f.write("""
import os
import subprocess

def process_user_input(user_input):
    # Potential security issue
    os.system(f"echo {user_input}")
    
def connect_to_db():
    # Database connection
    pass
""")
            
            with open(os.path.join(repo_path, "package.json"), "w") as f:
                json.dump({
                    "name": "test-app",
                    "dependencies": {
                        "express": "^4.0.0",
                        "lodash": "^4.0.0"
                    }
                }, f)
            
            with open(os.path.join(repo_path, "requirements.txt"), "w") as f:
                f.write("requests==2.28.0\nfastapi==0.100.0\n")
            
            # Create engine
            engine = ContextEngine("https://github.com/test/repo", output_dir=tmpdir)
            
            # Add mock modules
            mock_module1 = Mock()
            mock_module1.name = "test_module1"
            mock_module1.collect.return_value = [
                Finding("security_keyword", "os.system", "Use of os.system", "test_module1", 
                       metadata={"files": ["app.py"], "keyword": "os.system"}).to_dict()
            ]
            
            mock_module2 = Mock()
            mock_module2.name = "test_module2"
            mock_module2.collect.return_value = [
                Finding("dependency", "express", "Express.js dependency", "test_module2",
                       metadata={"tech_type": "nodejs", "version": "^4.0.0"}).to_dict()
            ]
            
            # Mock enrichment to avoid issues
            mock_module1.can_enrich.return_value = False
            mock_module2.can_enrich.return_value = False
            
            engine.add_module(mock_module1)
            engine.add_module(mock_module2)
            
            # Mock repo cloning
            with patch('repo_intel.engine.Repo') as mock_repo:
                mock_repo.clone_from.return_value = None
                
                # Run scan
                context = engine.run()
                
                # Verify results
                assert isinstance(context, AuditContext)
                assert len(context.findings) == 2
                assert len(context.modules_run) == 2
                assert context.summary["total_findings"] == 2
                
                # Check output files
                assert os.path.exists(os.path.join(tmpdir, "context.json"))
                assert os.path.exists(os.path.join(tmpdir, "audit_start.md"))

    @pytest.mark.integration
    def test_cli_with_test_repo(self):
        """Test CLI with actual test repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use the test repo in the project
            test_repo_path = os.path.join(os.path.dirname(__file__), "..", "code_intel_test_repo")
            
            if os.path.exists(test_repo_path):
                # Mock modules to avoid external dependencies
                with patch('repo_intel.cli.get_available_modules') as mock_available:
                    with patch('repo_intel.cli.get_module_categories') as mock_categories:
                        with patch('repo_intel.cli.get_module') as mock_get_module:
                            # Setup minimal module
                            mock_available.return_value = {"test_module": Mock}
                            mock_categories.return_value = {}
                            
                            mock_module = Mock()
                            mock_module.name = "test_module"
                            mock_module.collect.return_value = []
                            mock_get_module.return_value = mock_module
                            
                            # Run CLI
                            with patch('sys.argv', ['repo-intel', test_repo_path]):
                                main()
            else:
                pytest.skip("Test repository not found")

    @pytest.mark.integration
    def test_hotspot_identification(self):
        """Test hotspot identification with realistic data"""
        engine = ContextEngine("https://github.com/test/repo")
        
        # Add realistic findings
        findings = [
            # CVE with multiple related signals (Score High)
            Finding("cve", "CVE-2024-1234", "Remote code execution", "nvd_module", "critical",
                   metadata={"cve_id": "CVE-2024-1234", "files": ["app.py", "utils.py"]},
                   confidence_score=0.9, severity_score=0.9, research_value=0.9),
            
            # Security issues in same files
            Finding("security_keyword", "eval", "Use of eval function", "pattern_module", "high",
                   metadata={"files": ["app.py"], "keyword": "eval"},
                   confidence_score=0.8, severity_score=0.8, research_value=0.5),
            Finding("security_keyword", "exec", "Use of exec function", "pattern_module", "high",
                   metadata={"files": ["utils.py"], "keyword": "exec"},
                   confidence_score=0.8, severity_score=0.8, research_value=0.5),
            
            # GitHub issues related to security
            Finding("github_issue", "Fix security vulnerability", "Security issue reported", "github_module", "high",
                   metadata={"files": ["app.py"], "issue_number": "123"},
                   confidence_score=0.7, severity_score=0.7, research_value=0.7),
            
            # Dependency vulnerabilities
            Finding("vulnerable_dependency", "lodash", "Outdated lodash version", "deps_module", "medium",
                   metadata={"tech_type": "nodejs", "version": "4.0.0", "cve": "CVE-2021-23337"},
                   confidence_score=0.9, severity_score=0.6, research_value=0.5),
            
            # Multiple signals in auth.py
            Finding("security_keyword", "password", "Password handling", "pattern_module", "medium",
                   metadata={"files": ["auth.py"], "keyword": "password"},
                   confidence_score=0.6, severity_score=0.5, research_value=0.5),
            Finding("security_keyword", "token", "Token handling", "pattern_module", "medium",
                   metadata={"files": ["auth.py"], "keyword": "token"},
                   confidence_score=0.6, severity_score=0.5, research_value=0.5),
            Finding("github_issue", "Improve auth security", "Auth improvements", "github_module", "medium",
                   metadata={"files": ["auth.py"], "issue_number": "456"},
                   confidence_score=0.6, severity_score=0.5, research_value=0.5),
        ]
        
        for finding in findings:
            engine.context.add_finding(finding)
        
        # Identify hotspots
        engine._aggregate_module_scores()
        engine._apply_reinforcement() # Apply cross-signal boost
        engine._identify_hotspots()

        hotspots = engine.context.hotspots
        
        # Should have multiple hotspots
        assert len(hotspots) > 0
        
        # Check for CVE hotspot
        cve_hotspots = [h for h in hotspots if h["type"] == "cve"]
        assert len(cve_hotspots) > 0
        assert cve_hotspots[0]["priority"] == "critical"
        
        # Check for file hotspots (files with multiple signals)
        file_hotspots = {h["identifier"]: h for h in hotspots if h["type"] == "file"}
        assert "app.py" in file_hotspots  # Has CVE + eval + issue
        assert "auth.py" in file_hotspots  # Has multiple keywords + issue
        
        # app.py should have higher priority due to CVE
        app_hotspot = file_hotspots["app.py"]
        auth_hotspot = file_hotspots["auth.py"]
        
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        assert priority_order[app_hotspot["priority"]] <= priority_order[auth_hotspot["priority"]]

    @pytest.mark.integration
    def test_output_generation(self):
        """Test complete output generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = ContextEngine("https://github.com/test/repo", output_dir=tmpdir)
            
            # Add test data
            finding = Finding("test", "Test finding", "Test description", "test_module", "high")
            engine.context.add_finding(finding)
            engine.context.modules_run = ["test_module"]
            engine.context.summary = {"total_findings": 1}
            engine.context.hotspots = [
                {
                    "type": "test",
                    "identifier": "test_hotspot",
                    "priority": "high",
                    "reason": "Test reason",
                    "signal_count": 1,
                    "start_here": "Test action"
                }
            ]
            
            # Generate all outputs
            engine._save_results()
            
            # Check files exist
            assert os.path.exists(os.path.join(tmpdir, "context.json"))
            assert os.path.exists(os.path.join(tmpdir, "audit_start.md"))
            
            # Check JSON content
            with open(os.path.join(tmpdir, "context.json")) as f:
                data = json.load(f)
            
            assert data["repo"] == "test/repo"
            assert len(data["findings"]) == 1
            assert len(data["hotspots"]) == 1
            assert data["summary"]["total_findings"] == 1
            
            # Check markdown content
            with open(os.path.join(tmpdir, "audit_start.md")) as f:
                md_content = f.read()
            
            assert "Audit Starting Points" in md_content
            assert "test/repo" in md_content
            assert "Total signals found:** 1" in md_content
            assert "test_hotspot" in md_content

    @pytest.mark.integration
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        engine = ContextEngine("https://github.com/nonexistent/repo")
        
        # Add a module that will fail
        failing_module = Mock()
        failing_module.name = "failing_module"
        failing_module.collect.side_effect = Exception("Module failed")
        engine.add_module(failing_module)
        
        # Mock repo clone failure
        with patch('repo_intel.engine.Repo') as mock_repo:
            mock_repo.clone_from.side_effect = Exception("Clone failed")
            
            # Should handle error gracefully
            context = engine.run()
            
            # Should return context even on failure
            assert isinstance(context, AuditContext)
            assert len(context.modules_run) == 0

    @pytest.mark.integration
    def test_module_enrichment_workflow(self):
        """Test module enrichment workflow"""
        engine = ContextEngine("https://github.com/test/repo")
        
        # Add base module that produces findings
        base_module = Mock()
        base_module.name = "base_module"
        base_module.collect.return_value = [
            Finding("cve", "CVE-2024-1234", "Test vulnerability", "base_module",
                   metadata={"cve_id": "CVE-2024-1234"})
        ]
        
        # Add enrichment module
        enrich_module = Mock()
        enrich_module.name = "enrich_module"
        enrich_module.collect.return_value = []
        enrich_module.can_enrich.return_value = True
        enrich_module.enrich.return_value = [
            Finding("cve", "CVE-2024-1234", "Test vulnerability", "base_module",
                   metadata={"cve_id": "CVE-2024-1234", "exploit_available": True})
        ]
        
        engine.add_module(base_module)
        engine.add_module(enrich_module)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('repo_intel.engine.Repo'):
                engine.output_dir = tmpdir
                context = engine.run()
                
                # Should have enriched findings
                assert len(context.findings) == 1
                assert context.findings[0].metadata.get("exploit_available") is True


class TestRealWorldScenarios:
    """Tests based on real-world scenarios"""

    @pytest.mark.integration
    def test_nodejs_application(self):
        """Test scanning a Node.js application"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create typical Node.js project structure
            os.makedirs(os.path.join(tmpdir, "src"))
            
            # package.json with vulnerabilities
            package_json = {
                "name": "test-app",
                "dependencies": {
                    "express": "4.16.0",  # Old version
                    "lodash": "4.17.11",   # Known CVE
                    "request": "2.88.0"    # Deprecated
                }
            }
            
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                json.dump(package_json, f)
            
            # JavaScript files with security patterns
            js_code = """
const express = require('express');
const lodash = require('lodash');
const request = require('request');

app.get('/user/:id', (req, res) => {
    const userId = req.params.id;
    eval(`processUser(${userId})`);  // Security issue
    
    // SQL injection potential
    const query = `SELECT * FROM users WHERE id = ${userId}`;
    db.query(query, (err, results) => {
        res.json(results);
    });
});
"""
            
            with open(os.path.join(tmpdir, "src", "app.js"), "w") as f:
                f.write(js_code)
            
            # Test with tech stack module
            try:
                from repo_intel.modules.tech_stack import TechStack
                
                module = TechStack()
                findings = module.collect(
                    repo_url="https://github.com/test/nodejs-app",
                    repo_name="test/nodejs-app",
                    repo_path=tmpdir
                )
                
                assert isinstance(findings, list)
                if findings:
                    # Should detect Node.js and dependencies
                    tech_types = [f.get('metadata', {}).get('tech_type') for f in findings if isinstance(f, dict)]
                    assert 'nodejs' in tech_types
                    
            except ImportError:
                pytest.skip("TechStack module not available")

    @pytest.mark.integration
    def test_python_application(self):
        """Test scanning a Python application"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create typical Python project structure
            os.makedirs(os.path.join(tmpdir, "app"))
            
            # requirements.txt
            requirements = """flask==2.0.0
requests==2.25.0
sqlalchemy==1.3.0
cryptography==3.3.0
"""
            
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write(requirements)
            
            # Python files with security patterns
            python_code = """
from flask import Flask, request
import subprocess
import pickle
import sqlalchemy

app = Flask(__name__)

@app.route('/exec')
def execute_command():
    cmd = request.args.get('cmd')
    # Security issue: command injection
    subprocess.run(cmd, shell=True)
    return "Command executed"

@app.route('/deserialize')
def deserialize():
    data = request.args.get('data')
    # Security issue: unsafe deserialization
    obj = pickle.loads(data)
    return "Deserialized"

@app.route('/query')
def query_db():
    user_id = request.args.get('id')
    # Security issue: SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return str(result)
"""
            
            with open(os.path.join(tmpdir, "app", "main.py"), "w") as f:
                f.write(python_code)
            
            # Test with dependency analysis
            try:
                from repo_intel.modules.dependency_analysis import DependencyAnalysis
                
                module = DependencyAnalysis()
                findings = module.collect(
                    repo_url="https://github.com/test/python-app",
                    repo_name="test/python-app",
                    repo_path=tmpdir
                )
                
                assert isinstance(findings, list)
                
            except ImportError:
                pytest.skip("DependencyAnalysis module not available")
