# Platform Definition

## Runtime
- Supported Python version: 3.13 only (project assumes CPython 3.13+; do not downgrade).
- A `.python-version` file MUST pin `3.13` (add if missing).

## Environment & Dependency Management
- The ONLY allowed tool for dependency, environment, and build management is `uv` from Astral.
- `pip`, `pip-tools`, `poetry`, `rye`, `conda`, and manual `python -m venv` usage are prohibited in project scripts, docs, and automation.
- All dependency operations: `uv add`, `uv remove`, `uv lock`, `uv sync`, `uv upgrade`, `uv run`.
- Lock file: `uv.lock` must be committed.

## Build System
- Build backend: `uv_build`.
- `[build-system]` in `pyproject.toml` MUST specify:
```
[build-system]
requires = ["uv_build>=0.8.17,<0.9.0"]
build-backend = "uv_build"
```

## Project Layout
- Source packages should live under `src/` once introduced (future refactor—currently a single `main.py`).
- Tests under `tests/` (future) executed via `uv run -m pytest` once pytest added.

## Commands Policy
| Task | Command |
|------|---------|
| Run script | `uv run main.py` |
| Add dependency | `uv add <name>` |
| Remove dependency | `uv remove <name>` |
| Upgrade one | `uv lock --upgrade-package <name>` |
| Upgrade all | `uv lock --upgrade` |
| Sync env | `uv sync` |
| Build dist | `uv build` |
| Pin Python | `uv python pin 3.13` |

## Prohibited Patterns
- `pip install ...` (any form)
- `requirements.txt` (unless imported historical context—should not be used)
- Using `setup.py` or `setup.cfg` for metadata
- Direct `venv` activation instructions in docs (use `uv run` or `uv sync` + activation)

## Pre-Commit / CI Recommendations
1. Verify Python version: `uv python pin 3.13` (assert `.python-version` exists)
2. Run `uv lock --check` once available (future) or compare timestamps (script) to ensure sync
3. Run formatters/linters via `uvx ruff check` / `uvx ruff format` (once adopted)
4. Build: `uv build` and optionally install locally via `uv pip install dist/*.whl` (benchmark only)

## Future Enhancements (Not Yet Implemented)
- Introduce `src/quorabroker/__init__.py` package structure
- Add `ruff` and `pytest` as dev tools via `uv tool install` or project deps
- Add `pyproject.toml` optional settings under `[tool.uv]` (e.g., indexes, cache tuning)

## Rationale
Using a single fast tool (`uv`) ensures consistency, speed, and reproducibility across environments while reducing cognitive overhead from multiple overlapping tools.

## Change Log
- v1.0: Initial platform definition file created.
