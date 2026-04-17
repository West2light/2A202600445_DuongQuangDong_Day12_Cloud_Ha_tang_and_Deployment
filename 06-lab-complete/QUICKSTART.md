# 🚀 Lab 06: Quick Start (2 minutes)

## Status: ✅ COMPLETE & READY

Your production AI agent is **fully implemented** with all Day 12 concepts.

## 3-Step Test

### 1️⃣ Start Services
```bash
docker-compose up --build
```
(Wait for both agent and redis to be healthy ~30s)

### 2️⃣ Test in Another Terminal
```bash
# Health check
curl http://localhost:8000/health

# Ask the agent
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is production-ready code?"}'
```

### 3️⃣ See It Working
Response should be:
```json
{
  "question": "What is production-ready code?",
  "answer": "Đây là câu trả lời từ AI agent...",
  "model": "gpt-4o-mini",
  "timestamp": "2026-04-17T..."
}
```

## What's Implemented

### Code (app/)
- ✅ `main.py` — Full FastAPI with auth, rate limit, cost guard, health checks
- ✅ `config.py` — Environment-based 12-Factor config
- ✅ `utils/mock_llm.py` — Mock LLM for testing

### Infrastructure
- ✅ `Dockerfile` — Multi-stage: 1.66GB → 236MB
- ✅ `docker-compose.yml` — Agent + Redis with health checks
- ✅ `railway.toml` — Railway deployment ready
- ✅ `render.yaml` — Render deployment ready

### Security
- ✅ No hardcoded secrets (all in .env)
- ✅ .env in .gitignore
- ✅ Security headers (X-Content-Type-Options, X-Frame-Options)
- ✅ Non-root user in container
- ✅ CORS configured

### Features Verified
| Feature | Check |
|---------|-------|
| API Key Auth | ✅ X-API-Key header |
| Rate Limiting | ✅ 10/min sliding window |
| Cost Guard | ✅ $5/day budget |
| Health Check | ✅ /health endpoint |
| Readiness Probe | ✅ /ready endpoint |
| Graceful Shutdown | ✅ SIGTERM handling |
| JSON Logging | ✅ Structured format |
| Multi-stage Docker | ✅ Builder + Runtime |
| Non-root | ✅ Agent user |

## Next Steps

### Option A: Keep Testing Locally
```bash
docker-compose up
# Keep running while you develop
```

### Option B: Deploy to Cloud

**Railway (Easiest)**
```bash
npm i -g @railway/cli
railway login
railway init
railway variables set AGENT_API_KEY=your-secure-key
railway variables set JWT_SECRET=your-secure-key
railway up
railway domain  # Get your public URL
```

**Render (More Control)**
```bash
# Push to GitHub
git push

# Go to render.com → New → Blueprint
# Select your repo, Render reads render.yaml automatically
```

## Test Commands Reference

```bash
# Health (no auth)
curl http://localhost:8000/health

# Readiness (no auth)
curl http://localhost:8000/ready

# Ask agent (requires API key)
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question here"}'

# Get metrics (requires API key)
curl http://localhost:8000/metrics \
  -H "X-API-Key: dev-key-change-me-in-production"

# Test rate limit (send 15 requests)
for i in {1..15}; do curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Test $i\"}" & done; wait
```

## File Guide

| File | Purpose |
|------|---------|
| `app/main.py` | Main FastAPI application |
| `app/config.py` | Config from environment variables |
| `utils/mock_llm.py` | Mock LLM responses |
| `Dockerfile` | Container build (multi-stage) |
| `docker-compose.yml` | Local dev stack |
| `.env.example` | Config template |
| `railway.toml` | Railway deployment config |
| `render.yaml` | Render deployment config |
| `requirements.txt` | Python dependencies |
| `GETTING_STARTED.md` | Detailed guide |
| `check_production_ready.py` | Validation script |

## Environment Variables

For **Development** (.env.local):
```env
ENVIRONMENT=development
DEBUG=true
AGENT_API_KEY=dev-key-change-me-in-production
JWT_SECRET=dev-jwt-secret-change-in-production
RATE_LIMIT_PER_MINUTE=20
DAILY_BUDGET_USD=5.0
```

For **Production** (set in Railway/Render dashboard):
```env
ENVIRONMENT=production
DEBUG=false
AGENT_API_KEY=<strong-random-key>
JWT_SECRET=<strong-random-key>
```

---

**More details?** → See [GETTING_STARTED.md](GETTING_STARTED.md)  
**Lab instructions?** → See [../CODE_LAB.md](../CODE_LAB.md)

**You're ready to go live!** 🎉
