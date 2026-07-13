from resume_pipeline.schemas import Resume
from resume_pipeline.validate import categorize_error, validate_records


def test_valid_record_passes(sample_resume_dict):
    valid, invalid = validate_records([sample_resume_dict], Resume)
    assert len(valid) == 1
    assert len(invalid) == 0


def test_missing_field_categorized(sample_resume_dict):
    del sample_resume_dict["contact"]["email"]
    _, invalid = validate_records([sample_resume_dict], Resume)
    assert invalid[0]["errors"][0]["category"] == "missing_field"
    assert "email" in invalid[0]["errors"][0]["field"]


def test_format_violation_categorized(sample_resume_dict):
    sample_resume_dict["contact"]["email"] = "nope"
    _, invalid = validate_records([sample_resume_dict], Resume)
    assert invalid[0]["errors"][0]["category"] == "format_violation"


def test_type_mismatch_categorized(sample_resume_dict):
    sample_resume_dict["experience"][0]["responsibilities"] = "not a list"
    _, invalid = validate_records([sample_resume_dict], Resume)
    assert invalid[0]["errors"][0]["category"] == "type_mismatch"


def test_logical_inconsistency_categorized(sample_resume_dict):
    sample_resume_dict["experience"][0]["end_date"] = "2019-01-01"
    _, invalid = validate_records([sample_resume_dict], Resume)
    assert invalid[0]["errors"][0]["category"] == "logical_inconsistency"
