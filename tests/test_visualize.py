import json

import pandas as pd

from resume_pipeline import visualize


EXPECTED_CHARTS = {
    "failure_correlation_matrix.png",
    "failure_rates_by_fit_level.png",
    "failure_rates_by_template.png",
    "niche_vs_standard.png",
    "schema_validation_heatmap.png",
    "hallucination_by_seniority.png",
}


def test_all_visualizations_render_nonempty_pngs(monkeypatch, tmp_path):
    dataframe = pd.DataFrame(
        [
            {
                "skills_overlap": 0.9,
                "experience_mismatch": False,
                "seniority_mismatch": False,
                "missing_core_skills": False,
                "hallucinated_skills": False,
                "awkward_language": False,
                "low_skills_overlap": False,
                "fit_level": "excellent",
                "prompt_template": "formal",
                "is_niche_role": False,
                "resume_seniority": 0,
            },
            {
                "skills_overlap": 0.1,
                "experience_mismatch": True,
                "seniority_mismatch": True,
                "missing_core_skills": True,
                "hallucinated_skills": True,
                "awkward_language": True,
                "low_skills_overlap": True,
                "fit_level": "mismatch",
                "prompt_template": "career_changer",
                "is_niche_role": True,
                "resume_seniority": 4,
            },
        ]
    )
    failures = tmp_path / "schema_failure_modes.json"
    failures.write_text(
        json.dumps(
            {
                "field_by_category": {
                    "contact.email": {"format_violation": 2},
                    "experience": {"type_mismatch": 1},
                }
            }
        )
    )
    monkeypatch.setattr(visualize, "VIZ", tmp_path)
    monkeypatch.setattr(visualize, "latest", lambda *_args: failures)

    visualize.correlation_matrix(dataframe)
    visualize.rates_by(
        dataframe,
        "fit_level",
        "Failure Rates by Fit Level",
        "failure_rates_by_fit_level.png",
        order=visualize.FIT_ORDER,
    )
    visualize.rates_by(
        dataframe,
        "prompt_template",
        "Failure Rates by Prompt Template",
        "failure_rates_by_template.png",
    )
    visualize.niche_vs_standard(dataframe)
    visualize.schema_heatmap()
    visualize.hallucination_by_seniority(dataframe)

    assert {path.name for path in tmp_path.glob("*.png")} == EXPECTED_CHARTS
    assert all((tmp_path / filename).stat().st_size > 0 for filename in EXPECTED_CHARTS)
