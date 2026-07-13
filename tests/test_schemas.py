import pytest
from pydantic import ValidationError

from resume_pipeline.schemas import JobDescription, Resume, ResumePair


def test_valid_resume_parses(sample_resume_dict):
    resume = Resume.model_validate(sample_resume_dict)
    assert resume.contact.name == "Ada Lovelace"
    assert resume.skills[0].proficiency_level == "Expert"


def test_bad_email_rejected(sample_resume_dict):
    sample_resume_dict["contact"]["email"] = "not-an-email"
    with pytest.raises(ValidationError):
        Resume.model_validate(sample_resume_dict)


def test_short_phone_rejected(sample_resume_dict):
    sample_resume_dict["contact"]["phone"] = "12345"
    with pytest.raises(ValidationError):
        Resume.model_validate(sample_resume_dict)


def test_gpa_out_of_range_rejected(sample_resume_dict):
    sample_resume_dict["education"][0]["gpa"] = 4.5
    with pytest.raises(ValidationError):
        Resume.model_validate(sample_resume_dict)


def test_end_before_start_rejected(sample_resume_dict):
    sample_resume_dict["experience"][0]["end_date"] = "2019-01-01"
    with pytest.raises(ValidationError):
        Resume.model_validate(sample_resume_dict)


def test_non_iso_date_rejected(sample_resume_dict):
    sample_resume_dict["experience"][0]["start_date"] = "March 2020"
    with pytest.raises(ValidationError):
        Resume.model_validate(sample_resume_dict)


def test_valid_job_parses(sample_job_dict):
    job = JobDescription.model_validate(sample_job_dict)
    assert job.experience_level == "Senior"
    assert job.metadata.is_niche_role is False


def test_experience_years_bounds(sample_job_dict):
    sample_job_dict["experience_years"] = 45
    with pytest.raises(ValidationError):
        JobDescription.model_validate(sample_job_dict)


def test_pair_links_ids():
    pair = ResumePair(
        pair_id="pair-001",
        job_trace_id="job-001",
        resume_trace_id="res-001",
        fit_level="excellent",
        prompt_template="formal",
        is_niche_role=False,
        generated_at="2026-07-04T12:00:00",
    )
    assert pair.pair_id == "pair-001"
