# BRIA Pixel Playground Web

Minimal FastAPI wrapper plus a static front-end that mimics the FIBO playground to test the pixel pipeline in a browser.

## Quick start

1) Install deps (ideally in a virtualenv):
```
pip install -r ../requirements-web.txt
```

2) Set your BRIA API token (env var):
```
set BRIA_API_TOKEN=your-token-here
```

3) Run the server:
```
uvicorn server:app --reload
```

4) Open the UI: http://localhost:8000/

## Flow
- Generate: Prompt + style → pseudo pixel art (via `/api/generate`).
- Convert: Auto-detect block size → perfect pixel art (via `/api/convert`).
- Remove BG: Removes background from the latest image (via `/api/remove-bg`).

All artifacts are stored under `webapp/outputs` and served at `/outputs/<file>`.
