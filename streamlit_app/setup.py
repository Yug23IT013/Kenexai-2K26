# setup.py
"""
Setup script for Football Analytics Platform

This script helps configure and verify the environment before running the application.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple

def print_header():
    print("\n" + "="*60)
    print("⚙️  Football Analytics Platform - Setup & Configuration")
    print("="*60 + "\n")

def check_python_version() -> bool:
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. You have {sys.version}")
        return False
    print(f"✓ Python {sys.version.split()[0]}")
    return True

def check_command_exists(command: str) -> bool:
    """Check if a command is available in PATH"""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def check_dependencies() -> Tuple[bool, list]:
    """Check for required packages"""
    required = ["pip", "streamlit"]
    optional = ["jupyter", "git"]
    
    missing = []
    print("\n📦 Checking dependencies...")
    
    for cmd in required:
        if check_command_exists(cmd):
            print(f"   ✓ {cmd}")
        else:
            print(f"   ❌ {cmd} (required)")
            missing.append(cmd)
    
    for cmd in optional:
        if check_command_exists(cmd):
            print(f"   ✓ {cmd}")
        else:
            print(f"   ⚠️  {cmd} (optional)")
    
    return len(missing) == 0, missing

def setup_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path("streamlit_app/backend/.env")
    example_file = Path("streamlit_app/backend/.env.example")
    
    print("\n🔐 Environment Configuration...")
    
    if env_file.exists():
        print(f"   ✓ .env exists at {env_file}")
        return True
    
    if example_file.exists():
        print(f"   📋 .env.example found")
        print(f"   Creating .env from template...")
        
        try:
            example_content = example_file.read_text()
            env_file.write_text(example_content)
            print(f"   ✓ Created {env_file}")
            print(f"\n   ⚠️  IMPORTANT: Edit {env_file} and replace:")
            print("      - SNOWFLAKE_PASSWORD with your actual password")
            print("      - GROQ_API_KEY with your API key")
            return False  # Needs manual configuration
        except Exception as e:
            print(f"   ❌ Error creating .env: {e}")
            return False
    else:
        print(f"   ❌ .env.example not found")
        return False

def test_snowflake_connection(config: dict) -> bool:
    """Test Snowflake connection"""
    print("\n🗄️  Testing Snowflake Connection...")
    
    try:
        import snowflake.connector
        
        # Try with .env or defaults
        conn_params = {
            "account": config.get("account", "your_snowflake_account_here"),
            "user": config.get("user", "MARK"),
            "password": config.get("password"),
            "database": config.get("database", "sports_db"),
            "schema": config.get("schema", "analytics"),
            "warehouse": config.get("warehouse", "SPORTS_WH"),
        }
        
        if not conn_params["password"]:
            print("   ⚠️  No password provided - skipping connection test")
            print("   ℹ️  Set SNOWFLAKE_PASSWORD in .env to test")
            return False
        
        print("   Connecting to Snowflake...")
        conn = snowflake.connector.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM athlete_predictions")
        count = cursor.fetchone()[0]
        
        print(f"   ✓ Connected successfully!")
        print(f"   ✓ Found {count} records in athlete_predictions")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        print("   ⚠️  snowflake-connector not installed")
        print("   Install via: pip install snowflake-connector-python")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)[:100]}")
        return False

def test_groq_api(api_key: str) -> bool:
    """Test Groq API connection"""
    print("\n🤖 Testing Groq API...")
    
    if not api_key or api_key == "your_api_key_here":
        print("   ⚠️  No valid Groq API key - skipping test")
        print("   Get one at: https://console.groq.com/")
        return False
    
    try:
        from groq import Groq
        
        client = Groq(api_key=api_key)
        
        print("   Testing API connection...")
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "user", "content": "Say 'Hello from Groq' in one sentence"}
            ],
            max_tokens=50,
        )
        
        print(f"   ✓ Connected successfully!")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print("   ⚠️  groq package not installed")
        print("   Install via: pip install groq")
        return False
    except Exception as e:
        print(f"   ❌ API test failed: {str(e)[:100]}")
        return False

def install_backend_deps() -> bool:
    """Install backend dependencies"""
    print("\n📦 Installing Backend Dependencies...")
    
    req_file = Path("streamlit_app/backend/requirements.txt")
    if not req_file.exists():
        print(f"   ❌ {req_file} not found")
        return False
    
    try:
        print("   Installing packages...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)],
            check=True
        )
        print("   ✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Installation had issues: {e}")
        return False

def print_summary(results: dict):
    """Print setup summary"""
    print("\n" + "="*60)
    print("📊 Setup Summary")
    print("="*60)
    
    checks = {
        "Python Version": results.get("python", False),
        "Dependencies": results.get("dependencies", False),
        "Backend Packages": results.get("backend_deps", False),
        "Environment File": results.get("env_file", False),
        "Snowflake Connection": results.get("snowflake", False),
        "Groq API": results.get("groq", False),
    }
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    for check, result in checks.items():
        symbol = "✓" if result else "❌"
        print(f"{symbol} {check}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All systems ready! You can start the application now:")
        print("\n   python streamlit_app/run_app.py")
        print("\nOr manually:")
        print("   Terminal 1: python -m uvicorn streamlit_app.backend.api:app --port 8000")
        print("   Terminal 2: streamlit run streamlit_app/app.py --server.port=8501")
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
        print("   Common fixes:")
        print("   1. Ensure .env is configured with correct credentials")
        print("   2. Run: pip install -r streamlit_app/backend/requirements.txt")
        print("   3. Verify Snowflake account and password")
        print("   4. Get Groq API key from https://console.groq.com/")

def load_env_config():
    """Load configuration from .env"""
    from pathlib import Path
    
    env_file = Path("streamlit_app/backend/.env")
    config = {}
    
    if env_file.exists():
        for line in env_file.read_text().split("\n"):
            if line.strip() and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip().lower()] = value.strip()
    
    return config

def main():
    print_header()
    
    results = {}
    
    # Check Python
    results["python"] = check_python_version()
    if not results["python"]:
        sys.exit(1)
    
    # Check dependencies
    results["dependencies"], missing = check_dependencies()
    if missing:
        print(f"\n❌ Missing required: {', '.join(missing)}")
        sys.exit(1)
    
    # Setup env file
    results["env_file"] = setup_env_file()
    
    # Install backend deps
    results["backend_deps"] = install_backend_deps()
    
    # Load config
    config = load_env_config()
    
    # Test Snowflake
    results["snowflake"] = test_snowflake_connection(config)
    
    # Test Groq
    groq_key = config.get("groq_api_key", "")
    results["groq"] = test_groq_api(groq_key)
    
    # Print summary
    print_summary(results)
    
    # Return exit code (0 if all passed, 1 otherwise)
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
