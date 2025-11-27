<div align="center">
  <img src="front/src/assets/logo.png" alt="DevFriend Logo" width="200"/>

  # DevFriend

  **A secure manager for notes, integrations, and developer secrets**

  DevFriend is a modern web app for managing user notes, OAuth-based external integrations (Gmail, GitHub, Slack), and encrypted secrets, designed following Hexagonal/Clean Architecture principles.

  [![FastAPI](https://img.shields.io/badge/FastAPI-0.113+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat&logo=vue.js)](https://vuejs.org/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?style=flat&logo=postgresql)](https://www.postgresql.org/)
  [![Docker](https://img.shields.io/badge/Docker-compose-2496ED?style=flat&logo=docker)](https://www.docker.com/)
</div>

---

## 📋 Table of Contents
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [License](#-license)

---

## ✨ Features
- 📝 **Notes**: Full CRUD on personal notes (Markdown supported)
- 🔒 **Secrets Management**: Store OAuth/API credentials securely, encrypted with Fernet per user
- 🔑 **OAuth Integrations**:
    - Gmail: list and sync emails
    - GitHub: list repos, user profile, sync, notification count
    - Slack: (via "messages" API) list and sync channels and messages
- 👤 **Strong Auth**: JWT-based login with protected endpoints
- 🌙 **Dark Mode**: Built-in, toggleable
- 🎨 **Modern UI/UX**: Vue 3, responsive, desktop/mobile
- 🧪 **Real Testing**: Pytest coverage (backend controllers/services), Playwright E2E (frontend/UI)
- 🛡️ **Docker**: One-line start (frontend, backend, db) via Docker Compose

---

## 🏗️ Architecture
DevFriend uses real Hexagonal Architecture (Ports & Adapters):
- Strong separation: Domain, Application, Adapters (API, DB, OAuth, etc.)
- All business logic is infra-agnostic & fully tested
- PostgreSQL data source via repository adapters (non-coupled)
- Vue3 SPA frontend isolated from API
- Integrations are service-driven, supporting extension

### Architecture Overview
```mermaid
graph TD
    Front[Vue.js SPA]
    API[REST API (FastAPI)]
    Services[Services Layer]
    Domain[Entities/Models]
    Repo[Repository + PostgreSQL Adapter]
    DB[(PostgreSQL)]
    Front -->|HTTP JWT| API
    API --> Services --> Domain
    Services --> Repo --> DB
```

---

## 🛠️ Tech Stack
**Backend:**
- Python 3.12+, FastAPI, Pydantic v2
- PostgreSQL 15+, psycopg2
- JWT/Bcrypt, cryptography/Fernet
- Google, GitHub, Slack API clients
- Pytest (unit/integration)

**Frontend:**
- Vue.js 3 (Composition API)
- Axios, Vue CLI tooling
- Playwright E2E
- Custom CSS3 (dark/light)

**DevOps:**
- Docker Compose

---

## 🚀 Getting Started
**Prerequisites:** Docker & Docker Compose, Node 16+ (for frontend/dev), Python 3.12+ (if backend runs locally/not in Docker only).

**Quick start with Docker (recommended):**
```bash
git clone <YOUR_REPO_URL>
cd devFriend
cd back && cp .env.example .env && cd ..
docker compose up --build
```
- Frontend: http://localhost:88
- Backend: https://localhost:8888
- API Docs (Swagger): https://localhost:8888/docs

**Local Development:**
- Backend: `cd back && pip install -r requirements.txt && uvicorn src.main:app --reload --port 8888`
- Frontend: `cd front && npm install && npm run serve -- --port 88`
- Testing backend: `cd back && pytest`
- Testing frontend: `cd playwright && yarn install && yarn test`

---

## 📁 Project Structure
```
devFriend/
├── back/
│   ├── src/
│   │   ├── api/                # REST controllers: auth, notes, secrets, integrations, etc.
│   │   ├── models/             # Pydantic models: User, Note, Secret, Integration...
│   │   ├── repositories/       # Abstractions + adapters (PostgreSQL, ABCs)
│   │   ├── services/           # Business/services logic: Auth, Note, Secret, OAuth...
│   │   ├── middleware/         # JWT/CORS
│   │   ├── utils/              # Enc/dec, OAuth client helpers
│   │   └── main.py             # FastAPI entrypoint
│   ├── tests/                  # Pytest unit/integration tests
│   ├── requirements.txt
│   ├── Dockerfile
├── front/
│   ├── src/
│   │   ├── components/         # Vue UI modules
│   │   ├── services/           # JS API adapters (auth, notes, secrets, Gmail, GitHub, Slack)
│   │   ├── assets/
│   │   ├── App.vue
│   │   └── main.js
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
├── playwright/
│   ├── tests/
│   ├── Dockerfile
│   ├── package.json
├── db_schema.sql
├── docker-compose.yml
├── README.md
```

## Launch all python tests
docker-compose run --rm back python -m pytest  -v -s
## Launch PlayWright tests (local)
npx playwright test tests --headed --timeout=0

---

## 🌐 Deployment
### Docker Compose (Local/Dev, recommended):
All stack runs with one command (`docker compose up --build`). Default environment is local/dev (`.env.example` is enough).

**Environment Variables (Backend):**
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `DEVFRIEND_ENCRYPTION_KEY` (Fernet, required)
- `FRONTEND_URL`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`
- `SLACK_CLIENT_ID` / `SLACK_CLIENT_SECRET` (optional)
- `JWT_SECRET_KEY` (optionally override default)

**DB Schema:** Automatically set up by Docker, or init manually:
```bash
psql -h <host> -U <user> -d devfriend -f db_schema.sql
```

## Example of usage of pgadmin dockerized
docker run -d \
  --name pgadmin_devfriend \
  -p 8880:80 \
  -e PGADMIN_DEFAULT_EMAIL=admin@example.com \
  -e PGADMIN_DEFAULT_PASSWORD=supersecret \
  -v pgadmin_data_devfriend:/var/lib/pgadmin \
  dpage/pgadmin4

**Cloud:** Supports Render.com, Railway, Heroku, or any infra supporting Docker Compose and the above ENV variables. Set up OAuth redirect URIs per provider.

### Security Notes
- All sensitive data is Fernet-encrypted per user
- No secrets or keys in frontend code/repo
- JWT auth for all sensitive endpoints
- `.env` MUST NOT be versioned for production
- HTTPS required for OAuth in prod

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">
  Made with ❤️ for developers

  **[Report Bug](https://github.com/yourusername/devfriend/issues)** · **[Request Feature](https://github.com/yourusername/devfriend/issues)**
</div>
