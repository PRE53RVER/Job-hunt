"""Shared paths and normalisation for the job-hunt scripts.

All personal data lives under the project folder the skill is run from (the current directory):
  job-hunt/       profile.md, master_resume.html, search_config.json, jobs_seen.json, raw/
  Companies/      one folder per company with tailored resumes
  Reports/        one report per run
"""
import json
import re
from pathlib import Path

ROOT = Path.cwd()
DATA = ROOT / "job-hunt"
CONFIG = DATA / "search_config.json"
TRACKER = DATA / "jobs_seen.json"
COMPANIES = ROOT / "Companies"

_COMPANY_NOISE = r"\b(pvt|private|ltd|limited|llp|llc|inc|gmbh|corp|corporation|technologies|technology|solutions|software|services|india|global|systems|co|com)\b"
_ROLE_SYNONYMS = [
    (r"\b(engineer|developer|scientist|analyst|intern|trainee|programmer)s\b", r"\1"),
    (r"\bgenerative\s+ai\b|\bgen\s*ai\b", "genai"),
    (r"\bartificial\s+intelligence\b", "ai"),
    (r"\bmachine\s+learning\b", "ml"),
    (r"\bai\s*/\s*ml\b|\bai\s+ml\b|\bml\s*/\s*ai\b", "aiml"),
    (r"\blarge\s+language\s+models?\b", "llm"),
    (r"\bdeveloper\b", "engineer"),
    (r"\bsde\b|\bsoftware\s+development\s+engineer\b", "software engineer"),
]
_ROLE_NOISE = r"\b(junior|jr|associate|entry\s*level|fresher|freshers|graduate|i|1|ii|2|level)\b"


def norm_company(name: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    s = re.sub(_COMPANY_NOISE, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_role(title: str) -> str:
    s = (title or "").lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)  # drop "(0-1 yrs)", "[Remote]" etc.
    s = s.split(" - ")[0].split(" | ")[0]
    for pat, rep in _ROLE_SYNONYMS:
        s = re.sub(pat, rep, s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(_ROLE_NOISE, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def job_key(company: str, title: str) -> str:
    return f"{norm_company(company)}::{norm_role(title)}"


def load_config() -> dict:
    if not CONFIG.exists():
        raise SystemExit(f"{CONFIG} not found. Run /job-hunt setup first.")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_tracker() -> dict:
    if TRACKER.exists():
        return json.loads(TRACKER.read_text(encoding="utf-8"))
    return {"jobs": {}, "urls": []}


def save_tracker(t: dict) -> None:
    TRACKER.parent.mkdir(parents=True, exist_ok=True)
    TRACKER.write_text(json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")
