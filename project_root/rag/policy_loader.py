import os
from typing import List, Dict, Any
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
POLICY_DIR = os.path.join(BASE_DIR, "db", "resources")


def load_policy_documents(policy_dir: str = POLICY_DIR) -> List[Dict[str, Any]]:
    """Read all .md policy docs from db/resources into vector-store-ready dicts."""
    docs = []
    for filename in os.listdir(policy_dir):
        if not filename.endswith(".md"):
            continue
        path = os.path.join(policy_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        docs.append({
            "content": content,
            "metadata": {"type": "policy", "source": filename}
        })
    return docs