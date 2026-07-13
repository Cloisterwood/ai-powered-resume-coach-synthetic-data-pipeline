"""Stage 4: six rule-based failure metrics shared by batch and API code."""

import argparse
import json
import re
from collections import Counter
from datetime import date
from itertools import combinations
from typing import Any

from .normalize import jaccard, normalize_set
from .paths import latest, stage_dir, timestamp
from .schemas import SENIORITY_RANK, JobDescription, Resume

TITLE_SENIORITY = [
    (4, ("chief", "vp", "vice president", "director", "executive", "head of")),
    (3, ("lead", "principal", "staff")),
    (2, ("senior", "sr.", "sr ")),
    (0, ("junior", "jr.", "jr ", "intern", "entry", "associate", "trainee")),
]
BUZZWORDS = [
    "synergy",
    "leverage",
    "leveraging",
    "think outside the box",
    "thinking outside the box",
    "move the needle",
    "go-getter",
    "results-driven",
    "self-starter",
    "dynamic",
    "guru",
    "ninja",
    "rockstar",
    "paradigm",
    "disrupt",
    "cutting-edge",
    "best-in-class",
    "world-class",
    "value-add",
    "circle back",
    "low-hanging fruit",
]
BUZZWORD_THRESHOLD = 5
REPEAT_WINDOW = 30
HALLUCINATION_PHRASES = [
    "expert in all",
    "certified in everything",
    "mastery of all",
    "expert in every",
]
ENTRY_YEARS = 2.0
ENTRY_EXPERT_LIMIT = 10
MANY_SKILLS = 30
_STOPWORDS = {"the", "and", "a", "an", "of", "to", "in", "for", "with", "on", "at"}


def total_experience_years(resume: Resume) -> float:
    """Sum all listed job durations, using today for current roles."""
    total = 0.0
    for experience in resume.experience:
        end = experience.end_date or date.today()
        total += max(0.0, (end - experience.start_date).days / 365.25)
    return round(total, 2)


def resume_seniority_level(resume: Resume) -> int:
    """Infer seniority from the most recent role title; default to Mid."""
    if not resume.experience:
        return 0
    latest_experience = max(resume.experience, key=lambda item: item.start_date)
    title = latest_experience.title.lower()
    for rank, keywords in TITLE_SENIORITY:
        if any(keyword in title for keyword in keywords):
            return rank
    return 1


def has_impossible_timeline(resume: Resume) -> bool:
    """Flag three long-running roles that overlap for more than 180 days."""
    intervals = [
        (experience.start_date, experience.end_date or date.today())
        for experience in resume.experience
    ]
    for overlapping_roles in combinations(intervals, 3):
        overlap_start = max(start for start, _end in overlapping_roles)
        overlap_end = min(end for _start, end in overlapping_roles)
        if (overlap_end - overlap_start).days > 180:
            return True
    return False


def detect_hallucination(
    total_years: float,
    skills: list[dict[str, Any]],
    texts: list[str],
    impossible_timeline: bool = False,
) -> bool:
    """Flag implausible expertise quantities and explicit universal-skill claims."""
    if impossible_timeline:
        return True
    expert_count = sum(
        1 for skill in skills if skill.get("proficiency_level") == "Expert"
    )
    if total_years < ENTRY_YEARS and expert_count >= ENTRY_EXPERT_LIMIT:
        return True
    if len(skills) >= MANY_SKILLS and expert_count / max(1, len(skills)) >= 0.5:
        return True
    text = " ".join(texts).lower()
    return any(phrase in text for phrase in HALLUCINATION_PHRASES)


def detect_awkward_language(texts: list[str]) -> bool:
    """Flag dense buzzword use or three repeated meaningful words in one window."""
    text = " ".join(texts).lower()
    buzzword_hits = sum(text.count(buzzword) for buzzword in BUZZWORDS)
    if buzzword_hits > BUZZWORD_THRESHOLD:
        return True
    words = [word for word in re.findall(r"[a-z']+", text) if word not in _STOPWORDS]
    for index in range(len(words)):
        window = Counter(words[index : index + REPEAT_WINDOW])
        if window and window.most_common(1)[0][1] >= 3:
            return True
    return False


def _resume_texts(resume: Resume) -> list[str]:
    texts = [resume.summary or ""]
    for experience in resume.experience:
        texts.extend(experience.responsibilities)
        texts.extend(experience.achievements)
    return texts


def label_pair(resume: Resume, job: JobDescription) -> dict[str, Any]:
    """Compute every required failure metric for a resume/job pair."""
    resume_skills = normalize_set([skill.name for skill in resume.skills])
    job_skills = normalize_set(job.required_skills)
    core_skills = normalize_set(job.required_skills[:3])
    missing_core = sorted(core_skills - resume_skills)
    resume_years = total_experience_years(resume)
    resume_seniority = resume_seniority_level(resume)
    job_seniority = SENIORITY_RANK[job.experience_level]
    texts = _resume_texts(resume)
    skills = [skill.model_dump() for skill in resume.skills]
    return {
        "skills_overlap": round(jaccard(resume_skills, job_skills), 4),
        "experience_mismatch": resume_years < 0.5 * job.experience_years,
        "seniority_mismatch": abs(resume_seniority - job_seniority) > 1,
        "missing_core_skills": bool(missing_core),
        "hallucinated_skills": detect_hallucination(
            resume_years,
            skills,
            texts,
            impossible_timeline=has_impossible_timeline(resume),
        ),
        "awkward_language": detect_awkward_language(texts),
        "resume_years": resume_years,
        "resume_seniority": resume_seniority,
        "job_seniority": job_seniority,
        "missing_core_list": missing_core,
    }


def _read_jsonl(path) -> list[dict[str, Any]]:
    with path.open() as input_file:
        return [json.loads(line) for line in input_file if line.strip()]


def _artifact(stage: str, prefix: str, suffix: str, artifact_timestamp: str | None):
    if artifact_timestamp is None:
        return latest(stage, prefix)
    path = stage_dir(stage) / f"{prefix}{artifact_timestamp}{suffix}"
    if not path.exists():
        raise FileNotFoundError(f"artifact not found: {path}")
    return path


def run(
    generated_timestamp: str | None = None,
    validated_timestamp: str | None = None,
    corrected_timestamp: str | None = None,
) -> str:
    """Label pairs whose resume and job records are available after correction."""
    artifact_timestamp = timestamp()
    with _artifact(
        "validated", "validated_data_", ".json", validated_timestamp
    ).open() as input_file:
        validated = json.load(input_file)
    resumes = {
        record["metadata"]["trace_id"]: Resume.model_validate(record)
        for record in validated["resumes"]["records"]
    }
    jobs = {
        record["metadata"]["trace_id"]: JobDescription.model_validate(record)
        for record in validated["jobs"]["records"]
    }
    try:
        for record in _read_jsonl(
            _artifact("corrected", "corrected_", ".jsonl", corrected_timestamp)
        ):
            if record["record_type"] == "resumes":
                resume = Resume.model_validate(record["record"])
                resumes[resume.metadata.trace_id] = resume
            else:
                job = JobDescription.model_validate(record["record"])
                jobs[job.metadata.trace_id] = job
    except FileNotFoundError:
        pass

    pairs = _read_jsonl(
        _artifact("generated", "pairs_", ".jsonl", generated_timestamp)
    )
    output_dir = stage_dir("analysis")
    labeled = 0
    skipped = 0
    with (output_dir / f"failure_labels_{artifact_timestamp}.jsonl").open("w") as output:
        for pair in pairs:
            resume = resumes.get(pair["resume_trace_id"])
            job = jobs.get(pair["job_trace_id"])
            if resume is None or job is None:
                skipped += 1
                continue
            output.write(json.dumps({**pair, **label_pair(resume, job)}) + "\n")
            labeled += 1
    print(f"labeled {labeled} pairs, skipped {skipped} (invalid and uncorrected)")
    return artifact_timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-timestamp")
    parser.add_argument("--validated-timestamp")
    parser.add_argument("--corrected-timestamp")
    arguments = parser.parse_args()
    run(
        generated_timestamp=arguments.generated_timestamp,
        validated_timestamp=arguments.validated_timestamp,
        corrected_timestamp=arguments.corrected_timestamp,
    )
