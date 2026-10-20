from pathlib import Path


# Project Settings


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
KNOWN_FACES_DIR = BASE_DIR / "known_faces"
MODELS_DIR = BASE_DIR / "models"
SOUNDS_DIR = BASE_DIR / "sounds"
LOGS_DIR = BASE_DIR / "logs"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

DATABASE_FILE = DATA_DIR / "smart_glasses.db"
PEOPLE_JSON = DATA_DIR / "people.json"
PERSONS_FILE = DATA_DIR / "persons.json"

FACE_MODEL_FILE = MODELS_DIR / "face_model.yml"
FACE_LABELS_FILE = MODELS_DIR / "face_labels.json"

CAMERA_INDEX = 0
SAMPLE_COUNT = 30
FACE_SIZE = (200, 200)
CONFIDENCE_THRESHOLD = 75

APP_NAME = "Smart AI Glasses System"

LANGUAGES = {
    "1": {"name": "English", "code": "en"},
    "2": {"name": "French", "code": "fr"},
    "3": {"name": "Arabic", "code": "ar"},
    "4": {"name": "Spanish", "code": "es"},
    "5": {"name": "German", "code": "de"},
    "6": {"name": "Swahili", "code": "sw"},
}


def create_project_folders() -> None:
    """Create all required folders."""
    for folder in [
        DATA_DIR,
        KNOWN_FACES_DIR,
        MODELS_DIR,
        SOUNDS_DIR,
        LOGS_DIR,
        SCREENSHOTS_DIR,
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def print_project_info() -> None:
    print("=" * 45)
    print(APP_NAME)
    print("=" * 45)
    print(f"Base folder: {BASE_DIR}")
    print(f"Database: {DATABASE_FILE}")
    print("=" * 45)
