# job-hunt: a Claude Code skill

Drop your resume in this folder, type `/job-hunt`, and Claude will:

1. **Set up on the first run.** It reads your resume (PDF or DOCX), asks a few questions (preferred locations, target roles), and creates your profile, search settings and an editable master resume.
2. **Find fresh jobs** on LinkedIn, Indeed, Naukri and others, plus local job portals and Reddit/X hiring posts.
3. **Rank them** by your chance of getting an interview: level fit, skill match, location preference, freshness and referral potential.
4. **Build a package for each top job** in `Companies/<Company>/`:
   - `<Name>_<Role>.pdf`: a resume tailored to that job description. Always A4, never invents anything.
   - `JD_<Role>.txt`: the job description and apply link.
   - `referrals.txt`: people at that company who share your college, school, hometown or home state, found by public web search only (no account login), with a suggested message.
5. **Avoid duplicate work.** A job it has already handled is never redone. A new role at a company you already have gets its own resume in the same folder.

Nothing is applied for or sent automatically.

## Requirements
- [Claude Code](https://claude.com/claude-code): VS Code extension, desktop app or CLI
- Python 3.10+ (or [uv](https://docs.astral.sh/uv/), which can fetch Python for you)
- Microsoft Edge, Google Chrome or Chromium (used to render the PDFs)

Python packages install themselves into a private virtualenv (`.claude/skills/job-hunt/.venv`) the first time the skill runs.

## Use it
1. Clone this repo (or copy the `.claude/skills/job-hunt` folder into any project folder).
2. Put **your resume** (`.pdf` or `.docx`) in the repo folder.
3. Open the folder in VS Code, open the Claude Code panel and type:

| Command | What it does |
|---|---|
| `/job-hunt` | First run: setup, then a search. Later runs: search and prepare up to 5 jobs |
| `/job-hunt 3` | Prepare up to 3 jobs |
| `/job-hunt 3 quick` | Fewer searches, faster |
| `/job-hunt setup` | Redo setup, e.g. after updating your resume |

To use it from every folder, copy `.claude/skills/job-hunt` to `~/.claude/skills/job-hunt`.

## Files it creates (all git-ignored)
```
job-hunt/profile.md            your preferences + referral anchors (edit freely)
job-hunt/master_resume.html    your resume as editable HTML (source for all tailored versions)
job-hunt/search_config.json    search terms, cities, location tiers, skill keywords
job-hunt/jobs_seen.json        tracker that prevents duplicate work
Companies/<Company>/...        tailored resumes, JDs, referral lists
Reports/<date>.md              each run's ranked summary
```

## Notes
- Job-board scraping uses [JobSpy](https://github.com/speedyapply/JobSpy). LinkedIn sometimes rate-limits; the run carries on with the other sources.
- Referral contacts come only from public search results, and the skill never makes up names. Always check a profile before reaching out.
