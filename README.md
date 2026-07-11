<div align="center">

# 🎓 GrievEase
### AI-Powered University Grievance Management System

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)](https://sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**A full-stack complaint management system built for universities. Students submit grievances online, AI auto-categorizes them, staff resolves them, and admins monitor everything in real time.**

[Live Demo](#) · [API Docs](#api-documentation) · [Report Bug](https://github.com/yourusername/grievease/issues)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Deployment Guide](#deployment-guide)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)

---

## Overview

GrievEase eliminates paper-based university complaint systems. Students file complaints online, an ML model automatically routes them to the right department, staff resolves them with full audit trails, and admins get live analytics dashboards.

**Problem:** Manual complaint systems are slow, untraceable, and inefficient.  
**Solution:** A fully digital system with AI prediction, SLA tracking, auto-escalation, and real-time notifications.

---

## Features

### 👨‍🎓 Student Portal
- Register/login with name, email, and admission number
- Submit complaints with file attachments (PDF, images)
- AI auto-predicts category and priority
- Duplicate detection prevents repeat submissions
- Track complaint status with full timeline
- Rate resolved complaints (1–5 stars)
- Real-time notifications on every status change

### 👥 Staff Portal
- Login with credentials created by admin
- View only assigned complaints
- Update status, add remarks, add internal notes
- SLA countdown visible per complaint
- Comment thread with students

### 🔒 Admin Panel
- Full complaint management with filters
- Live analytics — 6 charts (category, status, priority, monthly, department, staff performance)
- Staff management — create, update, deactivate
- Bulk status updates
- Escalation management (auto + manual trigger)
- CSV export and database backup
- Complete audit log
- Department management

### 🤖 AI Features
- **ML Model:** TF-IDF + Logistic Regression trained on 130+ university complaints
- **Auto-categorization:** 10 categories (Academic, Hostel, IT Support, Fees, etc.)
- **Priority prediction:** Low / Medium / High / Critical
- **Duplicate detection:** Prevents same complaint being submitted twice
- **AI Chatbot:** Guides students in describing issues, auto-predicts category

### ⚡ System Features
- JWT authentication with role-based access (Student / Staff / Admin / Super Admin)
- WebSocket real-time notifications
- SLA tracking with auto-escalation (Dept Head → Admin → Principal)
- Email notifications (SMTP)
- File upload support
- Full audit log (who did what, when, from where)

---

## Architecture

```
┌─────────────────────┐    HTTP/WS    ┌─────────────────────┐
│   Frontend (HTML)   │◄─────────────►│  Backend (FastAPI)  │
│   Vercel CDN        │               │  Render.com         │
└─────────────────────┘               └──────────┬──────────┘
                                                  │ SQLAlchemy
                                                  ▼
                                       ┌──────────────────────┐
                                       │  PostgreSQL (Neon)   │
                                       │  or SQLite (local)   │
                                       └──────────────────────┘
```

**Request Flow:**
1. Student opens `index.html` → clicks Student Portal
2. Fills login form → POST `/api/users/student/login` → JWT returned
3. JWT stored in localStorage → used in `Authorization: Bearer <token>` header
4. Student submits complaint → POST `/api/complaints/json`
5. Backend runs AI prediction → saves to DB → sends notification
6. Staff sees complaint → updates status → student gets real-time update via WebSocket

---

## Folder Structure

```
GrievEase/
├── frontend/                    # Static HTML/CSS/JS (deploy to Vercel)
│   ├── index.html               # Landing page
│   ├── student-login.html       # Student login
│   ├── staff-login.html         # Staff login
│   ├── admin-login.html         # Admin login
│   ├── student-dashboard.html   # Student portal
│   ├── staff-dashboard.html     # Staff portal
│   ├── admin-dashboard.html     # Admin panel
│   ├── style.css                # All styles
│   └── script.js                # All frontend logic
│
├── backend/                     # FastAPI Python app (deploy to Render)
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings from .env
│   │   ├── database.py          # SQLAlchemy engine (SQLite/PostgreSQL)
│   │   ├── models.py            # ORM models
│   │   ├── schemas.py           # Pydantic validation schemas
│   │   ├── crud.py              # Database operations
│   │   ├── auth.py              # JWT + bcrypt + role guards
│   │   ├── nlp.py               # AI prediction engine
│   │   ├── websocket_manager.py # Real-time WebSocket manager
│   │   ├── routes/
│   │   │   ├── users.py         # Login endpoints
│   │   │   ├── complaints.py    # Complaint CRUD + AI
│   │   │   ├── staff.py         # Staff management + dashboard
│   │   │   ├── notifications.py # Notification endpoints
│   │   │   └── admin_extra.py   # Analytics, audit, backup, CSV
│   │   ├── services/
│   │   │   ├── notification_service.py
│   │   │   ├── escalation_service.py
│   │   │   └── email_service.py
│   │   └── ml/
│   │       ├── category_model.pkl       # Trained ML model
│   │       ├── category_vectorizer.pkl  # TF-IDF vectorizer
│   │       └── train_model.py           # Model training script
│   ├── .env                     # Local env vars (not committed)
│   ├── .env.example             # Template for env vars
│   ├── requirements.txt
│   ├── runtime.txt
│   └── Procfile
│
├── database/
│   ├── grievease.db             # SQLite DB (local dev)
│   └── sample_data.csv          # Sample complaint data
│
├── deployment/
│   ├── render.yaml              # Render deployment config
│   └── vercel.json              # Vercel deployment config
│
├── docs/                        # Additional documentation
├── .gitignore
├── LICENSE
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Chart.js |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| **Database** | SQLite (dev) / PostgreSQL (production) |
| **AI/ML** | Scikit-learn (TF-IDF + Logistic Regression) |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |
| **Real-time** | WebSocket |
| **Email** | SMTP (Gmail / any provider) |
| **Deployment** | Vercel (frontend) + Render (backend) + Neon (PostgreSQL) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- VS Code with Live Server extension

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/grievease.git
cd grievease
```

### 2. Set up the backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and set your values

# Start the server
uvicorn app.main:app --reload
```

Backend will start at: `http://127.0.0.1:8000`  
API Docs available at: `http://127.0.0.1:8000/docs`

### 3. Open the frontend
Open `frontend/index.html` with VS Code Live Server.

### 4. Default credentials
| Role | Username/Email | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Student | Any email | Any name + admission no. |
| Staff | Created by Admin | Set by Admin |

---

## Environment Variables

All variables go in `backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLite or PostgreSQL connection string | `sqlite:///./grievease.db` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | ⚠️ Change in production |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes | `10080` (7 days) |
| `ADMIN_USERNAME` | Default admin username | `admin` |
| `ADMIN_PASSWORD` | Default admin password | `admin123` |
| `FRONTEND_URL` | Your Vercel URL (for CORS) | `` |
| `DEBUG` | Enable debug mode | `False` |
| `SMTP_USER` | Gmail address for email alerts | `` |
| `SMTP_PASS` | Gmail app password | `` |

**For PostgreSQL (Neon):**
```
DATABASE_URL=postgresql://username:password@ep-xxx.us-east-1.aws.neon.tech/grievease?sslmode=require
```

---

## API Documentation

Full interactive docs at: `http://127.0.0.1:8000/docs`

### Key Endpoints

#### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/users/student/login` | Student login / auto-register |
| POST | `/api/users/admin/login` | Admin login |
| POST | `/api/users/staff/login` | Staff login |
| GET | `/api/users/me` | Get current user info |

#### Complaints
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/complaints/stats` | Public | Landing page counters |
| GET | `/api/complaints/` | Any | Get complaints (filtered by role) |
| POST | `/api/complaints/json` | Any | Submit complaint (JSON) |
| GET | `/api/complaints/{id}` | Any | Get single complaint |
| PUT | `/api/complaints/{id}` | Staff/Admin | Update status |
| GET | `/api/complaints/predict-category` | Any | AI prediction |
| GET | `/api/complaints/analytics` | Admin | Analytics data |
| POST | `/api/complaints/bulk-update` | Admin | Bulk status update |
| GET | `/api/complaints/{id}/timeline` | Any | Complaint timeline |
| POST | `/api/complaints/{id}/comments` | Any | Add comment |

#### Staff
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/staff/dashboard/me` | Staff | Staff stats |
| GET | `/api/staff/dashboard/complaints` | Staff | Assigned complaints |
| POST | `/api/staff/` | Admin | Create staff member |
| GET | `/api/staff/` | Admin | List all staff |
| DELETE | `/api/staff/{id}` | Super Admin | Deactivate staff |

#### Admin
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/audit-logs` | Admin | Audit log |
| GET | `/api/admin/reports/complaints/csv` | Admin | Export CSV |
| GET | `/api/admin/backup` | Admin | Database backup |
| POST | `/api/admin/run-escalation` | Admin | Trigger escalation |
| GET | `/api/admin/departments` | Admin | List departments |

---

## Deployment Guide

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: GrievEase v3.0"
git remote add origin https://github.com/yourusername/grievease.git
git push -u origin main
```

### Step 2 — Set up Neon PostgreSQL (Free)
1. Go to [neon.tech](https://neon.tech) → Sign up free
2. Create a new project → Copy the **connection string**
3. It looks like: `postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require`

### Step 3 — Deploy Backend to Render (Free)
1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repo
3. Set **Root Directory:** `backend`
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables:
   - `DATABASE_URL` = your Neon connection string
   - `SECRET_KEY` = random 64-character string
   - `ADMIN_PASSWORD` = your secure password
   - `DEBUG` = `False`
7. Deploy → Copy the Render URL (e.g. `https://grievease-api.onrender.com`)

### Step 4 — Update Frontend API URL
In `frontend/index.html`, add before `</body>`:
```html
<script>window.__API_BASE__ = "https://grievease-api.onrender.com";</script>
```
Add the same line to all other HTML files.

### Step 5 — Deploy Frontend to Vercel
1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your GitHub repo
3. Set **Root Directory:** `frontend`
4. Click Deploy → Copy your Vercel URL
5. Go back to Render → Add env var `FRONTEND_URL` = your Vercel URL
6. Redeploy backend (so CORS gets updated)

✅ Done! Your app is live.

---

## Screenshots

> Add screenshots of your running application here.

| Landing Page | Student Dashboard | Admin Analytics |
|---|---|---|
| *screenshot* | *screenshot* | *screenshot* |

---

## Future Improvements

- [ ] Mobile app (React Native)
- [ ] Push notifications (Firebase FCM)
- [ ] Multi-language support (Hindi, Tamil, etc.)
- [ ] Chatbot with GPT-4 integration
- [ ] QR code complaint submission
- [ ] Video/audio attachment support
- [ ] Advanced ML model (BERT for complaint analysis)
- [ ] Department-wise SLA configuration
- [ ] Student satisfaction survey module
- [ ] Complaint category clustering analytics

---

## Contributing

Pull requests are welcome. For major changes, open an issue first.

---

## License

[MIT](LICENSE) © 2025 GrievEase
