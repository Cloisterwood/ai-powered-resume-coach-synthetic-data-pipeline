# Self-Evaluation

This evaluation uses the final production artifacts: generation `20260713_111635`, validation `20260713_115120`, correction `20260713_121612`, labeling `20260713_121624`, and summary `20260713_121633`.

> **Assignment-text note:** Step 6 says “six self-evaluation questions,” but the supplied webpage lists five. This document answers every question that appears on the page and does not invent a sixth question.

## 1. Can you explain why a “poor fit” resume was labeled as such?

Yes. The label is traceable to the individual metrics, normalized skill comparison, and source records. For example, `pair-1bf64d85` has Jaccard similarity **0.3000** and `missing_core_skills=True`; its operations/account-management background provides limited nursing evidence. `pair-c13ce446` has Jaccard **0.2222** and lacks the principal settlement-system requirements for its cryptography job. Both were manually reviewed and agreed with the pipeline label in [`SPOT_CHECK.md`](SPOT_CHECK.md).

The explanation is not merely the controlled fit-level metadata: `labeler.py` calculates skills overlap, experience mismatch, seniority mismatch, missing core skills, hallucinated skills, and awkward language from the actual pair content. A reviewer can follow a pair ID into `data/analysis/failure_labels_20260712_164933.jsonl` and its generated source records through `trace_id`.

## 2. Do your visualizations reveal non-obvious patterns (for example, template bias or niche role challenges)?

Yes, with limits. [`failure_rates_by_fit_level.png`](../visualizations/failure_rates_by_fit_level.png) shows the intended degradation pattern: weaker controlled fits have more missing-core-skill and low-overlap flags. [`niche_vs_standard.png`](../visualizations/niche_vs_standard.png) shows that niche roles have higher missing-core-skill, awkward-language, and low-overlap rates than standard roles in this run. [`failure_rates_by_template.png`](../visualizations/failure_rates_by_template.png) and [`failure_correlation_matrix.png`](../visualizations/failure_correlation_matrix.png) make template-level differences and co-occurring labels inspectable.

The schema heatmap is a useful counterexample to overclaiming: the final run contains only four type mismatches, one each for `contact`, `education`, `experience`, and `skills`. Its uniform color correctly represents four equal counts of one, but it is not a rich pattern. It is retained as [`schema_validation_heatmap.png`](../visualizations/schema_validation_heatmap.png) rather than presented as a headline chart.

## 3. Does the correction loop actually improve data quality, or does it just mask errors?

Yes. The final production correction loop repaired **8/8** invalid date-format records (100%). The original invalid records, corrected records, and statistics remain in separate timestamped artifacts, so the improvement is auditable rather than hidden. The final strict-validation rate was **342/350 (97.71%)** before correction and all 300 pairs were then available for labeling.

## 4. Can the API handle edge cases (empty skills, missing fields, malformed JSON)?

Yes for validation and error handling. The API returns valid JSON and uses FastAPI’s `422` validation responses for empty-skills and missing-required-field payloads, rather than producing server errors. The test suite covers health, no-judge review, invalid request handling, and failure-rate behavior in [`tests/test_api.py`](../tests/test_api.py).

Malformed JSON is handled by FastAPI request parsing as a `422` JSON error response; it was not separately included in the six timed rows below. The measured edge-case responses had no 500 error.

## 5. Are failure modes distributed as expected across fit levels?

Yes. The final run contains **100 excellent** and **50 each** of good, partial, poor, and mismatch pairs. Missing core skills (66.00%), awkward language (56.00%), and low skill overlap (32.00%) are the prevalent labels; the fit-level chart shows failure pressure increasing toward poor and mismatch. The refreshed ten-pair review agreed with the labels on **10/10** samples.

## API performance measurements

Measurements were taken against the final production dataset on 2026-07-13. Times are wall-clock request durations.

| Endpoint | Payload | Time | Status | Result |
| --- | --- | ---: | ---: | --- |
| `GET /health` | N/A | 0.004642 s | 200 | Passed |
| `POST /review-resume` | Full pair, no judge | 0.001869 s | 200 | Passed; under 2 s target |
| `POST /review-resume` | Full pair, LLM judge | 4.421121 s | 200 | Passed; under 10 s target |
| `POST /review-resume` | Empty skills | 0.002552 s | 422 | Valid error response; no server error |
| `POST /review-resume` | Missing required fields | 0.001861 s | 422 | Valid error response; no server error |
| `GET /analysis/failure-rates` | N/A | 0.020865 s | 200 | Passed |

## Overall assessment

The pipeline meets the production-volume, traceability, strict-validation, correction, labeling, visualization, and API-latency goals. The final clean `run_all.py` invocation completed all stages and recorded populated timing values; the deterministic literal-null normalization repaired the remaining provider placeholders so all 300 pairs were labeled.
