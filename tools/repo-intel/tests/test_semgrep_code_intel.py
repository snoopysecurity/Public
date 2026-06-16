import unittest
from unittest.mock import patch, MagicMock
import os
import json
from repo_intel.modules.extractors.semgrep_code_intel import SemgrepCodeIntelModule

class TestSemgrepCodeIntelModule(unittest.TestCase):
    
    def setUp(self):
        self.module = SemgrepCodeIntelModule()

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_collect_success(self, mock_run, mock_which):
        # Mock semgrep existence
        mock_which.return_value = '/usr/bin/semgrep'
        
        # Mock semgrep output
        semgrep_output = {
            "results": [
                {
                    "path": "app.py",
                    "check_id": "rules.semgrep.auth.auth-detection",
                    "start": {"line": 10, "col": 5},
                    "end": {"line": 10, "col": 20},
                    "extra": {
                        "message": "Potential Authentication Logic",
                        "lines": "user.login()",
                        "metadata": {
                            "category": "feature",
                            "subcategory": "authentication"
                        }
                    }
                }
            ]
        }
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = json.dumps(semgrep_output)
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        findings = self.module.collect("http://github.com/test/repo", "test/repo", "/tmp/repo")
        
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding['signal_type'], 'feature_detected')
        self.assertEqual(finding['title'], 'Feature: Potential Authentication Logic')
        self.assertEqual(finding['metadata']['category'], 'feature')
        self.assertEqual(finding['metadata']['subcategory'], 'authentication')
        self.assertEqual(finding['metadata']['tool'], 'semgrep-code-intel')
        
        # Verify semgrep command arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], 'semgrep')
        self.assertEqual(args[1], 'scan')
        self.assertTrue(any('--config=' in arg for arg in args))

    @patch('shutil.which')
    def test_collect_no_semgrep(self, mock_which):
        # Mock semgrep missing
        mock_which.return_value = None
        
        findings = self.module.collect("http://github.com/test/repo", "test/repo", "/tmp/repo")
        self.assertEqual(len(findings), 0)

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_collect_semgrep_error(self, mock_run, mock_which):
        # Mock semgrep existence
        mock_which.return_value = '/usr/bin/semgrep'
        
        # Mock error
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ""
        mock_process.stderr = "error: failed to run"
        mock_run.return_value = mock_process
        
        findings = self.module.collect("http://github.com/test/repo", "test/repo", "/tmp/repo")
        self.assertEqual(len(findings), 0)
