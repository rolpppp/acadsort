"""Shared pytest configuration for backend tests."""

import os

import pytest


@pytest.fixture(autouse=True)
def disable_http_proxy_for_model_downloads(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hugging Face model downloads fail when a local HTTP proxy returns 403."""
    monkeypatch.setenv("NO_PROXY", "*")
    monkeypatch.setenv("no_proxy", "*")
    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("http_proxy", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
