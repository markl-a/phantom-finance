import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Every test gets its own ~/.phantom-mesh — never touch the real one."""
    monkeypatch.setenv("PHANTOM_MESH_HOME", str(tmp_path / "mesh"))
    monkeypatch.setenv("PHANTOM_FINANCE_HOME", str(tmp_path / "finance"))
    return tmp_path
