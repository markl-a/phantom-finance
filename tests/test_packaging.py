from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import phantom_finance


ROOT = Path(__file__).resolve().parents[1]


def _project_metadata() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as fp:
        return tomllib.load(fp)["project"]


def test_pyproject_metadata_matches_public_release_surface() -> None:
    project = _project_metadata()

    assert project["name"] == "phantom-finance"
    assert project["version"] == phantom_finance.__version__
    assert project["license"]["text"] == "Apache-2.0"
    assert project["requires-python"] == ">=3.10"
    assert project["readme"] == "README.md"
    assert project["authors"] == [{"name": "Mark Lai"}]

    classifiers = set(project["classifiers"])
    assert "Development Status :: 3 - Alpha" in classifiers
    assert "License :: OSI Approved :: Apache Software License" in classifiers
    assert "Programming Language :: Python :: 3.10" in classifiers
    assert "Topic :: Office/Business :: Financial :: Accounting" in classifiers

    urls = project["urls"]
    assert urls["Homepage"].endswith("/phantom-finance")
    assert urls["Documentation"].endswith("/phantom-finance/tree/main/docs")
    assert urls["Issues"].endswith("/phantom-finance/issues")
    assert urls["Source"].endswith("/phantom-finance")


def test_optional_dependencies_support_local_and_ci_verification() -> None:
    extras = _project_metadata()["optional-dependencies"]

    assert "pytest>=7" in extras["test"]
    assert "pytest>=7" in extras["dev"]
    assert "ruff>=0.6" in extras["dev"]


def test_cli_entrypoint_target_is_importable() -> None:
    project = _project_metadata()

    assert project["scripts"]["phantom-finance"] == "phantom_finance.cli:main"
    module_name, function_name = project["scripts"]["phantom-finance"].split(":")
    module = importlib.import_module(module_name)
    assert callable(getattr(module, function_name))
