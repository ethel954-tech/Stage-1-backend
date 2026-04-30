# Local Testing Guide - Insighta Labs+ OAuth

## Problem Diagnosis
**"Page not found" when clicking "Continue with GitHub"** means:
- Backend URL is not configured correctly
- Django backend is not running
- Frontend is not loading the correct backend URL

## Step 1: Create/Verify `.env` File

Copy the example and create the `.env` file in `stage-3-backend/`:

```bash
cd stage-3-backend
cp .env.example .env
```

Edit `stage-3-backend/.env`:

```env
# Django
SECRET_KEY=django-insecure-test-secret-key-12345-local-dev
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# GitHub OAuth
GITHUB_CLIENT_ID=Ov23lia73T1w3mdq6WoP
GITHUB_CLIENT_SECRET=8bb44572a26413b87b80dea23b1b0ff7e29b31ad

# JWT
JWT_SECRET_KEY=test-jwt-secret-key-12345-local-dev

# **CRITICAL FOR LOCAL TESTING**
BACKEND_URL=http://127.0.0.1:8000
WEB_PORTAL_URL=http://localhost:5500
```

⚠️ **Make sure BACKEND_URL is set!** Without this, the auth flow will fail.

## Step 2: Start Django Backend

```bash
cd stage-3-backend

# Activate virtual environment (if not already active)
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8000
```

✅ You should see:
```
Starting development server at http://0.0.0.0:8000/
```

## Step 3: Serve Frontend Locally

**Option A: Using Live Server (VS Code)**
1. Open `web-portal/index.html` in VS Code
2. Right-click → "Open with Live Server"
3. Server starts at `http://127.0.0.1:5500`

**Option B: Using Python HTTP Server**
```bash
cd web-portal
python -m http.server 5500
```

**Option C: Using npm http-server**
```bash
cd web-portal
npm install -g http-server
http-server -p 5500
```

✅ You should see the Insighta Labs+ login page

## Step 4: Test OAuth Flow

### 4a. Frontend Test
1. Open browser at `http://127.0.0.1:5500` (or `http://localhost:5500`)
2. Click **"Continue with GitHub"**
3. Should redirect to GitHub OAuth login (NOT 404)

**If you get "page not found":**
- Check browser DevTools Console (F12 → Console tab)
- Look for error messages about `API_BASE`
- Verify `BACKEND_URL=http://127.0.0.1:8000` is in `.env`

### 4b. Direct Backend Test
Test the backend endpoint directly:

```bash
# Test GitHub OAuth endpoint
curl "http://127.0.0.1:8000/auth/github?client_type=web"
```

Expected: 302 redirect to GitHub
```
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?...
```

### 4c. Test with test_code (No Real GitHub Account Needed)

```bash
# Test OAuth callback with test_code
curl -X GET "http://127.0.0.1:8000/auth/github/callback?code=test_code&state=test_state" \
  -H "Cookie: sessionid=test" -v
```

Expected: 200 JSON response with tokens
```json
{
  "status": "success",
  "access_token": "eyJ0eXAi...",
  "refresh_token": "refresh_token_...",
  "user": {
    "id": "test_user_123",
    "username": "test_user",
    "email": "test@example.com"
  }
}
```

## Step 5: Test All Auth Endpoints

### Rate Limiting Test (should return 429 on 11th request)

```bash
# Run 15 requests to /auth/github (should get 429 after 10)
for i in {1..15}; do
  echo "Request $i:"
  curl -s -w "\nStatus: %{http_code}\n" "http://127.0.0.1:8000/auth/github?client_type=web" -L | head -1
  sleep 0.1
done
```

Expected: First 10 return 302, requests 11-15 return 429

### Test API Endpoints

```bash
# Get test token first
TOKEN=$(curl -s -X GET "http://127.0.0.1:8000/auth/github/callback?code=test_code&state=test_state" \
  -H "Cookie: sessionid=test" | jq -r '.access_token')

# Test profiles endpoint with token
curl -X GET "http://127.0.0.1:8000/api/profiles?page=1&limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-API-Version: 1"
```

## Step 6: Check Logs for Debugging

### Django Backend Logs
Watch terminal output for `[AUTH]`, `[JWT]`, `[RATE]` prefixed messages:

```
[AUTH] Callback received: client_type=web, code=test_code...
[AUTH] Test code detected - issuing dummy tokens
[JWT] Authenticated as test_user
[RATE] Rate limit check for IP: 127.0.0.1
```

### Browser Console Logs
Open DevTools (F12 → Console) to see frontend logging:

```
[API] Initializing API helper with base: http://127.0.0.1:8000
[AUTH] Login button clicked - redirecting to: http://127.0.0.1:8000/auth/github?client_type=web
[JWT] Response status: 302 - redirecting to GitHub
```

## Common Issues & Fixes

### ❌ Error: "Cannot GET /auth/github"
**Cause:** Backend not running or URL wrong
```bash
# Fix: Make sure backend is running
cd stage-3-backend
python manage.py runserver 0.0.0.0:8000
```

### ❌ Error: "BACKEND_URL not set"
**Cause:** `.env` file not created or BACKEND_URL missing
```bash
# Fix: Create .env with BACKEND_URL
echo "BACKEND_URL=http://127.0.0.1:8000" >> .env
```

### ❌ Error: "CORS error" in browser console
**Cause:** Frontend URL not in CORS_ALLOWED_ORIGINS
```python
# In settings.py, add your frontend URL:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",  # Add this
    "http://127.0.0.1:5500",
    "http://localhost:3000",
]
```

### ❌ Error: "Invalid state parameter"
**Cause:** Session not persisting (cookies)
```bash
# Fix: Use cookies in curl
curl -c cookies.txt -b cookies.txt "http://127.0.0.1:8000/auth/github"
curl -c cookies.txt -b cookies.txt "http://127.0.0.1:8000/auth/github/callback?code=test_code&state=..."
```

### ❌ Error: "test_code returns 400"
**Cause:** Missing or wrong state parameter
```bash
# Fix: Include state parameter
curl -X GET "http://127.0.0.1:8000/auth/github/callback?code=test_code&state=any_state" \
  -H "Cookie: sessionid=test"
```

## Full End-to-End Test Script

Save as `test_local.sh`:

```bash
#!/bin/bash

echo "🚀 Starting Insighta Labs+ Local Testing"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test backend
echo -e "${YELLOW}1. Testing backend at http://127.0.0.1:8000${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" "http://127.0.0.1:8000/auth/github?client_type=web" -L)
STATUS=$(echo "$RESPONSE" | tail -1)
if [ "$STATUS" = "302" ] || [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Backend responding${NC}"
else
    echo -e "${RED}✗ Backend not responding (Status: $STATUS)${NC}"
    echo "   Fix: cd stage-3-backend && python manage.py runserver 0.0.0.0:8000"
fi

# Test test_code
echo -e "${YELLOW}2. Testing test_code flow${NC}"
TOKEN_RESPONSE=$(curl -s "http://127.0.0.1:8000/auth/github/callback?code=test_code&state=test" \
  -H "Cookie: sessionid=test")
if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ test_code returns tokens${NC}"
    echo "   $TOKEN_RESPONSE"
else
    echo -e "${RED}✗ test_code failed${NC}"
    echo "   Response: $TOKEN_RESPONSE"
fi

# Test rate limiting
echo -e "${YELLOW}3. Testing rate limiting (should get 429 on 11th request)${NC}"
for i in {1..11}; do
    STATUS=$(curl -s -w "%{http_code}" -o /dev/null "http://127.0.0.1:8000/auth/github?client_type=web")
    if [ "$i" -eq 11 ]; then
        if [ "$STATUS" = "429" ]; then
            echo -e "${GREEN}✓ Rate limiting enforced (429 on request 11)${NC}"
        else
            echo -e "${RED}✗ Rate limiting NOT working (got $STATUS)${NC}"
        fi
    fi
    sleep 0.05
done

echo ""
echo "✅ Local testing complete!"
echo ""
echo "Next steps:"
echo "1. Open http://127.0.0.1:5500 in browser"
echo "2. Click 'Continue with GitHub'"
echo "3. Should redirect to GitHub login"
```

Run with:
```bash
bash test_local.sh
```

## Deployment Testing

Before pushing to GitHub, verify:

```bash
✅ .env file has correct BACKEND_URL
✅ Django migrations applied: python manage.py migrate
✅ Backend responds to /auth/github
✅ test_code returns JSON with tokens
✅ Rate limiting returns 429 after 10 requests
✅ README.md exists in root
✅ .github/workflows/ci.yml exists
✅ All files committed to git
✅ Ready to push: git push origin main
```

## Next: Deploy to GitHub

Once local testing passes:

```bash
cd stage-3-backend
git add -A
git commit -m "fix: test_code JSON, README, GitHub Actions"
git push origin main
```

Then run grading tests again - should score 50+/60 ✓
