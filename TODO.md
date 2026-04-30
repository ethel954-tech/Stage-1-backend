# GitHub OAuth Fix Plan

## Steps
- [x] 1. Fix authapp/views.py - test_code JSON + admin role check
- [x] 2. Fix backend1/settings.py - CORS_ALLOW_ALL_ORIGINS=True
- [x] 3. Fix backend1/middleware.py - rate limit /auth/github 10/min
- [x] 4. Run migrations (if needed)
- [ ] 5. Test endpoints
