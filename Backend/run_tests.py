#!/usr/bin/env python3
"""
Comprehensive test runner for GrobsAI Backend.

This script provides various ways to run tests with different configurations
and generates detailed reports for analysis.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Test runner with multiple execution modes and reporting."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose=False, coverage=False):
        """Run unit tests only."""
        cmd = [sys.executable, "-m", "pytest", "-m", "unit"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
        
        cmd.extend(["-x", "--tb=short"])  # Stop on first failure, short traceback
        
        return self._execute_test_command(cmd, "unit_tests")
    
    def run_integration_tests(self, verbose=False, coverage=False):
        """Run integration tests only."""
        cmd = [sys.executable, "-m", "pytest", "-m", "integration"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, "integration_tests")
    
    def run_security_tests(self, verbose=False):
        """Run security-focused tests."""
        cmd = [sys.executable, "-m", "pytest", "-m", "security"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, "security_tests")
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests."""
        cmd = [sys.executable, "-m", "pytest", "-m", "performance"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, "performance_tests")
    
    def run_all_tests(self, verbose=False, coverage=False, parallel=False):
        """Run all tests."""
        cmd = [sys.executable, "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
        
        if parallel:
            cmd.extend(["-n", "auto"])  # Auto-detect CPU cores
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, "all_tests")
    
    def run_specific_test_file(self, test_file, verbose=False):
        """Run tests from a specific file."""
        cmd = [sys.executable, "-m", "pytest", str(test_file)]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, f"file_{Path(test_file).stem}")
    
    def run_tests_with_pattern(self, pattern, verbose=False):
        """Run tests matching a pattern."""
        cmd = [sys.executable, "-m", "pytest", "-k", pattern]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, f"pattern_{pattern.replace(' ', '_')}")
    
    def run_slow_tests_only(self, verbose=False):
        """Run only slow tests."""
        cmd = [sys.executable, "-m", "pytest", "-m", "slow"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, "slow_tests")
    
    def run_fast_tests_only(self, verbose=False):
        """Run only fast tests (exclude slow ones)."""
        cmd = [sys.executable, "-m", "pytest", "-m", "not slow"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend(["--tb=short"])
        
        return self._execute_test_command(cmd, "fast_tests")
    
    def _execute_test_command(self, cmd, report_name):
        """Execute a pytest command and generate reports."""
        print(f"Running command: {' '.join(cmd)}")
        print("=" * 60)
        
        # Add output options for detailed reporting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_report = self.reports_dir / f"{report_name}_{timestamp}.html"
        junit_report = self.reports_dir / f"{report_name}_{timestamp}.xml"
        
        cmd.extend([
            f"--html={html_report}",
            f"--junitxml={junit_report}",
            "--self-contained-html"
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            # Save detailed output
            output_file = self.reports_dir / f"{report_name}_{timestamp}_output.txt"
            with open(output_file, 'w') as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Return code: {result.returncode}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                f.write(f"STDERR:\n{result.stderr}\n")
            
            print(f"Test output saved to: {output_file}")
            print(f"HTML report: {html_report}")
            print(f"JUnit report: {junit_report}")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error running tests: {e}")
            return False


class TestAnalyzer:
    """Analyze test results and generate summaries."""
    
    def __init__(self, reports_dir):
        self.reports_dir = Path(reports_dir)
    
    def analyze_latest_reports(self):
        """Analyze the latest test reports."""
        latest_reports = list(self.reports_dir.glob("*.xml"))
        if not latest_reports:
            print("No test reports found.")
            return
        
        latest_report = max(latest_reports, key=lambda p: p.stat().st_mtime)
        self._parse_junit_report(latest_report)
    
    def _parse_junit_report(self, report_path):
        """Parse JUnit XML report and extract key metrics."""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(report_path)
            root = tree.getroot()
            
            total_tests = 0
            passed_tests = 0
            failed_tests = 0
            skipped_tests = 0
            
            for testsuite in root.findall('testsuite'):
                total_tests += int(testsuite.get('tests', 0))
                passed_tests += int(testsuite.get('tests', 0)) - int(testsuite.get('failures', 0)) - int(testsuite.get('skipped', 0))
                failed_tests += int(testsuite.get('failures', 0))
                skipped_tests += int(testsuite.get('skipped', 0))
            
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Skipped: {skipped_tests}")
            
            if total_tests > 0:
                pass_rate = (passed_tests / total_tests) * 100
                print(f"Pass Rate: {pass_rate:.1f}%")
            
            # Find failed tests
            failed_test_cases = []
            for testsuite in root.findall('testsuite'):
                for testcase in testsuite.findall('testcase'):
                    if testcase.find('failure') is not None:
                        failed_test_cases.append(testcase.get('name'))
            
            if failed_test_cases:
                print(f"\nFailed Tests:")
                for test in failed_test_cases:
                    print(f"  - {test}")
            
        except Exception as e:
            print(f"Error parsing report: {e}")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run GrobsAI Backend Tests")
    parser.add_argument("--mode", choices=[
        "unit", "integration", "security", "performance", "all", 
        "slow", "fast", "file", "pattern"
    ], help="Test execution mode")
    
    parser.add_argument("--file", help="Test file to run (for file mode)")
    parser.add_argument("--pattern", help="Test pattern to run (for pattern mode)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--analyze", action="store_true", help="Analyze latest test reports")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    analyzer = TestAnalyzer(runner.reports_dir)
    
    if args.analyze:
        analyzer.analyze_latest_reports()
        return
    
    if args.list:
        print("Available test files:")
        for test_file in runner.tests_dir.glob("test_*.py"):
            print(f"  - {test_file.name}")
        return
    
    success = False
    
    if args.mode == "unit":
        success = runner.run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.mode == "integration":
        success = runner.run_integration_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.mode == "security":
        success = runner.run_security_tests(verbose=args.verbose)
    elif args.mode == "performance":
        success = runner.run_performance_tests(verbose=args.verbose)
    elif args.mode == "all":
        success = runner.run_all_tests(verbose=args.verbose, coverage=args.coverage, parallel=args.parallel)
    elif args.mode == "slow":
        success = runner.run_slow_tests_only(verbose=args.verbose)
    elif args.mode == "fast":
        success = runner.run_fast_tests_only(verbose=args.verbose)
    elif args.mode == "file":
        if not args.file:
            print("Error: --file argument required for file mode")
            sys.exit(1)
        success = runner.run_specific_test_file(args.file, verbose=args.verbose)
    elif args.mode == "pattern":
        if not args.pattern:
            print("Error: --pattern argument required for pattern mode")
            sys.exit(1)
        success = runner.run_tests_with_pattern(args.pattern, verbose=args.verbose)
    else:
        print("Available modes: unit, integration, security, performance, all, slow, fast, file, pattern")
        print("Use --help for more information")
        sys.exit(1)
    
    if success:
        print("\n[PASS] All tests passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()