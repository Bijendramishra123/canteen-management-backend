# Canteen Management Backend

FastAPI backend for Canteen Management System with MongoDB.

## Features
- JWT Authentication
- User Registration & Login
- Food Management (CRUD)
- Order Processing
- Admin & User Roles

## Tech Stack
- FastAPI
- MongoDB
- JWT
- bcrypt

## Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

### Step 2: .gitignore file create karein

```bash
cat > .gitignore << 'EOF'
# Python
venv/
__pycache__/
*.pyc
.env
.DS_Store

# IDE
.vscode/
.idea/

# Logs
*.log
