# FastAPI Application

A Python FastAPI application with basic setup and environment configuration.

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install --upgrade pip

pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload --port $PORT 
```

The application will be available at http://localhost:8000

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

The application uses a `.env` file for configuration. Make sure to create this file with the following variables:
- APP_NAME
- DEBUG
- ENVIRONMENT


