# WhatsApp Weekly PDF Report Automation System

A production-ready, enterprise backend service engineered with **Python FastAPI**, **PostgreSQL**, **ReportLab**, **APScheduler**, and the official **Meta WhatsApp Cloud API (Graph API v21.0)**.

The system automatically compiles executive-grade PDF reports every week (configured in the `Asia/Kolkata` timezone), saves them to persistent storage, uploads media to Meta's servers, and dispatches document messages to opted-in WhatsApp recipients, tracking end-to-end delivery states via secure webhooks.

---

> [!IMPORTANT]
> **Production Notice & Meta Credentials Disclaimer:**
> **Do not claim that WhatsApp delivery works until valid Meta credentials and a configured business phone number have been supplied and tested.** In local or test environments without live credentials, reports are safely compiled with ReportLab, persisted to PostgreSQL/SQLite, and made available for immediate direct download via `GET /reports/{report_id}/download`.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Project Directory Structure](#project-directory-structure)
- [Prerequisites](#prerequisites)
- [How to Run this Project in VS Code](#how-to-run-this-project-in-vs-code)
- [Local Setup (CLI / Terminal)](#local-setup-cli--terminal)
- [Environment Variables Reference](#environment-variables-reference)
- [Meta WhatsApp Cloud API Configuration](#meta-whatsapp-cloud-api-configuration)
  - [1. Create Meta Developer App & WhatsApp Business Account](#1-create-meta-developer-app--whatsapp-business-account)
  - [2. Generate Permanent System User Access Token](#2-generate-permanent-system-user-access-token)
  - [3. Configure WhatsApp Template (for Out-of-Window Messaging)](#3-configure-whatsapp-template-for-out-of-window-messaging)
  - [4. Webhook Setup & Live Verification via ngrok](#4-webhook-setup--live-verification-via-ngrok)
- [API Reference & Swagger Documentation](#api-reference--swagger-documentation)
- [Weekly Workflow & Scheduling (APScheduler)](#weekly-workflow--scheduling-apscheduler)
- [Running Unit & Integration Tests](#running-unit--integration-tests)
- [Docker & Containerized Deployment](#docker--containerized-deployment)
- [Cloud Deployment (Railway & Render)](#cloud-deployment-railway--render)
- [Module Architecture Guide](#module-architecture-guide)

---

## System Architecture

```
                                  ┌──────────────────────────────────────────┐
                                  │   Meta WhatsApp Cloud API (v21.0)        │
                                  │   - Media Upload (PDF)                   │
                                  │   - Document Messages (wamid)            │
                                  │   - Real-time Webhooks (Statuses)        │
                                  └───────▲───────────────────────┬──────────┘
                                          │ Media / Messages      │ Delivery Updates
                                          │ (HTTPS)               │ (HMAC-SHA256)
┌─────────────────────────────────────────┴───────────────────────▼──────────┐
│              WhatsApp Weekly PDF Report Automation System                  │
│                                                                            │
│   ┌────────────────────┐   ┌─────────────────────┐   ┌─────────────────┐   │
│   │  FastAPI (Uvicorn) │   │ APScheduler Engine  │   │  ReportLab      │   │
│   │  - REST Endpoints  │   │ - Asia/Kolkata TZ   │   │  - Vector Charts│   │
│   │  - Webhook Auth    │   │ - Mon 09:00 AM IST  │   │  - KPI Tables   │   │
│   │  - Swagger /docs   │   │ - Deduplication Lock│   │  - 2-Pass Canvas│   │
│   └─────────┬──────────┘   └──────────┬──────────┘   └────────┬────────┘   │
│             │                         │                       │            │
│   ┌─────────▼─────────────────────────▼───────────────────────▼────────┐   │
│   │                   Report Orchestration Service                     │   │
│   └───────────────────────────────────┬────────────────────────────────┘   │
└───────────────────────────────────────┼────────────────────────────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
  ┌───────────────────────────────┐             ┌─────────────────────────────┐
  │     PostgreSQL Database       │             │   Persistent Storage        │
  │  - recipients                 │             │   - storage/reports/*.pdf   │
  │  - schedules                  │             │   - Stream Download Route   │
  │  - reports                    │             │                             │
  │  - message_delivery_logs      │             │                             │
  └───────────────────────────────┘             └─────────────────────────────┘
```

---

## Key Features

1. **Enterprise PDF Compilation (ReportLab)**:
   - Dynamic 2-pass `NumberedCanvas` computing running page numbers (`Page X of Y`), running headers, and confidentiality notices.
   - High-resolution corporate branding with `#1E3A8A` executive styling.
   - Key Performance Indicator (KPI) metrics cards (Total Revenue, Active Subscribers, Messages Delivered, System Uptime, WoW Growth).
   - Embedded vector bar charts rendered without external image conversion.
   - Daily operational breakdown table with alternating row striping.
   - Download endpoint: `GET /reports/{report_id}/download` with streaming `FileResponse`.

2. **Official Meta WhatsApp Cloud API**:
   - Official Graph API `v21.0` endpoints (`https://graph.facebook.com/v21.0`).
   - Secure media upload (`POST /{phone_number_id}/media`) to obtain `media_id`.
   - Native document message dispatch (`type: "document"`).
   - Template messaging fallback (`POST /{phone_number_id}/messages` with document header).
   - Exponential backoff retries on transient network disconnects.

3. **APScheduler with Asia/Kolkata Timezone**:
   - Automated weekly report trigger (default: every Monday at 09:00 AM IST).
   - Job deduplication mutex preventing overlapping runs.
   - Cycle-aware check preventing duplicate reports generated within 18 hours.
   - Dynamic synchronization with PostgreSQL `schedules` table.

4. **Security & Webhook Handling**:
   - Webhook verification challenge handshake (`GET /webhook`).
   - HMAC-SHA256 signature verification (`POST /webhook`) validating `X-Hub-Signature-256` header against `META_APP_SECRET`.
   - Real-time delivery status tracking: updates logs from `sent` -> `delivered` -> `read` or `failed`.
   - Inbound keyword processing: recipient replies `STOP` to opt out and `START` to opt back in.

5. **Database & Migrations**:
   - PostgreSQL support via SQLAlchemy 2.0 with connection pooling and `pool_pre_ping`.
   - Full Alembic migration suite (`alembic/versions/001_initial_schema.py`).
   - Built-in SQLite zero-configuration fallback for local testing in VS Code.

---

## Project Directory Structure

```
whatsapp-cloud-api-backend-main/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application factory & lifespan
│   ├── core/
│   │   ├── config.py               # Pydantic v2 BaseSettings & Meta validation
│   │   ├── database.py             # SQLAlchemy Engine, SessionLocal & get_db
│   │   ├── logging.py              # Structured logging configuration
│   │   └── security.py             # HMAC-SHA256 signature verification
│   ├── models/
│   │   ├── recipient.py            # Recipient table (opt-ins, phone numbers)
│   │   ├── schedule.py             # Schedule configuration table
│   │   ├── report.py               # Generated report metadata table
│   │   └── delivery_log.py         # Message delivery status tracking table
│   ├── schemas/
│   │   ├── recipient.py            # Pydantic request/response validation schemas
│   │   ├── schedule.py             # Schedule create/update schemas
│   │   ├── report.py               # Report generation schemas
│   │   ├── delivery_log.py         # Delivery logs and aggregates
│   │   └── webhook.py              # Meta Cloud API webhook schemas
│   ├── services/
│   │   ├── pdf_generator.py        # ReportLab PDF compilation & chart rendering
│   │   ├── storage.py              # Persistent storage file operations & security
│   │   ├── whatsapp_client.py      # Meta WhatsApp Cloud API client
│   │   ├── scheduler_service.py    # APScheduler in Asia/Kolkata timezone
│   │   └── report_service.py       # Report generation & distribution workflow
│   └── api/
│       ├── deps.py                 # Dependency injection
│       └── v1/
│           ├── router.py           # Combined API router
│           ├── health.py           # GET /health
│           ├── reports.py          # /reports, /reports/generate, /download
│           ├── schedules.py        # /schedules, /schedules/{id}/run
│           ├── recipients.py       # /recipients CRUD
│           ├── delivery_logs.py    # /delivery-logs
│           └── webhook.py          # GET & POST /webhook
├── alembic/
│   ├── env.py                      # Alembic migration environment
│   └── versions/
│       └── 001_initial_schema.py   # Initial database schema migration
├── storage/
│   └── reports/                    # Persistent local folder for PDF storage
├── scripts/
│   └── manual_test_pdf.py          # Quick manual PDF generator script
├── tests/
│   ├── conftest.py                 # Pytest fixtures & mock environment
│   ├── test_health.py              # Health check tests
│   ├── test_pdf_generator.py       # ReportLab PDF generation tests
│   ├── test_recipients_api.py      # Recipient registration & validation tests
│   ├── test_schedules_api.py       # Schedule creation & trigger tests
│   ├── test_reports_api.py         # Report generation & download tests
│   ├── test_whatsapp_client.py     # Mocked Meta WhatsApp Cloud API tests
│   └── test_webhook.py             # Webhook challenge & signature tests
├── .vscode/
│   ├── launch.json                 # VS Code F5 debug profiles
│   ├── tasks.json                  # VS Code build/test/run tasks
│   └── settings.json               # VS Code workspace settings
├── .env.example                    # Sample environment variables
├── .env                            # Active local configuration
├── Dockerfile                      # Production Docker container
├── docker-compose.yml              # PostgreSQL + FastAPI containerized stack
├── render.yaml                     # Render Infrastructure-as-Code blueprint
├── Procfile                        # Railway / PaaS process declaration
├── requirements.txt                # Python dependencies
└── README.md                       # Comprehensive guide
```

---

## Prerequisites

- **Python 3.11+** installed (Python 3.11, 3.12, or 3.13)
- **Git**
- Optional for production / containers:
  - **Docker & Docker Compose**
  - **PostgreSQL 14+** (if not using SQLite locally)
  - **ngrok** (for testing Meta WhatsApp Webhooks locally)

---

## How to Run this Project in VS Code

This repository comes pre-configured with complete VS Code settings (`.vscode/launch.json` and `.vscode/tasks.json`). Follow these steps:

### Step 1: Open the Project in VS Code
Launch VS Code and open the repository folder:
```bash
code .
```

### Step 2: Set Up Virtual Environment (Recommended)
Open the integrated terminal in VS Code (`Ctrl + ` `~` or `Terminal -> New Terminal`):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### Step 3: Run Database Migrations
Run the Alembic database migrations:
```bash
python -m alembic upgrade head
```

### Step 4: Run or Debug with One Click in VS Code
You can run and debug the server using several built-in VS Code methods:

1. **Using the Run & Debug Panel (F5)**:
   - Click the **Run and Debug** icon in the left Activity Bar (or press `Ctrl+Shift+D`).
   - Select **"FastAPI: Run & Debug Server (Uvicorn)"** from the dropdown menu at the top.
   - Press **F5** (or click the green Play arrow).
   - VS Code will start the FastAPI server with live reloading and attach the Python debugger. You can place breakpoints anywhere in `app/`!

2. **Using VS Code Tasks (`Ctrl+Shift+P` -> `Tasks: Run Task`)**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS).
   - Type `Tasks: Run Task` and press Enter.
   - Choose:
     - **`Run FastAPI Dev Server`**: Starts Uvicorn with auto-reload.
     - **`Run Pytest Suite`**: Executes all 14 unit tests.
     - **`Run Alembic Migrations`**: Applies pending database migrations.
     - **`Docker Compose Up (Postgres + App)`**: Launches full local Docker stack.

3. **Generate a Sample PDF Immediately in VS Code**:
   - In the Run & Debug dropdown, select **"Python: Generate Test PDF Report"** and press **F5**.
   - Or run in terminal:
     ```bash
     python scripts/manual_test_pdf.py
     ```
   - Look in the `storage/reports/` folder: a styled corporate PDF report with KPI cards and bar charts will be created instantly.

### Step 5: Explore the Interactive API Documentation
Open your browser to:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Local Setup (CLI / Terminal)

If you prefer standard terminal commands without VS Code:

```bash
# 1. Clone repository
git clone <repository_url>
cd whatsapp-cloud-api-backend-main

# 2. Create and activate venv
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install packages
pip install -r requirements.txt

# 4. Copy environment configuration
cp .env.example .env

# 5. Apply database migrations
python -m alembic upgrade head

# 6. Run the application
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Environment Variables Reference

All settings are managed via `app/core/config.py` with Pydantic v2 validation and can be placed in `.env`:

| Variable Name | Default Value | Description |
|---|---|---|
| `PROJECT_NAME` | `WhatsApp Weekly PDF Report Automation System` | Name of the service |
| `ENVIRONMENT` | `development` | Environment mode (`development` or `production`) |
| `DEBUG` | `true` | Enables FastAPI debug logs and auto-reload |
| `PORT` | `8000` | Port for the HTTP server |
| `PUBLIC_BASE_URL` | `http://localhost:8000` | Publicly reachable base URL of the service |
| `DATABASE_URL` | `sqlite:///./whatsapp_reports.db` | PostgreSQL or SQLite database connection URL |
| `STORAGE_DIR` | `storage/reports` | Persistent filesystem directory for PDF reports |
| `TIMEZONE` | `Asia/Kolkata` | Reporting timezone (standard: `Asia/Kolkata`) |
| `SCHEDULE_DAY_OF_WEEK` | `mon` | Weekly cron day (`mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`) |
| `SCHEDULE_HOUR` | `9` | Hour of scheduled run in 24h format (0-23) |
| `SCHEDULE_MINUTE` | `0` | Minute of scheduled run (0-59) |
| `WHATSAPP_API_URL` | `https://graph.facebook.com` | Official Meta Graph API base endpoint |
| `WHATSAPP_API_VERSION` | `v21.0` | Official Meta WhatsApp Cloud API version |
| `WHATSAPP_PHONE_NUMBER_ID` | `""` | Phone Number ID from Meta App Dashboard |
| `WHATSAPP_ACCESS_TOKEN` | `""` | Permanent System User access token from Meta Business Manager |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | `""` | WhatsApp Business Account (WABA) ID |
| `META_APP_SECRET` | `""` | Meta App Secret for HMAC-SHA256 signature verification |
| `WEBHOOK_VERIFY_TOKEN` | `whatsapp_report_verify_token_secure` | Custom secret string used during Meta webhook handshake |
| `WHATSAPP_TEMPLATE_NAME` | `weekly_report_document` | Approved Meta template name for out-of-window delivery |
| `WHATSAPP_TEMPLATE_LANG` | `en_US` | Language code for WhatsApp template message |
| `MAX_RETRIES` | `3` | Maximum retry attempts for Meta API network requests |
| `RETRY_BACKOFF_SECONDS` | `2.0` | Exponential backoff delay factor in seconds |
| `API_TIMEOUT` | `30` | Request timeout for Meta Cloud API calls in seconds |

---

## Meta WhatsApp Cloud API Configuration

To enable live delivery to WhatsApp recipients, set up the official Meta Cloud API:

### 1. Create Meta Developer App & WhatsApp Business Account
1. Visit [Meta for Developers](https://developers.facebook.com/) and register / sign in.
2. Click **My Apps** -> **Create App**.
3. Select **Other** -> choose app type **Business**.
4. In the App Dashboard, find **WhatsApp** under "Add products to your app" and click **Set up**.
5. Meta will create a sandbox test phone number and display:
   - **Temporary Access Token** (valid for 24 hours)
   - **Phone Number ID** (e.g., `102938475610293`)
   - **WhatsApp Business Account ID (WABA ID)** (e.g., `192837465019283`)
6. Copy the **Phone Number ID** and **WhatsApp Business Account ID** to your `.env`.

### 2. Generate Permanent System User Access Token
> Temporary tokens expire after 24 hours. For automated production schedules, generate a permanent token:

1. Open [Meta Business Suite / Business Manager](https://business.facebook.com/settings).
2. Go to **Settings** -> **Users** -> **System Users**.
3. Click **Add**, name the user (e.g. `whatsapp-report-bot`), and assign role **Admin**.
4. Click **Generate New Token**:
   - Select your WhatsApp App.
   - Set token expiration to **Never**.
   - Check the following permissions:
     - `whatsapp_business_messaging`
     - `whatsapp_business_management`
5. Click **Generate Token** and copy the resulting string into `.env`:
   ```bash
   WHATSAPP_ACCESS_TOKEN=EAAG...
   ```
6. Navigate to App Dashboard -> **App settings** -> **Basic** -> reveal **App Secret** and copy to `.env`:
   ```bash
   META_APP_SECRET=your_app_secret
   ```

### 3. Configure WhatsApp Template (for Out-of-Window Messaging)
When initiating a conversation with a recipient outside the 24-hour customer care window, Meta requires an approved message template:

1. In WhatsApp Manager, go to **Account Tools** -> **Message Templates**.
2. Click **Create Template**:
   - Category: **Marketing** or **Utility**
   - Name: `weekly_report_document`
   - Language: `English (US)` (`en_US`)
3. **Header**:
   - Choose **Media** -> **Document**.
4. **Body**:
   - Enter: `Hello {{1}}, here is your Weekly Performance Report for the period {{2}}. Please review the attached document.`
5. Click **Submit for Review** (approval typically takes between 2 minutes and a few hours).

### 4. Webhook Setup & Live Verification via ngrok
To receive real-time delivery confirmations (`sent`, `delivered`, `read`, `failed`):

1. Expose your local port 8000 using ngrok:
   ```bash
   ngrok http 8000
   ```
2. Copy the HTTPS forwarding address (e.g., `https://abcdef123.ngrok-free.app`).
3. In Meta Developer Dashboard, go to **WhatsApp** -> **Configuration** -> **Webhook**.
4. Click **Edit**:
   - **Callback URL**: `https://abcdef123.ngrok-free.app/webhook`
   - **Verify Token**: Must match `WEBHOOK_VERIFY_TOKEN` in `.env` (e.g. `whatsapp_report_verify_token_secure`).
5. Click **Verify and Save**. Meta will send a `GET /webhook` verification challenge. Your backend will validate the token and respond with `hub.challenge`.
6. Under **Webhook fields**, click **Manage** and subscribe to:
   - `messages`

---

## API Reference & Swagger Documentation

Once the server is running, all endpoints are fully documented at `http://localhost:8000/docs`.

### Core Endpoints

#### 1. System Health
- **`GET /health`**
  Returns database connectivity, scheduler status, persistent storage accessibility, and WhatsApp API configuration state.

#### 2. Reports Management
- **`POST /reports/generate`**
  Triggers immediate generation of a weekly PDF report.
  *Request Body:*
  ```json
  {
    "title": "Executive Performance Summary",
    "reporting_period_start": "2026-10-04T00:00:00",
    "reporting_period_end": "2026-10-11T23:59:59",
    "distribute_to_recipients": true,
    "custom_metrics": {
      "total_revenue": 185000.0,
      "growth_rate": 16.8
    }
  }
  ```
- **`GET /reports`**
  Lists all reports with pagination (`skip`, `limit`, `status`).
- **`GET /reports/{report_id}`**
  Fetches detailed report metadata and delivery metrics breakdown.
- **`GET /reports/{report_id}/download`**
  Streams the PDF file directly as a download (`application/pdf`).

#### 3. Schedules Management
- **`POST /schedules`**
  Creates an automated reporting schedule in the database.
  *Request Body:*
  ```json
  {
    "name": "Monday Executive Dispatch",
    "day_of_week": "mon",
    "hour": 9,
    "minute": 0,
    "timezone": "Asia/Kolkata",
    "is_active": true
  }
  ```
- **`GET /schedules`**
  Lists all configured reporting schedules.
- **`POST /schedules/{schedule_id}/run`**
  Forces an immediate execution of the specified schedule.

#### 4. Recipients Management
- **`POST /recipients`**
  Registers and subscribes a recipient. Phone numbers are automatically sanitized and validated to E.164 format.
  *Request Body:*
  ```json
  {
    "name": "Priya Sharma",
    "phone_number": "+91 98765 43210",
    "email": "priya@example.com",
    "department": "Operations",
    "is_active": true,
    "opted_in": true,
    "timezone": "Asia/Kolkata"
  }
  ```
- **`GET /recipients`**
  Lists subscribed recipients with filtering by `is_active` and `opted_in`.
- **`PUT /recipients/{recipient_id}`**
  Updates recipient profile or opt-in state.
- **`DELETE /recipients/{recipient_id}`**
  Deletes recipient.

#### 5. Delivery Logs
- **`GET /delivery-logs`**
  Lists message delivery logs with counts across `sent`, `delivered`, `read`, and `failed` states. Filterable by `report_id`, `recipient_id`, and `status`.

#### 6. Webhooks
- **`GET /webhook`**
  Meta verification challenge handler (`hub.mode`, `hub.verify_token`, `hub.challenge`).
- **`POST /webhook`**
  Receives real-time delivery status updates and incoming messages with HMAC-SHA256 signature verification.

---

## Weekly Workflow & Scheduling (APScheduler)

1. **Trigger Configuration**:
   The `SchedulerService` runs in the background using `apscheduler.schedulers.background.BackgroundScheduler` bound to the `Asia/Kolkata` timezone.
2. **Duplicate Suppression**:
   - **In-Memory Mutex**: If an execution is in progress, any simultaneous trigger is immediately skipped.
   - **Time Window Verification**: Before compiling, the system inspects the database. If a report was already generated within the last 18 hours, duplicate compilation is avoided unless explicitly forced via `/schedules/{id}/run`.
3. **Execution Flow**:
   - The scheduler calls `report_service.generate_and_distribute_report()`.
   - `pdf_generator.generate_weekly_report()` produces the PDF file in `storage/reports/`.
   - `Report` metadata is saved in PostgreSQL.
   - If Meta credentials are active:
     - PDF is uploaded to Meta via `whatsapp_client.upload_media()`, returning a `media_id`.
     - Document message is dispatched to all active opted-in recipients.
     - Individual `DeliveryLog` records are recorded with the `message_id` (`wamid.xxx`).
   - Meta webhooks report delivery confirmation (`delivered` and `read`).

---

## Running Unit & Integration Tests

The project includes a full unit test suite with mocked Meta WhatsApp Cloud API requests using `pytest` and FastAPI `TestClient`:

```bash
# Run all tests
python -m pytest -v

# Run with test coverage
python -m pytest -v --tb=short
```

### Test Suite Coverage
- `test_health.py`: Validates `/health` returns status of database, scheduler, storage, and WhatsApp configuration.
- `test_pdf_generator.py`: Verifies ReportLab builds valid multi-page PDFs with KPI blocks and vector charts.
- `test_recipients_api.py`: Validates recipient registration, E.164 normalization, uniqueness, and invalid number rejection.
- `test_schedules_api.py`: Validates schedule creation, listing, and manual trigger.
- `test_reports_api.py`: Tests report generation, detail inspection, and binary PDF downloading.
- `test_whatsapp_client.py`: Tests media upload, document message dispatch, template dispatch, and API error handling with mocked Meta Graph API responses.
- `test_webhook.py`: Tests `GET /webhook` verification handshake, `POST /webhook` HMAC-SHA256 signature validation, and real-time delivery status updates.

---

## Docker & Containerized Deployment

Run the complete multi-container stack with PostgreSQL 16 and persistent volumes:

```bash
# Build and run containers in background
docker compose up --build -d

# Check running services
docker compose ps

# View application logs
docker compose logs -f web

# Stop containers
docker compose down
```

### Docker Compose Volumes
- `postgres_data`: Persistent storage for the PostgreSQL database.
- `pdf_storage`: Persistent storage for generated PDF files (`/app/storage/reports`).
- `app_logs`: Persistent storage for application logs (`/app/logs`).

---

## Cloud Deployment (Railway & Render)

### Deploying to Render
1. Push your repository to GitHub or GitLab.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** -> **Blueprint**.
4. Connect your repository. Render will automatically detect `render.yaml` and configure:
   - **PostgreSQL Database** (`whatsapp-reports-db`)
   - **FastAPI Web Service** with Python 3.11
   - **10 GB Persistent Disk** mounted at `/app/storage/reports`
   - Background APScheduler running continuously
5. Add your Meta credentials in Render's Environment Variables tab:
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_BUSINESS_ACCOUNT_ID`
   - `META_APP_SECRET`
   - `WEBHOOK_VERIFY_TOKEN`
6. Register the Render URL with Meta Webhooks (`https://<your-render-service>.onrender.com/webhook`).

### Deploying to Railway
1. Log in to [Railway](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Add a **PostgreSQL** database service in the project canvas.
4. Railway automatically populates `DATABASE_URL` in your app service.
5. In the Web service settings, add a **Persistent Volume** mounted to `/app/storage/reports`.
6. Add the environment variables from `.env.example`.
7. Railway will execute the `Procfile` command:
   ```bash
   python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```

---

## Module Architecture Guide

| Module | Purpose |
|---|---|
| `app/main.py` | FastAPI application factory, lifespan startup/shutdown hooks, CORS, and Gzip middleware. |
| `app/core/config.py` | Pydantic v2 Settings class loading from `.env`, URL schema standardizer, and credential check. |
| `app/core/database.py` | SQLAlchemy database engine setup, connection pooling, `SessionLocal`, and `get_db` generator. |
| `app/core/security.py` | Constant-time HMAC-SHA256 signature verification for Meta webhook security. |
| `app/models/` | Declarative models for `Recipient`, `Schedule`, `Report`, and `DeliveryLog`. |
| `app/schemas/` | Pydantic validation schemas with `ConfigDict(from_attributes=True)` for serialization. |
| `app/services/pdf_generator.py` | Enterprise ReportLab PDF engine: 2-pass `NumberedCanvas`, vector bar charts, KPI tables, and footers. |
| `app/services/storage.py` | Filesystem storage abstraction with directory traversal protection and SHA256 checksums. |
| `app/services/whatsapp_client.py` | Official Meta WhatsApp Cloud API client handling media upload, document sending, and template messaging. |
| `app/services/scheduler_service.py` | APScheduler manager in `Asia/Kolkata` timezone with mutex locking and duplicate prevention. |
| `app/services/report_service.py` | Orchestrator connecting PDF generation, DB tracking, Meta media upload, and multi-recipient distribution. |
| `app/api/v1/` | FastAPI routers for `/health`, `/reports`, `/schedules`, `/recipients`, `/delivery-logs`, and `/webhook`. |

---

## License

This project is licensed under the MIT License.
