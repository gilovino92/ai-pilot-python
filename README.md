# X-Pilot AI Trading Assistant (Backend)

A sophisticated FastAPI-based backend service that powers the X-Pilot AI Assistant - an intelligent platform designed specifically for trading sales representatives. This service provides AI-powered conversations, market research capabilities, and comprehensive support for commodity trading operations.

## 🚀 Features

### Core Functionality
- **AI-Powered Chat Assistant**: Advanced conversational AI specialized for trading
- **Real-time Streaming**: Server-sent events (SSE) for live conversation updates
- **Web Search Integration**: Powered by Tavily API for current market information
- **Multi-LLM Support**: OpenAI GPT and AWS Bedrock Claude integration
- **Workflow Management**: LlamaIndex-based agent workflows for complex interactions

### Trading Features
- **Market Analysis**: Real-time commodity price trends and market insights
- **Company Verification**: Import/export history and reliability checks
- **Sales Communication**: Enhanced messaging with professional tone optimization
- **Lead Generation**: AI-powered prospect research and qualification
- **Documentation Support**: Trade document guidance and compliance assistance

### Technical Features
- **Authentication**: Keycloak OAuth2 integration
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic database migrations
- **API Security**: JWT token validation and API key middleware
- **Containerization**: Docker support with multi-stage builds
- **CORS**: Configured for cross-origin requests

## 🏗 Architecture

### Core Components
```
app/
├── api/                    # FastAPI routes and endpoints
│   ├── routes/
│   │   ├── copilot_chat/  # Chat-related endpoints
│   │   └── utils.py       # Utility endpoints
│   └── deps.py            # Dependency injection (auth, etc.)
├── ai_workflow/           # AI workflow management
│   ├── pilot_assistant/   # Main AI assistant workflow
│   ├── agents/           # Specialized AI agents
│   └── sale_agent_workflow.py # Sales-focused workflow
├── models/               # SQLAlchemy database models
├── tools/               # Utility functions and database tools
├── middleware/          # Custom middleware (API key validation)
└── config.py           # Application configuration
```

### Database Schema
- **PilotChat**: Chat sessions with user context
- **PilotChatMessage**: Individual messages with role and type classification
- **User Management**: Integrated with Keycloak for authentication

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Redis (optional, for caching)
- AWS account (for Bedrock integration)
- Tavily API key (for web search)
- Keycloak server (for authentication)

### 1. Environment Setup

Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Application Settings
APP_NAME=X-Pilot AI Assistant
APP_API_KEY=your-app-api-key
DEBUG=True
ENVIRONMENT=development
PORT=8000
API_V1_STR=/api/v1

# AI Settings
LLM=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# AWS Settings (for Bedrock)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION_NAME=us-east-1
AWS_BEDROCK_MODEL=us.anthropic.claude-3-7-sonnet-20250219-v1:0

# Database Settings
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=xpilot_db
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password

# Keycloak Authentication
KEYCLOAK_SERVER_URL=https://your-keycloak-server
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_REALM_NAME=your-realm
KEYCLOAK_CLIENT_SECRET_KEY=your-client-secret

# External APIs
TAVILY_API_KEY=your-tavily-api-key
TENANT_URL=your-tenant-api-url
TENANT_API_KEY=your-tenant-api-key
```

### 4. Database Setup

Run database migrations:
```bash
alembic upgrade head
```

### 5. Run the Application

#### Development Mode
```bash
uvicorn main:app --reload --port 8000
```

#### Using the provided script
```bash
chmod +x run.sh
./run.sh
```

#### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The application will be available at:
- **Main API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t x-pilot-backend .

# Run the container
docker run -d \
  --name x-pilot-backend \
  -p 8000:8000 \
  --env-file .env \
  x-pilot-backend
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    env_file:
      - .env
    depends_on:
      - postgres
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: xpilot_db
      POSTGRES_USER: your-db-user
      POSTGRES_PASSWORD: your-db-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

## 📡 API Endpoints

### Chat Management
- `GET /api/v1/copilot-chat/chat` - List user chats
- `POST /api/v1/copilot-chat/chat` - Create new chat
- `GET /api/v1/copilot-chat/chat/{chat_id}` - Get chat history
- `POST /api/v1/copilot-chat/chat/{chat_id}/messages` - Send message
- `GET /api/v1/copilot-chat/chat/{chat_id}/stream` - SSE stream for real-time updates

### Utilities
- `GET /api/v1/utils/health-check/` - Health check endpoint

### Authentication
All endpoints (except health check) require:
- **Bearer Token**: Valid JWT token from Keycloak
- **API Key**: `X-API-Key` header with valid API key

## 🤖 AI Workflow System

### Pilot Assistant Workflow
The core AI assistant uses a sophisticated workflow system built on LlamaIndex:

- **System Prompt**: Specialized for agricultural trading scenarios
- **Tool Integration**: Web search via Tavily API
- **Memory Management**: Maintains conversation context
- **Streaming Responses**: Real-time message delivery
- **Error Handling**: Graceful fallback mechanisms

### Agent Types
- **Sales Agent**: Specialized for sales communication and lead management
- **Company Agent**: Company research and verification
- **Market Agent**: Market analysis and pricing insights

## 🛠 Development

### Code Structure
```python
# Main FastAPI application
from fastapi import FastAPI
from app.config import settings
from app.api import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="X-Pilot AI Assistant Backend",
    version="1.0.0"
)
```

### Adding New Features
1. **New Endpoints**: Add routes in `app/api/routes/`
2. **Database Models**: Define in `app/models/`
3. **AI Workflows**: Extend workflows in `app/ai_workflow/`
4. **Tools**: Add utility functions in `app/tools/`

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_chat.py -v
```

## 📊 Monitoring and Logging

- **Logging**: Structured logging with different levels
- **Health Checks**: Built-in health check endpoint
- **Performance**: Database connection pooling
- **Error Handling**: Comprehensive exception handling

## 🔧 Configuration

### LLM Configuration
Switch between OpenAI and AWS Bedrock:
```env
LLM=openai  # or 'bedrock'
```

### Database Configuration
- **Connection Pooling**: Configurable pool size
- **Migration Support**: Alembic integration
- **Model Relationships**: Proper foreign key constraints

## 🚀 Production Deployment

### Environment Variables
Ensure all required environment variables are set in production.

### Security Considerations
- Use strong API keys
- Configure proper CORS settings
- Enable HTTPS in production
- Secure database connections
- Regular security updates

### Performance Optimization
- Enable database connection pooling
- Configure appropriate worker processes
- Use Redis for caching (optional)
- Monitor resource usage

## 📝 License

This project is proprietary software for X-Pilot AI agricultural trading platform.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For technical support or questions about the X-Pilot AI Assistant backend, please contact the development team.


