import os
import socket

import pytest
from azure.identity import DefaultAzureCredential

from foundry_security_accelerator.config import Settings


@pytest.fixture(autouse=True)
def forbid_test_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*args: object, **kwargs: object) -> None:
        raise AssertionError("Tests must inject service boundaries; network access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(DefaultAzureCredential, "get_token", denied)
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for key in os.environ:
        if key.startswith("FSA_"):
            monkeypatch.delenv(key)
