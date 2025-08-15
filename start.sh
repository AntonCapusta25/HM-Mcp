#!/usr/bin/env python3
"""
Server Startup Script with Enhanced Error Handling
Helps diagnose and fix common issues before starting the MCP server
"""

import os
import sys
import subprocess
import importlib
import logging
from pathlib import Path

def setup_logging():
    """Setup enhanced logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('server_startup.log')
        ]
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        raise Exception(f"Python 3.8+ required, found {sys.version}")
    print(f"✅ Python version: {sys.version}")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastmcp',
        'pydantic', 
        'DrissionPage',
        'requests',
        'asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} missing")
    
    if missing_packages:
        print(f"\n🔧 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'] + missing_packages
            )
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install packages: {e}")

def check_chrome_installation():
    """Check if Chrome/Chromium is available"""
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser', 
        '/usr/bin/chromium',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    ]
    
    # Try to find Chrome
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome found at: {path}")
            return True
    
    # Try command line
    try:
        subprocess.run(['google-chrome', '--version'], 
                      capture_output=True, check=True)
        print("✅ Chrome available via command line")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    try:
        subprocess.run(['chromium-browser', '--version'], 
                      capture_output=True, check=True)
        print("✅ Chromium available via command line")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    print("⚠️ Chrome/Chromium not found")
    print("Install instructions:")
    print("  Ubuntu/Debian: sudo apt-get install chromium-browser")
    print("  CentOS/RHEL: sudo yum install chromium")
    print("  macOS: brew install chromium")
    print("  Windows: Download from https://www.google.com/chrome/")
    return False

def check_file_structure():
    """Check if all required files exist"""
    required_files = [
        'bulletproof_scraper.py',
        'bulletproof_submitter.py'
    ]
    
    current_dir = Path('.')
    
    for file in required_files:
        file_path = current_dir / file
        if file_path.exists():
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            return False
    
    return True

def check_port_availability(port):
    """Check if the specified port is available"""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            print(f"✅ Port {port} is available")
            return True
    except OSError:
        print(f"⚠️ Port {port} is in use")
        return False

def setup_environment():
    """Setup environment variables"""
    env_vars = {
        'HEADLESS': os.getenv('HEADLESS', 'true'),
        'USE_STEALTH': os.getenv('USE_STEALTH', 'true'),
        'PORT': os.getenv('PORT', '8000'),
        'DEBUG': os.getenv('DEBUG', 'false')
    }
    
    print("🔧 Environment configuration:")
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  {key}={value}")
    
    return env_vars

def test_drissionpage():
    """Test DrissionPage functionality"""
    try:
        print("🧪 Testing DrissionPage...")
        from DrissionPage import ChromiumPage, ChromiumOptions
        
        # Test options creation
        co = ChromiumOptions()
        co.headless(True)
        print("✅ ChromiumOptions created")
        
        # Test page creation (but don't actually open browser)
        print("✅ DrissionPage imports working")
        return True
        
    except Exception as e:
        print(f"❌ DrissionPage test failed: {e}")
        return False

def run_health_check():
    """Run a basic health check"""
    try:
        print("🏥 Running health check...")
        
        # Import the main server
        from fixed_mcp_server import health_check
        import asyncio
        
        # Run health check
        result = asyncio.run(health_check())
        
        if result.get('status') == 'healthy':
            print("✅ Health check passed")
            return True
        else:
            print(f"⚠️ Health check issues: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Main startup function"""
    logger = setup_logging()
    
    print("🚀 Form Automation MCP Server - Startup Diagnostics")
    print("=" * 60)
    
    try:
        # Run all checks
        print("\n📋 System Checks:")
        check_python_version()
        
        print("\n📦 Dependency Checks:")
        check_dependencies()
        
        print("\n🌐 Browser Checks:")
        chrome_ok = check_chrome_installation()
        
        print("\n📁 File Structure Checks:")
        files_ok = check_file_structure()
        
        print("\n🔧 Environment Setup:")
        env_vars = setup_environment()
        
        print("\n🔌 Port Checks:")
        port = int(env_vars['PORT'])
        port_ok = check_port_availability(port)
        
        print("\n🧪 DrissionPage Test:")
        dp_ok = test_drissionpage()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 STARTUP SUMMARY:")
        
        checks = [
            ("Chrome/Chromium", chrome_ok),
            ("Required Files", files_ok), 
            ("Port Available", port_ok),
            ("DrissionPage", dp_ok)
        ]
        
        all_good = True
        for check_name, status in checks:
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {check_name}")
            if not status:
                all_good = False
        
        if all_good:
            print("\n🎉 All checks passed! Starting server...")
            
            # Start the actual server
            print(f"\n🌐 Starting server on port {port}...")
            print(f"🔗 Access via: http://localhost:{port}")
            
            # Import and run the fixed server
            from fixed_mcp_server import mcp
            
            if hasattr(mcp, 'run'):
                mcp.run(transport="sse")
            else:
                # Fallback for older versions
                mcp.run()
                
        else:
            print("\n❌ Some checks failed. Please fix the issues above before starting the server.")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        print(f"\n💥 Startup Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check that all required files are in the current directory")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Install Chrome/Chromium browser")
        print("4. Check file permissions")
        print("5. Try a different port with: PORT=8001 python start_server.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
