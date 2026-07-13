"""Render all six required PNG charts from the labeled pipeline artifacts."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .analyze import FLAG_COLS, load_labels
from .paths import VIZ, latest

ALL_FLAGS = FLAG_COLS + ["low_skills_overlap"]
FIT_ORDER = ["excellent", "good", "partial", "poor", "mismatch"]
SENIORITY_NAMES = {0: "Entry", 1: "Mid", 2: "Senior", 3: "Lead", 4: "Executive"}


def _save(figure, filename: str) -> None:
    VIZ.mkdir(exist_ok=True)
    figure.tight_layout()
    figure.savefig(VIZ / filename, dpi=150)
    plt.close(figure)
    print(f"wrote visualizations/{filename}")


def _style_axis(
    axis, *, threshold: float | None = None, label: str | None = None
) -> None:
    """Apply consistent chart references without adding grids to heatmaps."""
    is_heatmap = bool(axis.images or axis.collections)
    if not is_heatmap:
        axis.grid(axis="y", alpha=0.4)
    if threshold is not None:
        axis.axhline(threshold, color="red", linestyle="--", linewidth=1)
    if label and is_heatmap:
        axis.set_title(f"{axis.get_title()}\n{label}", fontsize=11)
    elif label:
        axis.text(
            0.01,
            0.98,
            label,
            transform=axis.transAxes,
            va="top",
            color="red" if threshold is not None else "#444444",
            fontsize=8,
        )


def correlation_matrix(dataframe: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(9, 7))
    correlation = dataframe[ALL_FLAGS].astype(float).corr().fillna(0.0)
    sns.heatmap(
        correlation,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
        ax=axis,
        linewidths=0.5,
    )
    axis.set_title("Failure Mode Correlation Matrix (which failures co-occur?)")
    _style_axis(axis, label="Color midpoint: 0 = no correlation")
    _save(figure, "failure_correlation_matrix.png")


def rates_by(
    dataframe: pd.DataFrame,
    group_column: str,
    title: str,
    filename: str,
    order: list[str] | None = None,
) -> None:
    rates = dataframe.groupby(group_column)[ALL_FLAGS].mean()
    if order:
        rates = rates.reindex(order).dropna(how="all")
    figure, axis = plt.subplots(figsize=(11, 6))
    rates.plot.bar(ax=axis, colormap="viridis", width=0.8)
    axis.set_title(title)
    axis.set_ylabel("Failure rate")
    axis.set_xlabel(group_column.replace("_", " ").title())
    axis.set_ylim(0, 1)
    axis.legend(title="Failure mode", bbox_to_anchor=(1.02, 1), loc="upper left")
    _style_axis(axis, threshold=0.5, label="50% reference")
    _save(figure, filename)


def niche_vs_standard(dataframe: pd.DataFrame) -> None:
    rates = dataframe.groupby("is_niche_role")[ALL_FLAGS].mean().T
    rates = rates.reindex(columns=[False, True], fill_value=0)
    rates.columns = ["Standard", "Niche"]
    figure, axis = plt.subplots(figsize=(10, 6))
    rates.plot.bar(ax=axis, color=["#4c72b0", "#dd8452"], width=0.75)
    axis.set_title("Failure Rates: Niche vs Standard Roles")
    axis.set_ylabel("Failure rate")
    axis.set_xlabel("Failure mode")
    axis.set_ylim(0, 1)
    _style_axis(axis)
    axis.legend(title="Role type")
    axis.tick_params(axis="x", rotation=30)
    _save(figure, "niche_vs_standard.png")


def schema_heatmap() -> None:
    with latest("validated", "schema_failure_modes_").open() as input_file:
        modes = json.load(input_file)
    field_by_category = modes["field_by_category"]
    if not field_by_category:
        field_by_category = {"(no validation failures)": {"missing_field": 0}}
    matrix = pd.DataFrame(field_by_category).T.fillna(0)
    top = (
        matrix.assign(total=matrix.sum(axis=1))
        .nlargest(15, "total")
        .drop(columns="total")
    )
    figure, axis = plt.subplots(figsize=(9, max(4, 0.4 * len(top))))
    sns.heatmap(top, annot=True, fmt=".0f", cmap="YlOrRd", ax=axis, linewidths=0.5)
    axis.set_title("Schema Validation Failures: Field × Error Category (top 15 fields)")
    axis.set_xlabel("Error category")
    axis.set_ylabel("Field")
    _style_axis(axis, label="Target: 0 validation failures")
    _save(figure, "schema_validation_heatmap.png")


def hallucination_by_seniority(dataframe: pd.DataFrame) -> None:
    copy = dataframe.copy()
    copy["seniority"] = copy["resume_seniority"].map(SENIORITY_NAMES)
    counts = (
        copy.groupby(["seniority", "hallucinated_skills"])
        .size()
        .unstack(fill_value=0)
        .reindex(list(SENIORITY_NAMES.values()), fill_value=0)
        .reindex(columns=[False, True], fill_value=0)
    )
    counts.columns = ["Clean", "Hallucinated"]
    figure, axis = plt.subplots(figsize=(9, 6))
    counts.plot.bar(stacked=True, ax=axis, color=["#55a868", "#c44e52"])
    axis.set_title("Hallucination Flags by Resume Seniority (stacked counts)")
    axis.set_ylabel("Number of pairs")
    axis.set_xlabel("Resume seniority")
    axis.legend(title="Hallucination flag")
    _style_axis(axis, threshold=0, label="Target: 0 hallucinations")
    _save(figure, "hallucination_by_seniority.png")


def run() -> None:
    dataframe = load_labels()
    correlation_matrix(dataframe)
    rates_by(
        dataframe,
        "fit_level",
        "Failure Rates by Fit Level",
        "failure_rates_by_fit_level.png",
        order=FIT_ORDER,
    )
    rates_by(
        dataframe,
        "prompt_template",
        "Failure Rates by Prompt Template",
        "failure_rates_by_template.png",
    )
    niche_vs_standard(dataframe)
    schema_heatmap()
    hallucination_by_seniority(dataframe)


if __name__ == "__main__":
    run()
