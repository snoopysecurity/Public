#!/usr/bin/env python3
"""
Test runner script for repo-intel
"""

import sys
import subprocess
import os


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✓ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    """Main test runner"""
    # Change to project root
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    all_passed = True
    
    # Run unit tests (fast)
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    unit_tests = [
        (["uv", "run", "pytest", "-m", "unit", "tests/"], "Unit Tests"),
        (["uv", "run", "pytest", "tests/test_cli.py", "-v"], "CLI Tests"),
        (["uv", "run", "pytest", "tests/test_engine.py", "-v"], "Engine Tests"),
        (["uv", "run", "pytest", "tests/test_modules.py", "-v"], "Module Tests"),
    ]
    
    for cmd, desc in unit_tests:
        if not run_command(cmd, desc):
            all_passed = False
    
    # Run integration tests (slower, may require network)
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TESTS")
    print("="*60)
    
    integration_tests = [
        (["uv", "run", "pytest", "-m", "integration", "tests/", "-v"], "Integration Tests"),
    ]
    
    for cmd, desc in integration_tests:
        if not run_command(cmd, desc):
            all_passed = False
    
    # Run coverage if requested
    if "--coverage" in sys.argv:
        print("\n" + "="*60)
        print("RUNNING COVERAGE")
        print("="*60)
        
        coverage_cmd = ["uv", "run", "pytest", "--cov=repo_intel", "--cov-report=html", 
                       "--cov-report=term-missing", "tests/"]
        if not run_command(coverage_cmd, "Coverage Report"):
            all_passed = False
        
        print("\nCoverage report generated in htmlcov/index.html")
    
    # Run linting
    if "--lint" in sys.argv:
        print("\n" + "="*60)
        print("RUNNING LINTING")
        print("="*60)
        
        linting_tests = [
            (["uv", "run", "ruff", "check", "tests/"], "Ruff Linting"),
            (["uv", "run", "black", "--check", "tests/"], "Black Formatting"),
            (["uv", "run", "mypy", "tests/"], "MyPy Type Checking"),
        ]
        
        for cmd, desc in linting_tests:
            if not run_command(cmd, desc):
                all_passed = False
    
    # Final summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print('='*60)
    
    if all_passed:
        print("✓ All tests PASSED!")
        sys.exit(0)
    else:
        print("✗ Some tests FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
