# InfraVersionHub

Infrastructure Version Management Platform - A full-stack application to centrally manage and track versions of infrastructure components across environments.

## Features

- **Component Registry**: Track infrastructure tools (ArgoCD, Fluentd, Kubernetes, etc.) with version history
- **Environment Mapping**: Map component versions to environments, clusters, and regions
- **Environment Matrix**: Visual grid view of components across all environments
- **Pluggable Storage**: Support for MongoDB and Filesystem storage backends
- **REST API**: OpenAPI-documented endpoints with JWT authentication
- **JSON Logging**: Structured logging for observability

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│    MongoDB      │
│   (React/Vite)  │     │   (FastAPI)     │     │                 │
│   Port: 3000    │     │   Port: 8000    │     │   Port: 27017   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| Backend | FastAPI, Python 3.11, Pydantic |
| Database | MongoDB 7 |
| Auth | JWT with RBAC |

## Project Structure

```
tools-version-management/
├── backend/                    # FastAPI backend service
│   ├── src/
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── logging_config.py  # JSON logging setup
│   │   ├── api/routes/        # API endpoints
│   │   ├── schemas/           # Pydantic models
│   │   ├── storage/           # Storage connectors
│   │   └── auth/              # JWT authentication
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React frontend service
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/             # Page components
│   │   ├── components/        # Reusable components
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript types
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml          # Local development setup
└── TECHNICAL_DESIGN.md         # Detailed technical specification
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tools-version-management
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/v1
   - API Documentation: http://localhost:8000/v1/docs

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

5. **Stop services**
   ```bash
   docker-compose down
   ```

---

## Running Services Locally

### Option 1: Docker Compose (Recommended)

This runs all services (Frontend, Backend, MongoDB) in containers.

```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# Restart a specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

### Option 2: Run Services Individually

#### Backend Only

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export STORAGE_BACKEND=mongodb
export MONGODB_URL=mongodb://admin:admin@localhost:27017
export MONGODB_DATABASE=infraversionhub
export JWT_SECRET=your-secret-key
export LOG_LEVEL=DEBUG

# Run the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Only

```bash
cd frontend

# Install dependencies
npm install

# Set environment variable for API
export VITE_API_URL=http://localhost:8000/v1

# Run development server
npm run dev
```

#### MongoDB Only

```bash
# Run MongoDB container
docker run -d \
  --name infraversionhub-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin \
  -e MONGO_INITDB_DATABASE=infraversionhub \
  mongo:7
```

---

## Building Docker Images

### Build Backend Image

```bash
cd backend

# Build the image
docker build -t infraversionhub-backend:latest .

# Run the container
docker run -d \
  --name backend \
  -p 8000:8000 \
  -e STORAGE_BACKEND=mongodb \
  -e MONGODB_URL=mongodb://admin:admin@host.docker.internal:27017 \
  -e MONGODB_DATABASE=infraversionhub \
  -e JWT_SECRET=your-secret-key \
  infraversionhub-backend:latest
```

### Build Frontend Image

```bash
cd frontend

# Build the image
docker build -t infraversionhub-frontend:latest .

# Run the container
docker run -d \
  --name frontend \
  -p 3000:8080 \
  infraversionhub-frontend:latest
```

---

## API Endpoints

### Health Check

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/health` | GET | Liveness probe |
| `/v1/health/ready` | GET | Readiness probe (checks DB) |

### Components

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/components` | GET | List all components |
| `/v1/components` | POST | Create a component |
| `/v1/components/{id}` | GET | Get component by ID |
| `/v1/components/{id}` | PUT | Update component |
| `/v1/components/{id}` | DELETE | Delete component |

### Mappings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/mappings` | GET | List all mappings |
| `/v1/mappings` | POST | Create a mapping |
| `/v1/mappings/{id}` | GET | Get mapping by ID |
| `/v1/mappings/{id}` | PUT | Update mapping |
| `/v1/mappings/{id}` | DELETE | Delete mapping |
| `/v1/mappings/matrix` | GET | Get environment matrix view |

---

## Example API Usage

### Create a Component

```bash
curl -X POST http://localhost:8000/v1/components \
  -H "Content-Type: application/json" \
  -d '{
    "name": "argocd",
    "display_name": "Argo CD",
    "category": "ci-cd",
    "current_version": "2.9.3",
    "description": "Declarative GitOps CD for Kubernetes",
    "owner_team": {
      "name": "Platform Team",
      "email": "platform@example.com"
    },
    "tags": ["gitops", "kubernetes", "cd"]
  }'
```

### Create an Environment Mapping

```bash
curl -X POST http://localhost:8000/v1/mappings \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "<component-id-from-above>",
    "component_version": "2.9.3",
    "environment_name": "production",
    "cluster_name": "prod-us-east-1",
    "cloud_provider": "aws",
    "region": "us-east-1",
    "namespace": "argocd",
    "deployment_status": "deployed"
  }'
```

### List Components

```bash
curl http://localhost:8000/v1/components
```

### Get Environment Matrix

```bash
curl http://localhost:8000/v1/mappings/matrix
```

---

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `STORAGE_BACKEND` | `filesystem` | Storage backend (mongodb, filesystem) |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection URL |
| `MONGODB_DATABASE` | `infraversionhub` | MongoDB database name |
| `JWT_SECRET` | - | Secret key for JWT tokens (required) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRATION_HOURS` | `24` | Token expiration time |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `/v1` | Backend API URL |

---

## Troubleshooting

### Services won't start

```bash
# Check if ports are in use
lsof -i :3000
lsof -i :8000
lsof -i :27017

# Remove existing containers
docker-compose down
docker rm -f infraversionhub-frontend infraversionhub-backend infraversionhub-mongodb

# Rebuild and start
docker-compose up -d --build
```

### MongoDB connection issues

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Check MongoDB logs
docker-compose logs mongodb

# Test MongoDB connection
docker exec -it infraversionhub-mongodb mongosh -u admin -p admin
```

### View container logs

```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Reset everything

```bash
# Stop services and remove volumes
docker-compose down -v

# Remove all related images
docker rmi infraversionhub-backend infraversionhub-frontend

# Start fresh
docker-compose up -d --build
```

---

## Development

### Backend Development

```bash
cd backend

# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn src.main:app --reload --port 8000

# Run tests
pytest

# Format code
black src/
isort src/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server with hot reload
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

---

## License

MIT License
