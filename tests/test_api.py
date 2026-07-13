from fastapi.testclient import TestClient

from resume_pipeline.api import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_review_resume_no_judge(sample_resume_dict, sample_job_dict):
    response = client.post(
        "/review-resume",
        json={
            "resume": sample_resume_dict,
            "job": sample_job_dict,
            "use_llm_judge": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["labels"]["skills_overlap"] <= 1.0
    assert body["judge"] is None
    assert isinstance(body["labels"]["hallucinated_skills"], bool)


def test_review_missing_fields_is_422(sample_job_dict):
    response = client.post(
        "/review-resume", json={"resume": {"contact": {}}, "job": sample_job_dict}
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_review_empty_skills_handled(sample_resume_dict, sample_job_dict):
    sample_resume_dict["skills"] = []
    response = client.post(
        "/review-resume", json={"resume": sample_resume_dict, "job": sample_job_dict}
    )
    assert response.status_code == 422


def test_malformed_json_is_422():
    response = client.post(
        "/review-resume",
        content=b"{not json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422


def test_failure_rates_endpoint():
    response = client.get("/analysis/failure-rates")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert "overall" in response.json()
