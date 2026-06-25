cat > README.md << 'EOF'
# Canteen Management Backend

FastAPI backend for Canteen Management System with MongoDB and Specmatic Contract Testing.

## Features
- JWT Authentication
- User Registration & Login
- Food Management (CRUD)
- Order Processing
- Admin & User Roles
- Contract Testing with Specmatic

## Tech Stack
- FastAPI
- MongoDB
- JWT
- bcrypt
- Specmatic (Contract Testing)

## Prerequisites
- Python 3.8 or higher
- MongoDB (local or Docker)
- Docker Desktop (for Specmatic)

## Setup

1. Clone the repository:
   git clone https://github.com/Bijendramishra123/canteen-management-backend.git
   cd canteen-management-backend

2. Create virtual environment:
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Create .env file:
   SECRET_KEY=mysecretkey
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   MONGO_URI=mongodb://localhost:27017

## Running the Application

### Local Development
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### Using Docker
docker-compose up -d

## OpenAPI Specification

Generate OpenAPI specification:
python -c "from app.main import app; import json; f=open('openapi.json','w'); json.dump(app.openapi(), f, indent=2); f.close(); print('openapi.json generated')"

## Specmatic Contract Testing

### 1. Verify Specmatic Image
docker run --rm specmatic/specmatic --version

### 2. Run Contract Tests
docker run --rm -v "$(pwd):/work" specmatic/specmatic test /work/openapi.json --host host.docker.internal --port 8000

### 3. Run with Examples
docker run --rm -v "$(pwd):/work" specmatic/specmatic test /work/openapi.json --examples /work/examples --host host.docker.internal --port 8000

### 4. Run with Resiliency Configuration
docker run --rm -v "$(pwd):/work" specmatic/specmatic test /work/openapi.json --config /work/specmatic.yaml --host host.docker.internal --port 8000

### 5. Generate JUnit Report
docker run --rm -v "$(pwd):/work" specmatic/specmatic test /work/openapi.json --junitReportDir /work/reports --host host.docker.internal --port 8000

## Mock Server

Run Specmatic as a mock server:
docker run --rm -v "$(pwd):/work" -p 8080:8080 specmatic/specmatic stub /work/openapi.json --port 8080

## Resiliency Tests

Resiliency configuration is in specmatic.yaml:
- Probes for health check endpoints
- Automatic monitoring of API stability

## Test Reports

Reports are generated in the reports/ folder:
- HTML report: reports/index.html
- JUnit XML: reports/junit.xml
- JSON report: reports/report.json

## Issues Fixed

| Issue | Specmatic Error | Status |
|-------|-----------------|--------|
| _id leakage | R2003 - Unknown Property | Fixed |
| null availability | R1001 - Type Mismatch | Fixed |
| missing 404 | R0002 - HTTP Status Mismatch | Fixed |

## Test Results

- Tests Run: 240
- Passed: 215
- Failed: 25
- Success Rate: 89.6%

## CI/CD Integration

### GitHub Actions Workflow

This project uses GitHub Actions for continuous integration. The workflow automatically runs Specmatic contract tests on every push and pull request to the main branch.

**Workflow File:** `.github/workflows/contract-tests.yml`

**What it does:**
1. Starts MongoDB container
2. Starts the API container
3. Waits for API to be ready
4. Runs Specmatic contract tests
5. Uploads test reports as artifacts

### Workflow Steps

```yaml
name: Contract Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Start MongoDB
      run: |
        docker run -d --name mongodb -p 27017:27017 mongo:6

    - name: Start API
      run: |
        docker run -d --name api -p 8000:8000 canteen-docker-compose-backend:latest

    - name: Wait for API
      run: |
        sleep 10

    - name: Run Specmatic Contract Tests
      run: |
        docker run --rm -v $(pwd):/work specmatic/specmatic test /work/openapi.json --host localhost --port 8000

    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: specmatic-reports
        path: reports/