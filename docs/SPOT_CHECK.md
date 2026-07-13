# Manual Spot-Check (10 pairs)

Balanced sample from `failure_labels_20260713_121624.jsonl`: two pairs from each
fit level. The metric columns are pipeline labels; the last two columns record
the manual review against the associated generated job and resume.

| Pair ID | Fit Level | Jaccard | Exp Mismatch | Seniority Mismatch | Missing Core | Hallucination | Awkward Lang | Manual Agrees? | Notes |
| ------- | --------- | ------- | ------------ | ------------------ | ------------ | ------------- | ------------ | -------------- | ----- |
| pair-8f4dd99d | excellent | 0.8750 | False | False | False | False | True | Yes | High overlap and no structural fit flags support excellent fit; wording supports the awkward-language flag. |
| pair-d087732f | excellent | 0.8571 | False | False | False | False | False | Yes | High overlap with no failure flags supports excellent fit. |
| pair-9efa1832 | good | 0.5000 | False | False | True | False | False | Yes | Moderate overlap with a missing core skill supports good rather than excellent fit. |
| pair-dd7a7bd1 | good | 0.5556 | False | True | True | False | True | Yes | Good overlap offset by seniority, missing-core, and language flags. |
| pair-eb4af89c | partial | 0.5000 | False | False | True | False | True | Yes | Partial skill coverage with missing-core and language flags is consistent with the label. |
| pair-c525d311 | partial | 0.5000 | True | False | True | False | True | Yes | Partial overlap plus experience, core-skill, and language flags supports partial fit. |
| pair-35a2bf14 | poor | 0.3000 | False | True | True | False | True | Yes | Low overlap and multiple fit flags support poor fit. |
| pair-308a93e8 | poor | 0.2000 | False | False | True | False | False | Yes | Low overlap and missing core skills support poor fit. |
| pair-7cac295d | mismatch | 0.0000 | False | False | True | False | False | Yes | No skill overlap and missing core skills support mismatch. |
| pair-a7c30eeb | mismatch | 0.1111 | True | False | True | False | False | Yes | Near-zero overlap plus experience and core-skill flags support mismatch. |
