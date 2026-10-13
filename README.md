# IRCTC Booking Platform

A full-featured IRCTC-like train booking platform with a React frontend that closely
resembles the real IRCTC website, backed by a FastAPI + SQLAlchemy API.

## Features

### Frontend (React + Vite)
- **Homepage** with IRCTC-style train search form, station autocomplete, quota/class selection
- **Train Search Results** with availability, class tabs, fare display, and "Book Now" action
- **Booking Flow** — multi-step (Passenger Details → Review & Payment → Confirmation)
- **PNR Status** — look up any booking, view passenger status, cancel with refund policy
- **My Bookings** — booking history with status filter (All/Confirmed/Cancelled)
- **Login & Registration** — JWT-based user authentication
- **Responsive Design** — works on desktop and mobile

### Backend (FastAPI + SQLite)
- **Train Search** across 42 stations and 50 trains (Rajdhani, Shatabdi, Duronto, Express)
- **Seat Availability** with real-time count per class/date
- **Ticket Booking** with PNR generation, multi-passenger, age-based discounts (child/senior)
- **Cancellation** with time-based refund policy (90%/50%/25%/0%)
- **User Auth** — register, login, JWT tokens (bcrypt password hashing)
- **Agent Chat** — natural-language booking assistant (keyword-based intent parsing)
- **Provider Abstraction** — pluggable data source (local SQLite or RapidAPI)

## Architecture

```
React Frontend (Vite, port 4200)
        │
        ▼  /api/*
FastAPI Backend (port 8000)
        │
routes  →  services  →  repositories  →  db (SQLAlchemy / SQLite)
                ▲
                │
          BookingAgent  (intent orchestrator)
```

| Layer         | Location                  | Responsibility                                    |
|---------------|---------------------------|---------------------------------------------------|
| Frontend      | `frontend/src/`           | React SPA with IRCTC-themed UI                    |
| API           | `backend/app/api/routes/` | FastAPI HTTP endpoints                            |
| Auth          | `backend/app/api/routes/auth.py` | JWT login/register/me                      |
| Agent         | `backend/app/agent/`      | Intent parsing + tool orchestration               |
| Services      | `backend/app/services/`   | Business rules (train, booking, payment, auth)    |
| Repositories  | `backend/app/repositories/` | Data access only                                |
| Schemas       | `backend/app/schemas/`    | Pydantic request/response contracts               |
| DB            | `backend/app/db.py`       | SQLAlchemy models (Station, Train, Coach, Booking, User) |

## Quick Start

### Option 1: Docker Compose

```bash
docker-compose up --build
```

- Frontend: http://localhost:4200
- Backend API: http://localhost:8000/docs

### Option 2: Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:4200 (proxies /api to backend)
- Swagger: http://localhost:8000/docs

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Login (returns JWT) |
| `GET`  | `/api/auth/me` | Current user profile |
| `GET`  | `/api/trains/stations` | List all stations |
| `GET`  | `/api/trains/search` | Search trains (source, destination, date) |
| `GET`  | `/api/trains/{number}/availability` | Check seat availability |
| `POST` | `/api/bookings` | Create a booking |
| `GET`  | `/api/bookings/{pnr}` | Get booking by PNR |
| `POST` | `/api/bookings/{pnr}/cancel` | Cancel booking |
| `GET`  | `/api/bookings` | List recent bookings |
| `POST` | `/api/agent/chat` | Agent chat (NL interface) |

## Seed Data

The platform comes pre-loaded with:
- **42 stations** — tier-1 metros + tier-2 cities across India
- **50 trains** — Rajdhani, Shatabdi, Duronto, Express, Intercity, Regional
- **Coach configurations** — class-specific seats and fares for each train

## Demo Walkthrough

1. Open http://localhost:4200
2. **Register** a new account (or browse without login)
3. **Search** trains: e.g., "New Delhi" (NDLS) to "Mumbai Central" (BCT)
4. **Select a train**, pick a class, click "Book Now"
5. **Add passengers** (name, age, gender, berth preference)
6. **Review** and click "Pay & Book"
7. **View confirmation** with PNR, passenger details, seat assignments
8. **Check PNR Status** or view **My Bookings** anytime
