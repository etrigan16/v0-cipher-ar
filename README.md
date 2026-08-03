# Cipher AR — Attack Surface Scanner + Phishing Simulator

Suite de ciberseguridad ofensiva para PYMES argentinas. Escaneo de superficie de ataque,
descubrimiento de activos, risk scoring potenciado por IA y simulaciones de phishing.

[![CI](https://github.com/aukalabs/cipher-ar/actions/workflows/ci.yml/badge.svg)](https://github.com/aukalabs/cipher-ar/actions/workflows/ci.yml)

---

## Stack

| Capa          | Tecnología                                          |
|---------------|------------------------------------------------------|
| Frontend      | Next.js 16 + React 19 + TypeScript 5.7 (strict)     |
| Estilos       | Tailwind CSS 4 + shadcn/ui                          |
| Backend       | FastAPI 0.115 + Python 3.12                         |
| ORM           | SQLAlchemy 2.0 (async) + Pydantic 2                 |
| Base de datos | PostgreSQL 16 + pgvector                            |
| Cache / Colas | Redis 7                                              |
| LLM           | Groq (Llama-3.1-70b) + Ollama local                 |
| Infra         | Vercel (frontend) + Render (backend + DB)           |

---

## Prerrequisitos

- Node.js 22+
- pnpm 11+
- Python 3.12+
- PostgreSQL 16 (o Docker Desktop con WSL2)
- Docker Compose (para backend + DB + Redis local)

---

## Quick Start

```bash
# 1. Clonar el repo
git clone https://github.com/aukalabs/cipher-ar.git
cd cipher-ar

# 2. Instalar dependencias del frontend
pnpm install

# 3. Configurar variables de entorno
cp backend/.env.example backend/.env
# Editar backend/.env con valores reales (al menos RESEND_API_KEY para el formulario de contacto)

# 4. Levantar servicios de backend (PostgreSQL + Redis + API)
docker compose up -d

# 5. Iniciar frontend en modo desarrollo
pnpm dev
```

Abrir [http://localhost:3000](http://localhost:3000) para ver la landing page.

---

## Tests

```bash
# Frontend (Vitest)
pnpm test

# Backend (pytest)
cd backend && pytest

# Linter
pnpm lint

# Type check
pnpm tsc --noEmit
```

Los tests se ejecutan automáticamente en CI (GitHub Actions) en cada push y PR a `main`.

---

## Estructura del Proyecto

```
cipher-ar/
├── app/                  # Next.js App Router pages
├── components/           # UI components (shadcn/ui + custom)
├── lib/                  # Frontend utilities
├── hooks/                # React hooks
├── backend/
│   ├── app/
│   │   ├── api/v1/       # FastAPI endpoints
│   │   ├── core/         # Config, security, database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── tests/            # Pytest suite
│   └── alembic/          # Database migrations
├── docker-compose.yml    # Backend services (PostgreSQL, Redis, API, Caddy)
├── Caddyfile             # TLS reverse proxy config (staging)
└── .env.example          # Environment variables reference
```

---

## Variables de Entorno

Ver `backend/.env.example` para la lista completa. Las variables principales incluyen:

| Variable              | Descripción                                  |
|-----------------------|----------------------------------------------|
| `DATABASE_URL`        | PostgreSQL connection string                 |
| `REDIS_URL`           | Redis connection string                      |
| `SECRET_KEY`          | JWT signing secret                           |
| `RESEND_API_KEY`      | API key para envío de emails (contacto)      |
| `GROQ_API_KEY`        | API key para Groq LLM                        |

---

## CI / CD

| Workflow   | Trigger                  | Checks                                    |
|------------|--------------------------|-------------------------------------------|
| `quality`  | Push / PR a `main`       | `pnpm lint` → `pnpm tsc --noEmit` → `pnpm test` → `cd backend && pytest` → `pnpm build` |

El workflow `quality` verifica lint, tipos, tests y build en cada cambio. El frontend se deploya automáticamente a Vercel desde `main`.

---

## Licencia

Privado — Aukalabs. Todos los derechos reservados.

---

_Última actualización: 2026-08_
