# RecoveryAI

AI-powered revenue recovery system for identifying failed payments, selecting intelligent recovery strategies, and managing recovery attempts through a full-stack dashboard.

## Project Status

🚀 **Day 7 — Core recovery platform completed and tested.**

## Overview

RecoveryAI is a full-stack revenue recovery platform designed to help businesses manage failed payments.

The system analyzes failed payments and determines an appropriate recovery strategy based on:

- Payment failure reason
- Payment amount
- Previous recovery attempts
- Recovery score
- Retry limits

The platform provides a dashboard where recovery attempts can be created, executed, monitored, and escalated to manual review when automatic recovery is no longer appropriate.

## Tech Stack

### Frontend
- React
- Vite
- JavaScript
- CSS

### Backend
- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

### Database
- PostgreSQL
- Neon PostgreSQL

## Core Features

### 1. Recovery Queue

Displays all failed payments that require recovery.

Each payment includes:

- Customer information
- Payment amount
- Currency
- Failure reason
- Due date
- Number of previous recovery attempts
- Recommended recovery strategy
- Recovery priority
- Recovery score

### 2. Intelligent Recovery Strategy

RecoveryAI determines a recovery action based on the payment failure reason and recovery history.

Supported strategies:

- `retry_payment`
- `update_payment_method`
- `contact_customer`
- `manual_review`

| Failure Reason | Recovery Strategy |
|---|---|
| Insufficient funds | Retry payment |
| Card expired | Update payment method |
| Card declined | Retry payment |
| Bank declined | Contact customer |
| Network error | Retry payment |

### 3. Recovery Scoring

Each failed payment receives a recovery score based on factors such as:

- Failure reason
- Payment amount
- Previous recovery attempts

Repeated recovery attempts reduce confidence in another automatic action.

### 4. Retry Guardrails

RecoveryAI prevents unlimited automatic recovery attempts.

Once the retry threshold is reached, the system stops automatic recovery and recommends:

```text
manual_review
```

### 5. Recovery Attempts

Users can create recovery attempts for failed payments.

Each attempt records:

- Payment ID
- Recovery strategy
- Channel
- Message
- Status
- Attempt timestamp

Supported statuses:

- `pending`
- `sent`
- `completed`
- `failed`

### 6. Recovery Execution

Recovery attempts can be executed directly from the dashboard.

The backend currently simulates execution while enforcing retry limits.

Possible actions include:

- Payment retry requested
- Payment method update requested
- Customer contact requested
- Manual review requested
- Escalation when retry limits are reached

### 7. Analytics Dashboard

The dashboard provides:

- Total recovery attempts
- Successful attempts
- Failed attempts
- Pending attempts
- Recovery success rate
- Strategy breakdown

### 8. Recovery History

The dashboard displays previously created recovery attempts and their current status, providing visibility into the recovery lifecycle.

## API Endpoints

### Health

```text
GET /
GET /health
GET /health/database
```

### Recovery Queue

```text
GET /api/recovery
```

Optional filters:

```text
GET /api/recovery?priority=high
GET /api/recovery?failure_reason=network_error
```

### Recovery Statistics

```text
GET /api/recovery/stats
```

### Recovery Analytics

```text
GET /api/recovery/analytics
```

### Recovery Attempts

```text
GET /api/recovery/attempts
```

### Create Recovery Attempt

```text
POST /api/recovery/attempts/{payment_id}
```

### Update Recovery Attempt

```text
PATCH /api/recovery/attempts/{attempt_id}
```

Example:

```json
{
  "status": "completed"
}
```

### Execute Recovery Attempt

```text
POST /api/recovery/attempts/{attempt_id}/execute
```

### Get Recovery Strategy

```text
GET /api/recovery/{payment_id}
```

## Running the Backend

From the project root:

```powershell
cd backend
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

## Running the Frontend

Open another PowerShell terminal from the project root:

```powershell
cd frontend
```

Install dependencies if required:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Database

RecoveryAI uses PostgreSQL for persistent storage and is configured to work with hosted PostgreSQL such as Neon.

Database credentials should be provided through environment variables.

**Never commit real database credentials to GitHub.**

Use `.env.example` as the configuration template.

## Project Structure

```text
RecoveryAI/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── services/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── seed.py
│   │   └── __init__.py
│   ├── .venv/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── data/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

## Recovery Flow

```text
Failed Payment
      ↓
Analyze Failure Reason
      ↓
Calculate Recovery Score
      ↓
Determine Recovery Strategy
      ↓
Check Previous Attempts
      ↓
Retry Limit Reached?
      │
   ┌──┴──┐
  Yes    No
   │      │
   ↓      ↓
Manual   Execute
Review   Strategy
           │
           ↓
     Record Attempt
           │
           ↓
     Update Dashboard
```

## Example Recovery Decisions

### Insufficient Funds

```text
Strategy: retry_payment
Priority: medium
```

The system recommends retrying the payment after the customer has had an opportunity to replenish funds.

### Card Expired

```text
Strategy: update_payment_method
Priority: medium
```

The customer should update their payment method before another payment attempt.

### Bank Declined

```text
Strategy: contact_customer
Priority: medium
```

The system recommends contacting the customer rather than repeatedly retrying the transaction.

### Network Error

```text
Strategy: retry_payment
Priority: high
```

Network-related failures are suitable for another payment retry, subject to retry guardrails.

### Retry Limit Reached

```text
Strategy: manual_review
Priority: high
```

The system stops automatic recovery after the configured retry threshold.

## Development Notes

The recovery execution layer currently simulates external actions.

Future production integrations could connect recovery strategies to:

- Payment providers
- Email services
- SMS providers
- Customer communication platforms
- Background job systems

The current architecture keeps these integrations separate from the core recovery decision engine.

## Security Notes

- Never commit `.env` files.
- Never expose database passwords in source code.
- Use `.env.example` for required configuration variables.
- Configure production CORS origins before deployment.
- Replace simulated recovery actions with authenticated payment-provider integrations in production.

## Future Improvements

Potential future extensions include:

- Stripe/payment gateway integration
- Automated email recovery campaigns
- Background retry scheduling
- AI/LLM-powered recovery messaging
- Customer lifetime value based prioritization
- Advanced recovery prediction models
- Authentication and role-based access
- Production deployment
- Real-time analytics
- Webhooks for payment status updates

## License

This project is currently intended for development and demonstration purposes.
