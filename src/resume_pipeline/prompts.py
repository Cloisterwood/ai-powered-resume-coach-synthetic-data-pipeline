"""Prompt templates with str.format variable injection for every pipeline stage."""

JOB_SYSTEM = "You are an HR content writer who produces realistic job descriptions."

JOB_PROMPT = """Write one realistic job description as structured data.

Industry: {industry}
Seniority level: {experience_level} (use exactly this word for experience_level)
Niche role: {niche_instruction}

Requirements:
- company MUST be an object with non-empty company.name, company.industry, company.size,
  and company.location fields (for example, size may be "201-500 employees")
- 5 to 8 required_skills (concrete technologies or competencies, not soft skills)
- 2 to 4 preferred_skills that do NOT repeat required_skills
- experience_years as a plain integer between 0 and 30, appropriate to the seniority
- A 2-4 sentence description paragraph
- Set is_niche_role to {is_niche} (a niche role is a rare specialization like
  "Quantum Compiler Engineer" or "Underwater Welding Inspector"; a standard role is
  common like "Backend Engineer" or "Account Manager")
"""

RESUME_SYSTEM = (
    "You generate synthetic resumes as structured data for ML training. "
    "Follow the persona instructions exactly."
)

_RESUME_CORE = """Generate one synthetic resume for a fictional candidate applying to this job:

JOB TITLE: {job_title}
JOB DESCRIPTION: {job_description}
JOB SENIORITY: {experience_level}, {experience_years} years experience required

FIT CONTROL (follow exactly — this creates a "{fit_level}" fit):
- Include these skills from the job (choose realistic proficiency levels): {skills_to_include}
- Do NOT include any of these job skills: {skills_to_exclude}
- You may add at most {max_extras} unrelated extra skills.
- Target candidate seniority: {target_seniority} with roughly {target_years} years of total experience
  spread over 1-4 jobs with realistic ISO dates (YYYY-MM-DD).

STRUCTURE RULES:
- contact: contact.name MUST be a non-empty full name; also provide a plausible email,
  phone with at least 10 digits, and city/state location
- education: at least one entry with degree, institution, ISO graduation_date; GPA between 0.0 and 4.0 if given
- experience: each entry needs company, title, ISO start_date, ISO end_date (or null for current job),
  1-4 responsibilities, 0-3 achievements; end_date must come after start_date
- every date value MUST use the ISO YYYY-MM-DD format (including graduation_date,
  start_date, and end_date)
- skills: objects with name and proficiency_level (Beginner/Intermediate/Advanced/Expert)
"""

RESUME_TEMPLATES = {
    "formal": _RESUME_CORE
    + """
WRITING STYLE: Formal corporate. Third-person-free, measured tone, conventional
titles, conservative achievement wording.""",
    "casual": _RESUME_CORE
    + """
WRITING STYLE: Casual startup. First-person summary, contractions, informal
titles ("Growth hacker in chief" is fine occasionally), friendly tone.""",
    "technical": _RESUME_CORE
    + """
WRITING STYLE: Technical and detail-heavy. Responsibilities name specific tools,
versions, architectures, and protocols. Dense, precise, minimal fluff.""",
    "achievement": _RESUME_CORE
    + """
WRITING STYLE: Achievement-focused. Nearly every bullet leads with a quantified
metric (%, $, time saved). Action verbs, results-first phrasing.""",
    "career_changer": _RESUME_CORE
    + """
WRITING STYLE: Career changer. Earlier jobs are in a DIFFERENT field; summary and
bullets emphasize transferable skills bridging the old field to this job.""",
}

CORRECTION_SYSTEM = (
    "You fix structured data so it passes schema validation. "
    "Change only what the errors require."
)

CORRECTION_PROMPT = """The following {record_type} data failed schema validation.

VALIDATION ERRORS:
{error_details}

ORIGINAL DATA:
{original_data}

{all_null_guidance}

Return a corrected version that fixes every listed error while changing as little
else as possible. Dates must be ISO YYYY-MM-DD. Emails must be valid. Phone numbers
need at least 10 characters. GPA must be between 0.0 and 4.0. end_date must be after
start_date. experience_years must be an integer 0-30."""

JUDGE_SYSTEM = "You are a strict resume-quality judge. Output structured judgments only."

JUDGE_PROMPT = """Evaluate this resume against this job description.

RESUME:
{resume_json}

JOB:
{job_json}

Assess:
1. Hallucinations: unverifiable or implausible claims, impossible timelines
2. Awkward language: excessive jargon, unnatural phrasing, obvious AI patterns
3. Fit: holistic skills + experience alignment with the job
4. Red flags: employment gaps, inconsistent career progression

Score overall_quality_score from 0.0 (unusable) to 1.0 (excellent)."""
