from resume_pipeline import judge
from resume_pipeline.schemas import JobDescription, Resume


def test_judge_uses_dedicated_judge_tier(monkeypatch, sample_resume_dict, sample_job_dict):
    observed = {}

    def fake_generate(response_model, system, user, **kwargs):
        observed["tier"] = kwargs["tier"]
        observed["temperature"] = kwargs["temperature"]
        return response_model(
            has_hallucinations=False,
            hallucination_details="None observed.",
            has_awkward_language=False,
            awkward_language_details="None observed.",
            overall_quality_score=0.9,
            fit_assessment="Strong fit.",
            recommendations=["Apply."],
            red_flags=[],
        )

    monkeypatch.setattr(judge, "generate", fake_generate)

    verdict = judge.judge_pair(
        Resume.model_validate(sample_resume_dict),
        JobDescription.model_validate(sample_job_dict),
    )

    assert verdict.overall_quality_score == 0.9
    assert observed == {"tier": "judge", "temperature": 0.0}
