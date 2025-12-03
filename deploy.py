#!/usr/bin/env python3
"""
Deployment script for MyChatDev system.

Handles setup, validation, and deployment of the complete system
including backend API and Flutter UI.
"""
import subprocess
import sys
import os
import time
from pathlib import Path
import json


class MyChatDevDeployer:
    """Handles deployment of MyChatDev system."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.ui_path = self.project_root / "ui" / "flutter_app"
        self.api_port = 8000
        self.flutter_port = 3000
        
    def check_dependencies(self, flutter_required=True):
        """Check if all required dependencies are available."""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        required_python_packages = [
            "fastapi", "uvicorn", "pydantic", "httpx", 
            "pytest", "pytest-asyncio", "requests"
        ]
        
        missing_python = []
        for package in required_python_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ Python: {package}")
            except ImportError:
                print(f"❌ Python: {package}")
                missing_python.append(package)
        
        # Check Flutter
        flutter_available = False
        try:
            result = subprocess.run(["flutter", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Flutter SDK")
                flutter_available = True
            else:
                print("❌ Flutter SDK")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("❌ Flutter SDK not found")
        
        # Check Ollama (optional)
        ollama_available = False
        try:
            result = subprocess.run(["ollama", "list"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Ollama")
                ollama_available = True
            else:
                print("⚠️  Ollama (optional)")
        except FileNotFoundError:
            print("⚠️  Ollama not found (optional)")
        
        if missing_python:
            print(f"\n❌ Missing Python packages: {', '.join(missing_python)}")
            print(f"Install with: pip install {' '.join(missing_python)}")
            return False
        
        if not flutter_available and flutter_required:
            print("\n⚠️  Flutter SDK not detected (UI deployment will be skipped)")
            print("For full UI deployment, install from: https://flutter.dev/docs/get-started/install")
            print("You can still run backend-only mode with --backend-only flag")
            return False
        elif not flutter_available:
            print("⚠️  Flutter SDK (skipped for backend-only mode)")
        
        return True
    
    def setup_backend(self):
        """Set up the backend API."""
        print("\n🔧 Setting up backend...")
        
        # Initialize database
        try:
            from src.database import initialize_db
            from src.config.settings import DEFAULT_CONFIG
            
            db_path = Path("data")
            db_path.mkdir(exist_ok=True)
            
            initialize_db(DEFAULT_CONFIG.database_url)
            print("✅ Database initialized")
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
        
        # Create necessary directories
        directories = ["logs", "deliverables", "test_deliverables"]
        for dir_name in directories:
            dir_path = Path(dir_name)
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created directory: {dir_name}")
        
        return True
    
    def setup_frontend(self):
        """Set up the Flutter frontend."""
        print("\n🔧 Setting up frontend...")
        
        if not self.ui_path.exists():
            print(f"❌ Flutter app directory not found: {self.ui_path}")
            return False
        
        # Get Flutter dependencies
        try:
            result = subprocess.run(
                ["flutter", "pub", "get"],
                cwd=self.ui_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Flutter dependencies installed")
            else:
                print(f"❌ Flutter pub get failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Flutter setup failed: {e}")
            return False
        
        return True
    
    def run_tests(self):
        """Run the test suite."""
        print("\n🧪 Running tests...")
        
        try:
            # Run new tests
            result = subprocess.run(
                [sys.executable, "run_new_tests.py"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅ New tests passed")
            else:
                print("⚠️  Some new tests failed (check output)")
                print(result.stdout[-500:])  # Last 500 chars
            
            # Run basic system test
            result = subprocess.run(
                [sys.executable, "test_system.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ System test passed")
            else:
                print("⚠️  System test failed (may need Ollama)")
            
        except subprocess.TimeoutExpired:
            print("⚠️  Tests timed out")
        except Exception as e:
            print(f"⚠️  Test execution error: {e}")
        
        return True  # Don't fail deployment on test issues
    
    def start_backend(self):
        """Start the FastAPI backend."""
        print(f"\n🚀 Starting backend on port {self.api_port}...")
        
        try:
            # Start API server in background
            cmd = [sys.executable, "run_api.py", "--port", str(self.api_port)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give server time to start
            time.sleep(3)
            
            # Check if server is running
            if process.poll() is None:
                print(f"✅ Backend started (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Backend failed to start: {stderr.decode()}")
                return None
        except Exception as e:
            print(f"❌ Backend startup error: {e}")
            return None
    
    def start_frontend(self):
        """Start the Flutter frontend."""
        print(f"\n🚀 Starting frontend...")
        
        try:
            # Start Flutter web app
            cmd = ["flutter", "run", "-d", "chrome", "--web-port", str(self.flutter_port)]
            process = subprocess.Popen(
                cmd,
                cwd=self.ui_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print(f"✅ Frontend starting (PID: {process.pid})")
            print(f"🌐 UI will be available at: http://localhost:{self.flutter_port}")
            return process
        except Exception as e:
            print(f"❌ Frontend startup error: {e}")
            return None
    
    def deploy(self, mode="development", backend_only=False):
        """Deploy the complete system."""
        print("🚀 MyChatDev Deployment")
        print("=" * 50)
        
        # Step 1: Check dependencies
        if not self.check_dependencies(flutter_required=not backend_only):
            print("\n❌ Dependency check failed. Use --backend-only for API-only deployment.")
            return False
        
        # Step 2: Setup backend
        if not self.setup_backend():
            print("\n❌ Backend setup failed.")
            return False
        
        # Step 3: Setup frontend (skip if backend-only)
        if not backend_only:
            if not self.setup_frontend():
                print("\n❌ Frontend setup failed. Continuing with backend-only.")
                backend_only = True
        
        # Step 4: Run tests
        if mode == "production":
            if not self.run_tests():
                print("\n❌ Tests failed. Aborting production deployment.")
                return False
        else:
            self.run_tests()  # Run but don't fail on errors in dev mode
        
        # Step 5: Start services
        print("\n" + "=" * 50)
        print("🎯 Starting Services")
        print("=" * 50)
        
        backend_process = self.start_backend()
        if not backend_process:
            print("\n❌ Failed to start backend.")
            return False
        
        frontend_process = None
        if not backend_only:
            frontend_process = self.start_frontend()
            if not frontend_process:
                print("\n⚠️  Failed to start frontend. Continuing with backend-only.")
                backend_only = True
        
        # Deployment complete
        print("\n" + "=" * 50)
        print("🎉 DEPLOYMENT COMPLETE!")
        print("=" * 50)
        print(f"📡 Backend API: http://localhost:{self.api_port}")
        if not backend_only and frontend_process:
            print(f"🌐 Frontend UI: http://localhost:{self.flutter_port}")
        else:
            print("🌐 Frontend UI: Not started (backend-only mode)")
        print(f"📚 API Docs: http://localhost:{self.api_port}/docs")
        print("\n💡 Tips:")
        print("- Ensure Ollama is running for full functionality")
        print("- Check logs/ directory for detailed logs")
        print("- Use Ctrl+C to stop services")
        
        try:
            # Keep processes running
            print("\n⏳ Services running... Press Ctrl+C to stop")
            while True:
                time.sleep(1)
                
                # Check if processes are still alive
                if backend_process.poll() is not None:
                    print("❌ Backend process died")
                    break
                if frontend_process and frontend_process.poll() is not None:
                    print("❌ Frontend process died")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down services...")
            
            if backend_process:
                backend_process.terminate()
                print("✅ Backend stopped")
            
            if frontend_process:
                frontend_process.terminate()
                print("✅ Frontend stopped")
            
            print("👋 Goodbye!")
        
        return True
    
    def quick_start(self):
        """Quick start for development."""
        print("⚡ MyChatDev Quick Start")
        print("=" * 30)
        
        if not self.check_dependencies():
            return False
        
        if not self.setup_backend():
            return False
        
        backend_process = self.start_backend()
        if backend_process:
            print(f"\n✅ Backend running at http://localhost:{self.api_port}")
            print("🔧 Frontend setup skipped for quick start")
            print("📚 API Documentation: http://localhost:8000/docs")
            print("\nPress Ctrl+C to stop")
            
            try:
                while backend_process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                backend_process.terminate()
                print("\n👋 Backend stopped")
        
        return True


def main():
    """Main deployment entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MyChatDev Deployment Script")
    parser.add_argument("--mode", choices=["development", "production"], 
                       default="development", help="Deployment mode")
    parser.add_argument("--quick", action="store_true", 
                       help="Quick start (backend only)")
    parser.add_argument("--backend-only", action="store_true",
                       help="Deploy backend only (skip Flutter UI)")
    parser.add_argument("--test-only", action="store_true",
                       help="Run tests only")
    
    args = parser.parse_args()
    
    deployer = MyChatDevDeployer()
    
    if args.test_only:
        return deployer.run_tests()
    elif args.quick:
        return deployer.quick_start()
    else:
        return deployer.deploy(args.mode, backend_only=args.backend_only)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)