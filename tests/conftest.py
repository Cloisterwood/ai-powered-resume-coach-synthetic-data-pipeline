import pytest


@pytest.fixture
def sample_resume_dict():
    return {
        "contact": {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "phone": "555-123-4567",
            "location": "Austin, TX",
        },
        "summary": "Backend engineer with 6 years building data platforms.",
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "UT Austin",
                "graduation_date": "2018-05-15",
                "gpa": 3.7,
            }
        ],
        "experience": [
            {
                "company": "Acme Corp",
                "title": "Senior Software Engineer",
                "start_date": "2020-03-01",
                "end_date": "2024-06-30",
                "responsibilities": ["Built ETL pipelines"],
                "achievements": ["Cut latency 40%"],
            },
            {
                "company": "Beta LLC",
                "title": "Software Engineer",
                "start_date": "2018-06-01",
                "end_date": "2020-02-28",
                "responsibilities": ["Maintained APIs"],
                "achievements": [],
            },
        ],
        "skills": [
            {"name": "Python", "proficiency_level": "Expert", "years": 6},
            {"name": "PostgreSQL", "proficiency_level": "Advanced"},
        ],
        "metadata": {
            "trace_id": "res-001",
            "generated_at": "2026-07-04T12:00:00",
            "prompt_template": "formal",
            "fit_level": "excellent",
            "writing_style": "formal",
        },
    }


@pytest.fixture
def sample_job_dict():
    return {
        "title": "Senior Backend Engineer",
        "company": {
            "name": "DataCo",
            "industry": "Fintech",
            "size": "200-500",
            "location": "Remote",
        },
        "description": "Own our payments data platform.",
        "required_skills": ["Python", "PostgreSQL", "AWS"],
        "preferred_skills": ["Terraform"],
        "education": "BS in CS or equivalent",
        "experience_years": 5,
        "experience_level": "Senior",
        "metadata": {
            "trace_id": "job-001",
            "generated_at": "2026-07-04T12:00:00",
            "is_niche_role": False,
        },
    }
