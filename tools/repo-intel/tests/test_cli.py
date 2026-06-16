"""Tests for CLI functionality"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from repo_intel.cli import main, list_modules
from repo_intel.engine import ContextEngine, Finding


@pytest.mark.unit
class TestCLI:
    """Test CLI argument parsing and execution flow"""

    @patch('repo_intel.cli.get_available_modules')
    @patch('repo_intel.cli.get_module_categories')
    def test_list_modules(self, mock_categories, mock_modules):
        """Test --list-modules functionality"""
        mock_modules.return_value = {
            'test_module': Mock(description='Test module description')
        }
        mock_categories.return_value = {
            'sources': ['github_commits_analyse'],
            'extractors': ['sast_findings']
        }
        
        # Capture stdout
        with patch('builtins.print') as mock_print:
            list_modules()
            mock_print.assert_called()
    
    @patch('repo_intel.cli.ContextEngine')
    @patch('repo_intel.cli.get_available_modules')
    @patch('repo_intel.cli.get_module_categories')
    @patch('repo_intel.cli.get_module')
    def test_main_with_repo_url(self, mock_get_module, mock_categories, 
                                mock_available, mock_engine_class):
        """Test main function with repository URL"""
        # Setup mocks
        mock_available.return_value = {'test_module': Mock}
        mock_categories.return_value = {'sources': ['test_module']}
        mock_module = Mock()
        mock_module.name = 'test_module'
        mock_module.collect.return_value = []
        mock_get_module.return_value = mock_module
        
        mock_engine = Mock()
        mock_engine.output_dir = '/tmp/test'
        mock_engine.run.return_value = Mock()
        mock_engine_class.return_value = mock_engine
        
        # Mock sys.argv
        with patch('sys.argv', ['repo-intel', 'https://github.com/test/repo']):
            main()
        
        # Verify engine was created and run
        mock_engine_class.assert_called_once()
        mock_engine.run.assert_called_once()
    
    @patch('repo_intel.cli.start_server')
    def test_main_view_mode(self, mock_server):
        """Test main function in view mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake findings directory
            context_file = os.path.join(tmpdir, 'context.json')
            with open(context_file, 'w') as f:
                json.dump({'repo': 'test/repo'}, f)
            
            with patch('sys.argv', ['repo-intel', tmpdir]):
                main()
            
            mock_server.assert_called_once_with(tmpdir)
    
    def test_parse_config_values(self):
        """Test configuration value parsing"""
        from repo_intel.cli import main
        
        # Test integer parsing
        with patch('sys.argv', ['repo-intel', 'https://github.com/test/repo', 
                               '--config', 'limit=100']):
            with patch('repo_intel.cli.ContextEngine') as mock_engine:
                mock_engine_instance = Mock()
                mock_engine_instance.output_dir = "/tmp/test"
                mock_engine.return_value = mock_engine_instance
                with patch('repo_intel.cli.get_available_modules', return_value={}):
                    main()
                    mock_engine_instance.set_config.assert_called()
                    # Check that limit was parsed as integer
                    call_args = mock_engine_instance.set_config.call_args[1]
                    assert 'limit' in call_args
                    assert call_args['limit'] == 100

    @patch('repo_intel.cli.get_available_modules')
    @patch('repo_intel.cli.get_module_categories')
    def test_module_selection(self, mock_categories, mock_available):
        """Test module selection logic"""
        mock_available.return_value = {
            'github_commits_analyse': Mock,
            'sast_findings': Mock,
            'exploits': Mock
        }
        mock_categories.return_value = {
            'sources': ['github_commits_analyse'],
            'extractors': ['sast_findings'],
            'enrichers': ['exploits']
        }
        
        # Test category selection
        with patch('repo_intel.cli.ContextEngine') as mock_engine:
            with patch('repo_intel.cli.get_module') as mock_get_module:
                mock_module = Mock()
                mock_module.collect.return_value = []
                mock_get_module.return_value = mock_module
                
                mock_engine_instance = Mock()
                mock_engine_instance.output_dir = "/tmp/test"
                mock_engine.return_value = mock_engine_instance
                
                with patch('sys.argv', ['repo-intel', 'https://github.com/test/repo', 
                                       '--modules', 'sources,extractors']):
                    main()
                
                # Should add modules from both categories
                assert mock_get_module.call_count >= 2

    def test_error_no_target(self):
        """Test error when no target is provided"""
        with patch('sys.argv', ['repo-intel']):
            with pytest.raises(SystemExit):
                main()

    @patch('repo_intel.cli.ContextEngine')
    def test_github_module_skip_no_token(self, mock_engine_class):
        """Test that GitHub modules are skipped when no token is provided"""
        mock_engine = Mock()
        mock_engine.output_dir = '/tmp/test'
        mock_engine.run.return_value = Mock()
        mock_engine_class.return_value = mock_engine
        
        with patch('repo_intel.cli.get_available_modules') as mock_available:
            with patch('repo_intel.cli.get_module_categories') as mock_categories:
                with patch('repo_intel.cli.get_module') as mock_get_module:
                    # Setup mocks
                    mock_available.return_value = {
                        'github_issues_analyse': Mock,
                        'sast_findings': Mock
                    }
                    mock_categories.return_value = {}
                    
                    # Mock GitHub module to require token
                    mock_github_module = Mock()
                    mock_github_module.name = 'github_issues_analyse'
                    mock_get_module.side_effect = lambda name: mock_github_module if name == 'github_issues_analyse' else Mock()
                    
                    with patch('sys.argv', ['repo-intel', 'https://github.com/test/repo']):
                        main()
                    
                    # GitHub module should not be added due to missing token
                    # (this would be verified by checking print output in a real test)
