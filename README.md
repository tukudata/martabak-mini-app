# 🥞 MMDS (Martabak Mini Dayung Sari) - Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Django](https://img.shields.io/badge/Framework-Django_6.0-092E20?logo=django)](https://www.djangoproject.com/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC?logo=tailwind-css)](https://tailwindcss.com/)
[![Storage](https://img.shields.io/badge/Storage-Supabase_S3-3ECF8E?logo=supabase)](https://supabase.com/)
[![Deployment](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway)](https://railway.app/)

**MMDS** is an integrated operational management system designed specifically for the F&B industry (Martabak Mini). This application handles the entire business workflow, from employee management and branch coordination to automated daily reporting and profit/loss calculations.

---

## 📸 App Screenshots

### Main Dashboard
![Main Dashboard](screenshots/dashboard.png)

### Partner Performance Evaluation
![Partner Evaluation](screenshots/evaluasi.png)

---

## ✨ Key Features

### 🏗️ Modular Architecture
The application is divided into core modules for maximum scalability:
- **Corporate:** Management of Departments, Employees (with auto-generated IDs `DSXXXX`), and Branches.
- **Operations:** Daily Report (DR) inputs, partner attendance tracking, and operational expense logs.
- **System:** Centralized settings for dough constant formulas, target price per gram, and bonus/salary schemes.

### 🧠 Automation & Business Logic
- **Smart Calculation:** Automatically calculates Target Revenue, Gross Revenue, Remaining Dough, and Discrepancies (Plus/Minus) in real-time as data is saved.
- **Strict Validation:** Built-in partner **double-entry protection** to prevent duplicate inputs for the same branch or date.
- **Image Pipeline:** Automated compression for receipts and transfer proof using **Pillow (PIL)** before uploading to cloud storage.

### 📊 Modern Dashboard
- Custom admin dashboard built with **Tailwind CSS**, visualizing key metrics such as Total Revenue, Active Branches, Active Partners, and Total Discrepancies.
- Seamless UI integration using **Jazzmin** for a professional administrative experience.

### 📈 Evaluation & Summaries
- **Dynamic Reporting:** Performance evaluation features based on flexible date ranges.
- **Analytics Table:** Automatically aggregates total work duration (in hours), accumulated revenue, and total "minus" per partner.
- **Branch Performance:** Monitors daily branch departures to track outlet productivity.

---

## 🛠️ Tech Stack
- **Backend:** Python 3.x, Django 6.0
- **Frontend:** Tailwind CSS, Jazzmin Admin
- **Database:** PostgreSQL
- **File Storage:** Supabase S3 (Boto3)
- **Deployment:** Railway / WhiteNoise (Static Files)

---

## 🚀 Local Installation

1. **Clone Repository:**
   ```bash
   git clone [https://github.com/username/mmds-martabak.git](https://github.com/username/mmds-martabak.git)
   cd mmds-martabak

2. **Setup Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt

4. **Environment Variables: Create a .env file and fill in the following:**
   ```bash
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_URL=your_postgres_url
   SUPABASE_ACCESS_KEY_ID=your_key
   SUPABASE_SECRET_ACCESS_KEY=your_secret
   SUPABASE_S3_ENDPOINT=your_endpoint

5. **Run Migrations & Server:**
   ```bash
   python manage.py migrate
   python manage.py runserver

## 📄 License

This project is licensed under the MIT License - free to use for learning or further development provided that original attribution is maintained.
