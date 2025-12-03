#!/usr/bin/env python3
"""
Test runner for new MyChatDev tests.

Runs the newly created unit and integration tests to validate
the testing infrastructure and identify any issues.
"""
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run the new test files and report results."""
    print("🧪 Running MyChatDev New Tests")
    print("=" * 50)
    
    # Test files to run
    test_files = [
        "tests/test_config_settings.py",
        "tests/test_llm_profiles.py", 
        "tests/integration/test_workflow_service_integration.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        test_path = Path(test_file)
        if not test_path.exists():
            print(f"❌ {test_file} - File not found")
            results[test_file] = "NOT_FOUND"
            continue
            
        print(f"\n🔍 Running {test_file}...")
        
        try:
            # Run pytest on the specific file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v"],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout per test file
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                results[test_file] = "PASSED"
            else:
                print(f"❌ {test_file} - FAILED")
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                print("STDERR:", result.stderr[-500:])  # Last 500 chars
                results[test_file] = "FAILED"
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} - TIMEOUT")
            results[test_file] = "TIMEOUT"
        except Exception as e:
            print(f"💥 {test_file} - ERROR: {e}")
            results[test_file] = "ERROR"
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r == "PASSED")
    total = len(results)
    
    for test_file, result in results.items():
        status_emoji = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "TIMEOUT": "⏰",
            "ERROR": "💥",
            "NOT_FOUND": "❓"
        }.get(result, "❓")
        
        print(f"{status_emoji} {test_file}: {result}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed - check output above")
        return False


def check_dependencies():
    """Check if required test dependencies are available."""
    print("🔍 Checking test dependencies...")
    
    required_packages = ["pytest", "pytest-asyncio"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def main():
    """Main test runner."""
    print("🚀 MyChatDev Test Runner")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependencies missing. Please install required packages.")
        return False
    
    print("\n" + "=" * 50)
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n🎉 Test run completed successfully!")
        return True
    else:
        print("\n❌ Test run completed with failures.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)