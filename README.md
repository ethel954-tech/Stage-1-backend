# Profile Manager API

This is a backend API built with Django REST Framework that manages user profiles and provides advanced querying capabilities, including rule-based natural language search.

---

## 🚀 Features

- Create and retrieve user profiles
- Advanced filtering using query parameters
- Sorting and pagination
- Rule-based natural language query parsing
- Input validation with proper error responses

---

## ⚙️ Setup Instructions

1. Clone the repository:
   git clone <your-repo-link>

2. Navigate into the project:
   cd project-folder

3. Create a virtual environment:
   python -m venv venv

4. Activate the environment:
   Windows: venv\Scripts\activate  
   Mac/Linux: source venv/bin/activate

5. Install dependencies:
   pip install -r requirements.txt

6. Apply migrations:
   python manage.py migrate

7. Seed the database:
   python manage.py seed_profiles

8. Run the server:
   python manage.py runserver

---

## 📡 API Endpoints

### 1. List Profiles
GET /api/profiles/

Supports:

Filtering:
- gender
- age_group
- country_id
- min_age
- max_age
- min_gender_probability
- min_country_probability

Sorting:
- sort_by = age | created_at | gender_probability
- order = asc | desc

Pagination:
- page (default: 1)
- limit (max: 50)

---

### 2. Natural Language Search
GET /api/profiles/search/?q=<query>

This endpoint allows users to search using plain English queries.

---

## 🧠 Natural Language Parsing Approach

The system uses a **rule-based parsing engine** built with Python’s `re` (regular expressions) module.

### 1. Keyword Detection

The parser scans the query string and extracts meaning using predefined keyword patterns.

#### Gender Detection
- male → male, males, men, boys
- female → female, females, women, girls

#### Gender Conflict Rule
If both male and female appear:
→ No gender filter is applied

Example:
"male and female teenagers" → returns all teenagers

---

### 2. Age Interpretation

#### "Young" Mapping
- "young" → age range 16–24  
  (min_age = 16, max_age = 24)

#### Numeric Conditions
- "above 30" → age >= 30
- "below 20" → age <= 20

These override default mappings when present.

---

### 3. Age Group Detection

- "adult" → age_group = adult
- "teenager", "teens" → age_group = teenager

---

### 4. Country Mapping

A predefined dictionary maps country names to ISO codes:

- nigeria → NG
- kenya → KE
- angola → AO

The parser detects both:
- "nigeria"
- "from nigeria"

---

### 5. Combined Query Handling

The parser supports combining multiple filters:

Examples:

| Query | Interpretation |
|------|--------------|
| young males | gender=male, age 16–24 |
| females above 30 | gender=female, age >= 30 |
| people from nigeria | country_id=NG |
| adult males from kenya | gender=male, age_group=adult, country=KE |
| male and female teenagers above 17 | age_group=teenager, age >= 17 (no gender filter) |

---

## 📦 Response Format

### Success Response
