# Candidate profile for /job-hunt

Created by first-run setup from the resume. Edit it freely; every run re-reads it.
Resume content lives in `master_resume.html`, and the search settings the scraper uses live in `search_config.json`.

## Candidate
- Name: {{name}}
- Source resume: {{file name}}
- Level: {{fresher | junior (1-3 yrs) | mid (3-6 yrs) | senior (6+ yrs)}}, {{one-line background, e.g. "B.Tech CSE 2026, CGPA 9.0"}}
- Target: {{the kind of role they want}}
- Not interested in: {{roles/industries to skip}}
- Resume page limit: {{1 for freshers/juniors, 2 if the original resume is 2 pages}}

## Target job titles
- {{title}}

## Location preference (tier 1 is the most preferred)
1. {{e.g. home state / city}}
2. {{e.g. nearest big tech hub}}
3. {{e.g. rest of the region}}
- Remote: {{yes/no}}. Anything else: {{skip | allow}}

## Connection anchors for referral search (strongest first)
Only include anchors that appear in the resume or that the user confirmed.
1. University/college: {{full name, plus alternate spellings and abbreviation, plus campus town}}
2. School: {{name, plus town if known}}
3. Home town / district: {{district, plus nearby towns}}
4. Wider network: {{e.g. affiliating university, previous employers, professional bodies}}
5. Home state / region: {{state}}. Use this only for jobs OUTSIDE it, and only when 1-4 return nobody at that company.
