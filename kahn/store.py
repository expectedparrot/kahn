from __future__ import annotations

import json
import re
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, TypeVar

from pydantic import BaseModel, ValidationError

from .models import (
    CriticalUncertainty,
    Force,
    OptionMeta,
    OptionPerformance,
    ProjectMeta,
    ScenarioMeta,
    ScenarioSignals,
)

T = TypeVar("T", bound=BaseModel)
ENVELOPE_SCHEMA_VERSION = "2.0"

PHASE_ORDER = [
    "forces",
    "uncertainty_selection",
    "scenario_construction",
    "option_evaluation",
    "complete",
]


class KahnError(Exception):
    def __init__(self, code: str, message: str, context: str | None = None, hint: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = context
        self.hint = hint


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def default_project_dir() -> Path:
    from os import getenv

    explicit = getenv("KAHN_PROJECT_DIR")
    if explicit:
        return Path(explicit)
    return Path("./kahn_project")


def make_json_envelope(command: str, data: Any, warnings: list[str] | None = None, next_steps: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "command": command,
        "status": "ok",
        "argv": sys.argv[1:],
        "data": data,
        "warnings": warnings or [],
        "errors": [],
        "next_steps": next_steps or [],
    }


def error_envelope(command: str, err: KahnError) -> dict[str, Any]:
    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "command": command,
        "status": "error",
        "argv": sys.argv[1:],
        "data": {},
        "warnings": [],
        "errors": [
            {
                "code": err.code,
                "message": err.message,
                "context": err.context,
                "hint": err.hint,
            }
        ],
        "next_steps": [],
    }


class ProjectStore:
    def __init__(self, root: Path):
        self.root = root

    @property
    def meta_path(self) -> Path:
        return self.root / "meta.json"

    def require_project(self) -> None:
        if not self.meta_path.exists():
            raise KahnError("ID_NOT_FOUND", "Project does not exist.", context=str(self.root), hint="Run `kahn init` first.")

    def init_project(self, meta: ProjectMeta, force: bool = False) -> None:
        if self.root.exists():
            if any(self.root.iterdir()) and not force:
                raise KahnError("ALREADY_EXISTS", "Project directory already exists.", context=str(self.root), hint="Pass `--force` to initialize anyway.")
            if force:
                shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        for path in [
            "forces/trends",
            "forces/uncertainties",
            "critical_uncertainties",
            "scenarios",
            "strategic_options",
            "snapshots",
            "output",
        ]:
            (self.root / path).mkdir(parents=True, exist_ok=True)
        self.write_model(self.meta_path, meta)

    @contextmanager
    def locked(self):
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = self.root / ".kahn.lock"
        with lock_path.open("w") as handle:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def read_model(self, path: Path, model_type: type[T]) -> T:
        try:
            data = json.loads(path.read_text())
            return model_type.model_validate(data)
        except FileNotFoundError as exc:
            raise KahnError("ID_NOT_FOUND", "File not found.", context=str(path)) from exc
        except ValidationError as exc:
            raise KahnError("VALIDATION_FAILED", "JSON validation failed.", context=f"{path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise KahnError("VALIDATION_FAILED", "Invalid JSON.", context=f"{path}: {exc}") from exc

    def write_model(self, path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(model.model_dump(mode="json"), indent=2) + "\n")

    def read_meta(self) -> ProjectMeta:
        self.require_project()
        return self.read_model(self.meta_path, ProjectMeta)

    def write_meta(self, meta: ProjectMeta) -> None:
        meta.updated_at = now_utc()
        self.write_model(self.meta_path, meta)

    def force_path(self, force_type: str, force_id: str) -> Path:
        folder = "trends" if force_type == "trend" else "uncertainties"
        return self.root / "forces" / folder / f"{force_id}.json"

    def list_force_paths(self) -> list[Path]:
        return sorted((self.root / "forces").glob("*/*.json"))

    def list_force_paths_stems(self) -> list[str]:
        return [path.stem for path in self.list_force_paths()]

    def list_forces(self) -> list[Force]:
        return [self.read_model(path, Force) for path in self.list_force_paths()]

    def get_force(self, force_id: str) -> Force:
        for path in self.list_force_paths():
            if path.stem == force_id:
                return self.read_model(path, Force)
        raise KahnError("ID_NOT_FOUND", "Force not found.", context=force_id)

    def save_force(self, force: Force) -> None:
        self.write_model(self.force_path(force.type, force.id), force)

    def delete_force(self, force_id: str) -> None:
        for path in self.list_force_paths():
            if path.stem == force_id:
                path.unlink()
                return
        raise KahnError("ID_NOT_FOUND", "Force not found.", context=force_id)

    def list_critical_uncertainties(self) -> list[CriticalUncertainty]:
        return [
            self.read_model(path, CriticalUncertainty)
            for path in sorted((self.root / "critical_uncertainties").glob("*.json"))
        ]

    def get_critical_uncertainty(self, cu_id: str) -> CriticalUncertainty:
        path = self.root / "critical_uncertainties" / f"{cu_id}.json"
        return self.read_model(path, CriticalUncertainty)

    def save_critical_uncertainty(self, cu: CriticalUncertainty) -> None:
        self.write_model(self.root / "critical_uncertainties" / f"{cu.id}.json", cu)

    def scenario_dir(self, scenario_id: str) -> Path:
        return self.root / "scenarios" / scenario_id

    def list_scenario_ids(self) -> list[str]:
        return sorted(path.name for path in (self.root / "scenarios").iterdir() if path.is_dir())

    def list_scenarios(self) -> list[ScenarioMeta]:
        metas: list[ScenarioMeta] = []
        for scenario_id in self.list_scenario_ids():
            metas.append(self.read_model(self.scenario_dir(scenario_id) / "meta.json", ScenarioMeta))
        return metas

    def get_scenario_meta(self, scenario_id: str) -> ScenarioMeta:
        return self.read_model(self.scenario_dir(scenario_id) / "meta.json", ScenarioMeta)

    def save_scenario_meta(self, meta: ScenarioMeta) -> None:
        meta.updated_at = now_utc()
        self.write_model(self.scenario_dir(meta.id) / "meta.json", meta)

    def get_scenario_narrative(self, scenario_id: str) -> str:
        path = self.scenario_dir(scenario_id) / "narrative.md"
        if not path.exists():
            raise KahnError("ID_NOT_FOUND", "Scenario narrative not found.", context=scenario_id)
        return path.read_text()

    def save_scenario_narrative(self, scenario_id: str, text: str) -> None:
        path = self.scenario_dir(scenario_id) / "narrative.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.rstrip() + "\n")

    def get_scenario_signals(self, scenario_id: str) -> ScenarioSignals:
        return self.read_model(self.scenario_dir(scenario_id) / "signals.json", ScenarioSignals)

    def save_scenario_signals(self, signals: ScenarioSignals) -> None:
        self.write_model(self.scenario_dir(signals.scenario_id) / "signals.json", signals)

    def option_dir(self, option_id: str) -> Path:
        return self.root / "strategic_options" / option_id

    def list_option_ids(self) -> list[str]:
        return sorted(path.name for path in (self.root / "strategic_options").iterdir() if path.is_dir())

    def list_options(self) -> list[OptionMeta]:
        return [self.read_model(self.option_dir(option_id) / "meta.json", OptionMeta) for option_id in self.list_option_ids()]

    def get_option_meta(self, option_id: str) -> OptionMeta:
        return self.read_model(self.option_dir(option_id) / "meta.json", OptionMeta)

    def save_option_meta(self, meta: OptionMeta) -> None:
        self.write_model(self.option_dir(meta.id) / "meta.json", meta)

    def get_option_performance(self, option_id: str) -> OptionPerformance:
        return self.read_model(self.option_dir(option_id) / "performance.json", OptionPerformance)

    def save_option_performance(self, performance: OptionPerformance) -> None:
        self.write_model(self.option_dir(performance.option_id) / "performance.json", performance)

    def save_snapshot(self, label: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", label):
            raise KahnError("VALIDATION_FAILED", "Snapshot label must be filesystem-safe.", context=label)
        destination = self.root / "snapshots" / label
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)
        for item in self.root.iterdir():
            if item.name == "snapshots":
                continue
            target = destination / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        return destination

    def restore_snapshot(self, label: str) -> None:
        source = self.root / "snapshots" / label
        if not source.exists():
            raise KahnError("ID_NOT_FOUND", "Snapshot not found.", context=label)
        for item in list(self.root.iterdir()):
            if item.name == "snapshots":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        for item in source.iterdir():
            target = self.root / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    def next_id(self, prefix: str, existing_ids: Iterable[str]) -> str:
        numeric = [int(item[len(prefix) :]) for item in existing_ids if item.startswith(prefix)]
        return f"{prefix}{(max(numeric) + 1 if numeric else 1):03d}"

    def assert_phase_unlocked(self, phase: str) -> None:
        meta = self.read_meta()
        if phase in meta.phase_locks:
            raise KahnError("PHASE_LOCKED", f"Phase `{phase}` is locked.", hint="Use a snapshot restore if you need to recover.")

    def assert_phase_locked(self, phase: str) -> None:
        meta = self.read_meta()
        if phase not in meta.phase_locks:
            raise KahnError("PHASE_REQUIRED", f"Phase `{phase}` must be locked before this command can run.")
