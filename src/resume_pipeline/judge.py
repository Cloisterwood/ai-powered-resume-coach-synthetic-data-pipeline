"""Optional LLM-as-Judge for subtle quality issues rules cannot catch."""

from pydantic import BaseModel, Field

from .llm_client import generate
from .prompts import JUDGE_PROMPT, JUDGE_SYSTEM
from .schemas import JobDescription, Resume


class JudgeVerdict(BaseModel):
    has_hallucinations: bool
    hallucination_details: str
    has_awkward_language: bool
    awkward_language_details: str
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    fit_assessment: str
    recommendations: list[str]
    red_flags: list[str]


def judge_pair(resume: Resume, job: JobDescription) -> JudgeVerdict:
    """Return a structured, optional quality review of one resume/job pair."""
    return generate(
        JudgeVerdict,
        JUDGE_SYSTEM,
        JUDGE_PROMPT.format(
            resume_json=resume.model_dump_json(),
            job_json=job.model_dump_json(),
        ),
        temperature=0.0,
        tier="judge",
    )
