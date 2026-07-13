from resume_pipeline.prompts import JOB_PROMPT, RESUME_TEMPLATES


def test_generation_prompts_require_fields_that_failed_production_validation():
    assert "company.name" in JOB_PROMPT
    assert "company.industry" in JOB_PROMPT
    assert "company.size" in JOB_PROMPT
    assert "company.location" in JOB_PROMPT

    resume_prompt = RESUME_TEMPLATES["formal"]
    assert "contact.name" in resume_prompt
    assert "YYYY-MM-DD" in resume_prompt
