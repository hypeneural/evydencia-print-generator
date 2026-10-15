"""Read-only compatibility gate: official pyproject bounds, never user's secrets."""
from scripts.audit_win11_print_generator_runtime import (
    matches_numeric_spec,
    required_version_spec,
)


def test_runtime_version_boundaries_for_python_and_pillow():
    assert matches_numeric_spec("3.13.1", ">=3.12,<3.14")
    assert not matches_numeric_spec("3.14.0", ">=3.12,<3.14")
    assert matches_numeric_spec("12.3.0", ">=12.3,<13")
    assert not matches_numeric_spec("11.1.0", ">=12.3,<13")
    assert not matches_numeric_spec("13.0.0", ">=12.3,<13")
    assert not matches_numeric_spec("12.3.0rc1", ">=12.3,<13")


def test_runtime_dependency_specs_are_extracted_without_markers():
    requirements = [
        "Pillow>=12.3,<13",
        "pywebview>=6.2.1,<7; sys_platform == 'win32'",
    ]
    assert required_version_spec(requirements, "Pillow") == ">=12.3,<13"
    assert required_version_spec(requirements, "pywebview") == ">=6.2.1,<7"
    assert required_version_spec(requirements, "MissingPackage") == ""
