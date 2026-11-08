---
name: job-hunt
description: Personal job-hunting assistant driven by the resume in the current folder. On first run it reads the resume and sets up a profile, search settings and an editable master resume. Each run then finds fresh matching jobs, ranks them by chance of getting an interview, builds a tailored A4 resume PDF per company and role, and lists referral contacts who share a college, school, hometown or region with the candidate. Run manually with /job-hunt.
argument-hint: "[setup] [how many jobs to prepare, default 5] [quick]"
disable-model-invocation: true
allowed-tools: Bash(python *), Bash(python3 *), Bash(py *), Bash(mkdir *), Bash(ls *), WebSearch, WebFetch, Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
---

# Job hunt

## Conventions
- **Project folder** = the current working directory. It holds the candidate's resume and all generated data:
  - `job-hunt/`: `profile.md`, `master_resume.html`, `search_config.json`, `jobs_seen.json`, `raw/`
  - `Companies/<Company>/`: tailored resumes, JDs, referrals
  - `Reports/`: one report per run
- **Skill folder** = the folder containing this SKILL.md (usually `.claude/skills/job-hunt/`, or `~/.claude/skills/job-hunt/` if installed globally). Below, `RUN` means `python <skill folder>/scripts/run.py`.
- Always run scripts through `RUN <script>.py ...` from the project folder. `run.py` creates the skill's private virtualenv (`<skill folder>/.venv`) on first use and installs `requirements.txt` into it, so never pip-install into the user's Python. If `python` isn't found, try `python3` or `py`.
- Arguments: `$ARGUMENTS`. `setup` forces setup again. A number sets N, the max jobs to prepare (default 5). `quick` passes `--quick` to the search.

## Step 0: Setup (only on first run)
Skip this step if `job-hunt/profile.md`, `job-hunt/master_resume.html` and `job-hunt/search_config.json` all exist and the arguments don't include `setup`.

1. `RUN --setup-only` creates the Python environment. Tell the user this happens once and may take a minute.
2. Find the resume: Glob `*.pdf` and `*.docx` in the project folder root, excluding `Companies/`, `Reports/` and `job-hunt/`.
   - If there's none, ask the user to put their resume (PDF or DOCX) in the folder, then stop.
   - If there are several, ask which one is theirs.
3. Read the resume two ways: run `RUN extract_resume.py "<file>"` for exact text and hyperlinks, and Read the file to see its layout.
4. Infer from the resume, then confirm with ONE AskUserQuestion call (up to 4 questions; put the recommended option first):
   - Location preference order. Propose tiers from where they live and study. Example: home state, then nearest major tech hub, then rest of the region, then remote.
   - Target roles. Propose 4-6 titles that match the resume.
   - Experience level, if it's ambiguous (fresher / junior / mid / senior).
   - Anything missing that the referral search needs, e.g. home town if the resume only names a state.
5. Create `job-hunt/master_resume.html` from `<skill folder>/templates/resume_template.html`:
   - Reproduce the original's content exactly: every section, bullet, number, date and hyperlink. Don't add or improve anything. Match the original's section order.
   - Keep the template's CSS, including `@page { size: A4 }`.
   - Render it: `RUN render_pdf.py job-hunt/master_resume.html job-hunt/master_resume_check.pdf --max-pages <original page count>`. Read the PDF and compare it with the original; fix any missing content and re-render.
6. Create `job-hunt/profile.md` from `templates/profile_template.md`, filling every `{{...}}`. List referral anchors only from facts in the resume or confirmed answers.
7. Create `job-hunt/search_config.json` from `templates/search_config.example.json` (drop the `_help` key):
   - `country_indeed` and `sites`: use Naukri only for India, and add region-specific boards where relevant (e.g. `zip_recruiter` for US/CA, `bayt` for the Gulf).
   - `search_terms`: 6-8 terms built from the confirmed roles, adding "fresher"/"entry level" to some terms for freshers.
   - `locations` and `tiers`: one search city per important city; `match` words must include state codes job boards use (e.g. Indeed India uses `KL`, `KA`, `TN`).
   - `skills`: 15-30 lower-case keywords from the resume.
   - `max_years_required`: fresher 1, junior 3, mid 6, senior 99.
   - `exclude_title_words`: for freshers and juniors keep the seniority words; for senior people remove them and exclude junior words instead.
   - `title_must_match`: fit to their field (it's not always tech).
   - `level_signals`: fit to their level.
8. Show a short setup summary (name, roles, location tiers, referral anchors, files created). If the arguments included `setup`, stop here; otherwise continue to Step 1.

## Step 1: Collect jobs
Read `job-hunt/profile.md` and `job-hunt/master_resume.html` first. The master resume is the only source of truth for what the candidate has done.

1. `RUN search_jobs.py [--quick]` scrapes job boards for recent postings using `search_config.json`. It drops already-seen jobs, wrong-level jobs and off-topic jobs, and writes `job-hunt/raw/<date>_candidates.json`, sorted by a rough pre-score.
2. `RUN tracker.py backlog` returns good jobs from earlier runs that weren't prepared yet. Re-rank them with today's jobs, dropping any older than 21 days or whose posting is gone.
3. Use up to 6 WebSearch calls on sources the scraper misses, chosen from the profile: local IT-park or regional job portals, company careers pages, `reddit` hiring threads for their city or field, and "hiring" posts on X or LinkedIn for their role and city. Only keep clearly current postings (about the last 2 weeks, or with a future deadline). Run `RUN tracker.py check "<company>" "<title>"` on each and drop `SEEN`.

## Step 2: Rank by chance of an interview
Score each candidate out of 100. Skim everything, but read the full JD for the top ~15. If a description is empty or short, fetch the job URL.

| Factor | Points |
|---|---|
| Level fit | JD explicitly targets the candidate's level 30; level unspecified 18; slightly above their level 8; clearly above `max_years_required`: drop |
| Skill match with master_resume | 0-30 |
| Location | tier 1: 15, tier 2: 10, remote (if wanted): 10, tier 3: 6, other: drop unless the profile allows it |
| Freshness | <=1 day 15, <=3 days 10, <=7 days 5, older 0 |
| Referral likelihood | company is in the candidate's home region or known to hire from their college 10; large employer with many staff 6; else 3 |

Red flags: training fee or paid internship charged to the candidate (drop), bond over 1 year (-10), staffing-agency repost with no named client (-5), restricted to colleges the candidate didn't attend (drop).

Pick the top N with score >= 55. For each, run `RUN tracker.py check`:
- `SEEN`: skip, it was already done.
- `NEW_ROLE_SAME_COMPANY (<folder>)`: reuse that folder and add a resume for this new role only. Don't redo referrals unless `referrals.txt` is older than 30 days.
- `NEW`: create `Companies/<Company_Name>/`.

The same role at the same company from a different site or city counts as a duplicate. Only one resume per (company, role).

## Step 3: Build each company package
In `Companies/<Company_Name>/` (clean name with underscores, no "Pvt Ltd" / "Inc"):

1. **`JD_<Role>.txt`**: apply URL (direct company link if available), source site, location, date posted, score with a one-line breakdown, and the full JD text.
2. **Tailored resume**: copy `job-hunt/master_resume.html` to `Companies/<Company>/source/<First>_<Last>_<Role>.html`, edit it, then render with:
   `RUN render_pdf.py "<html>" "Companies/<Company>/<First>_<Last>_<Role>.pdf" --max-pages <profile page limit>`
   Use the candidate's name and the role with underscores, e.g. `Anjana_B_Generative_AI_Engineer.pdf`.
   Tailoring rules (strict):
   - **The PDF MUST be A4 (210x297 mm) and within the page limit.** Never remove or change `@page { size: A4 }`. render_pdf exits with an ERROR if either check fails. Fix it and re-render; never keep a failing PDF.
   - NEVER add a skill, tool, project, employer, number or experience that isn't in master_resume.html. Reword, reorder and emphasise only.
   - Rewrite the summary to name the exact job title and lead with the 3-4 most relevant strengths for this JD.
   - Order experience/projects and bullets by relevance. Use the JD's wording where it truthfully describes their work.
   - Reorder skill categories and items so the JD's must-haves come first. Drop clearly irrelevant items if space is needed.
   - Read the rendered PDF once to sanity-check the layout.
3. **`referrals.txt`**: one per company, see Step 4.

## Step 4: Referral search (public web only, never log into anyone's account)
Find people currently working at the company who share a connection with the candidate. Use WebSearch, up to 8 searches per company, and stop early once you have 3+ solid people. Work down the anchors in `profile.md` in order:

1. College: `"<Company>" "<college full name>" linkedin`, plus variants with the abbreviation or campus town
2. School: `"<Company>" "<school name>" <town> linkedin`
3. Home town / district: `"<Company>" <district> linkedin` (add nearby towns if results are thin)
4. Wider network anchors from the profile (e.g. affiliating university)
5. Home state / region: ONLY if the job is outside it AND 1-4 found nobody, e.g. `"<Company>" <job city> "<home state>" linkedin`, or graduates of well-known colleges in that state working there

Rules: list a person only if the search result itself shows both that they work (or recently worked) at the company AND the connection. Never guess or invent names, roles or URLs. Prefer people in the same function as the job, and HR/talent people second.

Format:
```
REFERRAL CONTACTS: <Company>   (searched <date>)
Job(s): <role 1>, <role 2>

[STRONG: <college> alumni]
1. <Name>: <current role> at <Company>
   Connection: <what they share, e.g. same college, batch if shown>
   Profile: <url>
   Source: <where you saw it>

[MEDIUM: <school> / <home district>]
...
[WEAK: <wider network> / <home state>]
...
(If a tier has nobody, write "none found".)

SUGGESTED MESSAGE (edit before sending):
Hi <Name>, I'm <candidate first name>, <one-line background> from <shared connection>. I saw the <Role> opening at <Company> (<link>). <One line on their most relevant achievement from the resume.> Would you be open to referring me or sharing any advice? I've attached my resume. Thank you!
```

## Step 5: Record and report
1. Write a JSON list of every candidate you scored to `job-hunt/raw/<date>_decisions.json`. Statuses: prepared; backlog (scored >= 55 but beyond N); skipped (below 55 or dropped). Then run `RUN tracker.py record job-hunt/raw/<date>_decisions.json`. Fields: company, title, url, score, status, folder (if prepared), location, why (one short line). This is what prevents duplicate work next time.
2. Write `Reports/<date>.md`:
   - A ranked table of prepared jobs: rank, score, company, role, location, posted, apply link, folder, best referral contact.
   - Backlog: the next 5-10 good ones.
   - Notable skips (one line each).
   - Sources that failed (e.g. LinkedIn rate-limited).
3. Final chat message: the ranked top-N with scores, folder links and best referral per company, plus how many were scanned, new, skipped as duplicates and backlogged. Keep it short.

Never apply to jobs or message anyone automatically. The candidate does that.
