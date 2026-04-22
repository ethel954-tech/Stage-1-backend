# Profile Manager App

## 🎯 Overview
Modern full-stack web app for managing AI-generated user profiles. Built with **Django REST Framework** (backend) + **vanilla HTML/CSS/JS** (modern frontend).

**Live Demo:** Open `frontend/index.html` (backend must run at `http://127.0.0.1:8000`).

## ✨ Features
- **Add Profiles:** Enter name → POST to API → instant add
- **Filter & Load:** Dropdown toggle (▼/▲) → filter by Gender/Age → beautiful animated cards
- **Delete:** Per-profile delete with confirmation → auto-refresh list
- **Smart UX:**
  - Profiles **auto-clear** when closing filters
  - Smooth animations (staggered cards, dropdown slide)
  - Hover effects, glassmorphism, gradients
  - Responsive (mobile/desktop), empty/error states
  - Emojis, modern Inter font

## 🏗️ Tech Stack
- **Backend:** Django 5 + DRF + SQLite (`profiles` app: models/serializers/views/urls)
- **Frontend:** Pure HTML/CSS/JS (no build tools)
- **API:** `GET/POST/DELETE /api/profiles/` (filter ?gender= & ?age_group=)
- **Styles:** CSS3 gradients, backdrop-filter, @keyframes

## 🚀 Quick Start
1. **Backend:**
   ```
   cd backend1
   python manage.py migrate
   python manage.py runserver
   ```
2. **Frontend:** Open `frontend/index.html` in browser
3. **Test:** Add profiles → filter → delete → toggle hides everything

## 📁 Structure
```
backend1/          # Django project
├── profiles/      # App (models/views/API)
frontend/          # index.html (SPA)
manage.py          # Django CLI
db.sqlite3         # Data
README.md          # This file
```

## 🔮 Example Profiles Data
```
Name: John Doe
Gender: male
Age: 28 (adult) 
Country: 1
```

Profiles persist in SQLite. API ready for extensions (auth/charts/export).

## 🧠 Natural Language Query Engine
### Approach
Our parsing logic uses rule-based tokenization and regular expressions:
- **Gender:** Maps synonyms (males, guys, ladies) to strict gender categories.
- **Age Groups:** Recognizes keywords like "teenager" or "adult" to apply `age_group` filters.
- **Young Keyword:** Specifically maps "young" to the age range **16-24** (min_age=16, max_age=24).
- **Numerical Logic:** Detects phrases like "above X" or "over X" to apply `gte` filters.
- **Geographic Mapping:** A predefined ISO mapping converts country names (e.g., "Nigeria") to `country_id` ("NG").

### Limitations
- **Complex Logic:** Does not support nested boolean queries (e.g., "males from Nigeria AND females from Kenya").
- **Typos:** Matching is keyword-specific; misspelled country names will not be recognized.
- **Negation:** The parser does not handle negative constraints (e.g., "not from USA").

**Built with ❤️ by BLACKBOXAI** – Modern, beautiful, functional!
