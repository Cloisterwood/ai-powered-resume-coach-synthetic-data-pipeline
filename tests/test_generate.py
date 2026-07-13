import pytest

from resume_pipeline import generate as generation


def test_resume_generation_uses_larger_output_budget(monkeypatch, tmp_path):
    calls = []

    def fake_generate(response_model, *args, **kwargs):
        calls.append((response_model.__name__, kwargs["max_tokens"]))
        if response_model.__name__ == "LooseJob":
            return response_model(
                title="Data Analyst",
                description="Analyze business data.",
                required_skills=["SQL", "Python"],
                experience_level="Entry",
                experience_years=1,
            )
        return response_model(
            contact={},
            education=[{}],
            experience=[{}],
            skills=[{"name": "SQL", "proficiency_level": "Intermediate"}],
        )

    monkeypatch.setattr(generation, "generate", fake_generate)
    monkeypatch.setattr(generation, "stage_dir", lambda _stage: tmp_path)
    monkeypatch.setattr(generation, "timestamp", lambda: "20260712_123456")

    generation.run(n_jobs=1, resumes_per_job=1)

    assert calls == [("LooseJob", 1200), ("LooseResume", 4096)]


def test_generation_retries_an_all_null_resume_response(monkeypatch, tmp_path):
    calls = []
    resume_responses = [
        {"contact": None, "education": None, "experience": None, "skills": None},
        {
            "contact": {},
            "education": [{}],
            "experience": [{}],
            "skills": [{"name": "SQL", "proficiency_level": "Intermediate"}],
        },
    ]

    def fake_generate(response_model, *args, **kwargs):
        calls.append(response_model.__name__)
        if response_model.__name__ == "LooseJob":
            return response_model(
                title="Data Analyst",
                description="Analyze business data.",
                required_skills=["SQL"],
                experience_level="Entry",
                experience_years=1,
            )
        return response_model(**resume_responses.pop(0))

    monkeypatch.setattr(generation, "generate", fake_generate)
    monkeypatch.setattr(generation, "stage_dir", lambda _stage: tmp_path)
    monkeypatch.setattr(generation, "timestamp", lambda: "20260713_123456")

    generation.run(n_jobs=1, resumes_per_job=1)

    assert calls == ["LooseJob", "LooseResume", "LooseResume"]


def test_generation_stops_before_writing_an_all_null_resume_pair(monkeypatch, tmp_path):
    def fake_generate(response_model, *args, **kwargs):
        if response_model.__name__ == "LooseJob":
            return response_model(
                title="Data Analyst",
                description="Analyze business data.",
                required_skills=["SQL"],
                experience_level="Entry",
                experience_years=1,
            )
        return response_model(
            contact=None,
            education=None,
            experience=None,
            skills=None,
        )

    monkeypatch.setattr(generation, "generate", fake_generate)
    monkeypatch.setattr(generation, "stage_dir", lambda _stage: tmp_path)
    monkeypatch.setattr(generation, "timestamp", lambda: "20260713_130000")

    with pytest.raises(RuntimeError, match="all-null resume"):
        generation.run(n_jobs=1, resumes_per_job=1)

    pairs_path = tmp_path / "pairs_20260713_130000.jsonl"
    assert pairs_path.read_text() == ""
