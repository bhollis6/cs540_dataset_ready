from __future__ import annotations

import tempfile
import unittest
import subprocess
from pathlib import Path

from src.harness.python_env import (
    _build_venv_command,
    _ensure_pytest_for_pytest_oracle,
    _extract_conda_create_installs,
    _extract_inline_requirement_files,
    _extract_pip_installs,
    _extract_python_version,
    _extract_workspace_setup_commands,
    _ensure_setuptools_compat_install,
    _filter_workspace_pip_args,
    _append_cflag,
    _append_pip_flags,
    _commit_workspace_setup_changes,
    _requires_legacy_astropy_build,
    _requires_legacy_markupsafe,
    _pylint_astroid_requirement,
    _resolve_local_install_arg,
    _should_use_workspace_pip,
)


class FakeTestSpec:
    def __init__(self, eval_script_list: list[str]) -> None:
        self.eval_script_list = eval_script_list


class PythonEnvTest(unittest.TestCase):
    def test_extract_pip_installs(self) -> None:
        installs = _extract_pip_installs(
            [
                "source /opt/miniconda3/bin/activate",
                "conda activate testbed",
                "python -m pip install py==1.11.0 packaging==23.1",
                "conda activate testbed && python -m pip install -r $HOME/requirements.txt",
                "python -m pip install -e .",
            ]
        )

        self.assertEqual(
            installs,
            [
                ["py==1.11.0", "packaging==23.1"],
                ["-r", "$HOME/requirements.txt"],
                ["-e", "."],
            ],
        )

    def test_extract_inline_requirement_files(self) -> None:
        files = _extract_inline_requirement_files(
            [
                "cat <<'EOF_TEST' > $HOME/requirements.txt\nasgiref\nsqlparse\nEOF_TEST",
            ]
        )

        self.assertEqual(files, {"$HOME/requirements.txt": "asgiref\nsqlparse\n"})

    def test_extract_conda_create_installs(self) -> None:
        installs = _extract_conda_create_installs(
            [
                "conda create -n testbed python=3.9 pytest pytest-cov=5.0 -y",
                "conda create --name other --channel conda-forge python=3.10 numpy=1.26 requests --yes",
                "conda create -n science python=3.9 'numpy==1.19.2' 'pandas<2.0.0' --yes",
                "conda create -n build python=3.9 'cython==3.0.10' --yes",
            ]
        )

        self.assertEqual(
            installs,
            [
                ["pytest", "pytest-cov==5.0"],
                ["numpy<2", "requests"],
                ["numpy<2", "pandas<2.0.0"],
                ["cython==3.0.10"],
            ],
        )

    def test_extract_python_version(self) -> None:
        version = _extract_python_version(
            [
                "source /opt/miniconda3/bin/activate",
                "conda create -n testbed python=3.9  -y",
                "conda activate testbed",
            ]
        )

        self.assertEqual(version, "3.9")

    def test_extract_workspace_setup_commands(self) -> None:
        commands = _extract_workspace_setup_commands(
            [
                "source /opt/miniconda3/bin/activate",
                "sed -i 's/requires = \\[\"setuptools\",/requires = \\[\"setuptools==68.0.0\",/' pyproject.toml",
                "python -m pip install -e .[test] --verbose",
            ]
        )

        self.assertEqual(
            commands,
            ["sed -i 's/requires = \\[\"setuptools\",/requires = \\[\"setuptools==68.0.0\",/' pyproject.toml"],
        )

    def test_build_venv_command_clears_existing_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / ".pilot-venv"
            venv_dir.mkdir()

            command = _build_venv_command(venv_dir, "3.9")

            self.assertEqual(command, ["uv", "venv", "--seed", str(venv_dir), "--clear", "--python", "3.9"])

    def test_resolve_local_install_arg_maps_workspace_relative_paths(self) -> None:
        workspace = Path("/tmp/example-workspace")

        self.assertEqual(_resolve_local_install_arg(".", workspace), str(workspace))
        self.assertEqual(
            _resolve_local_install_arg("./requirements.txt", workspace),
            str(workspace / "requirements.txt"),
        )
        self.assertEqual(_resolve_local_install_arg(".[test]", workspace), f"{workspace}[test]")
        self.assertEqual(_resolve_local_install_arg("pytest", workspace), "pytest")

    def test_should_use_workspace_pip_detects_local_workspace_install(self) -> None:
        workspace = Path("/tmp/example-workspace")

        self.assertTrue(_should_use_workspace_pip(["-e", str(workspace)], workspace))
        self.assertTrue(_should_use_workspace_pip(["-e", f"{workspace}[test]"], workspace))
        self.assertFalse(_should_use_workspace_pip(["pytest", "numpy==1.26.0"], workspace))

    def test_filter_workspace_pip_args_drops_unsupported_legacy_flags(self) -> None:
        filtered = _filter_workspace_pip_args(
            ["-v", "--no-use-pep517", "--no-build-isolation", "-e", "/tmp/workspace"]
        )

        self.assertEqual(filtered, ["-v", "--no-build-isolation", "-e", "/tmp/workspace"])

    def test_append_pip_flags_adds_missing_flags_once(self) -> None:
        patched = _append_pip_flags(["-e", "/tmp/workspace", "--no-deps"], ["--no-build-isolation", "--no-deps"])

        self.assertEqual(patched, ["-e", "/tmp/workspace", "--no-deps", "--no-build-isolation"])

    def test_append_cflag_preserves_existing_flags(self) -> None:
        patched = _append_cflag({"CFLAGS": "-O2"}, "-Wno-error=incompatible-pointer-types")

        self.assertEqual(patched["CFLAGS"], "-O2 -Wno-error=incompatible-pointer-types")

    def test_ensure_setuptools_compat_install_preserves_explicit_pin(self) -> None:
        self.assertEqual(
            _ensure_setuptools_compat_install([["setuptools==68.0.0"], ["-e", "."]]),
            [["setuptools==68.0.0"], ["-e", "."]],
        )
        self.assertEqual(
            _ensure_setuptools_compat_install([["pytest"], ["-e", "."]])[0],
            ["setuptools==70.0.0"],
        )

    def test_ensure_pytest_for_pytest_oracle_adds_missing_runner(self) -> None:
        installs = _ensure_pytest_for_pytest_oracle(
            [["numpy<2"], ["-e", "."]],
            FakeTestSpec(["pytest -rA tests/test_example.py"]),  # type: ignore[arg-type]
        )

        self.assertEqual(installs[0], ["pytest"])

    def test_ensure_pytest_for_pytest_oracle_tolerates_unmatched_eval_quote(self) -> None:
        installs = _ensure_pytest_for_pytest_oracle(
            [["numpy<2"], ["-e", "."]],
            FakeTestSpec(["pytest -rA tests/test_example.py --bad='unterminated"]),  # type: ignore[arg-type]
        )

        self.assertEqual(installs[0], ["pytest"])

    def test_ensure_pytest_for_pytest_oracle_preserves_existing_runner(self) -> None:
        installs = _ensure_pytest_for_pytest_oracle(
            [["pytest-cov"], ["pytest==8.3.5"], ["-e", "."]],
            FakeTestSpec(["python -m pytest -rA tests/test_example.py"]),  # type: ignore[arg-type]
        )

        self.assertEqual(installs, [["pytest-cov"], ["pytest==8.3.5"], ["-e", "."]])

    def test_ensure_pytest_for_pytest_oracle_ignores_non_pytest_eval(self) -> None:
        installs = _ensure_pytest_for_pytest_oracle(
            [["numpy<2"], ["-e", "."]],
            FakeTestSpec(["python test_runner.py"]),  # type: ignore[arg-type]
        )

        self.assertEqual(installs, [["numpy<2"], ["-e", "."]])

    def test_requires_legacy_markupsafe_detects_historical_sphinx_cap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self.assertFalse(_requires_legacy_markupsafe(workspace))
            (workspace / "setup.py").write_text("install_requires = ['markupsafe<=2.0.1']\n", encoding="utf-8")
            self.assertTrue(_requires_legacy_markupsafe(workspace))

    def test_requires_legacy_astropy_build_detects_historical_wcs_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self.assertFalse(_requires_legacy_astropy_build(workspace))
            (workspace / "astropy" / "wcs").mkdir(parents=True)
            (workspace / "pyproject.toml").write_text(
                '[build-system]\nrequires = ["extension-helpers", "oldest-supported-numpy"]\n',
                encoding="utf-8",
            )

            self.assertTrue(_requires_legacy_astropy_build(workspace))

    def test_commit_workspace_setup_changes_commits_tracked_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
            target = workspace / "pyproject.toml"
            target.write_text('[build-system]\nrequires = ["setuptools"]\n', encoding="utf-8")
            subprocess.run(["git", "add", "pyproject.toml"], cwd=workspace, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=test@example.com",
                    "-c",
                    "user.name=Test",
                    "commit",
                    "-m",
                    "initial",
                ],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            target.write_text('[build-system]\nrequires = ["setuptools==68.0.0"]\n', encoding="utf-8")

            _commit_workspace_setup_changes(workspace)

            diff = subprocess.run(
                ["git", "-c", "core.fileMode=false", "diff", "--name-only"],
                cwd=workspace,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(diff.stdout, "")

    def test_pylint_astroid_requirement_reads_setup_cfg_constraint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            self.assertIsNone(_pylint_astroid_requirement(workspace))
            (workspace / "setup.cfg").write_text(
                "[options]\ninstall_requires =\n    astroid>=2.11.5,<=2.12.0-dev0  # pinned by checkout\n",
                encoding="utf-8",
            )

            self.assertEqual(_pylint_astroid_requirement(workspace), "astroid>=2.11.5,<=2.12.0-dev0")


if __name__ == "__main__":
    unittest.main()
