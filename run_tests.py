#!/usr/bin/env python3
"""Test runner for MCP implementation"""

import sys
import subprocess
import os

def run_unit_tests():
    """Run unit tests"""
    print("Running unit tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/unit/", "-v", "--tb=short"
    ], cwd=os.path.dirname(__file__))
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests"""
    print("Running integration tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/integration/", "-v", "--tb=short"
    ], cwd=os.path.dirname(__file__))
    return result.returncode == 0

def main():
    """Main test runner"""
    print("MCP Implementation Test Suite")
    print("=" * 40)
    
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    
    print("\nTest Results:")
    print(f"Unit Tests: {'PASS' if unit_success else 'FAIL'}")
    print(f"Integration Tests: {'PASS' if integration_success else 'FAIL'}")
    
    if unit_success and integration_success:
        print("\nAll tests passed! ✅")
        return 0
    else:
        print("\nSome tests failed! ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())