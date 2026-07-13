from resume_pipeline.correct import correct_record


def _invalid(sample_resume_dict):
    bad = {
        key: (dict(value) if isinstance(value, dict) else value)
        for key, value in sample_resume_dict.items()
    }
    bad["contact"] = dict(bad["contact"], email="broken")
    return {
        "record": bad,
        "record_type": "resumes",
        "errors": [
            {
                "field": "contact.email",
                "category": "format_violation",
                "message": "value is not a valid email address",
            }
        ],
    }


def test_correct_on_first_attempt(sample_resume_dict):
    def fake_llm(response_model, system, user, **kwargs):
        fixed = dict(sample_resume_dict)
        return response_model.model_validate(
            {
                key: fixed.get(key)
                for key in ("contact", "summary", "education", "experience", "skills")
            }
        )

    result = correct_record(_invalid(sample_resume_dict), llm=fake_llm)
    assert result["success"] is True
    assert result["attempts"] == 1
    assert result["corrected"]["contact"]["email"] == "ada@example.com"


def test_gives_up_after_three(sample_resume_dict):
    def stubborn_llm(response_model, system, user, **kwargs):
        still_bad = {
            key: sample_resume_dict.get(key)
            for key in ("contact", "summary", "education", "experience", "skills")
        }
        still_bad["contact"] = dict(still_bad["contact"], email="still-broken")
        return response_model.model_validate(still_bad)

    result = correct_record(_invalid(sample_resume_dict), llm=stubborn_llm)
    assert result["success"] is False
    assert result["attempts"] == 3
    assert result["final_errors"]


def test_error_messages_reach_the_prompt(sample_resume_dict):
    seen = {}

    def spy_llm(response_model, system, user, **kwargs):
        seen["user"] = user
        return response_model.model_validate(
            {
                key: sample_resume_dict.get(key)
                for key in ("contact", "summary", "education", "experience", "skills")
            }
        )

    correct_record(_invalid(sample_resume_dict), llm=spy_llm)
    assert "contact.email" in seen["user"]
    assert "not a valid email" in seen["user"]


def test_literal_null_date_is_repaired_without_an_llm_call(sample_resume_dict):
    sample_resume_dict["experience"][0]["end_date"] = "null"
    invalid = {
        "record": sample_resume_dict,
        "record_type": "resumes",
        "errors": [
            {
                "field": "experience.0.end_date",
                "category": "format_violation",
                "message": "Input should be a valid date or datetime",
            }
        ],
    }

    result = correct_record(invalid, llm=lambda *_args, **_kwargs: None)

    assert result["success"] is True
    assert result["attempts"] == 0
    assert result["corrected"]["experience"][0]["end_date"] is None


def test_all_null_resume_uses_complete_replacement_guidance(sample_resume_dict):
    all_null = {
        "record": {
            "contact": None,
            "summary": None,
            "education": None,
            "experience": None,
            "skills": None,
            "metadata": sample_resume_dict["metadata"],
        },
        "record_type": "resumes",
        "errors": [
            {
                "field": field,
                "category": "type_mismatch",
                "message": "Input should be a valid list or object",
            }
            for field in ("contact", "education", "experience", "skills")
        ],
    }
    seen = {}

    def repair_llm(response_model, system, user, **kwargs):
        seen["user"] = user
        return response_model.model_validate(
            {
                key: sample_resume_dict.get(key)
                for key in ("contact", "summary", "education", "experience", "skills")
            }
        )

    result = correct_record(all_null, llm=repair_llm)

    assert result["success"] is True
    assert result["corrected"]["metadata"] == sample_resume_dict["metadata"]
    assert "ALL CORE RESUME FIELDS ARE MISSING" in seen["user"]
