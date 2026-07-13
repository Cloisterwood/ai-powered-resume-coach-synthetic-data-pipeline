# Iteration Log — AI-Powered Resume Coach: Synthetic Data Pipeline

Every configuration or threshold change is recorded here (spec format).

| Date | Component | Change | Reason | Before Metric | After Metric | Delta | Keep/Revert |
| ---- | --------- | ------ | ------ | ------------- | ------------ | ----- | ----------- |
| 2026-07-12 | Pipeline | Baseline production run (`20260712_150547`) | Establish volume, diversity, validation, and correction metrics on 50 jobs × 6 resumes. | N/A | 50 jobs, 300 pairs; initial strict validation 106/350 (30.29%); correction 244/244 (100%). | Baseline | Keep |
| 2026-07-12 | Generation | Raised resume output cap from 2,000 to 4,096 tokens | A niche Executive/career-changer resume exceeded 2,000 tokens and stopped a production run after 19 jobs / 114 resumes. | 19 jobs / 114 resumes before `IncompleteOutputException`. | Completed 50 jobs / 300 resumes without token-limit failure (`20260712_150547`). | +31 jobs, +186 resumes; completed run. | Keep |
| 2026-07-13 | Prompts | Explicitly required `contact.name`, `company.size`, `company.location`, and ISO dates | Baseline failures were dominated by missing contact and company fields. | Initial validation 106/350 (30.29%); 196 missing `contact.name`, 83 missing company fields. | 349/350 initial strict-valid records (99.71%) on `20260712_164928`. | +69.42 percentage points. | Keep |
| 2026-07-13 | OpenAI adapter | Use `max_completion_tokens`, omit temperature, and set low-skill reasoning effort to `none` for GPT-5 chat completions | OpenAI rejected the previous GPT-5 parameter combination during correction. | Full run stopped after 295/300 resumes validated, with a 400 from the correction request. | Resumed the same run and repaired 5/5 records; judge latency was 4.421 s. | Completion rate from stopped to 300/300 labeled; judge met the 10 s target. | Keep |
