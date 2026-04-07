# AI Chatbot Assessment

FastAPI backend for a ChatGPT-style conversational assistant with persistent session memory, Gemini-powered responses, Docker packaging, and the exact endpoints required by the assessment.

## Features

- `POST /chat` for multi-turn AI chat responses
- `GET /history/{session_id}` for ordered session history retrieval
- `DELETE /history/{session_id}` for session reset
- `GET /health` for service checks
- SQLite-backed persistent memory so session history survives multiple API calls and container restarts
- `.env`-driven configuration with no hardcoded credentials
- Docker and Docker Compose support
- `pytest` coverage for the core API behavior

## Project Structure

```text
app/
  main.py
  config.py
  models/
    schemas.py
  routes/
    chat.py
  services/
    ai.py
    memory.py
data/
tests/
Dockerfile
docker-compose.yml
.env.example
README.md
```

## Architecture Notes

### 1. API Layer

`app/routes/chat.py` owns HTTP concerns only:

- request validation
- status codes
- calling the correct services
- shaping responses

### 2. Memory Layer

`app/services/memory.py` stores each session's messages in SQLite. This was chosen over a plain in-memory dictionary because it gives stronger persistence with minimal operational overhead and no extra container dependency.

### 3. AI Layer

`app/services/ai.py` wraps the Gemini provider behind a single service boundary. The route layer never depends on provider-specific request details, so swapping providers later remains straightforward.

### 4. Configuration Layer

`app/config.py` centralizes all runtime configuration through environment variables loaded from `.env`.

## Requirements

- Python 3.10+
- A Gemini API key
- Docker Desktop if you want to use the containerized workflow

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env`.
4. Add your real `GEMINI_API_KEY`.
5. Start the API.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Setup

1. Copy `.env.example` to `.env`.
2. Set `GEMINI_API_KEY`.
3. Build and run with Docker Compose.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The API will be exposed on port `8000`.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `APP_NAME` | No | Display name for the API |
| `APP_ENV` | No | Runtime environment label |
| `APP_DEBUG` | No | FastAPI debug flag |
| `APP_HOST` | No | Bind host for local runs |
| `APP_PORT` | No | Bind port for local runs |
| `DATABASE_PATH` | No | SQLite file path for message persistence |
| `GEMINI_API_KEY` | Yes | API key for the Gemini API |
| `GEMINI_API_BASE_URL` | No | Base URL for Gemini REST models |
| `GEMINI_MODEL` | No | Gemini model identifier to call |
| `LLM_TIMEOUT_SECONDS` | No | HTTP timeout for provider calls |
| `TEMPERATURE` | No | Sampling temperature |
| `SYSTEM_PROMPT` | No | Default assistant instruction |

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

### Send a Chat Message

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session",
    "message": "Hello, who are you?"
  }'
```

Example response:

```json
{
  "session_id": "demo-session",
  "reply": "Hello! I am your AI assistant...",
  "history_length": 2
}
```

### Fetch Session History

```bash
curl http://localhost:8000/history/demo-session
```

### Clear Session History

```bash
curl -X DELETE http://localhost:8000/history/demo-session
```

## Running Tests

```powershell
pytest
```

The tests use a fake AI service and a temporary SQLite database so they run without a real API key.

## Demo Video Checklist

Record a screen capture that shows all of the following:

1. `docker compose up --build`
2. `GET /health`
3. two `POST /chat` calls using the same `session_id`
4. `GET /history/{session_id}` returning the full stored conversation
5. `DELETE /history/{session_id}` clearing the conversation

## Submission Notes

- Keep `.env` out of version control
- Include `.env.example`
- Verify the project runs from scratch using only this README
- Add your demo video link below before submission

### Video Demonstration Link

`Add your YouTube or Google Drive link here`
