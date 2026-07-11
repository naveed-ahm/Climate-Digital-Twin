from pathlib import Path


def test_required_docs_exist():
    root = Path(__file__).resolve().parents[1]
    docs_dir = root / "docs"

    for filename in ["ARCHITECTURE.md", "API_REFERENCE.md", "DEMO_SCRIPT.md"]:
        assert (docs_dir / filename).exists(), f"Missing required documentation: {filename}"
