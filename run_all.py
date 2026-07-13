"""End-to-end pipeline: generate, validate, correct, label, analyze, visualize."""

import argparse
import sys
import time

sys.path.insert(0, "src")

from resume_pipeline import analyze, correct, generate, labeler, validate, visualize


def _run_timed(name: str, function, timings: dict[str, float]):
    print(f"\n=== {name} ===")
    started_at = time.time()
    result = function()
    timings[name] = round(time.time() - started_at, 1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=50)
    parser.add_argument("--resumes-per-job", type=int, default=6)
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Run downstream stages on the latest generated artifact set.",
    )
    arguments = parser.parse_args()

    timings: dict[str, float] = {}
    generated_timestamp = None
    if not arguments.skip_generate:
        generated_timestamp = _run_timed(
            "generate",
            lambda: generate.run(arguments.jobs, arguments.resumes_per_job),
            timings,
        )
    validated_timestamp = _run_timed(
        "validate", lambda: validate.run(generated_timestamp), timings
    )
    corrected_timestamp = _run_timed(
        "correct", lambda: correct.run(validated_timestamp), timings
    )
    _run_timed(
        "label",
        lambda: labeler.run(
            generated_timestamp=generated_timestamp,
            validated_timestamp=validated_timestamp,
            corrected_timestamp=corrected_timestamp,
        ),
        timings,
    )
    _run_timed("analyze", lambda: analyze.run(stage_timings=timings), timings)
    _run_timed("visualize", visualize.run, timings)
    print(f"\nstage timings: {timings}")


if __name__ == "__main__":
    main()
