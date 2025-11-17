# Car Dealership Management System

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)


```bash
# Clone repository
git clone https://github.com/yourusername/car-dealership-backend.git
cd car-dealership-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install pipenv
pipenv install --dev

# Copy environment file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Redis
redis-server

# Terminal 1: Start Django
python manage.py runserver

# Terminal 2: Start Celery Worker
celery -A config worker -l info

# Terminal 3: Start Celery Beat
celery -A config beat -l info
```

---

## Documentation

### API Documentation
- **Swagger UI**: http://localhost:8000/api/docs/swagger/
- **ReDoc**: http://localhost:8000/api/docs/redoc/

### Key Endpoints

#### Authentication
```
POST   /api/auth/token/                   - Get JWT token
POST   /api/auth/token/refresh/           - Refresh token
POST   /api/customers/register/           - Register new customer
POST   /api/auth/password-reset-request/  - Reset password
```

#### Dealerships
```
GET    /api/dealerships/                  - List dealerships
POST   /api/dealerships/                  - Create dealership
GET    /api/dealerships/{id}/             - Get dealership details
PATCH  /api/dealerships/{id}/             - Update dealership
```

#### Suppliers
```
GET    /api/suppliers/                    - List suppliers
GET    /api/supplier-offers/              - List supplier offers
GET    /api/supplier-actions/             - List supplier promotions
```

#### Transactions
```
GET    /api/offers/                       - List customer offers
POST   /api/offers/                       - Create offer
GET    /api/transactions/                 - List transactions
```

#### Statistics
```
GET    /api/stats/global/                 - Global statistics
GET    /api/stats/dealerships/{id}/       - Dealership stats
GET    /api/stats/me/                     - Customer own stats
```

---

## Celery Tasks

### Scheduled Tasks

| Task | Frequency | Description |
|------|-----------|-------------|
| `process_dealership_purchases` | Every 10 min | Auto-purchase cars from suppliers |
| `update_all_preferred_suppliers` | Every hour | Update supplier preferences |
| `process_pending_offers` | Every 5 min | Process customer offers |
| `cleanup_expired_offers` | Daily at 3 AM | Clean old offers |
| `generate_daily_reports` | Daily at 11:50 PM | Generate statistics |