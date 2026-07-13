from resume_pipeline.normalize import jaccard, normalize_set, normalize_skill


def test_lowercase():
    assert normalize_skill("Python") == "python"


def test_version_stripped():
    assert normalize_skill("Python 3.10") == "python"
    assert normalize_skill("Java 17") == "java"
    assert normalize_skill("Vue3") == "vue"


def test_suffix_stripped():
    assert normalize_skill("React.js") == "react"
    assert normalize_skill("python developer") == "python"
    assert normalize_skill("Data Engineer") == "data"
    assert normalize_skill("Node.JS") == "node"


def test_whitespace_and_punct():
    assert normalize_skill("  PostgreSQL  ") == "postgresql"


def test_normalize_set_dedupes():
    assert normalize_set(["Python", "python 3.10", "PYTHON"]) == {"python"}


def test_jaccard_worked_example():
    """Specification example: two shared skills in a six-skill union."""
    first = normalize_set(["python", "javascript", "react", "node"])
    second = normalize_set(["python", "javascript", "docker", "kubernetes"])
    assert abs(jaccard(first, second) - 2 / 6) < 1e-9


def test_jaccard_empty_sets():
    assert jaccard(set(), set()) == 0.0
    assert jaccard({"python"}, set()) == 0.0
