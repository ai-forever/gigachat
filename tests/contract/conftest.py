"""Isolate SDK contract tests from credentials in the developer environment."""

import os

import pytest


@pytest.fixture(autouse=True)
def _clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {})
