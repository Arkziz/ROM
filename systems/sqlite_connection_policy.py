#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical ROM V1 SQLite runtime connection policy.

This module applies only connection-local safety defaults. Transaction ownership,
journal-mode changes, schema mutations, and connection lifecycle remain with each
runtime owner.
"""
from __future__ import annotations

import sqlite3
from os import PathLike
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_BUSY_TIMEOUT_MS = 30000


def connect_runtime(
    database: str | bytes | PathLike[str] | PathLike[bytes],
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    *,
    check_same_thread: bool = True,
    uri: bool = False,
    foreign_keys: bool = True,
    query_only: bool = False,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    row_factory: Any = None,
    **kwargs: Any,
) -> sqlite3.Connection:
    """Open one runtime connection with proven common connection-local policy."""
    if timeout <= 0:
        raise ValueError("SQLite timeout must be positive")
    if busy_timeout_ms < 0:
        raise ValueError("SQLite busy_timeout must be non-negative")
    connection = sqlite3.connect(
        database,
        timeout=float(timeout),
        check_same_thread=check_same_thread,
        uri=uri,
        **kwargs,
    )
    try:
        connection.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
        if foreign_keys:
            connection.execute("PRAGMA foreign_keys=ON")
        if query_only:
            connection.execute("PRAGMA query_only=ON")
        if row_factory is not None:
            connection.row_factory = row_factory
        return connection
    except Exception:
        connection.close()
        raise
