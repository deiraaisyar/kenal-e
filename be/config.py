from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)
DATA = Path(__file__).resolve().parent / 'data'
ARTIFACTS = Path(os.getenv('AI_ARTIFACTS_DIR', str(ROOT / 'ai/artifacts')))
SPACE = os.getenv('HF_SPACE_ID', 'ayaayaa/still-e-okay-ai')
TOKEN = os.getenv('HF_TOKEN') or None
TIMEOUT = int(os.getenv('AI_TIMEOUT_SECONDS', '180'))
ORIGINS = [x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
