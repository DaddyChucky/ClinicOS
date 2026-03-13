[View the write-up (PDF)](./WRITE_UP.pdf)

# ClinicOS

**ClinicOS** is the operating system for modern dental and medical practices.

ClinicOS brings support operations, patient growth strategy, and marketing planning into one connected product with two primary surfaces:
- **Practice Desk** for clinic teams
- **Operations Console** for internal operators and specialists

Live application: `https://growth-and-support-copilot.vercel.app/`

## Product Surfaces

### Practice Desk
- Route: `/workspace`
- Client-facing workspace used directly by clinic teams
- Built around a persistent conversation with **ClinicOS AI**
- Support-only scope: software help, billing FAQs, upgrade guidance, and escalation routing
- Stores conversation history, practice memory, and a progressive **Practice Profile**
- Supports human escalation with clear queue state and persistent in-chat handoff context

### Operations Console
- Route: `/admin`
- Internal workspace for oversight, specialist workflows, and operator controls
- Shows active conversations, practice profile data, orchestration state, deleted chat archive, and audit visibility
- Lets operators suspend chats or take the triage agent offline at the chat level or globally
- Includes the merged human takeover queue, Sales & Outreach, and Marketing

## Angle And Point Of View

The core angle behind ClinicOS is that small and mid-sized dental or medical practices do not just need "an AI chatbot." They need a system that connects the clinic-facing support experience to the internal operational team that actually resolves issues, tracks risk, and drives follow-through.

That is why the product is split into two views:

**Practice Desk** is the client-facing surface. Its job is to give a clinic one calm, persistent support thread for software issues, billing questions, upgrade options, and escalation routing. The main experience is an active chat connected to **ClinicOS AI**. It can answer directly, maintain memory over time, use practice context, and decide when a support case should move to a human specialist. The handoff logic is intentionally operational rather than cosmetic: it reacts to explicit requests for a person, frustration, looping conversations, low-confidence situations, or signals that the issue is better handled by a human.

**Operations Console** is the internal surface for your team, not the clinic. Its job is to oversee active conversations, specialist work, and human review while giving the team control over how the system behaves in real time. Internal operators can inspect transcripts, review logs for traceability, update chat-linked practice data, treat the console as a database-like operational view, and control the **ClinicOS AI Triage Agent** either per conversation or across the full workspace.

The creative angle is that this is not three unrelated demos for support, sales, and marketing. It is one operating layer for clinic operations:
- Practice Desk captures real support context
- Operations Console gives humans control and traceability
- Review Queue turns AI handoff into a usable human workflow
- Sales & Outreach and Marketing reuse the same product vocabulary and operational understanding in specialist workspaces

## Tracks Covered

ClinicOS combines all three tracks, but the strongest point of view is **Track A** with connected internal follow-through.

- **Track A — Customer Support Agent:** the main clinic-facing experience is a support agent that handles software help, billing FAQs, upgrade guidance, and escalation routing in a persistent thread
- **Track B — Sales & Outreach Agent:** internal reps can research a real clinic, score fit, and draft outreach grounded in public operational signals
- **Track C — Marketing Agent:** internal teams can generate campaign plans, nurture ideas, and channel-ready messaging from an audience, objective, and custom notes

The reason for combining them is practical: support, sales, and marketing are adjacent workflows for a clinic operations business, and showing them inside one coherent system makes the product feel more like something that could be shipped and operated, not just presented

## Route Map

- `/` -> ClinicOS landing page and entry point
- `/workspace` -> Practice Desk
- `/admin` -> Operations Console overview
- `/admin/support` -> merged Review Queue for human takeover
- `/admin/review` -> same merged Review Queue
- `/admin/sales` -> Sales & Outreach
- `/admin/marketing` -> Marketing

Legacy redirects still exist for `/support`, `/review`, `/sales`, and `/marketing`.

## Core Capabilities

- Persistent thread memory across conversations
- Practice Profile memory and admin overrides
- Support-first AI guidance inside Practice Desk
- Human escalation with persisted states: `queued`, `reviewing`, `live_chat`
- Internal transcript review, audit visibility, and deleted-chat archive
- Real clinic research for prospecting using the OpenAI SDK plus Scrapling
- Personalized outreach draft generation with saved research history
- Marketing brief and nurture-sequence generation with saved campaign history
- Suggested prompts, guidance modals, and scenario starters across major views

## Current Behavior

- **Practice Desk is support-only.** Sales, outreach, and marketing requests are redirected to specialist tools in Operations Console.
- **Review Queue is for human takeover.** It shows explicit Practice Desk support escalations, full transcript context, practice profile data, and audit history.
- **Deleted chats are soft-deleted.** They disappear from live rails but remain visible in the Operations Console archive and audit flow.
- **Sales and Marketing save history directly.** These workspaces no longer create an approval queue for normal admin usage.
- **Live AI is optional.** When `OPENAI_API_KEY` is unavailable, ClinicOS falls back to local non-live behavior.

## How This Answers The Evaluation Criteria

### Relevance

The workflows are grounded in how dental and medical practices actually operate:
- support requests are framed around software issues, billing questions, upgrade paths, and human escalation
- practice memory and profile fields reflect operational context such as location, PMS / EHR, provider and front-desk sizing, and billing signals
- sales research focuses on clinic operating signals like front-desk pressure, recall workflows, follow-up bottlenecks, intake friction, and staffing signals
- marketing output is tied to clinic audiences and concrete growth objectives rather than generic copy generation

### Agent Quality

The agent behavior is designed around multi-step work, not single prompts:
- Practice Desk supports persistent threads and progressive memory
- escalation is conditional and stateful rather than a one-click fake transfer
- human takeover has explicit queue states and audit visibility
- the sales path can do online research, fit scoring, and outreach drafting as a chain
- the system keeps functioning when live AI is unavailable by falling back to local paths instead of failing closed

### Shipping Instinct

This project was built as a real, hosted application rather than a polished but fragile demo:
- frontend, backend, and database are deployed as separate production surfaces
- the backend has migrations, persisted models, review flows, history views, archive behavior, and env-driven configuration
- operators can control the triage agent, inspect logs, and modify real-time chat-linked data
- sales and marketing outputs are saved and usable instead of being one-off ephemeral responses

### Creativity

The main creative choice was to treat the problem as an **operations system** rather than a single agent prompt. The higher-value workflow is the connection between:
- a clinic-facing support agent
- an internal operational control layer
- a merged human takeover queue
- specialist sales and marketing workspaces that live inside the same product language and data model

That makes the product feel closer to a real clinic operations platform than a standalone chatbot, outreach writer, or campaign generator.

## Sales & Outreach

- Route: `/admin/sales`
- Internal prospect research workspace for dental and medical clinics
- Uses clinic name plus location to generate:
  - research brief
  - fit score and qualification signals
  - operating insights
  - personalized outreach email
- Persists research history and supports direct email drafting via `mailto:`
- Uses the OpenAI SDK for live research when available and Scrapling-backed page scraping for richer public-site context

Sales & Outreach is designed to help the internal team work from real clinic context instead of static prospect templates. Given a clinic name and location, ClinicOS uses **Scrapling** together with the **OpenAI SDK** to research public information online, infer operational signals and likely workflow pain points, score prospect fit, and generate a customized outreach draft intended to maximize relevance and lead quality.

## Marketing

- Route: `/admin/marketing`
- Internal campaign planning workspace
- Generates:
  - structured campaign brief
  - strategy outline
  - nurture sequence
  - operationally grounded messaging
- Persists campaign history
- Supports PDF export and direct email drafting

Marketing is built to turn a growth objective into something a team can actually use. Users provide an audience, an objective, and optional notes to steer the agent. ClinicOS then produces a campaign plan, message direction, and nurture sequence that can be emailed directly or downloaded for printing and offline handouts.

## Review Queue

- Routes: `/admin/support`, `/admin/review`
- Human takeover layer for escalated Practice Desk conversations
- Automatically surfaces chats where a human is needed
- Lets specialists inspect the full transcript, practice profile, and audit context
- Allows operators to take over the AI flow and reply directly as a human

Once a human takes over, the queue becomes the bridge between Practice Desk and the internal support team: ClinicOS AI steps back for that conversation and the specialist continues the support flow directly.

## Guidance And Suggested Prompts

Every major workspace includes guided onboarding elements so the product is usable on first touch:
- suggested prompts and starter scenarios
- modal-based help for each major tool or workflow
- quick examples for users who are stuck or unfamiliar with the system

This applies across Practice Desk, Review Queue, Sales & Outreach, and Marketing.

## Technology and Deployment

- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Pydantic
- Migrations: Alembic
- Database: PostgreSQL in production, compatible with direct Supabase Postgres connections
- Local DB option: PostgreSQL or SQLite fallback for local-only convenience
- AI runtime: OpenAI SDK, `gpt-4.1-mini`
- Web research/scraping: OpenAI hosted tools plus Scrapling
- Frontend hosting: Vercel
- Backend hosting: Render
- Production database hosting: Supabase PostgreSQL or equivalent direct Postgres

The application is deployed online as a real hosted system:
- Frontend on **Vercel**
- Backend on **Render**
- Database on **Supabase PostgreSQL**
- Live app at `https://growth-and-support-copilot.vercel.app/`

The frontend and backend are deployed separately, and the backend uses a real GPT-backed SDK path rather than a docs-only or local-only prototype flow. The actual web stack is **Next.js + FastAPI + PostgreSQL**, not Flask.

## Local Development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Environment Variables

### Backend

- `ENVIRONMENT` -> use `development`, `local`, `test`, `staging`, or `production`
- `DATABASE_URL` -> required in staging/production; direct PostgreSQL connection string
- `LOCAL_SQLITE_PATH` -> optional local SQLite path when `DATABASE_URL` is unset
- `AUTO_CREATE_SQLITE_SCHEMA` -> local SQLite convenience only
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `ENABLE_LIVE_SALES_RESEARCH`
- `LIVE_RESEARCH_TIMEOUT_SECONDS`
- `ENABLE_MARKETING`
- `CORS_ORIGINS`
- `FRONTEND_URL`
- `TRUSTED_HOSTS`
- `LOG_LEVEL`

### Frontend

- `NEXT_PUBLIC_API_URL` -> backend base URL; defaults locally to `http://localhost:8000`

## Database and Migrations

ClinicOS uses Alembic for repository-managed schema changes.

Run migrations:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Local fallback behavior:
- In `development`/`local`/`test`, if `DATABASE_URL` is unset, the backend can fall back to SQLite
- In `staging`/`production`, PostgreSQL via `DATABASE_URL` is required

Existing SQLite data can be copied into a migrated PostgreSQL target with:

```bash
cd backend
source .venv/bin/activate
python scripts/port_sqlite_to_database.py \
  --source-url sqlite:///$(pwd)/clinic_copilot.db \
  --target-url "$DATABASE_URL"
```

## Verification

### Backend

```bash
cd backend
source .venv/bin/activate
pytest
python -m compileall app
```

### Frontend

```bash
cd frontend
npx tsc --noEmit
npm run build
```

## Deployment

### Render backend

- Set `ENVIRONMENT=production`
- Set `DATABASE_URL`
- Set `CORS_ORIGINS` to include the Vercel frontend origin
- Set `OPENAI_API_KEY` for live AI and live sales research
- Optional: `FRONTEND_URL`, `TRUSTED_HOSTS`, `LOG_LEVEL`

Suggested commands:

```bash
pip install -r requirements.txt && alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Vercel frontend

- Set `NEXT_PUBLIC_API_URL` to the deployed backend URL

## Tradeoffs

ClinicOS was built to ship a real system quickly, so the architecture intentionally favors clarity, typed boundaries, and operational control over maximum framework sophistication.

### Why these choices

- **FastAPI instead of Flask**
  - FastAPI gave a faster path to typed APIs, async-friendly handlers, and schema-first request/response validation
  - that fit the project better because the backend is handling agent workflows, queue state, admin actions, and structured outputs rather than serving a minimal web layer

- **Pydantic for schemas and agent payloads**
  - Pydantic made it easier to keep API contracts, health responses, research results, and persisted read models predictable
  - this reduced glue code and made the system easier to reason about while moving quickly

- **SQLAlchemy plus Postgres**
  - the app has strongly relational concerns: conversations, messages, escalations, review state, outreach history, campaign history, audit/archive flows, and per-chat controls
  - a direct relational model was a better fit than prematurely introducing extra data layers

- **OpenAI SDK directly instead of LangChain-first orchestration**
  - using the SDK directly kept the call path simpler, easier to deploy, and easier to debug
  - it reduced abstraction overhead and let the agent logic stay close to the actual product flows
  - this was a deliberate shipping tradeoff: fewer moving parts, less framework ceremony, faster iteration

- **`gpt-4.1-mini` as the single default model**
  - chosen to keep latency and cost manageable while still enabling a real hosted deployment
  - this helped move faster and made it easier to keep the live app functional within practical constraints

### What we did not optimize yet

- **Model benchmarking**
  - a stronger production version would compare multiple models for support quality, escalation judgment, research accuracy, and marketing usefulness instead of hard-defaulting to one

- **Higher-end reasoning**
  - larger models would likely produce better nuance, stronger context synthesis, and more reliable judgment in messy edge cases
  - the tradeoff is cost, latency, and the need for a larger evaluation budget

- **Framework-heavy orchestration**
  - LangChain, semantic routing layers, or richer agent frameworks could become useful if the system grows into more retrieval-heavy or deeply multi-agent behavior
  - I did not start there because it would have added complexity before the core workflows were proven
  - the tradeoff is that the current system has less built-in abstraction for evaluation pipelines, retrieval chains, and advanced orchestration patterns

- **Semantic retrieval and memory infrastructure**
  - the current version leans on persisted relational memory and structured practice context rather than a larger retrieval stack or vector-first memory layer
  - that keeps the system straightforward, but a more advanced version might benefit from retrieval for long-running account history, knowledge grounding, or cross-chat reasoning

### Point of view on what to do next

If this were pushed further, the next high-value step would be to benchmark and harden the support and escalation workflows first, because that is the core product surface and the clearest source of real operational leverage. After that, I would expand evaluation around live sales-research accuracy and marketing usefulness, then decide whether heavier orchestration tools are actually justified.

In short, the architecture tradeoff was intentional: build something real, controllable, and deployable first; add heavier orchestration, broader model selection, and richer retrieval only when the operational workflows prove they need it.
