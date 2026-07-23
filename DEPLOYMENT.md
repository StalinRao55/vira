# VIRA Deployment Guide

## Local development

```bash
# Clone the repository
git clone <repository-url>
cd vira

# Copy environment files
cp backend/.env.example backend/.env    # fill in your API keys
cp frontend/.env.example frontend/.env

# Start services with Docker Compose
docker compose up --build

# Or run without Docker:
# Backend: cd backend && pip install -e . && uvicorn app.main:app --reload
# Frontend: cd frontend && npm install && npm run dev
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000
- Postgres/Redis are exposed on default ports for local inspection via `psql`/`redis-cli`.

## Environment Configuration

Three environment files for different deployment stages:

### Development (`.env`)
- Safe defaults, suitable for local development
- Mock/test API keys
- Local database connections

### Staging (`.env.staging`)
- Real but non-production credentials
- Staging database and external services
- Used for integration testing before production

### Production (`.env.production`)
- Real production credentials
- Production database and services
- Strict security configurations
- **NEVER committed to version control**

### Required Environment Variables

```
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# Redis
REDIS_URL=redis://user:password@host:6379

# JWT (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=<32-byte-hex-string>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Google OAuth
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/callback/google

# AI Providers
GEMINI_API_KEY=4daa3118bd1a40dbbc05bba3a60c4c23.fjqnciYzNPkJVd0Tn7NajnAQ

# App Configuration
ENVIRONMENT=production|staging|development
FRONTEND_URL=https://your-frontend-domain.com
```

## Database Migrations

Migrations are managed with Alembic and should be run before deploying:

```bash
# Generate a migration from SQLAlchemy models
docker compose exec backend alembic revision --autogenerate -m "migration description"

# Apply migrations to the database
docker compose exec backend alembic upgrade head

# Production deployment
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Production Deployment with Docker Compose

For production deployments using Docker Compose with Nginx:

```bash
# 1. Prepare environment file (never commit this)
cp backend/.env.production backend/.env
cp frontend/.env.production frontend/.env
# Edit .env files with real production credentials

# 2. Generate TLS certificates (using Let's Encrypt)
certbot certonly --standalone -d your-domain.com
# Copy certificates to nginx/certs/:
# - fullchain.pem (public certificate chain)
# - privkey.pem (private key)

# 3. Update Nginx configuration with your domain
# Edit nginx/nginx.conf and update server_name directives

# 4. Build and run with production compose file
docker compose -f docker-compose.prod.yml up -d --build

# 5. Run database migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. Verify services are healthy
docker compose -f docker-compose.prod.yml ps
```

## Deployment to Render (Recommended)

Render provides a simple platform for deploying both backend and frontend with automatic SSL/TLS.

### Prerequisites
- Render account (https://render.com)
- GitHub repository connected to Render
- Secrets configured in Render environment

### Steps

1. **Fork/Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Create Render Services**

   **Backend (Python/FastAPI):**
   - Runtime: Python 3.12
   - Build Command: `cd backend && pip install -e .`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables: All from `.env.production`
   - Plan: Standard (minimum recommended for production)

   **Frontend (Node.js/Next.js):**
   - Runtime: Node 20
   - Build Command: `cd frontend && npm install && npm run build`
   - Start Command: `cd frontend && npm start`
   - Environment Variables:
     - `NEXT_PUBLIC_API_URL`: (URL of backend service, e.g., `https://vira-backend.onrender.com/api/v1`)
   - Plan: Starter or Standard

3. **Connect Databases**

   Create the following databases in Render:
   - PostgreSQL 16 (for app data)
   - Redis (for caching and job queues)

   Render will automatically provide connection URLs as environment variables:
   - `DATABASE_URL` for PostgreSQL
   - `REDIS_URL` for Redis

4. **Configure Secrets**

   In Render dashboard, add environment variables (use Render's secret manager):
   ```
   JWT_SECRET_KEY = (generate with: openssl rand -hex 32)
   GEMINI_API_KEY = <your-gemini-api-key>
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
   GOOGLE_REDIRECT_URI = https://vira-backend.onrender.com/auth/callback/google
   FRONTEND_URL = https://your-frontend.onrender.com
   ENVIRONMENT = production
   ```

5. **Deploy**

   Render will automatically deploy when you push to the configured branch (main).

6. **Run Migrations**

   After first deployment, manually run migrations:
   ```bash
   # Via Render shell or logs
   alembic upgrade head
   ```

## Deployment to Vercel (Frontend Only)

For deploying the Next.js frontend to Vercel:

### Prerequisites
- Vercel account (https://vercel.com)
- GitHub repository connected to Vercel

### Steps

1. **Connect Repository**
   - Import the repository in Vercel dashboard
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

2. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL = https://vira-backend.onrender.com/api/v1
   ```

3. **Deploy**
   - Vercel automatically deploys on push to main branch
   - Preview deployments for pull requests

**Note**: Backend must run on a separate platform (Render, AWS, GCP, etc.) since Vercel doesn't support long-running Python services.

## Hybrid Deployment (Render Backend + Vercel Frontend)

The recommended setup for scalability:

1. **Deploy Backend to Render**
   - FastAPI backend with PostgreSQL and Redis
   - See "Deployment to Render" section above

2. **Deploy Frontend to Vercel**
   - Next.js frontend optimized for edge
   - See "Deployment to Vercel" section above

3. **Configure Environment Variables**

   Backend (Render):
   ```
   FRONTEND_URL = https://your-frontend.vercel.app
   ```

   Frontend (Vercel):
   ```
   NEXT_PUBLIC_API_URL = https://vira-backend.onrender.com/api/v1
   ```

4. **CORS Configuration**
   - Backend CORS origin is automatically set from `FRONTEND_URL`
   - Next.js frontend can call backend API directly

## Scaling Recommendations

### Before Multiple Backend Replicas

The current implementation has two critical limitations for scaling:

1. **Vector Store (FAISS)**
   - Currently in-process and non-persistent
   - **Required Fix**: Swap `FaissVectorStore` for a `QdrantVectorStore` implementing `IVectorStore`
   - This allows multiple backend instances to share one external vector index
   ```python
   # app/infrastructure/vector_store/qdrant_store.py
   class QdrantVectorStore(IVectorStore):
       def __init__(self, url: str):
           self.client = QdrantClient(url=url)
       # Implement IVectorStore methods...
   ```

2. **File Storage (LocalFileStorage)**
   - Currently disk-based and won't work across replicas
   - **Required Fix**: Swap `LocalFileStorage` for an S3-compatible implementation
   - Options: AWS S3, Supabase Storage, Cloudflare R2, MinIO
   ```python
   # app/infrastructure/storage/s3_storage.py
   class S3FileStorage(IFileStorage):
       def __init__(self, bucket: str, client: S3Client):
           self.bucket = bucket
           self.client = client
       # Implement IFileStorage methods...
   ```

### Application-Level Scaling

Once vector store and file storage are externalized:

1. **Backend**: Horizontal scaling behind a load balancer
   - Render automatically handles this with replicas
   - Database and external services are shared

2. **Database**: PostgreSQL connection pooling
   - Configure PgBouncer or use managed connection pooling
   - Example for Render-managed PostgreSQL: built-in

3. **Background Jobs**: Move document ingestion to async queue
   - Use Celery + Redis for background tasks
   - Currently synchronous in upload request
   - Prevents large uploads from timing out

4. **Caching**: Redis for session data and query results
   - Already provisioned in production compose
   - Implement caching at application level for performance

## Monitoring & Logging

### Health Checks

Backend provides health check endpoint:
```
GET /health → {"status": "ok"}
```

Render and other platforms use this for:
- Liveness checks (is the service running?)
- Readiness checks (can it handle traffic?)

### Metrics

Metrics endpoint available at:
```
GET /metrics
```

In production, integrate Prometheus:
```python
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose()
```

### Structured Logging

Enabled in production mode via `configure_logging()`:
- JSON format for easy parsing
- Request tracing via X-Request-ID header
- Error tracking and aggregation

## Troubleshooting

### Database Connection Issues
```bash
# Test connection locally
psql postgresql://user:password@host:5432/database

# Check backend logs
docker compose logs backend
```

### OAuth Errors
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Ensure `GOOGLE_REDIRECT_URI` matches Google Cloud Console configuration
- Check CORS configuration in backend

### Performance Issues
1. Check if document ingestion is async (should be moved to Celery)
2. Verify database indexes are created (run migrations)
3. Monitor Redis and database performance
4. Consider caching common queries

## Rollback Procedure

To rollback to a previous deployment:

```bash
# With Render: Use "Manual Deploy" and select previous build
# With Docker: Stop current services and restart previous image tags
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

Database migrations are forward-only. If you need to rollback:
```bash
docker compose -f docker-compose.prod.yml exec backend alembic downgrade -1
```
- **Database**: add read replicas once conversation/message read volume grows; the repository pattern means only DI wiring changes, not use cases.
- **Rate limiting**: not yet implemented — Redis is provisioned for a sliding-window limiter keyed by user_id, added as FastAPI middleware.
- **Horizontal scaling**: increase `--workers` in the backend Dockerfile's `CMD`, or run multiple replicas behind Nginx/a cloud load balancer — safe once the vector store and file storage points above are addressed.

## Monitoring in production

- Wire `prometheus-fastapi-instrumentator` at `/metrics` (currently a placeholder) for real request-rate/latency/error-rate metrics.
- Ship JSON logs (already configured for `ENVIRONMENT=production`) to your aggregator (CloudWatch, Datadog, Loki) via the platform's standard stdout log collection.
- `X-Request-ID` response header lets you correlate a user-reported issue to exact log lines.
