from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)
DATA = Path(__file__).resolve().parent / 'data'
BUNDLED_ARTIFACTS = DATA / 'artifacts'
default_artifacts = BUNDLED_ARTIFACTS if (BUNDLED_ARTIFACTS / 'reference.npz').is_file() else ROOT / 'ai/artifacts'
ARTIFACTS = Path(os.getenv('AI_ARTIFACTS_DIR', str(default_artifacts)))
if not ARTIFACTS.is_absolute():
    ARTIFACTS = ROOT / ARTIFACTS
SPACE = os.getenv('HF_SPACE_ID', 'ayaayaa/still-e-okay-ai').strip().removeprefix('https://huggingface.co/spaces/').strip('/')
TOKEN = (os.getenv('HF_TOKEN') or '').strip() or None
TIMEOUT = int(os.getenv('AI_TIMEOUT_SECONDS', '180'))
ORIGINS = [x.strip() for x in os.getenv('CORS_ORIGINS', 'https://kenal-e.vercel.app,http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
