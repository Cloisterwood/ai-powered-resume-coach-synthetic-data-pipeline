"""REST API sharing the exact batch labeler used by the pipeline."""

import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .analyze import failure_rates, load_labels
from .labeler import label_pair
from .schemas import JobDescription, Resume

app = FastAPI(title="Resume Coach API", version="1.0.0")


class ReviewRequest(BaseModel):
    resume: Resume
    job: JobDescription
    use_llm_judge: bool = False


class ReviewResponse(BaseModel):
    labels: dict
    judge: dict | None = None
    elapsed_seconds: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "resume-coach", "version": "1.0.0"}


@app.post("/review-resume", response_model=ReviewResponse)
def review_resume(request: ReviewRequest) -> ReviewResponse:
    started_at = time.time()
    labels = label_pair(request.resume, request.job)
    verdict = None
    if request.use_llm_judge:
        from .judge import judge_pair

        try:
            verdict = judge_pair(request.resume, request.job).model_dump()
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"LLM judge failed: {error}")
    return ReviewResponse(
        labels=labels,
        judge=verdict,
        elapsed_seconds=round(time.time() - started_at, 3),
    )


@app.get("/analysis/failure-rates")
def analysis_failure_rates() -> dict:
    try:
        return failure_rates(load_labels())
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="no failure labels found — run the batch pipeline first",
        )
