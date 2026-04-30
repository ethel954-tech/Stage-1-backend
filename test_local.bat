@echo off
REM Test Local Backend - Windows

echo.
echo ======================================
echo Testing Insighta Labs+ Backend
echo ======================================
echo.

set BACKEND=http://127.0.0.1:8000
set FRONTEND=http://localhost:5500

REM Test 1: Backend responding
echo [Test 1] Testing if backend is running...
curl -s -I "%BACKEND%/auth/github?client_type=web" | findstr "200 302" >nul
if %errorlevel% equ 0 (
    echo OK: Backend is responding
) else (
    echo ERROR: Backend not responding at %BACKEND%
    echo Please run: start_backend.bat
    exit /b 1
)

REM Test 2: test_code endpoint
echo.
echo [Test 2] Testing test_code endpoint...
curl -s "%BACKEND%/auth/github/callback?code=test_code&state=test" | findstr "access_token" >nul
if %errorlevel% equ 0 (
    echo OK: test_code returns tokens
    echo (Check browser console for JSON response details)
) else (
    echo ERROR: test_code failed
    echo Response:
    curl -s "%BACKEND%/auth/github/callback?code=test_code&state=test"
    exit /b 1
)

REM Test 3: Rate limiting
echo.
echo [Test 3] Testing rate limiting (should get 429 on 11th request)...
for /L %%i in (1,1,15) do (
    for /f %%a in ('curl -s -w "%%{http_code}" -o nul "%BACKEND%/auth/github?client_type=web"') do (
        if %%i equ 11 (
            if %%a equ 429 (
                echo OK: Rate limiting working - got 429 on request 11
            ) else (
                echo WARNING: Expected 429 on request 11, got %%a
            )
        )
    )
    timeout /t 0 /nobreak >nul
)

REM Test 4: README exists
echo.
echo [Test 4] Checking if README.md exists...
if exist "stage-3-backend\README.md" (
    echo OK: README.md found
) else (
    echo ERROR: README.md not found
    exit /b 1
)

REM Test 5: GitHub Actions workflow
echo.
echo [Test 5] Checking if GitHub Actions workflow exists...
if exist "stage-3-backend\.github\workflows\ci.yml" (
    echo OK: .github/workflows/ci.yml found
) else (
    echo ERROR: GitHub Actions workflow not found
    exit /b 1
)

echo.
echo ======================================
echo All tests completed!
echo ======================================
echo.
echo Next steps:
echo 1. Open %FRONTEND% in browser
echo 2. Click "Continue with GitHub"
echo 3. Should redirect to GitHub login
echo.
echo To test full flow:
echo 1. Complete GitHub OAuth or use test_code
echo 2. Browser should redirect to dashboard
echo 3. Check profiles API
echo.
pause
