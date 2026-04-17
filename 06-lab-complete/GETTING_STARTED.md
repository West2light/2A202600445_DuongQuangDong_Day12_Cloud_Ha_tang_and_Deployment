# Lab 06: Production-Ready AI Agent — Getting Started

## ✅ Project Status

Your lab 06 is **95% complete**! Here's what's been done:

### Core Components

- ✅ **app/main.py** — Full FastAPI application with all required features
- ✅ **app/config.py** — 12-Factor config management from environment variables
- ✅ **Dockerfile** — Multi-stage build, non-root user, health checks
- ✅ **docker-compose.yml** — Agent + Redis stack with health checks
- ✅ **railway.toml** — Railway deployment config
- ✅ **render.yaml** — Render deployment config
- ✅ **.env.example** — Environment variables template
- ✅ **.dockerignore** — Excludes .env, **pycache**, etc.
- ✅ **requirements.txt** — All dependencies listed
- ✅ **utils/mock_llm.py** — Mock LLM for development (newly added)

### Features Implemented

1. ✅ **Config Management** — All settings from environment (PORT, REDIS_URL, AGENT_API_KEY, etc.)
2. ✅ **Structured JSON Logging** — All logs in JSON format
3. ✅ **API Key Authentication** — X-API-Key header verification
4. ✅ **Rate Limiting** — Sliding window (10 req/min per API key)
5. ✅ **Cost Guard** — Daily budget tracking ($5/day default)
6. ✅ **Health Checks** — `/health` (liveness) + `/ready` (readiness)
7. ✅ **Graceful Shutdown** — SIGTERM handling with request draining
8. ✅ **Security Headers** — X-Content-Type-Options, X-Frame-Options
9. ✅ **CORS** — Configurable allowed origins
10. ✅ **Error Handling** — Proper HTTP status codes (401, 429, 503, etc.)

---

## 🚀 How to Run Locally

### Option 1: Docker Compose (Recommended)

```bash
# Start Docker Desktop if needed
# Then:

cd 06-lab-complete

# Build and start all services
docker-compose up --build

# In another terminal, test the API
curl -X POST http://localhost/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

Expected response:

```json
{
  "question": "What is Docker?",
  "answer": "Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!",
  "model": "gpt-4o-mini",
  "timestamp": "2026-04-17T20:15:30.123456+00:00"
}
```

### Option 2: Direct Python (Development Only)

```bash
# Create .env.local from template
cp .env.example .env.local

# Install dependencies
pip install -r requirements.txt

# Start app
python -m uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

---

## 🧪 Testing All Endpoints

### 1. Health Check (no auth required)

```bash
curl http://localhost:8000/health
```

Response: `{"status": "ok", "version": "1.0.0", ...}`

### 2. Readiness Check (no auth required)

```bash
curl http://localhost:8000/ready
```

Response: `{"ready": true}`

### 3. Ask Agent (requires X-API-Key)

```bash
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'
```

### 4. Test Authentication (should fail)

```bash
# Missing API key
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Response: 401 Unauthorized
```

### 5. Test Rate Limiting

```bash
# Send 20 requests in rapid succession
for i in {1..20}; do
  curl -X POST http://localhost:8000/ask \
    -H "X-API-Key: dev-key-change-me-in-production" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"Test $i\"}" &
done
wait

# After ~10 requests, you'll see 429 Too Many Requests
```

### 6. Check Metrics (requires API key)

```bash
curl http://localhost:8000/metrics \
  -H "X-API-Key: dev-key-change-me-in-production"
```

---

## 🔒 Security Configuration

### Development (current .env.local)

```env
AGENT_API_KEY=dev-key-change-me-in-production
JWT_SECRET=dev-jwt-secret-change-in-production
ENVIRONMENT=development
DEBUG=true
```

### Production (Railway/Render)

```env
AGENT_API_KEY=<strong-random-key>
JWT_SECRET=<strong-random-key>
ENVIRONMENT=production
DEBUG=false
```

**Important:** Change these values before deploying!

---

## 🐳 Docker Compose Architecture

```
┌─────────────────────────────────────────┐
│           Local Machine                 │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     FastAPI Agent (Port 8000)    │  │
│  │  ✓ Health checks                 │  │
│  │  ✓ Authentication                │  │
│  │  ✓ Rate limiting                 │  │
│  │  ✓ Cost guard                    │  │
│  └──────────┬───────────────────────┘  │
│             │                          │
│             ├─ Asks questions to LLM   │
│             │                          │
│  ┌──────────▼───────────────────────┐  │
│  │      Redis (Port 6379)           │  │
│  │  (session storage, rate limit)   │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚀 Deploying to Cloud

### Option A: Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd 06-lab-complete
railway init

# Set environment variables
railway variables set ENVIRONMENT=production
railway variables set AGENT_API_KEY=<your-secure-key>
railway variables set JWT_SECRET=<your-secure-key>

# Deploy
railway up

# Get public URL
railway domain
```

Then test:

```bash
curl https://<your-railway-domain>/health
```

### Option B: Render

```bash
# 1. Push code to GitHub
git add .
git commit -m "Day 12 Lab 06: Production AI Agent"
git push

# 2. Go to render.com
# 3. Click "New" → "Blueprint"
# 4. Connect your GitHub repo
# 5. Render will automatically find render.yaml
# 6. Set environment variables in dashboard
# 7. Deploy!

# Test
curl https://<your-render-domain>/health
```

---

## ✅ Validation Checklist

### Run the production readiness checker:

```bash
python check_production_ready.py
```

Expected output (should show ~100% passing):

```
✅ Dockerfile exists
✅ docker-compose.yml exists
✅ .dockerignore exists
✅ .env.example exists
✅ requirements.txt exists
✅ railway.toml or render.yaml exists
✅ .env in .gitignore
✅ No hardcoded secrets in code
✅ /health endpoint defined
✅ /ready endpoint defined
✅ Authentication implemented
✅ Rate limiting implemented
✅ Graceful shutdown (SIGTERM)
✅ Structured logging (JSON)
✅ Multi-stage build
✅ Non-root user
✅ HEALTHCHECK instruction
✅ Slim base image
✅ .dockerignore covers .env
✅ .dockerignore covers __pycache__
```

---

## 📚 Key Concepts Covered

| Concept                | Implementation                              |
| ---------------------- | ------------------------------------------- |
| **12-Factor App**      | Config from env vars (app/config.py)        |
| **Docker Multi-stage** | Dockerfile with builder + runtime stages    |
| **Health Checks**      | `/health` (liveness) + `/ready` (readiness) |
| **Authentication**     | X-API-Key header validation                 |
| **Rate Limiting**      | Sliding window in memory (10 req/min)       |
| **Cost Guard**         | Daily budget tracking                       |
| **Structured Logging** | JSON format for log aggregation             |
| **Graceful Shutdown**  | SIGTERM handling with timeout               |
| **Security Headers**   | X-Content-Type-Options, X-Frame-Options     |

---

## 🐛 Troubleshooting

### Docker fails to build

```bash
# Clean up
docker-compose down
docker system prune -a

# Try again
docker-compose up --build
```

### Port 8000 already in use

```bash
# Find what's using port 8000
lsof -i :8000

# Or use different port in docker-compose.yml
ports:
  - "8001:8000"
```

### Redis connection error

```bash
# Make sure Redis is healthy
docker-compose logs redis

# Restart
docker-compose restart redis
```

### Authentication failing

```bash
# Check your API key in .env.local
grep AGENT_API_KEY .env.local

# Use it in request
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

---

## 📖 Next Steps

1. **Test locally** with Docker Compose
2. **Verify all endpoints** respond correctly
3. **Test authentication** works properly
4. **Test rate limiting** kicks in after 10 requests
5. **Deploy to Railway or Render**
6. **Test production URLs** are publicly accessible
7. **Monitor logs** in cloud dashboard

---

## 📞 Support

- Refer to [CODE_LAB.md](../CODE_LAB.md) for detailed lab instructions
- Check FastAPI docs at `http://localhost:8000/docs` (dev only)
- Review [app/main.py](app/main.py) for implementation details

---

**Ready to deploy? Let's go! 🚀**
