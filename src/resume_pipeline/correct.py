"""Stage 3: correct invalid records with Pydantic feedback, up to three attempts."""

import json
from collections import Counter
from typing import Any, Callable

from .llm_client import generate
from .loose_schemas import LooseJob, LooseResume
from .paths import latest, stage_dir, timestamp
from .prompts import CORRECTION_PROMPT, CORRECTION_SYSTEM
from .schemas import JobDescription, Resume
from .validate import validate_records

MAX_ATTEMPTS = 3
_STRICT = {"resumes": Resume, "jobs": JobDescription}
_LOOSE = {"resumes": LooseResume, "jobs": LooseJob}
_PRESERVE = "metadata"
_RESUME_CORE_FIELDS = ("contact", "education", "experience", "skills")


def _is_all_null_resume(record_type: str, record: dict[str, Any]) -> bool:
    """Identify a resume whose required structural sections are all absent."""
    return record_type == "resumes" and all(
        record.get(field) is None for field in _RESUME_CORE_FIELDS
    )


def _normalize_null_placeholders(value: Any) -> Any:
    """Convert an LLM's literal JSON-null placeholder to a Python null."""
    if isinstance(value, str) and value.strip().lower() == "null":
        return None
    if isinstance(value, list):
        return [_normalize_null_placeholders(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_null_placeholders(item) for key, item in value.items()}
    return value


def correct_record(
    invalid: dict[str, Any], llm: Callable[..., Any] = generate
) -> dict[str, Any]:
    """Attempt to correct one invalid record, preserving its pipeline metadata."""
    record_type = invalid["record_type"]
    record = invalid["record"]
    metadata = record.get(_PRESERVE)
    current = _normalize_null_placeholders(record)
    current_errors = invalid["errors"]
    started_all_null = _is_all_null_resume(record_type, record)
    all_null_guidance = ""
    if started_all_null:
        all_null_guidance = """ALL CORE RESUME FIELDS ARE MISSING.
Return a complete replacement resume with a non-null contact object, at least one
education item, at least one experience item, and at least one skill. Preserve the
candidate's intended fit level and writing style where the original metadata allows it."""

    valid, still_invalid = validate_records([current], _STRICT[record_type])
    if valid:
        return {
            "success": True,
            "attempts": 0,
            "corrected": valid[0],
            "final_errors": [],
            "started_all_null": started_all_null,
        }
    current_errors = still_invalid[0]["errors"]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        error_details = "\n".join(
            f"- {error['field']}: {error['message']} ({error['category']})"
            for error in current_errors
        )
        body = {key: value for key, value in current.items() if key != _PRESERVE}
        proposal = llm(
            _LOOSE[record_type],
            CORRECTION_SYSTEM,
            CORRECTION_PROMPT.format(
                record_type=record_type[:-1],
                error_details=error_details,
                original_data=json.dumps(body, default=str),
                all_null_guidance=all_null_guidance,
            ),
            temperature=0.2,
            tier="low_skill",
        )
        candidate = proposal.model_dump()
        if metadata is not None:
            candidate[_PRESERVE] = metadata

        valid, still_invalid = validate_records([candidate], _STRICT[record_type])
        if valid:
            return {
                "success": True,
                "attempts": attempt,
                "corrected": valid[0],
                "final_errors": [],
                "started_all_null": started_all_null,
            }
        current = candidate
        current_errors = still_invalid[0]["errors"]

    return {
        "success": False,
        "attempts": MAX_ATTEMPTS,
        "corrected": None,
        "final_errors": current_errors,
        "started_all_null": started_all_null,
    }


def run(validated_timestamp: str | None = None) -> str:
    """Correct invalid records from one validation run and write artifacts."""
    artifact_timestamp = timestamp()
    output_dir = stage_dir("corrected")
    invalid_path = latest("validated", "invalid_")
    if validated_timestamp is not None:
        invalid_path = stage_dir("validated") / f"invalid_{validated_timestamp}.jsonl"
        if not invalid_path.exists():
            raise FileNotFoundError(f"validation artifact not found: {invalid_path}")
    with invalid_path.open() as input_file:
        invalids = [json.loads(line) for line in input_file if line.strip()]

    stats: dict[str, Any] = {
        "total": len(invalids),
        "corrected": 0,
        "failed": 0,
        "attempts_histogram": Counter(),
        "failure_reasons": Counter(),
    }
    with (output_dir / f"corrected_{artifact_timestamp}.jsonl").open("w") as output:
        for index, invalid in enumerate(invalids, start=1):
            result = correct_record(invalid)
            if result["success"]:
                stats["corrected"] += 1
                stats["attempts_histogram"][result["attempts"]] += 1
                output.write(
                    json.dumps(
                        {
                            "record_type": invalid["record_type"],
                            "attempts": result["attempts"],
                            "record": result["corrected"],
                        }
                    )
                    + "\n"
                )
            else:
                stats["failed"] += 1
                if result["started_all_null"]:
                    stats["failure_reasons"]["all_null_record"] += 1
                for error in result["final_errors"]:
                    stats["failure_reasons"][error["category"]] += 1
            status = "ok" if result["success"] else "FAILED"
            print(f"[{index}/{len(invalids)}] {status} in {result['attempts']} attempt(s)")

    stats["success_rate"] = round(stats["corrected"] / max(1, stats["total"]), 4)
    stats["attempts_histogram"] = dict(stats["attempts_histogram"])
    stats["failure_reasons"] = dict(stats["failure_reasons"])
    with (output_dir / f"correction_stats_{artifact_timestamp}.json").open("w") as output:
        json.dump(stats, output, indent=2)
    print(f"correction success rate: {stats['success_rate']:.0%} (target > 50%)")
    return artifact_timestamp


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--validated-timestamp")
    arguments = parser.parse_args()
    run(arguments.validated_timestamp)
