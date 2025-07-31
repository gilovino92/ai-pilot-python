from pydantic import PostgresDsn
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings
from pydantic import computed_field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "FastAPI Application"
    APP_API_KEY: str
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    # API Settings
    API_V1_STR: str = ""

    LLM: str = "openai"
    
    # AI Settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # AWS Settings
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str = "us-east-1"
    AWS_BEDROCK_MODEL: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    
    # Add more settings as needed
    # DATABASE_URL: Optional[str] = None
    # SECRET_KEY: Optional[str] = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Keycloak Settings
    KEYCLOAK_SERVER_URL: str
    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_REALM_NAME: str
    KEYCLOAK_CLIENT_SECRET_KEY: str

    TENANT_URL: str
    TENANT_API_KEY: str

    TAVILY_API_KEY: str

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

settings = Settings();