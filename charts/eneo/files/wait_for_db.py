import psycopg2
import time
import sys
from psycopg2 import sql
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Configuration
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    postgres_user: str
    postgres_host: str
    postgres_password: str
    postgres_port: int
    postgres_db: str

    default_tenant_name: Optional[str] = None
    default_tenant_quota_limit: Optional[int] = None
    default_user_name: Optional[str] = None
    default_user_email: Optional[str] = None
    default_user_password: Optional[str] = None

settings = Settings()

# Wait for PostgreSQL to be ready
def wait_for_postgres(max_retries=30, initial_delay=1, max_delay=10):
    """
    Wait for PostgreSQL to be ready with exponential backoff.
    
    Args:
        max_retries: Maximum number of connection attempts
        initial_delay: Initial delay in seconds between retries
        max_delay: Maximum delay in seconds between retries
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                connect_timeout=5
            )
            conn.close()
            print("PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"PostgreSQL not ready yet (attempt {attempt + 1}/{max_retries}). Waiting {delay}s... Error: {e}")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)  # Exponential backoff with cap
            else:
                print(f"Failed to connect to PostgreSQL after {max_retries} attempts.")
                sys.exit(1)
    return False

# Main script
if __name__ == "__main__":
    # Wait for PostgreSQL to be ready
    wait_for_postgres()
    exit(0)