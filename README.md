# quorabroker

Kafka topic subscriber that consumes "quora" (task) messages containing URLs to fetch, retrieves the corresponding web pages, and stores the raw HTML (and optional normalized metadata) into a MongoDB Atlas collection. The service is fully managed with `uv` (environment, dependencies, build) on Python 3.13.

## Core Responsibilities

1. Subscribe to a Kafka topic (e.g., `quora.fetch.requests`).
2. Parse each message (expected JSON with at minimum: `url`, optional `id`, `priority`).
3. Fetch the target page (HTTP GET) with resilient, async, rate‑aware client.
4. Persist result into MongoDB Atlas (raw HTML + fetch metadata + timestamp).
5. Emit structured logs and (future) optional success/failure events.

## Features / Intent

- Single-tool workflow (`uv`) – no pip usage
- Deterministic environments via `uv.lock`
- English-only codebase (see `definitions/language-definition.md`)
- Strong platform definition (Python 3.13, see `definitions/platform-definition.md`)

## Architecture (Planned High-Level)

- Consumer Loop: async Kafka consumer (likely `aiokafka`)
- Fetch Layer: async HTTP client (e.g., `httpx`) with timeout + retry + backoff
- Persistence Layer: MongoDB driver (`motor`) writing documents
- Schema Strategy: minimal required fields first; evolve with migrations-like approach
- Observability: structured logging (JSON), future metrics hooks

## Directory Layout (Current / Planned)

```text
quorabroker/
  main.py
  pyproject.toml
  README.md
  definitions/
    language-definition.md
    platform-definition.md
  docs/
    requirements.md
  # Future
  # src/quorabroker/__init__.py
  # src/quorabroker/consumer.py
  # src/quorabroker/fetcher.py
  # src/quorabroker/storage.py
  # tests/
```

## Environment Configuration

Runtime configuration comes from a `.env` file (NOT committed). Example:

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=quora.fetch.requests
MONGO_URI=mongodb+srv://user:pass@cluster.example.mongodb.net
MONGO_DB=quorabroker
MONGO_COLLECTION=pages
HTTP_TIMEOUT_SECONDS=15
MAX_CONCURRENT_FETCHES=10
USER_AGENT=quorabroker/0.1 (+https://example.org)
LOG_LEVEL=INFO
```

You can load this via a small helper (e.g., `python-dotenv`) or manual parsing; dependency will be added when implementation begins.

## Operational Flow (Planned)

1. Start consumer – subscribe to topic
2. For each message: validate JSON -> enqueue fetch task
3. Fetch executor performs HTTP request with retry (e.g., exponential backoff)
4. Persist document:

   ```json
   {
     "_id": "<uuid-or-message-id>",
     "url": "https://...",
     "status_code": 200,
     "fetched_at": "2025-09-13T12:34:56Z",
     "latency_ms": 123,
     "content_length": 54321,
     "html": "<html>...</html>",
     "error": null,
     "meta": {"retries": 1}
   }
   ```
5. Commit Kafka offset after successful persistence
6. On failure: store error record + (future) dead-letter topic

## Development Workflow

Prerequisites and tool installation are documented in `docs/requirements.md` (refer there instead of duplicating instructions here).

Common commands:

```bash
uv sync            # sync environment
uv run main.py     # run entrypoint (temporary until consumer scaffolding exists)
uv build           # build distributions (uv_build backend)
```

### Ruff (Lint & Format)

Install dev dependencies if not already synced (Ruff is in optional `dev` group):

```bash
uv sync --group dev
```

Run lint checks:

```bash
uv run ruff check .
```

Auto-fix and format:

```bash
uv run ruff check --fix .
uv run ruff format .
```

Optional pre-commit hook snippet (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format
```

## Conventions

- All identifiers, comments, docs: English only
- No `pip install` instructions; only `uv` commands
- Future modules placed under `src/` once introduced

## Roadmap (Initial Milestones)

- [ ] Introduce `src/` package + bootstrap consumer skeleton
- [ ] Add dependencies: `aiokafka`, `httpx`, `motor`, `python-dotenv`, `orjson`, `structlog` (candidate stack)
- [ ] Implement message schema validation (pydantic or lightweight dataclass)
- [ ] Add graceful shutdown (signal handling)
- [ ] Add retry & backoff strategy
- [ ] Add basic test harness

## Logging & Observability (Planned)

- Structured JSON logs (choose library: `structlog` or stdlib + formatter)
- Timings per fetch
- Error classification (network vs. HTTP vs. parse)

## Security Considerations

- Avoid logging full HTML payloads
- Support optional allowlist of domains
- Plan rate limiting to avoid abuse

## License

Add license details here (update `pyproject.toml` and include LICENSE file).

## Changelog

Initialize a `CHANGELOG.md` once the first release is cut.

