# Job Scout Agent

AI-powered daily job scout that scrapes career pages, scores matches against your experience, and emails you a curated digest.

---

## Architecture

The Job Scout Agent is built with a layered pipeline architecture:

- **Trigger Layer**: Spring Boot `@Scheduled` cron (Java) manages daily execution and scheduling
- **Scraper Layer**: Playwright + Redis cache for efficient multi-page scraping with intelligent caching
- **LLM Tools**: Python-based tools handle job extraction, match scoring, and digest composition using LLMs
- **Orchestration**: LangChain-style tool pipeline coordinates the workflow with Gemini/Anthropic API backends
- **RAG Memory**: pgvector stores job embeddings and experience chunks for semantic-based retrieval and contextual matching
- **Observability**: Langfuse traces every agent run end-to-end with structured spans for debugging and monitoring
- **Trust Layer**: Gate checks before email dispatch with comprehensive audit logging to prevent errors
- **Output**: Gmail SMTP for email delivery and PostgreSQL for persistent storage of jobs and runs

---

## Tech Stack

- **Scheduling**: Java 21, Spring Boot 3
- **Core Agent**: Python 3.11, LangChain concepts
- **Scraping**: Playwright, Redis
- **LLM Backends**: Gemini API (dev), Claude Sonnet (prod options)
- **Vector DB**: pgvector, PostgreSQL
- **Observability**: Langfuse
- **Email**: Gmail SMTP

---

## Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Java 21+
- API keys: Gemini (dev) or Anthropic (prod), Langfuse, Gmail App Password

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Job-Scout_Agent.git
   cd Job-Scout_Agent
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - GEMINI_API_KEY or ANTHROPIC_API_KEY
   # - DATABASE_URL (postgres connection)
   # - GMAIL_USER, GMAIL_APP_PASSWORD, EMAIL_TO
   # - LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   # Starts PostgreSQL, Redis, and other dependencies
   ```

4. **Install Python dependencies**
   ```bash
   cd agent
   pip install -r requirements.txt
   ```

5. **Install Playwright browser**
   ```bash
   playwright install chromium
   ```

6. **Test single run**
   ```bash
   python orchestrator.py
   ```

7. **Start scheduled runs** (optional)
   ```bash
   cd scheduler
   mvn spring-boot:run
   ```

---

## Project Structure

```
.
├── README.md
├── docker-compose.yml
├── agent/
│   ├── main.py                    # Entry point
│   ├── orchestrator.py            # Core pipeline orchestration
│   ├── llm_provider.py            # LLM backend abstraction (Gemini/Anthropic)
│   ├── email_sender.py            # Gmail SMTP integration
│   ├── observability.py           # Langfuse tracing setup
│   │
│   ├── database/
│   │   ├── db.py                  # PostgreSQL operations (jobs, runs)
│   │   └── vector_store.py        # pgvector embeddings & RAG
│   │
│   ├── scraper/
│   │   ├── playwright_scraper.py  # Async Playwright scraping
│   │   └── redis_cache.py         # Cache layer for pages
│   │
│   ├── tools/
│   │   ├── extract_jobs.py        # LLM-powered job extraction
│   │   ├── match_score.py         # Job scoring with RAG context
│   │   └── compose_digest.py      # Email digest generation
│   │
│   └── trust/
│       └── trust_gate.py          # Safety checks before email send
│
├── scheduler/
│   ├── pom.xml
│   ├── mvnw
│   └── src/
│       └── main/java/in/jobscout/scheduler/
│           └── SchedulerApplication.java  # Spring Boot @Scheduled trigger
│
└── eval/
    └── test_extraction.py         # Evaluation harness for extraction quality
```

---

## Features

### End-to-End Pipeline
1. **Scrape**: Multi-page career scraping with Redis caching
2. **Extract**: LLM-powered job title/description parsing
3. **Score**: RAG-enhanced job matching against candidate experience
4. **Summarize**: Intelligent digest composition
5. **Gate**: Trust layer safety checks
6. **Send**: Conditional Gmail delivery
7. **Persist**: Database storage + vector embeddings
8. **Trace**: Full observability via Langfuse

### RAG-Augmented Matching
- Experience chunks indexed as embeddings
- Similar past job scores surfaced during evaluation
- Contextual scoring improves match quality over time

### Resilience & Observability
- Langfuse end-to-end tracing per run
- Rate-limit retry logic (60/120/180s backoff)
- Structured audit logs for compliance
- Error recovery and graceful degradation

---

## Environment Variables

```bash
# LLM Provider
LLM_PROVIDER=gemini  # or 'anthropic'
LLM_MODEL=gemini-2.0-flash
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/jobscout

# Email
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=...
EMAIL_TO=recipient@example.com

# Observability
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com

# Trust gate
TRUST_MAX_JOBS=50
```

---

## Running Tests

Evaluate extraction quality from the eval suite:
```bash
cd eval
python test_extraction.py
```

Tests 2 realistic career page fixtures and reports precision/recall metrics.

---

## Portfolio Note

Built as a portfolio project demonstrating AI agent engineering skills including:
- **Tool use**: LLM-powered extraction, scoring, and composition
- **Orchestration**: LangChain-style pipeline execution
- **RAG**: Vector embeddings and semantic retrieval (pgvector)
- **Observability**: End-to-end tracing with structured spans
- **Trust layers**: Safety gates and audit logging

Targeting **Staff/AI Agent Engineer** roles.

---

## License

MIT

---

## Contact

Questions or collaboration opportunities? Open an issue or reach out directly.
