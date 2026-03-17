# conftest.py
from pathlib import Path
from dotenv import load_dotenv
import os
import pytest

# 1. Load .env from your project root
env_path = Path(__file__).parent.parent.parent / ".env"  # adjust as needed
load_dotenv(dotenv_path=env_path)

# 2. (Optional) Verify required vars are present
required = [
    "GOOGLE_API_KEY",
    "WEAVIATE_URL",
    "WEAVIATE_API_KEY",
    "STATE_DB_URL",
    "BUSINESS_DB_URL",
    "CHAT_MODEL",
    "JWT_SECRET_KEY",
]
missing = [k for k in required if k not in os.environ]
if missing:
    pytest.exit(f"Missing required env vars: {missing}", returncode=1)


# 3. (Optional) Define any global fixtures
@pytest.fixture(autouse=True)
def always_set_timezone():
    # If your Settings model expects a TIMEZONE, you can set it here:
    os.environ.setdefault("TIMEZONE", "Africa/Cairo")
    # This fixture is applied automatically to every test.
    yield
