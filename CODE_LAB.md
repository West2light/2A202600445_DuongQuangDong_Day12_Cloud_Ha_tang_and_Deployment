# Code Lab: Deploy Your AI Agent to Production

> **AICB-P1 · VinUniversity 2026**  
> Thời gian: 3-4 giờ | Độ khó: Intermediate

## Mục Tiêu

Sau khi hoàn thành lab này, bạn sẽ:

- Hiểu sự khác biệt giữa development và production
- Containerize một AI agent với Docker
- Deploy agent lên cloud platform
- Bảo mật API với authentication và rate limiting
- Thiết kế hệ thống có khả năng scale và reliable

---

## Yêu Cầu

```bash
 Python 3.11+
 Docker & Docker Compose
 Git
 Text editor (VS Code khuyến nghị)
 Terminal/Command line
```

**Không cần:**

- OpenAI API key (dùng mock LLM)
- Credit card
- Kinh nghiệm DevOps trước đó

---

## Lộ Trình Lab

| Phần       | Thời gian | Nội dung                |
| ---------- | --------- | ----------------------- |
| **Part 1** | 30 phút   | Localhost vs Production |
| **Part 2** | 45 phút   | Docker Containerization |
| **Part 3** | 45 phút   | Cloud Deployment        |
| **Part 4** | 40 phút   | API Security            |
| **Part 5** | 40 phút   | Scaling & Reliability   |
| **Part 6** | 60 phút   | Final Project           |

---

## Part 1: Localhost vs Production (30 phút)

### Concepts

**Vấn đề:** "It works on my machine" — code chạy tốt trên laptop nhưng fail khi deploy.

**Nguyên nhân:**

- Hardcoded secrets
- Khác biệt về environment (Python version, OS, dependencies)
- Không có health checks
- Config không linh hoạt

**Giải pháp:** 12-Factor App principles

### Exercise 1.1: Phát hiện anti-patterns

```bash
cd 01-localhost-vs-production/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm ít nhất 5 vấn đề.

<details>
<summary> Gợi ý</summary>

Tìm:

- API key hardcode
- Port cố định
- Debug mode
- Không có health check
- Không xử lý shutdown

</details>

### Exercise 1.2: Chạy basic version

```bash
pip install -r requirements.txt
python app.py
```

Test:

```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Quan sát:** Nó chạy! Nhưng có production-ready không?

### Exercise 1.3: So sánh với advanced version

```bash
cd ../production
cp .env.example .env
pip install -r requirements.txt
python app.py
```

**Nhiệm vụ:** So sánh 2 files `app.py`. Điền vào bảng:

| Feature      | Basic     | Advanced                 | Tại sao quan trọng?                                                                                                                  |
| ------------ | --------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| Config       | Hardcode  | Env vars                 | Bảo mật thông tin nhạy cảm, dễ dàng linh hoạt thay đổi cấu hình theo từng môi trường mà không cần sửa đổi code.                      |
| Health check | Không có  | Có (`/health`, `/ready`) | Cho phép hệ thống/Cloud platform tự động giám sát trạng thái, routing traffic chính xác và restart nếu app bị lỗi.                   |
| Logging      | `print()` | JSON                     | Định dạng có cấu trúc giúp dễ dàng parse/truy vấn qua các log aggregator (Kibana, Loki, Datadog), tránh log nhầm thông tin nhạy cảm. |
| Shutdown     | Đột ngột  | Graceful                 | Đảm bảo xử lý nốt các (in-flight) requests đang chạy và release các connection an toàn trước khi container bị tắt.                   |

### Checkpoint 1

- [x] Hiểu tại sao hardcode secrets là nguy hiểm
- [x] Biết cách dùng environment variables
- [x] Hiểu vai trò của health check endpoint
- [x] Biết graceful shutdown là gì

---

## Part 2: Docker Containerization (45 phút)

### Concepts

**Vấn đề:** "Works on my machine" part 2 — Python version khác, dependencies conflict.

**Giải pháp:** Docker — đóng gói app + dependencies vào container.

**Benefits:**

- Consistent environment
- Dễ deploy
- Isolation
- Reproducible builds

### Exercise 2.1: Dockerfile cơ bản

```bash
cd ../../02-docker/develop
```

**Nhiệm vụ:** Đọc `Dockerfile` và trả lời:

1. Base image là gì?
   Base image: python:3.11
   Đây là image chính thức từ Docker Hub, đã cài sẵn Python 3.11 và các công cụ cần thiết.
   Nó khá “nặng” (~1GB) vì là full distribution (không phải bản slim).
2. Working directory là gì?
   Working directory: /app
   Đây là thư mục làm việc mặc định bên trong container. Khi container khởi động, shell sẽ mở tại thư mục này.
   Ý nghĩa:
   Mọi lệnh sau đó (COPY, RUN, CMD…) sẽ chạy trong thư mục /app
   Nếu thư mục chưa tồn tại, Docker sẽ tự tạo
3. Tại sao COPY requirements.txt trước?
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   Lý do:
   Docker cache layers: Mỗi lệnh trong Dockerfile tạo ra một layer.
   Khi bạn thay đổi code (app.py), layer COPY app.py sẽ thay đổi → Docker phải build lại từ đầu.
   Khi chỉ thay đổi dependencies, layer COPY requirements.txt không đổi → Docker dùng cached layer → build nhanh hơn.
4. CMD vs ENTRYPOINT khác nhau thế nào?
   CMD: Lệnh mặc định khi container start.Là lệnh mặc định.Có thể bị override khi chạy container.
   ENTRYPOINT: Lệnh chính (executable). Là lệnh chính, không thể bị override khi chạy container.
   Ví dụ:
   CMD ["python", "app.py"] → Chạy python app.py
   ENTRYPOINT ["python", "app.py"] → Chạy python app.py
   Nếu có CMD: CMD sẽ override ENTRYPOINT
   Nếu có ENTRYPOINT: CMD sẽ là arguments cho ENTRYPOINT

### Exercise 2.2: Build và run

```bash
# Build image
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run container
docker run -p 8000:8000 my-agent:develop

# Test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'

C:\Users\DuongDong>curl "http://localhost:8000/ask?question=What%20is%20Docker?" -X POST
{"answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"}
```

**Quan sát:** Image size là bao nhiêu?

```bash
docker images my-agent:develop
```

| IMAGE            | ID           | DISK USAGE | CONTENT SIZE | EXTRA |
| :--------------- | :----------- | :--------- | :----------- | :---- |
| my-agent:develop | 55abb312e91d | 1.66GB     | 424MB        | U     |

### Exercise 2.3: Multi-stage build

```bash
cd ../production
```

**Nhiệm vụ:** Đọc `Dockerfile` và tìm:

- Stage 1 làm gì?

  Stage 1: Builder
  Cài đặt tất cả dependencies
  Image này KHÔNG được dùng để deploy
  Cụ thể trong file:
  FROM python:3.11-slim AS builder
  Dùng image nhẹ (slim) nhưng vẫn đủ để build
  apt-get install -y gcc libpq-dev
  Cài:
  gcc → compile C extensions
  libpq-dev → cho PostgreSQL
  pip install --user -r requirements.txt
  Điểm quan trọng:
  Cài vào: /root/.local
  → dễ copy sang stage 2
  Kết luận Stage 1:
  --> "Build everything needed, but không dùng để chạy"

- Stage 2 làm gì?

  Stage 2: Runtime
  Stage 2 = runtime environment (production)
  Chỉ copy những gì cần để CHẠY, không cần để BUILD
  Cụ thể:
  FROM python:3.11-slim AS runtime
  Một image mới, sạch hoàn toàn (không có gcc, build tools)
  Những gì nó làm:
  1. Tạo user an toàn
     useradd appuser
     Không chạy bằng root → security best practice
  2. Copy dependencies từ builder
     COPY --from=builder /root/.local /home/appuser/.local
     Chỉ lấy:
     package đã build xong
     bỏ hết tool build
  3. Copy source code
     COPY main.py .
     COPY utils/mock_llm.py ...
  4. Set environment
     ENV PATH=/home/appuser/.local/bin:$PATH
     ENV PYTHONPATH=/app
     Để Python tìm được package
  5. Run app
     CMD ["uvicorn", "main:app", ...]
     Kết luận Stage 2:
     --> "Chỉ chứa những gì cần để chạy app"

- Tại sao image nhỏ hơn?
  Stage 1:
  có gcc, libpq-dev, pip build…
  nhưng bị bỏ đi hoàn toàn
  Stage 2 chỉ có:
  Python runtime
  packages đã build
  source code
  --> NHẸ + SẠCH
  --> không mang theo build tools, cache, file rác

Build và so sánh:

```bash
docker build -t my-agent:advanced .
docker images | grep my-agent
```

| IMAGE             | ID           | DISK USAGE | CONTENT SIZE | EXTRA |
| :---------------- | :----------- | :--------- | :----------- | :---- |
| my-agent:advanced | 7e1f9e14e8d2 | 236MB      | 56.6MB       |       |
| my-agent:develop  | 55abb312e91d | 1.66GB     | 424MB        | U     |

### Exercise 2.4: Docker Compose stack

**Nhiệm vụ:** Đọc `docker-compose.yml` và vẽ architecture diagram.

```mermaid
graph TD
    Client([Client]) -->|HTTP 80 / HTTPS 443| Nginx[Nginx Reverse Proxy\n& Load Balancer]

    subgraph Docker Internal Network
        Nginx -->|Traffic Routing| Agent[FastAPI Agent 1..N]
        Agent -->|Session / Rate Limit| Redis[(Redis)]
        Agent -->|Vector RAG| Qdrant[(Qdrant)]
    end
```

```bash
docker compose up
```

```bash
(venv) PS D:\VinAI\Ex12\day12_ha-tang-cloud_va_deployment\02-docker\production> docker compose down; docker compose up -d
[+] Running 5/5
✔ Container production-nginx-1 Removed 0.1s
✔ Container production-agent-1 Removed 0.1s
✔ Container production-qdrant-1 Removed 0.4s
✔ Container production-redis-1 Removed 0.5s
✔ Network production_internal Removed 0.3s
[+] Running 5/5
✔ Network production_internal Created 0.0s
✔ Container production-redis-1 Healthy 11.5s
✔ Container production-qdrant-1 Healthy 16.5s
✔ Container production-agent-1 Started 16.5s
✔ Container production-nginx-1 Started 16.6s
```

Services nào được start? Chúng communicate thế nào?

- **Services chạy:**
  agent
  redis
  qdrant
  nginx
- **Communication:**
  Qua Docker network internal
  Gọi nhau bằng service name (DNS nội bộ)
  Entry point:
  nginx (localhost:80)

Test:

```bash
# Health check
curl http://localhost/health

C:\Users\Duong Dong>curl http://localhost/health
{"status":"ok","uptime_seconds":146.7,"version":"2.0.0","timestamp":"2026-04-17T08:40:36.837513"}

# Agent endpoint
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'

C:\Users\Duong Dong>curl -X POST http://localhost/ask -H "Content-Type: application/json" -d "{\"question\":\"Explain microservices\"}"
{"answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}
```

### Checkpoint 2

- [x] Hiểu cấu trúc Dockerfile
- [x] Biết lợi ích của multi-stage builds
- [x] Hiểu Docker Compose orchestration
- [x] Biết cách debug container (`docker logs`, `docker exec`)

---

## Part 3: Cloud Deployment (45 phút)

### Concepts

**Vấn đề:** Laptop không thể chạy 24/7, không có public IP.

**Giải pháp:** Cloud platforms — Railway, Render, GCP Cloud Run.

**So sánh:**

| Platform  | Độ khó | Free tier   | Best for      |
| --------- | ------ | ----------- | ------------- |
| Railway   | ⭐     | $5 credit   | Prototypes    |
| Render    | ⭐⭐   | 750h/month  | Side projects |
| Cloud Run | ⭐⭐⭐ | 2M requests | Production    |

### Exercise 3.1: Deploy Railway (15 phút)

```bash
cd ../../03-cloud-deployment/railway
```

**Steps:**

1. Install Railway CLI:

```bash
npm i -g @railway/cli
```

2. Login:

```bash
railway login
```

3. Initialize project:

```bash
railway init
```

4. Set environment variables:

```bash
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
```

5. Deploy:

```bash
railway up
```

6. Get public URL:

```bash
railway domain
```

**Nhiệm vụ:** Test public URL với curl hoặc Postman.
https://agent-production-64db.up.railway.app

Test:

```bash
# Health check
curl http://student-agent-domain/health

C:\Users\DuongDong>curl https://agent-production-64db.up.railway.app/health
{"status":"ok","uptime_seconds":173.8,"platform":"Railway","timestamp":"2026-04-17T10:19:41.081192+00:00"}

# Agent endpoint
curl http://studen-agent-domain/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'

C:\Users\DuongDong>curl -X POST https://agent-production-64db.up.railway.app/ask -H "Content-Type: application/json" -d "{\"question\":\"Explain microservices\"}"
{"question":"Explain microservices","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","platform":"Railway"}
```

### Exercise 3.2: Deploy Render (15 phút)

```bash
cd ../render
```

**Steps:**

1. Push code lên GitHub (nếu chưa có)
2. Vào [render.com](https://render.com) → Sign up
3. New → Blueprint
4. Connect GitHub repo
5. Render tự động đọc `render.yaml`
6. Set environment variables trong dashboard
7. Deploy!

**Nhiệm vụ:** So sánh `render.yaml` với `railway.toml`. Khác nhau gì?

**Trả lời:**

1. **Phạm vi (Scope) & Định dạng:**
   - `render.yaml` (Blueprint IaC): Dùng cú pháp YAML, có khả năng định nghĩa **toàn bộ hạ tầng** bao gồm nhiều services hoạt động cùng nhau (ví dụ: Web Service `ai-agent` chạy cùng với một Data Service như Redis `agent-cache`). File này cũng chứa thông tin chi tiết về hạ tầng như `region` (khu vực deploy) và `plan` (gói cước).
   - `railway.toml`: Dùng cú pháp TOML, thường chỉ định cấu hình riêng biệt cho việc **build và deploy của một service đơn lẻ** mà mã nguồn hiện tại đang đứng.

2. **Cách thức Build & Định hình Môi trường:**
   - Trong `render.yaml` cần khai báo rõ ràng `buildCommand` cụ thể (ví dụ: `pip install -r requirements.txt`) và `runtime: python` để hệ thống biết cách build.
   - `railway.toml` trong ví dụ sử dụng `builder = "NIXPACKS"`, một công cụ của Railway có khả năng tự động phân tích code (auto-detect Python & requirements) và build môi trường một cách ma thuật mà không cần lệnh build chi tiết.

3. **Quản lý Biến môi trường (Environment Variables):**
   - Định dạng của `render.yaml` cho phép định nghĩa trực tiếp cấu trúc biến môi trường bên trong mã nguồn hạ tầng. Nó cho phép phân loại cụ thể các biến thông thường (`ENVIRONMENT=production`), biến không muốn đồng bộ lên Git (`sync: false`), và tự động sinh key ẩn danh (`generateValue: true`).
   - `railway.toml` thì không lưu trực tiếp giá trị của Environment Variables. Việc quản trị biến môi trường trong Railway hoàn toàn dựa vào Dashboard UI, hoặc sử dụng câu lệnh từ CLI (`railway variables set`).

### Exercise 3.3: (Optional) GCP Cloud Run (15 phút)

```bash
cd ../production-cloud-run
```

**Yêu cầu:** GCP account (có free tier).

**Nhiệm vụ:** Đọc `cloudbuild.yaml` và `service.yaml`. Hiểu CI/CD pipeline.

### Checkpoint 3

- [x] Deploy thành công lên ít nhất 1 platform
- [x] Có public URL hoạt động
- [x] Hiểu cách set environment variables trên cloud
- [x] Biết cách xem logs

---

## Part 4: API Security (40 phút)

### Concepts

**Vấn đề:** Public URL = ai cũng gọi được = hết tiền OpenAI.

**Giải pháp:**

1. **Authentication** — Chỉ user hợp lệ mới gọi được
2. **Rate Limiting** — Giới hạn số request/phút
3. **Cost Guard** — Dừng khi vượt budget

### Exercise 4.1: API Key authentication

```bash
cd ../../04-api-gateway/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm:

- API key được check ở đâu?
  **Trả lời:** Khóa được kiểm tra tại hàm dependency tên là `verify_api_key`, hàm này lấy giá trị từ header `X-API-Key`. Đồng thời, route `/ask` có khai báo `_key: str = Depends(verify_api_key)` để tự động chạy hàm kiểm tra này trước khi xử lý request.
- Điều gì xảy ra nếu sai key?
  **Trả lời:** Dựa trên định nghĩa lỗi:
  - Nếu thiếu key (không gửi header), server ném lỗi `HTTPException` với status code `401 Unauthorized`.
  - Nếu gửi sai key (không khớp với biến môi trường), server ném lỗi status code `403 Forbidden`.
- Làm sao rotate key?
  **Trả lời:** Hệ thống tham chiếu giá trị từ biến môi trường thông qua lệnh `os.getenv("AGENT_API_KEY")`. Do đó, để đổi khóa (rotate key), bạn chỉ cần thay đổi giá trị của biến môi trường `AGENT_API_KEY` ở host/server/dashboard và restart lại hệ thống, không cần sửa đổi thông tin trong code.

Test:

```bash
python app.py

#  Không có key
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'

C:\Users\DuongDong>curl http://localhost:8000/ask -X POST -H "Content-Type: application/json" -d "{\"question\": \"Hello\"}"
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

#  Có key
curl http://localhost:8000/ask -X POST \
  -H "X-API-Key: secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'

C:\Users\DuongDong>curl http://localhost:8000/ask -X POST -H "X-API-Key: demo-key-change-in-production" -H "Content-Type: application/json" -d "{\"question\": \"Hello\"}"
{"question":"Hello","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."}
```

### Exercise 4.2: JWT authentication (Advanced)

```bash
cd ../production
```

**Nhiệm vụ:**

1. Đọc `auth.py` — hiểu JWT flow
2. Lấy token:

```bash
python app.py

curl http://localhost:8000/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret"}'
```

```bash
DuongDong@DESKTOP-KA0RASH MINGW64 /d/VinAI/Ex12/day12_ha-tang-cloud_va_deployment (main)
$ curl http://localhost:8000/auth/token -X POST -H "Content-Type: application/json" -d "{\"username\": \"student\", \"password\":  \"demo123\"}"
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0Mjc0MDQsImV4cCI6MTc33NjQzMTAwNH0.QAVrnQgHn64elel5nLY7RBv6MQEUJ5R5i1NTLHXKMeI","token_type":"bearer","expires_in_minutes":60,"hint":"Include in header : Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."}
```

3. Dùng token để gọi API:

```bash
TOKEN="<token_từ_bước_2>"
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

```bash
# 1. Lấy token và lưu vào biến (Lưu ý: dùng dấu ngoặc đơn cho JSON)
export TOKEN=$(curl -s http://localhost:8000/auth/token -X POST \
  -H "Content-Type: application/json" \
  -d '{"username": "student", "password": "demo123"}' | sed -E 's/.*"access_token":"([^"]+)".*/\1/')

# 2. Kiểm tra xem biến đã có token chưa
echo $TOKEN

# 3. Chạy lệnh ask
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

```bash
DuongDong@DESKTOP-KA0RASH MINGW64 /d/VinAI/Ex12/day12_ha-tang-cloud_va_deployment (main)
$ curl http://localhost:8000/ask -X POST \
>   -H "Authorization: Bearer $TOKEN" \
>   -H "Content-Type: application/json" \
>   -d '{"question": "Explain JWT"}'
{"question":"Explain JWT","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":9,"budget_remaining_usd":1.9e-05}}
```

```bash
INFO:     127.0.0.1:57839 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=3 cost=$0.0001/1.0
INFO:     127.0.0.1:57841 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=4 cost=$0.0001/1.0
INFO:     127.0.0.1:57843 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=5 cost=$0.0001/1.0
INFO:     127.0.0.1:57845 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=6 cost=$0.0001/1.0
INFO:     127.0.0.1:57847 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=7 cost=$0.0001/1.0
INFO:     127.0.0.1:57861 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=8 cost=$0.0001/1.0
INFO:     127.0.0.1:57863 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=9 cost=$0.0002/1.0
INFO:     127.0.0.1:57868 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=10 cost=$0.0002/1.0
INFO:     127.0.0.1:57870 - "POST /ask HTTP/1.1" 200 OK
INFO:cost_guard:Usage: user=student req=11 cost=$0.0002/1.0
INFO:     127.0.0.1:57872 - "POST /ask HTTP/1.1" 200 OK
INFO:     127.0.0.1:57882 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57884 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57886 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57888 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57895 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57897 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57899 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57901 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57912 - "POST /ask HTTP/1.1" 429 Too Many Requests
INFO:     127.0.0.1:57914 - "POST /ask HTTP/1.1" 429 Too Many Requests
```

### Exercise 4.3: Rate limiting

**Nhiệm vụ:** Đọc `rate_limiter.py` và trả lời:

- Algorithm nào được dùng? (Token bucket? Sliding window?)
  **Trả lời:** Thuật toán **Sliding Window Log** (sử dụng `deque` để lưu timestamps và loại bỏ các bản ghi cũ ngoài window 60s).
- Limit là bao nhiêu requests/minute?
  **Trả lời:** Hạn mức khác nhau tùy theo role: 10 req/phút cho **User** và 100 req/phút cho **Admin**.
- Làm sao bypass limit cho admin?
  **Trả lời:** Thay vì dùng instance `rate_limiter_user`, hệ thống kiểm tra role trong JWT và chuyển sang dùng instance `rate_limiter_admin` với cấu hình hạn mức cao hơn (100 req/phút).

Test:

```bash
# Gọi liên tục 20 lần
for i in {1..20}; do
  curl http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done
```

Quan sát response khi hit limit.

```bash
DuongDong@DESKTOP-KA0RASH MINGW64 /d/VinAI/Ex12/day12_ha-tang-cloud_va_deployment (main)
$ for i in {1..20}; do
>   curl http://localhost:8000/ask -X POST \
>     -H "Authorization: Bearer $TOKEN" \
>     -H "Content-Type: application/json" \
>     -d '{"question": "Test '$i'"}'
>   echo ""
> done
{"question":"Test 1","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":9,"budget_remaining_usd":3.5e-05}}
{"question":"Test 2","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":8,"budget_remaining_usd":5.6e-05}}
{"question":"Test 3","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":7,"budget_remaining_usd":7.7e-05}}
{"question":"Test 4","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":6,"budget_remaining_usd":9.3e-05}}
{"question":"Test 5","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":5,"budget_remaining_usd":0.000112}}
{"question":"Test 6","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","usage":{"requests_remaining":4,"budget_remaining_usd":0.000128}}
{"question":"Test 7","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":3,"budget_remaining_usd":0.000146}}
{"question":"Test 8","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":2,"budget_remaining_usd":0.000165}}
{"question":"Test 9","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":1,"budget_remaining_usd":0.000186}}
{"question":"Test 10","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":0,"budget_remaining_usd":0.000207}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":57}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":56}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":55}}
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":54}}
```

### Exercise 4.4: Cost guard

**Nhiệm vụ:** Đọc `cost_guard.py` và implement logic:

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    """
    Return True nếu còn budget, False nếu vượt.

    Logic:
    - Mỗi user có budget $10/tháng
    - Track spending trong Redis
    - Reset đầu tháng
    """
    # TODO: Implement
    pass
```

**Phân tích `cost_guard.py`:**

- **Budget mỗi user:** $1/ngày (per-user daily budget) và $10/ngày cho toàn hệ thống (global budget).
- **Cách tính chi phí:** Dựa trên số tokens, gồm input ($0.15/1M tokens) và output ($0.60/1M tokens), tính theo giá GPT-4o-mini.
- **Cơ chế reset:** Dùng `time.strftime("%Y-%m-%d")` để kiểm tra ngày hiện tại. Nếu sang ngày mới, `UsageRecord` của user được tạo lại từ đầu → budget tự động reset mỗi ngày.
- **Cảnh báo:** Khi user dùng ≥ 80% budget, hệ thống ghi `WARNING` vào log.
- **Block:** Vượt per-user budget → `402 Payment Required`. Vượt global budget → `503 Service Unavailable`.

<details>
<summary> Solution</summary>

```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False

    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days
    return True
```

</details>

### Checkpoint 4

- [x] Implement API key authentication
- [x] Hiểu JWT flow
- [x] Implement rate limiting
- [x] Implement cost guard với Redis

---

## Part 5: Scaling & Reliability (40 phút)

### Concepts

**Vấn đề:** 1 instance không đủ khi có nhiều users.

**Giải pháp:**

1. **Stateless design** — Không lưu state trong memory
2. **Health checks** — Platform biết khi nào restart
3. **Graceful shutdown** — Hoàn thành requests trước khi tắt
4. **Load balancing** — Phân tán traffic

### Exercise 5.1: Health checks

```bash
cd ../../05-scaling-reliability/develop
```

**Nhiệm vụ:** Implement 2 endpoints:

```python
@app.get("/health")
def health():
    """Liveness probe — container còn sống không?"""
    # TODO: Return 200 nếu process OK
    pass

@app.get("/ready")
def ready():
    """Readiness probe — sẵn sàng nhận traffic không?"""
    # TODO: Check database connection, Redis, etc.
    # Return 200 nếu OK, 503 nếu chưa ready
    pass
```

**Trả lời:**

- **`/health` (Liveness probe):** Kiểm tra xem process có còn sống không. Trả về `200 OK` với uptime và version. Nếu endpoint này không response → platform restart container.
- **`/ready` (Readiness probe):** Kiểm tra xem agent có sẵn sàng nhận traffic không. Trả về `503` khi đang khởi động (`_is_ready = False`) hoặc đang shutdown. Load balancer dùng endpoint này để quyết định có route request vào instance hay không.
- **Sự khác biệt quan trọng:** `/health` = "còn sống không?", `/ready` = "sẵn sàng phục vụ chưa?". Một container có thể còn sống (health OK) nhưng chưa ready (model đang load).

```python
@app.get("/health")
def health():
    uptime = round(time.time() - START_TIME, 1)
    return {
        "status": "ok",
        "uptime_seconds": uptime,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(
            status_code=503,
            detail="Agent not ready. Check back in a few seconds.",
        )
    return {"ready": True, "in_flight_requests": _in_flight_requests}
```

<details>
<summary> Solution gốc</summary>

```python
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        # Check Redis
        r.ping()
        # Check database
        db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready"}
        )
```

</details>

### Exercise 5.2: Graceful shutdown

**Nhiệm vụ:** Implement signal handler:

```python
import signal
import sys

def shutdown_handler(signum, frame):
    """Handle SIGTERM from container orchestrator"""
    # TODO:
    # 1. Stop accepting new requests
    # 2. Finish current requests
    # 3. Close connections
    # 4. Exit
    pass

signal.signal(signal.SIGTERM, shutdown_handler)
```

**Trả lời:** Trong file `05-scaling-reliability/develop/app.py`, graceful shutdown được implement theo pattern hiện đại hơn bằng `lifespan` context manager của FastAPI thay vì signal handler thủ công:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    # --- Startup ---
    _is_ready = True
    yield
    # --- Shutdown (chạy khi nhận SIGTERM) ---
    _is_ready = False  # 1. Ngừng nhận request mới (ready probe trả 503)
    timeout = 30
    elapsed = 0
    while _in_flight_requests > 0 and elapsed < timeout:  # 2. Chờ request đang xử lý
        time.sleep(1)
        elapsed += 1
    # 3. Connections đóng tự động khi app thoát
    logger.info("Shutdown complete")

def handle_sigterm(signum, frame):
    """uvicorn tự bắt SIGTERM và gọi lifespan shutdown."""
    logger.info(f"Received signal {signum}")

signal.signal(signal.SIGTERM, handle_sigterm)
```

Test:

```bash
python app.py &
PID=$!

py app.py ; PID=$!

# Gửi request
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Ngay lập tức kill
kill -TERM $PID

# Quan sát: Request có hoàn thành không?
```

### Exercise 5.3: Stateless design

```bash
cd ../production
```

**Nhiệm vụ:** Refactor code để stateless.

**Anti-pattern:**

```python
#  State trong memory
conversation_history = {}

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])
    # ...
```

**Correct:**

```python
#  State trong Redis
@app.post("/ask")
def ask(user_id: str, question: str):
    history = r.lrange(f"history:{user_id}", 0, -1)
    # ...
```

Tại sao? Vì khi scale ra nhiều instances, mỗi instance có memory riêng.

**Trả lời:** Khi có 3 instances (Agent1, Agent2, Agent3) chạy sau Nginx load balancer:

- Request 1 (hỏi câu A) → Agent1, lưu vào `conversation_history` của Agent1.
- Request 2 (hỏi tiếp câu B) → Nginx route sang Agent2 → Agent2 **không có** lịch sử → trả lời sai.
- Dùng Redis: Cả 3 agents đều đọc/ghi vào cùng một Redis → lịch sử được chia sẻ → đúng.

### Exercise 5.4: Load balancing

**Nhiệm vụ:** Chạy stack với Nginx load balancer:

```bash
docker compose up --scale agent=3
```

Quan sát:

- 3 agent instances được start
- Nginx phân tán requests
- Nếu 1 instance die, traffic chuyển sang instances khác

**Trả lời:** Nginx sử dụng thuật toán **Round-Robin** mặc định để phân phối request tuần tự qua các instances. Khi 1 instance die, Nginx phát hiện qua health check (`/health` hoặc kết nối TCP thất bại) và tự động loại instance đó khỏi pool, chuyển traffic sang các instances còn lại.

Test:

```bash
# Gọi 10 requests
for i in {1..10}; do
  curl http://localhost/ask -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
done

# Check logs — requests được phân tán
docker compose logs agent
```

### Exercise 5.5: Test stateless

```bash
python test_stateless.py
```

Script này:

1. Gọi API để tạo conversation
2. Kill random instance
3. Gọi tiếp — conversation vẫn còn không?

**Trả lời:** Nếu app được thiết kế stateless (lưu state trong Redis), conversation **vẫn còn** sau khi instance bị kill vì dữ liệu được lưu ở Redis dùng chung — không phụ thuộc vào instance cụ thể nào.

### Checkpoint 5

- [x] Implement health và readiness checks
- [x] Implement graceful shutdown
- [x] Refactor code thành stateless
- [x] Hiểu load balancing với Nginx
- [x] Test stateless design

---

## Part 6: Final Project (60 phút)

### Objective

Build một production-ready AI agent từ đầu, kết hợp TẤT CẢ concepts đã học.

### Requirements

**Functional:**

- [x] Agent trả lời câu hỏi qua REST API
- [x] Support conversation history
- [x] Streaming responses (optional)

**Non-functional:**

- [x] Dockerized với multi-stage build
- [x] Config từ environment variables
- [x] API key authentication
- [x] Rate limiting (10 req/min per user)
- [x] Cost guard ($10/month per user)
- [x] Health check endpoint
- [x] Readiness check endpoint
- [x] Graceful shutdown
- [x] Stateless design (state trong Redis)
- [x] Structured JSON logging
- [x] Deploy lên Railway hoặc Render
- [x] Public URL hoạt động

### 🏗 Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Nginx (LB)     │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐
   │Agent1│  │Agent2│  │Agent3│
   └───┬──┘  └───┬──┘  └───┬──┘
       │         │         │
       └─────────┴─────────┘
                 │
                 ▼
           ┌──────────┐
           │  Redis   │
           └──────────┘
```

### Step-by-step

#### Step 1: Project setup (5 phút)

```bash
mkdir my-production-agent
cd my-production-agent

# Tạo structure
mkdir -p app
touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/auth.py
touch app/rate_limiter.py
touch app/cost_guard.py
touch Dockerfile
touch docker-compose.yml
touch requirements.txt
touch .env.example
touch .dockerignore
```

#### Step 2: Config management (10 phút)

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # TODO: Define all config
    # - PORT
    # - REDIS_URL
    # - AGENT_API_KEY
    # - LOG_LEVEL
    # - RATE_LIMIT_PER_MINUTE
    # - MONTHLY_BUDGET_USD
    pass

settings = Settings()
```

#### Step 3: Main application (15 phút)

**File:** `app/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

app = FastAPI()

@app.get("/health")
def health():
    # TODO
    pass

@app.get("/ready")
def ready():
    # TODO: Check Redis connection
    pass

@app.post("/ask")
def ask(
    question: str,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    # TODO:
    # 1. Get conversation history from Redis
    # 2. Call LLM
    # 3. Save to Redis
    # 4. Return response
    pass
```

#### Step 4: Authentication (5 phút)

**File:** `app/auth.py`

```python
from fastapi import Header, HTTPException

def verify_api_key(x_api_key: str = Header(...)):
    # TODO: Verify against settings.AGENT_API_KEY
    # Return user_id if valid
    # Raise HTTPException(401) if invalid
    pass
```

#### Step 5: Rate limiting (10 phút)

**File:** `app/rate_limiter.py`

```python
import redis
from fastapi import HTTPException

r = redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str):
    # TODO: Implement sliding window
    # Raise HTTPException(429) if exceeded
    pass
```

#### Step 6: Cost guard (10 phút)

**File:** `app/cost_guard.py`

```python
def check_budget(user_id: str):
    # TODO: Check monthly spending
    # Raise HTTPException(402) if exceeded
    pass
```

#### Step 7: Dockerfile (5 phút)

```dockerfile
# TODO: Multi-stage build
# Stage 1: Builder
# Stage 2: Runtime
```

#### Step 8: Docker Compose (5 phút)

```yaml
# TODO: Define services
# - agent (scale to 3)
# - redis
# - nginx (load balancer)
```

#### Step 9: Test locally (5 phút)

```bash
docker compose up --scale agent=3

# Test all endpoints
curl http://localhost/health
curl http://localhost/ready
curl -H "X-API-Key: secret" http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "user1"}'
```

#### Step 10: Deploy (10 phút)

```bash
# Railway
railway init
railway variables set REDIS_URL=...
railway variables set AGENT_API_KEY=...
railway up

# Hoặc Render
# Push lên GitHub → Connect Render → Deploy
```

### Validation

Chạy script kiểm tra:

```bash
cd 06-lab-complete
python check_production_ready.py
```

Script sẽ kiểm tra:

- Dockerfile exists và valid
- Multi-stage build
- .dockerignore exists
- Health endpoint returns 200
- Readiness endpoint returns 200
- Auth required (401 without key)
- Rate limiting works (429 after limit)
- Cost guard works (402 when exceeded)
- Graceful shutdown (SIGTERM handled)
- Stateless (state trong Redis, không trong memory)
- Structured logging (JSON format)

### Grading Rubric

| Criteria          | Points | Description                       |
| ----------------- | ------ | --------------------------------- |
| **Functionality** | 20     | Agent hoạt động đúng              |
| **Docker**        | 15     | Multi-stage, optimized            |
| **Security**      | 20     | Auth + rate limit + cost guard    |
| **Reliability**   | 20     | Health checks + graceful shutdown |
| **Scalability**   | 15     | Stateless + load balanced         |
| **Deployment**    | 10     | Public URL hoạt động              |
| **Total**         | 100    |                                   |

---

## Hoàn Thành!

Bạn đã:

- Hiểu sự khác biệt dev vs production
- Containerize app với Docker
- Deploy lên cloud platform
- Bảo mật API
- Thiết kế hệ thống scalable và reliable

### Next Steps

1. **Monitoring:** Thêm Prometheus + Grafana
2. **CI/CD:** GitHub Actions auto-deploy
3. **Advanced scaling:** Kubernetes
4. **Observability:** Distributed tracing với OpenTelemetry
5. **Cost optimization:** Spot instances, auto-scaling

### Resources

- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)

---

## Q&A

**Q: Tôi không có credit card, có thể deploy không?**  
A: Có! Railway cho $5 credit, Render có 750h free tier.

**Q: Mock LLM khác gì với OpenAI thật?**  
A: Mock trả về canned responses, không gọi API. Để dùng OpenAI thật, set `OPENAI_API_KEY` trong env.

**Q: Làm sao debug khi container fail?**  
A: `docker logs <container_id>` hoặc `docker exec -it <container_id> /bin/sh`

**Q: Redis data mất khi restart?**  
A: Dùng volume: `volumes: - redis-data:/data` trong docker-compose.

**Q: Làm sao scale trên Railway/Render?**  
A: Railway: `railway scale <replicas>`. Render: Dashboard → Settings → Instances.

---

**Happy Deploying! **
