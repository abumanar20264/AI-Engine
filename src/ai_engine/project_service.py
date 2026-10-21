"""Application operations connecting the control UI to project contracts and storage."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
from typing import Any

from .project_store import ProjectStore, ProjectValidationError, create_project


class ProjectService:
    """Coordinate project creation, validation, and persistence for UI clients."""

    def __init__(self, store: ProjectStore) -> None:
        self.store = store

    def new_project(self, name: str) -> dict[str, Any]:
        return create_project(name)

    def save_project(self, project: Mapping[str, object]) -> dict[str, Any]:
        return self.store.save(project)

    def load_project(self, project_id: str) -> dict[str, Any]:
        return self.store.load(project_id)

    def list_projects(self) -> list[dict[str, Any]]:
        if not self.store.root.exists():
            return []
        return self.store.list_projects()


def validation_field(error: ProjectValidationError) -> str | None:
    """Return the contract path prefix suitable for attaching an inline UI error."""
    field, separator, _ = str(error).partition(":")
    if not separator:
        return None
    return re.sub(r"\[\d+\]$", "", field)


def default_projects_directory(repository_root: Path) -> Path:
    """Return the local project directory without creating it."""
    return repository_root / "projects"
