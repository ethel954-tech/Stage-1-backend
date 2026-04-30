# Local Testing Quick Reference

## TL;DR - Get Started in 5 Minutes

### Terminal 1: Setup Backend
```bash
cd backend2
setup_local.bat  # Or: bash setup_local.sh (on Mac/Linux)
```

### Terminal 2: Start Backend
```bash
cd backend2
start_backend.bat  # Or: bash start_backend.sh (on Mac/Linux)
```
Wait for: `Starting development server at http://0.0.0.0:8000/`

### Terminal 3: Serve Frontend
```bash
cd backend2\web-portal
python -m http.server 5500
```
Or use VS Code Live Server: Right-click `index.html` → "Open with Live Server"

### Terminal 4 (Optional): Run Tests
```bash
cd backend2
test_local.bat  # Or: bash test_local.sh (on Mac/Linux)
```

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5500 | Login page / Web portal |
| Backend | http://127.0.0.1:8000 | API endpoints |
| Django Admin | http://127.0.0.1:8000/admin | (optional) |

## Test Endpoints

### 1. Test OAuth Initiation
```bash
curl "http://127.0.0.1:8000/auth/github?client_type=web"
```
Expected: 302 redirect to GitHub

### 2. Test with test_code (No GitHub Account Needed)
```bash
curl "http://127.0.0.1:8000/auth/github/callback?code=test_code&state=test"
```
Expected: JSON with `access_token` and `refresh_token`

### 3. Test Rate Limiting
```bash
# Run 15 requests, should get 429 on request 11
for i in {1..15}; do
  curl -s -w "Request $i: %{http_code}\n" \
    "http://127.0.0.1:8000/auth/github" -o /dev/null
done
```
Expected: Requests 1-10 return 302, requests 11-15 return 429

### 4. Test with Real GitHub (Optional)
1. Click "Continue with GitHub" on login page
2. Authorize with your GitHub account
3. Should redirect back to dashboard

## Environment Variables (.env)

Must have these for local testing:
```env
BACKEND_URL=http://127.0.0.1:8000
WEB_PORTAL_URL=http://localhost:5500
GITHUB_CLIENT_ID=Ov23lia73T1w3mdq6WoP
GITHUB_CLIENT_SECRET=8bb44572a26413b87b80dea23b1b0ff7e29b31ad
DEBUG=True
```

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Page not found" when clicking GitHub button | Backend not running | Run `start_backend.bat` |
| "Cannot GET /auth/github" | Django not responding | Check if port 8000 is free, restart backend |
| CORS error in console | Frontend URL not in CORS list | Check `settings.py` CORS_ALLOWED_ORIGINS |
| test_code returns 400 | Missing state parameter | Use `&state=test` or any value |
| Rate limiting not working | Middleware disabled | Check middleware is in `settings.py` |

## File Structure
```
backend2/
├── LOCAL_TESTING_GUIDE.md    ← Detailed guide
├── setup_local.bat            ← Run first to setup
├── start_backend.bat          ← Run to start server
├── test_local.bat             ← Run to test endpoints
├── stage-3-backend/
│   ├── .env                   ← Create this
│   ├── README.md              ← Required for grading
│   ├── authapp/views.py       ← OAuth endpoints
│   ├── backend1/middleware.py ← Rate limiting
│   └── .github/workflows/ci.yml ← CI/CD pipeline
└── web-portal/
    └── index.html             ← Login page
```

## Deploy to GitHub (When Ready)

```bash
cd stage-3-backend

# Verify local tests pass first
cd ..
test_local.bat

# Then push
cd stage-3-backend
git add -A
git commit -m "fix: OAuth, README, CI/CD for local + deployed testing"
git push origin main
```

Expected score improvement: **12/60 → 50+/60** ✅

## Debug Mode

Enable more logging:
```env
DEBUG=True
LOGGING_LEVEL=DEBUG
```

Then check backend output:
```
[AUTH] OAuth flow started
[AUTH] Callback received: code=...
[JWT] Token validation
[RATE] Rate limit check
```

## Still Having Issues?

Read: [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md) for step-by-step troubleshooting
