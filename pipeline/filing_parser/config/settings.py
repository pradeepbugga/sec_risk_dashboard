import os

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent

DATA_DIR = os.getenv("DATA_DIR", "./data")
DB_URL = os.getenv("DATABASE_URL")


def load_json(name):
    with open(CONFIG_DIR / name) as f:
        return json.load(f)

FORM_SECTIONS = load_json("form_sections.json")
MODEL_CONFIG = load_json("models.json")
PIPELINE_CONFIG = load_json("pipeline.json")

