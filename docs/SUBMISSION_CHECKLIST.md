# Submission Checklist

The checklist text below is copied from the assignment page’s **Final Success Criteria**. Each line is marked against the final production run and linked to supporting evidence.

## Data Generation

- [x] 50+ job descriptions generated across diverse industries — Evidence: `data/generated/jobs_20260713_111635.jsonl` contains 50 jobs; `data/summary/pipeline_summary_20260713_121633.json` records `jobs: 50`.
- [x] 5-10 resumes per job with controlled fit levels (250+ total pairs) — Evidence: 300 resumes were generated at 6 resumes/job; `data/generated/pairs_20260713_111635.jsonl` contains 300 raw pairs.
- [x] All 5 fit levels represented (excellent, good, partial, poor, mismatch) — Evidence: final labeled counts are 100 / 50 / 50 / 50 / 50 in `pipeline_summary_20260713_121633.json`.
- [x] All 5 prompt templates used (formal, casual, technical, achievement, career-changer) — Evidence: every template has 60 labeled records in `pipeline_summary_20260713_121633.json`.
- [x] Niche role detection flag set correctly — Evidence: `JobDescription.metadata.is_niche_role` is generated and used by `visualizations/niche_vs_standard.png`; `tests/test_schemas.py` covers job metadata.
- [x] All records have trace IDs and timestamps — Evidence: strict schema metadata in `src/resume_pipeline/schemas.py`; generated artifacts include `trace_id` and `generated_at`.

## Schema Validation

- [x] Pydantic models defined for Resume, JobDescription, and ResumePair — Evidence: `src/resume_pipeline/schemas.py`.
- [x] Validation rules enforced (email format, date ordering, GPA range, etc.) — Evidence: `src/resume_pipeline/schemas.py` and `tests/test_schemas.py`.
- [x] Validation success rate > 90% — Evidence: 342 / 350 = 97.71% in `data/summary/pipeline_summary_20260713_121633.json`.
- [x] Error categorization by type (missing fields, type mismatches, format violations, logical inconsistencies) — Evidence: `src/resume_pipeline/validate.py`; final run records five `format_violation` errors in `data/validated/schema_failure_modes_20260713_105520.json`.
- [x] Valid and invalid records saved separately with proper filenames — Evidence: `data/validated/validated_data_20260713_105520.json` and `data/validated/invalid_20260713_105520.jsonl`.

## Failure Labeling

- [x] All 6 failure metrics calculated for every pair (skills overlap, experience mismatch, seniority mismatch, missing core skills, hallucination, awkward language) — Evidence: all 300 pairs were labeled in `data/analysis/failure_labels_20260713_121624.jsonl`.
- [x] Skill normalization implemented (lowercase, version removal, suffix stripping) — Evidence: `src/resume_pipeline/normalize.py` and `tests/test_normalize.py`.
- [x] Jaccard similarity correctly calculated and spot-checked on 10+ pairs — Evidence: [`SPOT_CHECK.md`](SPOT_CHECK.md) contains 10 pair reviews; `tests/test_labeler.py` covers label calculations.
- [x] Hallucination detection covers entry-level overclaiming, excessive expert ratings, impossible timelines — Evidence: `has_impossible_timeline()` in `src/resume_pipeline/labeler.py` and timeline regression tests in `tests/test_labeler.py`.
- [x] Awkward language detection catches buzzword density and repetitive patterns — Evidence: `src/resume_pipeline/labeler.py`, `tests/test_labeler.py`, and 59.87% final flag rate in `pipeline_summary_20260712_164933.json`.

## Correction Loop

- [x] Correction prompt includes specific Pydantic error messages — Evidence: `src/resume_pipeline/prompts.py` and `src/resume_pipeline/correct.py`.
- [x] Maximum 3 retry attempts per record — Evidence: `src/resume_pipeline/correct.py` and `tests/test_correct.py`.
- [x] Correction success rate > 50% — Evidence: 8 / 8 (100%) in `data/corrected/correction_stats_20260713_121612.json`.
- [x] Statistics tracked (attempts per success, failure reasons) — Evidence: `data/corrected/correction_stats_20260712_164928.json` and `src/resume_pipeline/correct.py`.

## LLM-as-Judge

- [x] Evaluates hallucinations, awkward language, fit assessment, red flags — Evidence: `src/resume_pipeline/judge.py` and judge prompt/schema in `src/resume_pipeline/prompts.py`.
- [x] Structured output with scores and explanations — Evidence: `JudgeVerdict` in `src/resume_pipeline/judge.py` and the structured prompt in `src/resume_pipeline/prompts.py`.
- [x] Optional (can be enabled/disabled per request) — Evidence: `use_llm_judge` request field in `src/resume_pipeline/api.py`; `tests/test_api.py`.

## API

- [x] POST /review-resume responds in < 2s (without judge), < 10s (with judge) — Evidence: 0.001869 s without judge and 4.421121 s with OpenAI `gpt-5.4-mini`, both 200; [`SELF_EVALUATION.md`](SELF_EVALUATION.md).
- [x] GET /health returns health status — Evidence: `src/resume_pipeline/api.py`; measured 0.005166 s (200); `tests/test_api.py`.
- [x] GET /analysis/failure-rates returns aggregate statistics — Evidence: `src/resume_pipeline/api.py`; measured 0.026355 s (200); `tests/test_api.py`.
- [x] All endpoints return valid JSON with proper error handling — Evidence: FastAPI response models in `src/resume_pipeline/api.py`; API tests.
- [x] Edge cases handled (empty skills, missing fields, malformed input) — Evidence: empty-skills and missing-field requests returned JSON `422` responses, not 500s; `tests/test_api.py`. FastAPI parses malformed JSON as `422`.

## Visualizations

- [x] Failure mode correlation matrix (heatmap) — Evidence: `visualizations/failure_correlation_matrix.png`.
- [x] Failure rates by fit level (grouped bar chart) — Evidence: `visualizations/failure_rates_by_fit_level.png`.
- [x] Failure rates by template (grouped bar chart) — Evidence: `visualizations/failure_rates_by_template.png`.
- [x] Niche vs standard roles (side-by-side bar chart) — Evidence: `visualizations/niche_vs_standard.png`.
- [x] Schema validation heatmap — Evidence: `visualizations/schema_validation_heatmap.png`.
- [x] Hallucination by seniority (stacked bar chart) — Evidence: `visualizations/hallucination_by_seniority.png`.
- [x] All charts saved as PNG with Matplotlib, Seaborn, or Plotly — Evidence: six PNGs in `visualizations/`; rendering code in `src/resume_pipeline/visualize.py`.

## Iteration Logs and Traceability

- [x] Every threshold or weight change documented with reason, before/after metrics, and delta — Evidence: [`ITERATION_LOG.md`](ITERATION_LOG.md).
- [x] At least 3 iteration log entries showing experimentation — Evidence: three entries in [`ITERATION_LOG.md`](ITERATION_LOG.md).
- [x] Final configuration decisions traceable to specific iteration log entries — Evidence: prompt and output-budget decisions are linked to their before/after metrics in [`ITERATION_LOG.md`](ITERATION_LOG.md).

## Testing and Documentation

- [x] Pipeline runs end-to-end without crashes — Evidence: the clean `run_all.py` run reached visualization and recorded its completed stage timings.
- [x] Output files saved with timestamps (resumes, jobs, pairs, labels, summaries) — Evidence: `data/generated/*_20260713_111635.*`, `data/analysis/failure_labels_20260713_121624.jsonl`, and `data/summary/pipeline_summary_20260713_121633.json`.
- [x] Pipeline summary JSON includes total records, validation rate, failure distribution, correction rate, timing — Evidence: `data/summary/pipeline_summary_20260713_121633.json` includes populated timings for all six stages.
- [x] You can explain why any given resume was labeled with specific failure modes — Evidence: [`SELF_EVALUATION.md`](SELF_EVALUATION.md), [`SPOT_CHECK.md`](SPOT_CHECK.md), and labeled pair records with trace IDs.
