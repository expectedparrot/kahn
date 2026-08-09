from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError

from ..renderer import emit_json, render_error
from ..store import KahnError, ProjectStore, default_project_dir, error_envelope, make_json_envelope

ProjectDirOption = typer.Option(None, "--project-dir", help="Override the project directory.")
HumanOption = typer.Option(False, "--human", help="Rich human-readable output instead of JSON.")
QuietOption = typer.Option(False, "--quiet", help="Suppress non-error output.")


def resolve_project_dir(project_dir: Path | None) -> Path:
    return project_dir or default_project_dir()


def should_emit_json(human: bool) -> bool:
    if human:
        return False
    return os.getenv("KAHN_HUMAN_OUTPUT", "").lower() != "true"


def store_for(project_dir: Path | None) -> ProjectStore:
    return ProjectStore(resolve_project_dir(project_dir))


def finish(command: str, data: Any, warnings: list[str] | None = None, next_steps: list[str] | None = None) -> None:
    emit_json(make_json_envelope(command, data, warnings=warnings, next_steps=next_steps))


def fail(command: str, err: KahnError, json_flag: bool) -> None:
    if json_flag:
        emit_json(error_envelope(command, err))
    else:
        render_error(err)
    raise typer.Exit(code=1)


def fail_validation(command: str, err: ValidationError, json_flag: bool) -> None:
    """Translate expected Pydantic input errors into Kahn's stable envelope."""
    detail = err.errors()[0]
    field = ".".join(str(part) for part in detail.get("loc", ()))
    context = {"field": field, "value": detail.get("input")}
    expected = detail.get("ctx", {}).get("expected")
    if expected:
        context["accepted"] = [item.strip(" '") for item in str(expected).replace(" or ", ",").split(",")]
    fail(
        command,
        KahnError(
            "INVALID_ENUM_VALUE" if detail.get("type") == "literal_error" else "VALIDATION_FAILED",
            f"Invalid value for {field or 'input'}: {detail.get('msg', 'validation failed')}.",
            context=context,
            hint="Choose one of the accepted values shown in the error context.",
        ),
        json_flag,
    )
