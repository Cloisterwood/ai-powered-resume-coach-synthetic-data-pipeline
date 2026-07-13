"""Stage 1: generate jobs, then resumes per job at controlled fit levels."""

import argparse
import json
import random
import uuid
from datetime import datetime

from .llm_client import generate
from .loose_schemas import LooseJob, LooseResume
from .paths import stage_dir, timestamp
from .prompts import JOB_PROMPT, JOB_SYSTEM, RESUME_SYSTEM, RESUME_TEMPLATES

INDUSTRIES = [
    "Healthcare",
    "Fintech",
    "E-commerce",
    "Education",
    "Manufacturing",
    "Logistics",
    "Media",
    "Cybersecurity",
    "Biotech",
    "Real Estate",
    "Gaming",
    "Energy",
    "Insurance",
    "Agriculture",
    "Aerospace",
]
LEVELS = ["Entry", "Mid", "Senior", "Lead", "Executive"]
LEVEL_YEARS = {
    "Entry": (0, 2),
    "Mid": (2, 5),
    "Senior": (5, 10),
    "Lead": (8, 15),
    "Executive": (12, 25),
}
FIT_LEVELS = ["excellent", "good", "partial", "poor", "mismatch"]
FIT_INCLUDE_FRACTION = {
    "excellent": (0.85, 1.0),
    "good": (0.6, 0.8),
    "partial": (0.4, 0.6),
    "poor": (0.2, 0.4),
    "mismatch": (0.0, 0.15),
}
TEMPLATES = list(RESUME_TEMPLATES)
NICHE_RATE = 0.2
JOB_GENERATION_MAX_TOKENS = 1200
RESUME_GENERATION_MAX_TOKENS = 4096


def _fit_plan(required: list[str], fit_level: str) -> tuple[list[str], list[str]]:
    """Select an exact subset of required skills for the target fit level."""
    low, high = FIT_INCLUDE_FRACTION[fit_level]
    count = round(random.uniform(low, high) * len(required))
    count = max(0, min(len(required), count))
    included = random.sample(required, count)
    excluded = [skill for skill in required if skill not in included]
    return included, excluded


def _seniority_plan(job_level: str, fit_level: str) -> tuple[str, int]:
    """Match seniority for strong fits and introduce controlled drift for weak ones."""
    level = job_level if job_level in LEVELS else "Mid"
    job_index = LEVELS.index(level)
    drift_options = {
        "excellent": [0],
        "good": [0, 1],
        "partial": [0, 1, -1],
        "poor": [1, -1, 2, -2],
        "mismatch": [2, -2, 3, -3],
    }[fit_level]
    target_index = min(4, max(0, job_index + random.choice(drift_options)))
    target_level = LEVELS[target_index]
    return target_level, random.randint(*LEVEL_YEARS[target_level])


def _generated_at() -> str:
    return datetime.now().isoformat()


def _generate_nonempty_resume(prompt: str) -> LooseResume:
    """Retry once when the provider returns an entirely empty resume object."""
    for _attempt in range(2):
        resume = generate(
            LooseResume,
            RESUME_SYSTEM,
            prompt,
            temperature=0.9,
            max_tokens=RESUME_GENERATION_MAX_TOKENS,
        )
        if any(
            getattr(resume, field) is not None
            for field in ("contact", "education", "experience", "skills")
        ):
            return resume
    raise RuntimeError("LLM returned an all-null resume after one retry")


def run(n_jobs: int, resumes_per_job: int, seed: int = 42) -> str:
    """Generate timestamped job, resume, and pair JSONL artifacts."""
    random.seed(seed)
    artifact_timestamp = timestamp()
    output_dir = stage_dir("generated")

    with (
        (output_dir / f"jobs_{artifact_timestamp}.jsonl").open("w") as jobs_file,
        (output_dir / f"resumes_{artifact_timestamp}.jsonl").open("w") as resumes_file,
        (output_dir / f"pairs_{artifact_timestamp}.jsonl").open("w") as pairs_file,
    ):
        for job_index in range(n_jobs):
            requested_niche_role = random.random() < NICHE_RATE
            requested_level = LEVELS[job_index % len(LEVELS)]
            industry = INDUSTRIES[job_index % len(INDUSTRIES)]
            job = generate(
                LooseJob,
                JOB_SYSTEM,
                JOB_PROMPT.format(
                    industry=industry,
                    experience_level=requested_level,
                    niche_instruction=(
                        "RARE NICHE specialization"
                        if requested_niche_role
                        else "standard, common role"
                    ),
                    is_niche=requested_niche_role,
                ),
                temperature=0.9,
                max_tokens=JOB_GENERATION_MAX_TOKENS,
            )
            job_data = job.model_dump()
            generated_niche_role = job_data.pop("is_niche_role", None)
            is_niche_role = (
                requested_niche_role
                if generated_niche_role is None
                else bool(generated_niche_role)
            )
            job_data["metadata"] = {
                "trace_id": f"job-{uuid.uuid4().hex[:8]}",
                "generated_at": _generated_at(),
                "is_niche_role": is_niche_role,
            }
            jobs_file.write(json.dumps(job_data) + "\n")

            required_skills = job_data.get("required_skills") or ["general aptitude"]
            job_level = job_data.get("experience_level")
            if job_level not in LEVELS:
                job_level = requested_level

            for resume_index in range(resumes_per_job):
                fit_level = FIT_LEVELS[resume_index % len(FIT_LEVELS)]
                template = TEMPLATES[(job_index + resume_index) % len(TEMPLATES)]
                included_skills, excluded_skills = _fit_plan(required_skills, fit_level)
                target_level, target_years = _seniority_plan(job_level, fit_level)
                resume = _generate_nonempty_resume(
                    RESUME_TEMPLATES[template].format(
                        job_title=job_data.get("title", ""),
                        job_description=job_data.get("description", ""),
                        experience_level=job_level,
                        experience_years=job_data.get("experience_years", 5),
                        fit_level=fit_level,
                        skills_to_include=", ".join(included_skills) or "(none)",
                        skills_to_exclude=", ".join(excluded_skills) or "(none)",
                        max_extras=3,
                        target_seniority=target_level,
                        target_years=target_years,
                    )
                )
                resume_data = resume.model_dump()
                resume_data["metadata"] = {
                    "trace_id": f"res-{uuid.uuid4().hex[:8]}",
                    "generated_at": _generated_at(),
                    "prompt_template": template,
                    "fit_level": fit_level,
                    "writing_style": template,
                }
                resumes_file.write(json.dumps(resume_data) + "\n")
                pairs_file.write(
                    json.dumps(
                        {
                            "pair_id": f"pair-{uuid.uuid4().hex[:8]}",
                            "job_trace_id": job_data["metadata"]["trace_id"],
                            "resume_trace_id": resume_data["metadata"]["trace_id"],
                            "fit_level": fit_level,
                            "prompt_template": template,
                            "is_niche_role": is_niche_role,
                            "generated_at": _generated_at(),
                        }
                    )
                    + "\n"
                )
            print(
                f"[{job_index + 1}/{n_jobs}] "
                f"{job_data.get('title')} — {resumes_per_job} resumes"
            )

    print(f"done: timestamp {artifact_timestamp}")
    return artifact_timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=50)
    parser.add_argument("--resumes-per-job", type=int, default=6)
    arguments = parser.parse_args()
    run(arguments.jobs, arguments.resumes_per_job)
