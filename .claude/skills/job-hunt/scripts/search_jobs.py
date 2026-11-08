"""Scrape fresh job listings with JobSpy, drop seen/irrelevant ones, and write a JSON shortlist.

Usage: python run.py search_jobs.py [--hours N] [--per-query N] [--quick]
Everything person-specific (terms, locations, tiers, skills, level) comes from job-hunt/search_config.json.
Prints the output path; the file holds candidates sorted by a rough pre-score.
"""
import argparse
import json
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from jobspy import scrape_jobs

from common import DATA, job_key, load_config, load_tracker

logging.disable(logging.WARNING)

EXP_IN_DESC = re.compile(r"(?:minimum|min\.?|at least)?\s*(\d{1,2})\s*\+?\s*(?:-\s*\d+\s*)?(?:years|yrs)(?:\s+of)?\s+(?:\w+\s+){0,3}experience", re.I)


def words_re(words):
    return re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.I) if words else None


def min_years(exp: str):
    m = re.search(r"(\d+)\s*-\s*\d+", exp or "")
    return int(m.group(1)) if m else None


def run_query(cfg, term, loc, hours, per_query):
    try:
        df = scrape_jobs(site_name=cfg["sites"], search_term=term, location=loc, results_wanted=per_query,
                         hours_old=hours, country_indeed=cfg.get("country_indeed", "usa"),
                         fetch_description=True, verbose=0)
        return df.to_dict("records")
    except Exception as e:  # one bad site/query shouldn't kill the run
        print(f"warn: {term} @ {loc}: {e}", file=sys.stderr)
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int)
    ap.add_argument("--per-query", type=int, default=15)
    ap.add_argument("--quick", action="store_true", help="fewer terms/locations for a fast run")
    a = ap.parse_args()

    cfg = load_config()
    hours = a.hours or cfg.get("hours_old", 72)
    terms, locs = cfg["search_terms"], cfg["locations"]
    if a.quick:
        terms, locs = terms[:cfg.get("quick_terms", 3)], locs[:cfg.get("quick_locations", 4)]
    tiers = {int(k): v for k, v in cfg["tiers"].items()}
    tier_res = {t: words_re(v.get("match", [])) for t, v in tiers.items()}
    exclude = words_re(cfg.get("exclude_title_words", []))
    must = re.compile("|".join(cfg["title_must_match"]), re.I) if cfg.get("title_must_match") else None
    level = words_re(cfg.get("level_signals", []))
    skills = [s.lower() for s in cfg.get("skills", [])]
    max_years = cfg.get("max_years_required", 99)

    tracker = load_tracker()
    seen_urls, seen_keys = set(tracker["urls"]), set(tracker["jobs"])

    rows = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_query, cfg, t, l["search"], hours, a.per_query): l["tier"] for t in terms for l in locs}
        for f in as_completed(futs):
            for r in f.result():
                r["_tier"] = futs[f]
                rows.append(r)

    out, batch_keys = [], set()
    for r in rows:
        title, company = str(r.get("title") or ""), str(r.get("company") or "")
        url = r.get("job_url") or ""
        key = job_key(company, title)
        if not title or not company or url in seen_urls or key in seen_keys or key in batch_keys:
            continue
        if (exclude and exclude.search(title)) or (must and not must.search(title)):
            continue
        exp = str(r.get("experience_range") or "")
        desc = str(r.get("description") or "")
        asked = [int(n) for n in EXP_IN_DESC.findall(desc[:5000])]
        if min_years(exp) is not None:
            asked.append(min_years(exp))
        if asked and min(asked) > max_years:
            continue
        text = f"{title}\n{desc}".lower()
        hits = [s for s in skills if s in text]
        if skills and not hits:
            continue
        loc = str(r.get("location") or "")
        tier = next((t for t, rx in sorted(tier_res.items()) if rx and rx.search(loc)), r["_tier"])
        level_fit = bool(level and level.search(f"{title} {exp} {desc[:3000]}"))
        prescore = len(hits) * 3 + (15 if level_fit else 0) + tiers.get(tier, {}).get("bonus", 0)
        batch_keys.add(key)
        out.append({
            "key": key, "title": title, "company": company, "location": loc, "tier": tier,
            "site": r.get("site"), "url": url, "url_direct": r.get("job_url_direct") or "",
            "date_posted": str(r.get("date_posted") or ""), "experience_range": exp,
            "job_level": str(r.get("job_level") or ""), "level_signal": level_fit,
            "skill_hits": hits, "prescore": prescore, "description": desc[:4000],
        })

    out.sort(key=lambda j: j["prescore"], reverse=True)
    raw = DATA / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    path = raw / f"{date.today().isoformat()}_candidates.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"{len(rows)} scraped, {len(out)} new relevant -> {path}")


if __name__ == "__main__":
    main()
