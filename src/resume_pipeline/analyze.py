"""Stage 5: aggregate failure statistics and write the pipeline summary."""

import json
from typing import Any

import pandas as pd

from .paths import latest, stage_dir, timestamp

FLAG_COLS = [
    "experience_mismatch",
    "seniority_mismatch",
    "missing_core_skills",
    "hallucinated_skills",
    "awkward_language",
]
JACCARD_FLAG_THRESHOLD = 0.3


def load_labels() -> pd.DataFrame:
    """Load the latest failure labels and derive the low-overlap flag."""
    dataframe = pd.read_json(latest("analysis", "failure_labels_"), lines=True)
    dataframe["low_skills_overlap"] = (
        dataframe["skills_overlap"] < JACCARD_FLAG_THRESHOLD
    )
    return dataframe


def failure_rates(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Aggregate overall, segmented, and correlation statistics for all flags."""
    columns = FLAG_COLS + ["low_skills_overlap"]
    return {
        "n_pairs": len(dataframe),
        "overall": {
            column: round(float(dataframe[column].mean()), 4) for column in columns
        },
        "avg_jaccard_by_fit": {
            key: round(float(value), 4)
            for key, value in dataframe.groupby("fit_level")["skills_overlap"]
            .mean()
            .items()
        },
        "by_fit_level": {
            key: {column: round(float(values[column].mean()), 4) for column in columns}
            for key, values in dataframe.groupby("fit_level")
        },
        "by_template": {
            key: {column: round(float(values[column].mean()), 4) for column in columns}
            for key, values in dataframe.groupby("prompt_template")
        },
        "by_niche": {
            str(key): {
                column: round(float(values[column].mean()), 4) for column in columns
            }
            for key, values in dataframe.groupby("is_niche_role")
        },
        "correlation_matrix": dataframe[columns].astype(float).corr().round(3).to_dict(),
    }


def run(stage_timings: dict[str, float] | None = None) -> str:
    """Write failure statistics and the turn-in pipeline summary artifacts."""
    artifact_timestamp = timestamp()
    dataframe = load_labels()
    stats = failure_rates(dataframe)
    analysis_dir = stage_dir("analysis")
    with (analysis_dir / f"failure_stats_{artifact_timestamp}.json").open("w") as output:
        json.dump(stats, output, indent=2)

    with latest("validated", "validated_data_").open() as input_file:
        validated = json.load(input_file)
    with latest("validated", "schema_failure_modes_").open() as input_file:
        failure_modes = json.load(input_file)
    try:
        with latest("corrected", "correction_stats_").open() as input_file:
            correction = json.load(input_file)
    except FileNotFoundError:
        correction = None

    total = sum(validated[kind]["total"] for kind in ("resumes", "jobs"))
    valid = sum(validated[kind]["valid"] for kind in ("resumes", "jobs"))
    summary = {
        "generated": {
            "jobs": validated["jobs"]["total"],
            "resumes": validated["resumes"]["total"],
            "pairs": int(stats["n_pairs"]),
        },
        "validation": {
            "total_records": total,
            "valid_records": valid,
            "success_rate": round(valid / max(1, total), 4),
            "error_categories": failure_modes["by_category"],
        },
        "failure_mode_distribution": stats["overall"],
        "correction": correction,
        "fit_level_counts": dataframe["fit_level"].value_counts().to_dict(),
        "template_counts": dataframe["prompt_template"].value_counts().to_dict(),
        "stage_timings_seconds": stage_timings,
        "timestamp": artifact_timestamp,
    }
    with (stage_dir("summary") / f"pipeline_summary_{artifact_timestamp}.json").open(
        "w"
    ) as output:
        json.dump(summary, output, indent=2)
    print(json.dumps(summary["validation"], indent=2))
    print("fit level counts:", summary["fit_level_counts"])
    return artifact_timestamp


if __name__ == "__main__":
    run()
