"""Stage 2: strict validation and error categorization."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from .paths import latest, stage_dir, timestamp
from .schemas import JobDescription, Resume

_MISSING = {"missing"}
_TYPE = {
    "int_type",
    "float_type",
    "string_type",
    "list_type",
    "dict_type",
    "bool_type",
    "int_parsing",
    "float_parsing",
    "model_type",
}
_FORMAT = {
    "value_error",
    "string_pattern_mismatch",
    "date_from_datetime_parsing",
    "date_parsing",
    "datetime_parsing",
    "string_too_short",
    "greater_than_equal",
    "less_than_equal",
    "too_short",
    "enum",
    "literal_error",
}


def categorize_error(error: dict[str, Any]) -> str:
    """Map Pydantic's error details to the four required failure categories."""
    error_type = error["type"]
    message = str(error.get("msg", "")).lower()
    if error_type in _MISSING:
        return "missing_field"
    if "end_date must be after start_date" in message:
        return "logical_inconsistency"
    if error_type in _TYPE:
        return "type_mismatch"
    if error_type in _FORMAT:
        return "format_violation"
    return "format_violation"


def validate_records(
    records: list[dict[str, Any]], model: type[BaseModel]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return strict-model-valid records and structured details for invalid records."""
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for record in records:
        try:
            valid.append(model.model_validate(record).model_dump(mode="json"))
        except ValidationError as error:
            invalid.append(
                {
                    "record": record,
                    "errors": [
                        {
                            "field": ".".join(str(part) for part in detail["loc"]),
                            "category": categorize_error(detail),
                            "message": detail["msg"],
                        }
                        for detail in error.errors()
                    ],
                }
            )
    return valid, invalid


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open() as artifact:
        return [json.loads(line) for line in artifact if line.strip()]


def _generated_artifact(record_type: str, generated_timestamp: str | None) -> Path:
    if generated_timestamp is None:
        return latest("generated", record_type)
    path = stage_dir("generated") / f"{record_type}_{generated_timestamp}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"generated artifact not found: {path}")
    return path


def run(generated_timestamp: str | None = None) -> str:
    """Validate one generation run and write timestamped validation artifacts."""
    artifact_timestamp = timestamp()
    output_dir = stage_dir("validated")
    results: dict[str, Any] = {}
    failure_modes: dict[str, Any] = {
        "by_category": Counter(),
        "by_field": Counter(),
        "field_by_category": defaultdict(Counter),
    }
    all_invalid: list[dict[str, Any]] = []

    for record_type, model in (("resumes", Resume), ("jobs", JobDescription)):
        records = _read_jsonl(_generated_artifact(record_type, generated_timestamp))
        valid, invalid = validate_records(records, model)
        results[record_type] = {
            "total": len(records),
            "valid": len(valid),
            "rate": round(len(valid) / max(1, len(records)), 4),
            "records": valid,
        }
        for item in invalid:
            item["record_type"] = record_type
            all_invalid.append(item)
            for error in item["errors"]:
                failure_modes["by_category"][error["category"]] += 1
                failure_modes["by_field"][error["field"]] += 1
                failure_modes["field_by_category"][error["field"]][
                    error["category"]
                ] += 1

    with (output_dir / f"validated_data_{artifact_timestamp}.json").open("w") as output:
        json.dump(results, output, indent=2)
    with (output_dir / f"invalid_{artifact_timestamp}.jsonl").open("w") as output:
        for item in all_invalid:
            output.write(json.dumps(item) + "\n")
    with (output_dir / f"schema_failure_modes_{artifact_timestamp}.json").open(
        "w"
    ) as output:
        json.dump(
            {
                "by_category": dict(failure_modes["by_category"]),
                "by_field": dict(failure_modes["by_field"]),
                "field_by_category": {
                    field: dict(categories)
                    for field, categories in failure_modes["field_by_category"].items()
                },
            },
            output,
            indent=2,
        )

    for record_type in ("resumes", "jobs"):
        result = results[record_type]
        print(
            f"{record_type}: {result['valid']}/{result['total']} valid "
            f"({result['rate']:.0%})"
        )
    return artifact_timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generated-timestamp",
        help="Validate this matching jobs/resumes generation timestamp instead of latest files.",
    )
    arguments = parser.parse_args()
    run(arguments.generated_timestamp)
