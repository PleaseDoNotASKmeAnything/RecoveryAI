# RevPay

> **AI-assisted revenue recovery platform for failed payments**

RevPay is a full-stack revenue recovery platform that identifies failed payments, evaluates their recovery potential, recommends the next best recovery action, and manages bounded recovery attempts through an interactive dashboard.

The system combines deterministic recovery decisioning, scoring, retry guardrails, execution tracking, escalation, and analytics into a single workflow.

## 🎯 Problem

Failed payments directly affect business revenue.

A failed transaction should not simply be retried indefinitely. Different failure reasons require different interventions, and repeated unsuccessful attempts can lead to unnecessary retries, poor customer experience, and operational overhead.

RevPay addresses this by creating a structured recovery workflow:

```text
Failed Payment
      ↓
Analyze Failure
      ↓
Score Recovery Potential
      ↓
Select Recovery Strategy
      ↓
Check Recovery History
      ↓
Execute Bounded Action
      ↓
Success / Retry / Escalate
```

## 💡 Solution

RevPay turns a failed payment into an actionable recovery case.

For every failed payment, the system considers:
- Failure reason
- Payment amount
- Previous recovery attempts
- Recovery score
- Retry limits

It then recommends an appropriate recovery strategy.

The system also maintains a complete recovery-attempt history and prevents an already-processed attempt from being executed again.

When automatic recovery is no longer appropriate, the system escalates the payment to `manual_review`.

# 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │      React UI        │
                    │      Vite            │
                    └──────────┬───────────┘
                               │ REST API
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI         │
                    │      Backend         │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │  Recovery   │ │  Recovery   │ │  Analytics  │
        │  Decision   │ │  Execution  │ │   Service   │
        │   Engine    │ │   Engine    │ │             │
        └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
               │               │               │
               └───────────────┼───────────────┘
                               ▼
                    ┌──────────────────────┐
                    │    PostgreSQL        │
                    │       Neon           │
                    └──────────────────────┘
```

# 🧠 Recovery Decision Engine

RevPay currently uses a **deterministic, rule-based decision engine** rather than a trained machine-learning model.

This makes the recovery decisions:
- Explainable
- Reproducible
- Easy to audit
- Easy to test
- Bounded by explicit business rules

### Supported Strategies

| Failure Reason | Recommended Strategy |
|---|---|
| `insufficient_funds` | `retry_payment` |
| `card_expired` | `update_payment_method` |
| `card_declined` | `retry_payment` |
| `bank_declined` | `contact_customer` |
| `network_error` | `retry_payment` |
| Maximum attempts reached | `manual_review` |

# 📊 Recovery Scoring

Each failed payment receives a recovery score based on recovery-related signals such as payment failure reason, payment amount, and previous recovery attempts.

The score helps prioritize recovery cases and determine whether automatic recovery remains appropriate.

```text
Payment
   ↓
Failure Reason
   ↓
Recovery Score
   ↓
Priority
   ↓
Recommended Action
```

# 🛡️ Recovery Guardrails

RevPay is designed around **bounded recovery actions**.

## Retry Limit

Automatic retry attempts are limited. Once the retry threshold is reached, the payment is escalated to manual review.

```text
Automatic Recovery
        ↓
Retry Limit Reached
        ↓
Manual Review
```

## Duplicate Execution Protection

A recovery attempt can only enter the execution engine while its status is `pending`. Once processed, attempting to execute the same recovery attempt again is rejected.

```text
pending → execute → sent → ❌ execute again
```

# 🔄 Recovery Lifecycle

Each recovery attempt follows a tracked lifecycle:

```text
pending
   │
   ▼
execute
   │
   ▼
sent / completed
   │
   └──────────────► failed
```

Supported statuses:
- `pending`
- `sent`
- `completed`
- `failed`

Every attempt stores the payment ID, recovery strategy, channel, recovery message, status, and attempt timestamp.

# ⚡ Recovery Execution

Depending on the selected strategy, the system currently simulates actions such as:

```text
retry_payment          → Payment retry requested
update_payment_method  → Customer prompted to update payment method
contact_customer       → Customer contact requested
manual_review          → Payment flagged for manual review
```

### Important

The current execution layer **simulates the external recovery action**. It does not currently perform a real monetary transaction or charge a customer.

# 📈 Analytics Dashboard

RevPay provides recovery analytics including:
- Total recovery attempts
- Successful attempts
- Failed attempts
- Pending attempts
- Recovery attempt success rate
- Strategy distribution

# 🖥️ Dashboard

The frontend provides a centralized recovery workspace.

### Recovery Queue

View customer, payment amount, failure reason, recovery priority, recovery score, previous attempts, and recommended strategy.

### Recovery Actions

The UI dynamically changes based on the payment's recovery history and retry limits:

```text
Create Attempt → Execute → Create Next Attempt → Manual Review
```

# 🔌 API

RevPay exposes a REST API through FastAPI.

## Health

```http
GET /
GET /health
GET /health/database
```

## Recovery Queue

```http
GET /api/recovery
GET /api/recovery?priority=high
GET /api/recovery?failure_reason=network_error
```

## Recovery Statistics

```http
GET /api/recovery/stats
```

## Recovery Analytics

```http
GET /api/recovery/analytics
```

## Recovery Attempts

```http
GET /api/recovery/attempts
```

## Create Recovery Attempt

```http
POST /api/recovery/attempts/{payment_id}
```

## Update Recovery Attempt

```http
PATCH /api/recovery/attempts/{attempt_id}
```

Example:

```json
{
  "status": "completed"
}
```

## Execute Recovery Attempt

```http
POST /api/recovery/attempts/{attempt_id}/execute
```

## Get Recovery Strategy

```http
GET /api/recovery/{payment_id}
```

# 🗄️ Database

RevPay uses PostgreSQL for persistent storage. The development environment uses **Neon PostgreSQL**.

The database stores:

```text
customers
subscriptions
payments
recovery_attempts
```

The recovery-attempt table provides the historical state required for retry counting, strategy selection, execution tracking, analytics, and escalation.

### Security

Database credentials are provided through environment variables.

**Never commit real database credentials to GitHub.**

Use `.env.example` as the configuration template.

# 🛠️ Tech Stack

## Frontend
- React
- Vite
- JavaScript
- CSS

## Backend
- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

## Database
- PostgreSQL
- Neon PostgreSQL

## Architecture
- REST API
- Rule-based recovery engine
- Stateful recovery workflow
- Persistent recovery history
- Analytics

# 📁 Project Structure

```text
RevPay/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── customer.py
│   │   │   ├── payment.py
│   │   │   ├── recovery.py
│   │   │   └── subscription.py
│   │   │
│   │   ├── services/
│   │   │   └── recovery_service.py
│   │   │
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── seed.py
│   │   └── __init__.py
│   │
│   ├── .venv/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   │
│   ├── package.json
│   └── vite.config.js
│
├── data/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

# 🚀 Running Locally

## 1. Clone

```powershell
git clone https://github.com/PleaseDoNotASKmeAnything/RevPay.git
cd RevPay
```

## 2. Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend: `http://127.0.0.1:8000`

Docs: `http://127.0.0.1:8000/docs`

## 3. Frontend

Open another PowerShell terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

# 🔐 Environment Configuration

Create required configuration based on `.env.example`:

```text
DATABASE_URL=your_postgresql_connection_string
```

Do not commit `.env` files containing real credentials.

# 🧪 Example Recovery Flow

For insufficient funds:

```text
Payment Failed
      ↓
Failure = insufficient_funds
      ↓
Recovery Engine
      ↓
Strategy = retry_payment
      ↓
Create Recovery Attempt
      ↓
Execute Attempt
      ↓
Retry Requested
```

If repeated retries fail:

```text
Retry Attempt 1
      ↓
Retry Attempt 2
      ↓
Retry Attempt 3
      ↓
Maximum Attempts Reached
      ↓
manual_review
```

# 🎬 Demo Flow

1. Open the dashboard and view the failed-payment recovery queue.
2. Inspect failure reason, amount, recovery score, priority, and previous attempts.
3. Create a recovery attempt; the backend determines the appropriate strategy.
4. Execute the attempt; the execution engine performs the corresponding simulated action.
5. Observe `pending → sent`.
6. For retryable payments, create additional attempts until the retry threshold is reached.
7. Observe escalation from `retry_payment` to `manual_review`.
8. Review analytics and strategy breakdown.


The implementation focuses on:
- Explainable recovery decisions
- Bounded automatic actions
- Retry limits
- Manual escalation
- Recovery history
- Execution state tracking
- Duplicate-execution protection
- Analytics

The current system uses simulated execution so that the complete recovery workflow can be demonstrated safely without performing real customer charges.

# 🧩 Design Principles

### Explainability
Every recovery recommendation is based on explicit rules and payment context.

### Bounded Automation
Automatic actions have defined limits.

### Human Escalation
When automatic recovery is no longer appropriate, the system moves the case to manual review.

### Auditability
Every recovery attempt is persisted with its strategy, status, message, and timestamp.

### Safety
An already-processed recovery attempt cannot be executed again.

### Separation of Decision and Execution
The system first determines **what should happen?** and then separately executes the selected recovery action.

# 🔮 Future Improvements

Potential future extensions:
- Razorpay test-mode Payment Link integration
- Razorpay webhook integration
- Real payment-status synchronization
- LLM-assisted recovery reasoning
- Learned recovery scoring
- Customer communication through email/SMS
- Automated recovery outcome tracking
- More advanced prioritization
- Historical recovery-performance analysis
- Role-based access control
- Production deployment

# 📌 Current Status

```text
✅ Recovery queue
✅ Recovery strategy engine
✅ Recovery scoring
✅ Retry limits
✅ Manual escalation
✅ Recovery attempt tracking
✅ Recovery execution flow
✅ Duplicate execution protection
✅ Analytics dashboard
✅ PostgreSQL persistence
✅ FastAPI backend
✅ React frontend
✅ Local development setup
```

# 👨‍💻 Author

**Aayush Negi**

Computer Science & Engineering

Built as a full-stack AI-assisted revenue recovery platform.
