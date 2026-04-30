#!/usr/bin/env python3
"""
Local Testing Script - Works on Windows, Mac, Linux
Tests all critical endpoints and auth flows
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*50}{RESET}\n")

def print_ok(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def check_backend_running(url="http://127.0.0.1:8000"):
    """Check if backend is running"""
    try:
        response = requests.get(f"{url}/auth/github?client_type=web", timeout=2, allow_redirects=False)
        return response.status_code in [302, 200]
    except:
        return False

def test_test_code(url="http://127.0.0.1:8000"):
    """Test test_code endpoint"""
    try:
        response = requests.get(
            f"{url}/auth/github/callback?code=test_code&state=test_state",
            timeout=5
        )
        data = response.json()
        if "access_token" in data and "refresh_token" in data:
            return True, data
        return False, response.text
    except Exception as e:
        return False, str(e)

def test_rate_limiting(url="http://127.0.0.1:8000"):
    """Test rate limiting (should get 429 after 10 requests)"""
    results = []
    for i in range(1, 16):
        try:
            response = requests.get(
                f"{url}/auth/github?client_type=web",
                timeout=2,
                allow_redirects=False
            )
            results.append((i, response.status_code))
            time.sleep(0.05)
        except Exception as e:
            results.append((i, f"Error: {e}"))
    
    # Check if we got 429 on request 11
    if len(results) >= 11:
        status_11 = results[10][1]
        return status_11 == 429, results
    return False, results

def check_file_exists(path, description):
    """Check if a required file exists"""
    if Path(path).exists():
        print_ok(f"{description} found")
        return True
    else:
        print_error(f"{description} NOT found: {path}")
        return False

def main():
    print_header("Insighta Labs+ Local Testing Suite")
    
    backend_url = "http://127.0.0.1:8000"
    frontend_url = "http://localhost:5500"
    root_dir = Path(__file__).parent
    
    all_passed = True
    
    # Test 1: Backend running
    print(f"{YELLOW}Test 1: Backend Connectivity{RESET}")
    if check_backend_running(backend_url):
        print_ok(f"Backend responding at {backend_url}")
    else:
        print_error(f"Backend NOT responding at {backend_url}")
        print(f"   Run: python manage.py runserver 0.0.0.0:8000")
        all_passed = False
        return False
    
    # Test 2: test_code endpoint
    print(f"\n{YELLOW}Test 2: test_code Endpoint{RESET}")
    success, result = test_test_code(backend_url)
    if success:
        print_ok("test_code returns valid tokens")
        print(f"   Access Token: {result.get('access_token', 'N/A')[:30]}...")
        print(f"   User: {result.get('user', {}).get('username', 'N/A')}")
    else:
        print_error(f"test_code failed: {result}")
        all_passed = False
    
    # Test 3: Rate limiting
    print(f"\n{YELLOW}Test 3: Rate Limiting (10 req/min){RESET}")
    success, results = test_rate_limiting(backend_url)
    
    print("   Request statuses:")
    for req_num, status in results:
        status_str = str(status)
        if req_num <= 10 and status == 302:
            symbol = "✓"
            color = GREEN
        elif req_num == 11 and status == 429:
            symbol = "✓"
            color = GREEN
        elif req_num > 11 and status == 429:
            symbol = "✓"
            color = GREEN
        else:
            symbol = "✗"
            color = RED
        
        print(f"   {color}Req {req_num:2d}: {status_str:3s}{RESET}")
    
    if success:
        print_ok("Rate limiting enforced correctly")
    else:
        print_warning("Rate limiting may not be working correctly")
        all_passed = False
    
    # Test 4: Files exist
    print(f"\n{YELLOW}Test 4: Required Files{RESET}")
    
    readme_path = root_dir / "stage-3-backend" / "README.md"
    workflow_path = root_dir / "stage-3-backend" / ".github" / "workflows" / "ci.yml"
    
    files_ok = True
    files_ok &= check_file_exists(readme_path, "README.md")
    files_ok &= check_file_exists(workflow_path, ".github/workflows/ci.yml")
    
    if not files_ok:
        all_passed = False
    
    # Test 5: .env file
    print(f"\n{YELLOW}Test 5: Environment Configuration{RESET}")
    env_path = root_dir / "stage-3-backend" / ".env"
    if check_file_exists(env_path, ".env"):
        with open(env_path) as f:
            content = f.read()
            if "BACKEND_URL" in content:
                print_ok("BACKEND_URL configured")
            else:
                print_warning("BACKEND_URL not found in .env (will use request host)")
    else:
        print_warning(".env not found (will use defaults)")
    
    # Summary
    print_header("Test Summary")
    
    if all_passed:
        print_ok("All tests passed! ✓")
        print(f"\n{GREEN}You're ready to:{RESET}")
        print(f"1. Open {frontend_url} in browser")
        print(f"2. Click 'Continue with GitHub'")
        print(f"3. Should redirect to GitHub login")
        print(f"\n{GREEN}When ready to deploy:{RESET}")
        print(f"   git add -A")
        print(f"   git commit -m 'fix: OAuth, README, CI/CD'")
        print(f"   git push origin main")
        return True
    else:
        print_error("Some tests failed. See above for details.")
        print(f"\n{YELLOW}Troubleshooting:{RESET}")
        print(f"1. Check backend is running: python manage.py runserver")
        print(f"2. Check .env has BACKEND_URL set")
        print(f"3. Check README.md and .github/workflows/ci.yml exist")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Testing interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
