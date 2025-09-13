# Project Requirements & Tooling

## Toolchain
- Python: 3.13 (pinned via `.python-version`)
- Package / environment manager: `uv` (exclusive)
- Build backend: `uv_build`

## Installing uv
Follow the official instructions: <https://docs.astral.sh/uv/>

macOS / Linux (standalone installer):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Verify installation:
```bash
uv --version
```

(Optional) Add to PATH if not already exported (installer usually handles this):
```bash
# Example; adjust shell profile as needed
export PATH="$HOME/.local/bin:$PATH"
```

## Initial Project Setup
```bash
uv python pin 3.13          # create .python-version if missing
uv sync                     # create venv and install deps (none yet)
uv run main.py              # test entrypoint
```

## Adding Dependencies
```bash
uv add aiokafka httpx motor  # (example future deps)
uv lock --upgrade            # upgrade all
```

## Building
```bash
uv build
ls dist/
```

## Rationale
A single fast tool (uv) ensures reproducibility, speed, and lowers cognitive overhead versus multiple overlapping utilities (pip, venv, pip-tools, etc.).
