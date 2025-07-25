# seed_mongodb.py  –  create the Ethronics course structure in MongoDB
import os, json, textwrap
from pymongo import MongoClient
from pathlib import Path
import tomllib  # Python 3.11+; for earlier versions use tomli

# ── Mongo connection string ──────────────────────────────────────────
URI = os.getenv("MONGO_URI")
if not URI:
    try:
        secrets = tomllib.loads(Path(".streamlit/secrets.toml").read_text())
        URI = secrets["mongo"]["uri"]
    except Exception:
        raise RuntimeError(
            "MongoDB URI not found. Set MONGO_URI env var or secrets.toml"
        )

client = MongoClient(URI)
db = client["ethronics"]
col = db["courses"]          # same collection name used in Streamlit app
DOC_ID = "curriculum_v1"     # fixed _id so the app can upsert

# ── Course metadata ──────────────────────────────────────────────────
groups = {
    "EG1": ["DM101", "EE102", "RM101", "PY201"],
    "EG3": ["EE101", "ES101", "PY101", "RO101"],
    "EG4": ["EE101", "ES101", "PY101", "RO101"],
}

descriptions = {
    "DM101": "Introductory data science and machine learning for high school students.",
    "EE102": "Fundamentals of electrical and electronic engineering.",
    "RM101": "Robotics and embedded systems for beginners.",
    "PY201": "Python for juniors with a focus on projects.",
    "EE101": "Core principles of electrical and electronic engineering.",
    "ES101": "General engineering science for first‑year students.",
    "PY101": "Python from scratch for engineers.",
    "RO101": "Foundations of robotics and AI.",
}

sample_content = textwrap.dedent(
    """
    ### Week 1 overview

    Welcome to the course. This session covers the syllabus, required software, and a short coding exercise.

    ```python
    print("Hello Ethronics")
    ```
    """
).strip()

sample_assessment = (
    "1. List three goals you want to achieve in this course.\n"
    "2. Run the setup notebook and upload a screenshot."
)

# ── Build the nested dictionary ──────────────────────────────────────
data = {}
for grp, course_list in groups.items():
    data[grp] = {}
    for code in course_list:
        data[grp][code] = {
            "Description": descriptions[code],
            "Week 1": {
                "content": sample_content,
                "assessment": sample_assessment,
            },
        }

# ── Write (upsert) to MongoDB ────────────────────────────────────────
result = col.update_one(
    {"_id": DOC_ID},
    {"$set": {"data": data}},
    upsert=True,
)

print(
    "Done. Document id:", DOC_ID,
    "| matched", result.matched_count,
    "| modified", result.modified_count,
    "| upserted_id", result.upserted_id,
)
