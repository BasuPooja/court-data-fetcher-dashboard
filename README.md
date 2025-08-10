# 🏛 Court-Data Fetcher & Mini-Dashboard

A Flask-based system to fetch case details from an Indian district court website, store them in a database, and display them via a mini-dashboard with PDF report generation.

---

## 📋 Court Chosen
- **District Court: Faridabad (Haryana)**
- **Portal:** eCourts Services Portal (https://faridabad.dcourts.gov.in/)
- Scraping targets:
  - Parties’ names
  - Filing & next-hearing dates
  - Order/judgment PDF links (latest available)
  - Registration details
  - Status

---

## ⚙️ Setup Steps

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/court-data-fetcher.git
cd court-data-fetcher
```

### 2️⃣ Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3️⃣ Install Requirements
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Environment Variables
Create a `.env` file in the root folder (see **Sample Env Vars** section).

### 5️⃣ Initialize Database
```bash
flask db upgrade
```
or for SQLite:
```bash
python
>>> from app import db
>>> db.create_all()
```

### 6️⃣ Run the Application
```bash
flask run
```
Access it at **http://127.0.0.1:5000**

---

## 🔑 CAPTCHA Strategy

### Problem
Many Indian court sites use image CAPTCHAs or viewstate tokens to block bots.

### Our Approach:
1. **Custom Local CAPTCHA** for user verification before making requests to the court site.
2. For actual court CAPTCHAs:
   - Option A: Use **manual human input** within the UI (simplest, legal).
   - Option B: Use OCR (Tesseract) for **non-distorted CAPTCHAs** — if legally permitted.
3. **Viewstate & hidden form fields**:
   - Extracted dynamically using `BeautifulSoup` from the first GET request.
   - Passed back with POST request containing case search details.

---

## 🌱 Sample `.env` File

```env
# Flask Settings
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=supersecretkey123

# Database URL (Choose one)
DATABASE_URL=sqlite:///court_data.db
# DATABASE_URL=postgresql+psycopg2://username:password@localhost/court_db

# Selenium Settings
SELENIUM_DRIVER=chrome
SELENIUM_HEADLESS=True

# Logging
LOG_LEVEL=INFO
```

---

## 📂 Features
- **Search UI**: Case Type, Case Number, Filing Year, Court Complex
- **Scraping Layer**: Requests/Selenium + BeautifulSoup
- **Data Storage**: PostgreSQL or SQLite
- **Dashboard**: Case trends, status distribution, top case types
- **PDF Generation**: xhtml2pdf + custom styled report
- **Error Handling**: User-friendly messages

---

## 🖼 Dashboard Preview
*(Add screenshots here if available)*

---

## 📜 License
This project is for educational/demo purposes only. Scraping court websites may be subject to legal restrictions — **always comply with applicable laws**.
