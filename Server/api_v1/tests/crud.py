import json
from pathlib import Path

TESTS_DIR = Path("Server/data/tests")
TESTS_DIR.mkdir(parents=True, exist_ok=True) 

def get_all_tests_metadata():
    metadata = []
    for file in TESTS_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                metadata.append({
                    "id": data.get("id"), 
                    "name": data.get("name"), 
                    "desc": data.get("desc", "")
                })
        except Exception:
            continue
    return metadata

def get_test_by_id(test_id: str):
    
    file_path = TESTS_DIR / f"{test_id}.json"
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)