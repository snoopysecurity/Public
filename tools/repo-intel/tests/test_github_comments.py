
import unittest
from unittest.mock import Mock, patch, MagicMock
from repo_intel.modules.sources.github_prs import GithubPrsAnalyseModule

class TestGithubCommentAnalysis(unittest.TestCase):
    
    @patch('time.sleep')
    @patch('repo_intel.modules.sources.github_prs.Github')
    def test_cve_in_comment(self, mock_github_cls, mock_sleep):
        """Test that CVEs in comments are detected."""
        
        # Setup Mock GitHub
        mock_github = Mock()
        mock_github_cls.return_value = mock_github
        mock_user = Mock()
        mock_user.login = "testuser"
        mock_github.get_user.return_value = mock_user
        
        # Setup Mock PR
        mock_pr = Mock()
        mock_pr.number = 123
        mock_pr.title = "Update deps"
        mock_pr.body = "Routine update"
        mock_pr.html_url = "http://github.com/test/repo/pull/123"
        mock_pr.state = "open"
        mock_pr.created_at.isoformat.return_value = "2023-01-01T00:00:00"
        mock_pr.labels = []
        mock_pr.user.login = "author"
        mock_pr.pull_request = True # It's a PR
        
        # Mock Comments
        mock_comment1 = Mock()
        mock_comment1.body = "This fixes CVE-2023-1234 in the backend."
        
        mock_pr.get_issue_comments.return_value = [mock_comment1]
        
        # Setup Search Results
        # The module searches for keywords. We need to trigger the search loop.
        # We can force the search to return our mock PR for the keyword "CVE"
        mock_github.search_issues.return_value = [mock_pr]
        
        # Initialize Module
        module = GithubPrsAnalyseModule(github_token="fake_token")
        
        # Run Collect
        # logic: collect calls _search_prs. _search_prs fetches comments.
        findings = module.collect("http://github.com/test/repo", "test/repo")
        
        # Assertions
        # We expect a finding for CVE-2023-1234
        cve_findings = [f for f in findings if f["signal_type"] == "cve"]
        
        # Check if we found the CVE
        self.assertTrue(len(cve_findings) > 0, "Should have found CVE finding")
        
        found_cve = cve_findings[0]
        self.assertEqual(found_cve["metadata"]["cve_id"], "CVE-2023-1234")
        self.assertIn("PR Comment", found_cve["metadata"]["context"])
        self.assertIn("CVE reference found in PR Comment", found_cve["description"])

    @patch('time.sleep')
    @patch('repo_intel.modules.sources.github_prs.Github')
    def test_multiple_cves_in_comments(self, mock_github_cls, mock_sleep):
        """Test that multiple different CVEs in comments are detected."""
        
        # Setup
        mock_github = Mock()
        mock_github_cls.return_value = mock_github
        mock_github.get_user.return_value = Mock(login="testuser")
        
        mock_pr = Mock()
        mock_pr.number = 456
        mock_pr.title = "Security Fixes"
        mock_pr.body = "Fixing bugs."
        mock_pr.html_url = "http://url"
        mock_pr.state = "open"
        mock_pr.created_at.isoformat.return_value = "2023-01-01"
        mock_pr.labels = []
        mock_pr.user.login = "author"
        mock_pr.pull_request = True
        
        # Two comments with DIFFERENT CVEs
        c1 = Mock()
        c1.body = "Addressing CVE-2023-0001."
        c2 = Mock()
        c2.body = "Also fixing CVE-2023-0002."
        
        mock_pr.get_issue_comments.return_value = [c1, c2]
        mock_github.search_issues.return_value = [mock_pr]
        
        module = GithubPrsAnalyseModule(github_token="fake")
        findings = module.collect("http://repo", "repo")
        
        cve_findings = [f for f in findings if f["signal_type"] == "cve"]
        
        # Should find BOTH
        self.assertEqual(len(cve_findings), 2, "Should find 2 unique CVEs")
        cve_ids = sorted([f["metadata"]["cve_id"] for f in cve_findings])
        self.assertEqual(cve_ids, ["CVE-2023-0001", "CVE-2023-0002"])

if __name__ == '__main__':
    unittest.main()
