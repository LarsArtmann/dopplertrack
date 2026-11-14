"""Offline-suite invariant: no test may perform real network I/O.

Every test that needs the network monkeypatches the client layer (requests.get,
fetch.requests.get, terrain.requests.get); this autouse guard patches the socket layer
underneath so a test that reaches for real sockets fails loudly instead of quietly
depending on the outside world."""

import socket

import pytest


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    def _denied(*args, **kwargs):
        raise AssertionError("test performed network I/O; mock the client layer instead")

    monkeypatch.setattr(socket, "create_connection", _denied, raising=False)
    monkeypatch.setattr(socket.socket, "connect", _denied, raising=False)
    monkeypatch.setattr(socket, "getaddrinfo", _denied, raising=False)
