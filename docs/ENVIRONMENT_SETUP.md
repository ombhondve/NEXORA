# NEXORA — Environment Configuration & Deployment Architecture

This document defines the separated, security-hardened environment configuration architecture for the **NEXORA** Recursive OSINT Discovery Engine.

---

## 1. Architecture Overview

NEXORA enforces strict separation between client-side (frontend) and server-side (backend) environments:

```text
┌──────────────────────────────────────────────────┐
│                   Next.js Web                    │
│                  (apps/web)                      │
│                                                  │
│  - Configuration: apps/web/.env.local            │
│  - Template:      apps/web/.env.example          │
│  - Scope:         Public NEXT_PUBLIC_* variables │
│  - Security:      Bundled into browser JS        │
│                   ZERO backend secrets allowed   │
└─────────────────────────▲────────────────────────┘
                          │ HTTPS / REST API
┌─────────────────────────▼────────────────────────┐
│                 FastAPI Backend                  │
│                    (backend)                     │
│                                                  │
│  - Configuration: backend/.env                   │
│  - Template:      backend/.env.example           │
│  - Scope:         Database, Redis, JWT secrets,  │
│                   API keys, Crawler & SSRF rules │
│  - Security:      Strictly server-side           │
│                   Passwords redacted from logs   │
└──────────────────────────────────────────────────┘
```

---

## 2. Directory Layout

```text
NEXORA/
├── .gitignore                      # Enforces ignore of real .env files across all directories
├── .env.example                    # Root unified reference / Docker orchestration template
├── package.json                    # Monorepo build and development scripts
│
├── apps/
│   └── web/
│       ├── .env.example            # Frontend environment template
│       ├── .env.local              # Local frontend config (gitignored)
│       ├── next.config.mjs         # Next.js configuration and API rewrites
│       ├── package.json            # Frontend dependencies
│       └── src/
│           ├── lib/
│           │   ├── config.ts       # Validated frontend config module
│           │   └── api-client.ts   # Authenticated API client
│           └── app/                # Next.js App Router
│
├── backend/
│   ├── .env.example                # Backend environment template
│   ├── .env                        # Local backend config (gitignored)
│   ├── vercel.json                 # Backend serverless routing (/api/index.py)
│   ├── requirements.txt            # Python dependencies
│   ├── api/
│   │   └── index.py                # Vercel Serverless Function entry point
│   ├── migrations/                 # Alembic database migrations
│   └── src/
│       └── recursive_osint/
│           ├── config.py           # Pydantic Settings with deterministic dotenv loader
│           ├── main.py             # FastAPI application
│           └── db/                 # Database models and session management
│
├── scripts/
│   ├── build-web.js                # Monorepo build script with NFT trace repair
│   ├── check-env.py                # Environment verification & diagnostic tool
│   ├── migrate.py                  # Schema migration executor
│   └── setup-dev.py                # Local development database & storage initializer
│
└── docs/
    └── ENVIRONMENT_SETUP.md        # This guide
```

---

## 3. Local Development Quickstart

### Step 1: Create Environment Files

#### PowerShell (Windows):
```powershell
# Create frontend local environment
Copy-Item apps/web/.env.example apps/web/.env.local

# Create backend local environment
Copy-Item backend/.env.example backend/.env
```

#### Bash (Linux / macOS):
```bash
# Create frontend local environment
cp apps/web/.env.example apps/web/.env.local

# Create backend local environment
cp backend/.env.example backend/.env
```

> [!NOTE]
> If `.env.local` or `backend/.env` already exists with custom values, do not overwrite it.

---

### Step 2: Initialize Database and Local Storage

Run the development initializer to create `./storage/uploads` and set up the local development SQLite/PostgreSQL schema:

```powershell
python scripts/setup-dev.py
```

Verify your active environment and connectors:

```powershell
python scripts/check-env.py
```

---

### Step 3: Run the Application

#### Terminal 1 — Backend:
```powershell
cd backend
uvicorn recursive_osint.main:app --reload --host 127.0.0.1 --port 8000
```
API Documentation will be live at: `http://127.0.0.1:8000/docs`

#### Terminal 2 — Frontend:
```powershell
npm --prefix apps/web run dev
# or from root:
npm run dev
```
Frontend Web Dashboard will be live at: `http://localhost:3000`

---

## 4. Frontend Environment Variables (`apps/web/.env.local`)

| Variable | Required | Default (Dev) | Description |
| :--- | :---: | :--- | :--- |
| `NEXT_PUBLIC_APP_NAME` | No | `"NEXORA"` | Application name displayed in titles and navigation headers. |
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend API base URL. In production, points to the deployed FastAPI backend. |

> [!CAUTION]
> Every variable with the `NEXT_PUBLIC_` prefix is bundled into client JavaScript sent to every visitor. **Never** place database connection strings, Redis URLs, JWT signing secrets, or private API keys in frontend configuration.

---

## 5. Backend Environment Variables (`backend/.env`)

### Application & Security Settings

| Variable | Required | Default | Sensitivity | Description |
| :--- | :---: | :--- | :---: | :--- |
| `ENVIRONMENT` | Yes | `development` | Public | Runtime mode: `development`, `test`, `staging`, `production`. |
| `DEBUG` | No | `false` | Internal | Enables detailed debug traces (must be `false` in production). |
| `LOG_LEVEL` | No | `INFO` | Internal | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `HOST` | No | `127.0.0.1` | Internal | Binding host for the API server. |
| `PORT` | No | `8000` | Internal | Binding port for the API server. |
| `SECRET_KEY` | **Yes (Prod)** | Dev default | **Secret** | Cryptographic key for JWT tokens. Min 32 characters in production. |
| `ALGORITHM` | No | `HS256` | Internal | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `120` | Internal | Lifetime of access tokens in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Internal | Lifetime of refresh tokens in days. |
| `ALLOW_ANONYMOUS_DEV_AUTH` | No | `false` | Internal | Dev auth bypass (strictly forbidden in production). |
| `ENABLE_DEV_SEEDS` | No | `false` | Internal | Seeds demo analyst accounts on launch. |
| `CORS_ORIGINS` | Yes | `http://localhost:3000` | Public | Comma-separated allowed frontend origins. |

---

### Database Configuration (Neon PostgreSQL / Local Dev)

The backend determines its database connection using strict precedence:
1. `DATABASE_NEXORA_POSTGRES_URL` *(Preferred pooled endpoint via PgBouncer)*
2. `DATABASE_NEXORA_DATABASE_URL` *(Secondary Vercel integration alias)*
3. `DATABASE_URL` *(Standard local dev / docker fallback)*
4. Default SQLite (`sqlite+aiosqlite:///./osint_dev.db`, development/test only)

| Variable | Required | Sensitivity | Description |
| :--- | :---: | :---: | :--- |
| `DATABASE_NEXORA_POSTGRES_URL` | **Yes (Prod)** | **Secret** | Pooled PostgreSQL connection string for API queries. |
| `DATABASE_NEXORA_POSTGRES_URL_NON_POOLING` | No | **Secret** | Direct (non-pooled) connection string preferred for migrations/DDL. |
| `DATABASE_POOL_SIZE` | No | `5` | Connection pool size. |
| `DATABASE_MAX_OVERFLOW` | No | `10` | Maximum overflow connections beyond pool size. |
| `DATABASE_POOL_TIMEOUT` | No | `30` | Seconds to wait before timing out on connection checkout. |
| `DATABASE_USE_NULLPOOL` | No | `false` | Uses NullPool for serverless short-lived lambdas. |

---

### Redis (Task Queue & Cache)

Strict precedence:
1. `Redis_REDIS_URL` *(Preferred Vercel Upstash integration variable)*
2. `REDIS_URL` *(Standard fallback)*

| Variable | Required | Sensitivity | Description |
| :--- | :---: | :---: | :--- |
| `Redis_REDIS_URL` | No | **Secret** | Vercel Upstash Redis connection string. |
| `REDIS_URL` | No | **Secret** | Standard fallback Redis connection string. |
| `REDIS_CACHE_TTL_SECONDS` | No | `3600` | Default cache TTL in seconds. |

---

### External Services & Connectors

| Variable | Required | Sensitivity | Description |
| :--- | :---: | :---: | :--- |
| `OPENSEARCH_URL` | No | Internal | OpenSearch cluster URL (default: `http://localhost:9200`). |
| `STORAGE_BACKEND` | No | Internal | Storage provider (`local` or `s3`). |
| `STORAGE_LOCAL_ROOT` | No | Internal | Upload directory (default: `./storage/uploads`). |
| `ENABLE_SSRF_PROTECTION` | No | Security | Blocks local/private IP addresses from recursive crawling (default: `true`). |
| `AI_PROVIDER` | No | Public | LLM synthesis provider: `none`, `openai`, `anthropic`, `ollama`. |
| `AI_API_KEY` | No | **Secret** | API key for configured AI provider. |
| `TAVILY_API_KEY` | No | **Secret** | Tavily search API key (optional). |
| `SERPER_API_KEY` | No | **Secret** | Serper Google search API key (optional). |
| `BRAVE_SEARCH_API_KEY` | No | **Secret** | Brave search API key (optional). |

---

## 6. Vercel Deployment Configuration

When deploying NEXORA to Vercel, deploy as **two independent projects**:

### Project 1: `nexora-frontend` (Next.js)

- **Repository**: `https://github.com/ombhondve/NEXORA`
- **Root Directory**: `apps/web` (or root with `node scripts/build-web.js`)
- **Framework Preset**: `Next.js`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`

#### Environment Variables in Vercel:
```env
NEXT_PUBLIC_APP_NAME="NEXORA"
NEXT_PUBLIC_API_URL="https://nexora-backend.vercel.app"
```

---

### Project 2: `nexora-backend` (FastAPI)

- **Repository**: `https://github.com/ombhondve/NEXORA`
- **Root Directory**: `backend`
- **Framework Preset**: `Other`
- **Build Command**: *(leave empty)*
- **Output Directory**: *(leave empty)*

#### Environment Variables in Vercel:
```env
ENVIRONMENT="production"
SECRET_KEY="<generate-64-char-random-hex-key>"
DATABASE_NEXORA_POSTGRES_URL="postgresql://neondb_owner:***@ep-***-pooler.aws.neon.tech/neondb?sslmode=require"
DATABASE_NEXORA_POSTGRES_URL_NON_POOLING="postgresql://neondb_owner:***@ep-***.aws.neon.tech/neondb?sslmode=require"
Redis_REDIS_URL="redis://default:***@ep-***.upstash.io:6379"
CORS_ORIGINS="https://nexora-frontend.vercel.app"
```

---

## 7. Production Readiness Verification

The backend executes `validate_production_readiness()` on startup. In production (`ENVIRONMENT=production`), the system enforces:

1. **Secret Key Strength**: `SECRET_KEY` cannot be the development default and must contain at least 32 characters.
2. **Database Provider**: SQLite is strictly forbidden; a valid PostgreSQL connection string must be supplied.
3. **SSL Requirement**: Unencrypted connections (`sslmode=disable` or `DATABASE_NEXORA_POSTGRES_URL_NO_SSL`) are rejected.
4. **Security Controls**: `DEBUG` must be `false` and `ALLOW_ANONYMOUS_DEV_AUTH` must be `false`.
5. **Zero Credential Leaks**: Passwords in database URLs and Redis URLs are sanitized with `***` before printing to logs or diagnostic scripts.
