from resume_pipeline.labeler import (
    detect_awkward_language,
    detect_hallucination,
    has_impossible_timeline,
    label_pair,
    resume_seniority_level,
    total_experience_years,
)
from resume_pipeline.schemas import JobDescription, Resume


def test_experience_years_sums_jobs(sample_resume_dict):
    resume = Resume.model_validate(sample_resume_dict)
    assert 5.5 < total_experience_years(resume) < 6.5


def test_seniority_from_latest_title(sample_resume_dict):
    resume = Resume.model_validate(sample_resume_dict)
    assert resume_seniority_level(resume) == 2


def test_good_pair_has_no_flags(sample_resume_dict, sample_job_dict):
    resume = Resume.model_validate(sample_resume_dict)
    sample_job_dict["required_skills"] = ["Python", "PostgreSQL"]
    job = JobDescription.model_validate(sample_job_dict)
    labels = label_pair(resume, job)
    assert labels["skills_overlap"] == 1.0
    assert labels["experience_mismatch"] is False
    assert labels["seniority_mismatch"] is False
    assert labels["missing_core_skills"] is False


def test_missing_core_and_low_jaccard(sample_resume_dict, sample_job_dict):
    sample_job_dict["required_skills"] = ["Rust", "Go", "Kafka"]
    resume = Resume.model_validate(sample_resume_dict)
    job = JobDescription.model_validate(sample_job_dict)
    labels = label_pair(resume, job)
    assert labels["skills_overlap"] == 0.0
    assert labels["missing_core_skills"] is True
    assert set(labels["missing_core_list"]) == {"rust", "go", "kafka"}


def test_experience_mismatch_under_half(sample_resume_dict, sample_job_dict):
    sample_job_dict["experience_years"] = 15
    resume = Resume.model_validate(sample_resume_dict)
    job = JobDescription.model_validate(sample_job_dict)
    assert label_pair(resume, job)["experience_mismatch"] is True


def test_seniority_mismatch_two_levels(sample_resume_dict, sample_job_dict):
    sample_job_dict["experience_level"] = "Executive"
    resume = Resume.model_validate(sample_resume_dict)
    job = JobDescription.model_validate(sample_job_dict)
    assert label_pair(resume, job)["seniority_mismatch"] is True


def test_hallucination_entry_level_many_experts():
    skills = [
        {"name": f"skill{index}", "proficiency_level": "Expert"}
        for index in range(11)
    ]
    assert detect_hallucination(total_years=1.0, skills=skills, texts=[]) is True


def test_hallucination_phrase():
    assert (
        detect_hallucination(
            total_years=10.0,
            skills=[{"name": "python", "proficiency_level": "Advanced"}],
            texts=["I am an expert in all technologies"],
        )
        is True
    )


def test_no_hallucination_normal():
    assert (
        detect_hallucination(
            total_years=6.0,
            skills=[{"name": "python", "proficiency_level": "Expert"}],
            texts=["Built data pipelines"],
        )
        is False
    )


def test_hallucination_detects_three_long_overlapping_roles(
    sample_resume_dict, sample_job_dict
):
    sample_resume_dict["experience"] = [
        {
            "company": "Alpha",
            "title": "Engineer",
            "start_date": "2018-01-01",
            "end_date": "2022-01-01",
            "responsibilities": ["Built services"],
            "achievements": [],
        },
        {
            "company": "Beta",
            "title": "Engineer",
            "start_date": "2019-01-01",
            "end_date": "2022-01-01",
            "responsibilities": ["Built services"],
            "achievements": [],
        },
        {
            "company": "Gamma",
            "title": "Engineer",
            "start_date": "2020-01-01",
            "end_date": "2022-01-01",
            "responsibilities": ["Built services"],
            "achievements": [],
        },
    ]
    resume = Resume.model_validate(sample_resume_dict)

    assert has_impossible_timeline(resume) is True
    job = JobDescription.model_validate(sample_job_dict)
    assert label_pair(resume, job)["hallucinated_skills"] is True


def test_hallucination_allows_normal_sequential_roles(sample_resume_dict):
    assert has_impossible_timeline(Resume.model_validate(sample_resume_dict)) is False


def test_hallucination_allows_two_overlapping_roles(sample_resume_dict):
    sample_resume_dict["experience"] = [
        {
            "company": "Alpha",
            "title": "Engineer",
            "start_date": "2020-01-01",
            "end_date": "2022-01-01",
            "responsibilities": ["Built services"],
            "achievements": [],
        },
        {
            "company": "Beta",
            "title": "Consultant",
            "start_date": "2020-06-01",
            "end_date": "2021-06-01",
            "responsibilities": ["Advised teams"],
            "achievements": [],
        },
    ]

    assert has_impossible_timeline(Resume.model_validate(sample_resume_dict)) is False


def test_awkward_buzzword_density():
    text = (
        "Leveraging synergy as a results-driven go-getter, I move the needle "
        "with cutting-edge, best-in-class, world-class paradigm shifts."
    )
    assert detect_awkward_language([text]) is True


def test_awkward_repetition():
    assert detect_awkward_language(["delivered value delivered value delivered value"]) is True


def test_plain_text_not_awkward():
    assert (
        detect_awkward_language(
            ["Maintained the billing API and reduced error rates by 12%."]
        )
        is False
    )
