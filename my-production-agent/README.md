## My Production Agent (Part 6)

### Local (PowerShell)

```powershell
cd my-production-agent
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Copy-Item .env.example .env

# edit .env and set AGENT_API_KEYS + OPENAI_API_KEY
.\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Test:

```powershell
curl.exe "http://localhost:8000/health"
curl.exe "http://localhost:8000/ready"
curl.exe -X POST "http://localhost:8000/ask" -H "X-API-Key: change-me" -H "Content-Type: application/json" -d "{\"question\":\"What is Docker?\"}"
```

### Docker Compose

```powershell
cd my-production-agent
docker compose up -d --build
```

Test via nginx:

```powershell
curl.exe "http://localhost/health"
curl.exe -X POST "http://localhost/ask" -H "X-API-Key: change-me" -H "Content-Type: application/json" -d "{\"question\":\"Hello\"}"
```

Stop:

```powershell
docker compose down
```

