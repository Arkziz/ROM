"""Canonical filesystem paths for ROM V2 runtime artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    """Hold isolated runtime directories rooted below one explicit base path."""

    root: Path
    database: Path
    logs: Path
    export: Path
    temporary: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "RuntimePaths":
        """Resolve the canonical `.runtime/v2` directory tree."""
        resolved_project_root = project_root.resolve()
        runtime_root = resolved_project_root / ".runtime" / "v2"
        return cls(
            root=runtime_root,
            database=runtime_root / "db",
            logs=runtime_root / "logs",
            export=runtime_root / "export",
            temporary=runtime_root / "temporary",
        )

    def create(self) -> None:
        """Create every canonical runtime directory idempotently."""
        for directory in self.directories():
            directory.mkdir(parents=True, exist_ok=True)

    def directories(self) -> tuple[Path, Path, Path, Path]:
        """Return runtime directories in stable ownership order."""
        return (self.database, self.logs, self.export, self.temporary)

    def validate(self) -> None:
        """Reject paths that escape the canonical runtime root."""
        root = self.root.resolve()
        for directory in self.directories():
            resolved = directory.resolve()
            if root != resolved and root not in resolved.parents:
                raise ValueError("runtime_path_escapes_v2_root")
