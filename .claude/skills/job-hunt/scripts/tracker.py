"""Duplicate-work tracker.

  python tracker.py check "<company>" "<title>"   -> NEW | SEEN (<status>, <folder>) | NEW_ROLE_SAME_COMPANY (<folder>)
  python tracker.py record <file.json>          -> record a list of evaluated jobs:
        [{"company", "title", "url", "score", "status": prepared|backlog|skipped, "folder", "location", "why"}]
  python tracker.py backlog                     -> JSON of good jobs not yet prepared (re-rank these each run)
  python tracker.py list                        -> everything recorded so far
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from common import job_key, load_tracker, norm_company, save_tracker


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("company"); c.add_argument("title")
    r = sub.add_parser("record"); r.add_argument("file")
    sub.add_parser("backlog")
    sub.add_parser("list")
    a = ap.parse_args()
    t = load_tracker()

    if a.cmd == "check":
        key = job_key(a.company, a.title)
        if key in t["jobs"] and t["jobs"][key]["status"] != "backlog":
            j = t["jobs"][key]
            print(f"SEEN ({j['status']}, {j.get('folder', '')})")
            return
        same = [j for k, j in t["jobs"].items()
                if k.split("::")[0] == norm_company(a.company) and j.get("folder")]
        print(f"NEW_ROLE_SAME_COMPANY ({same[0]['folder']})" if same else "NEW")
    elif a.cmd == "record":
        items = json.loads(Path(a.file).read_text(encoding="utf-8"))
        for it in items:
            key = job_key(it["company"], it["title"])
            prev = t["jobs"].get(key, {})
            t["jobs"][key] = {**prev, **it, "date": prev.get("date", date.today().isoformat()),
                              "updated": date.today().isoformat()}
            if it.get("url") and it["url"] not in t["urls"]:
                t["urls"].append(it["url"])
        save_tracker(t)
        print(f"recorded {len(items)} jobs ({len(t['jobs'])} total)")
    elif a.cmd == "backlog":
        print(json.dumps([j for j in t["jobs"].values() if j["status"] == "backlog"], indent=1, ensure_ascii=False))
    else:
        for j in sorted(t["jobs"].values(), key=lambda j: (j["date"], -j.get("score", 0))):
            print(f"{j['date']}  {j['status']:<8} {j.get('score', 0):>3}  {j['company']} | {j['title']}  {j.get('folder', '')}")


if __name__ == "__main__":
    main()
