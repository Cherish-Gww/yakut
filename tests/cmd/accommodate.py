# Copyright (c) 2020 UAVCAN Consortium
# This software is distributed under the terms of the MIT License.
# Author: Pavel Kirienko <pavel@uavcan.org>

from __future__ import annotations
import typing
import pytest
from tests.subprocess import Subprocess, execute_cli
from tests.dsdl import compiled_dsdl, OUTPUT_DIR
from tests.transport import TRANSPORT_FACTORIES, TransportFactory


@pytest.mark.parametrize("transport_factory", TRANSPORT_FACTORIES)  # type: ignore
def _unittest_accommodate_swarm(transport_factory: TransportFactory, compiled_dsdl: typing.Any) -> None:
    _ = compiled_dsdl
    # We spawn a lot of processes here, which might strain the test system a little, so beware. I've tested it
    # with 120 processes and it made my workstation (24 GB RAM ~4 GHz Core i7) struggle to the point of being
    # unable to maintain sufficiently real-time operation for the test to pass. Hm.
    used_node_ids = list(range(10))
    pubs = [
        Subprocess.cli(
            f"--transport={transport_factory(idx).expression}",
            f"--path={OUTPUT_DIR}",
            "pub",
            "--period=0.4",
            "--count=60",
        )
        for idx in used_node_ids
    ]
    _, stdout, _ = execute_cli(
        "-v",
        f"--path={OUTPUT_DIR}",
        f"--transport={transport_factory(None).expression}",
        "accommodate",
        timeout=100.0,
    )
    assert int(stdout) not in used_node_ids
    for p in pubs:
        p.wait(100.0, interrupt=True)


def _unittest_accommodate_loopback() -> None:
    _, stdout, _ = execute_cli(
        "-v",
        f"--path={OUTPUT_DIR}",
        "accommodate",
        timeout=30.0,
        environment_variables={"YAKUT_TRANSPORT": "Loopback(None),Loopback(None)"},
    )
    assert 0 <= int(stdout) < 2 ** 64


def _unittest_accommodate_udp_localhost() -> None:
    _, stdout, _ = execute_cli(
        "-v",
        f"--path={OUTPUT_DIR}",
        "accommodate",
        timeout=30.0,
        environment_variables={"YAKUT_TRANSPORT": 'UDP("127.0.0.1",anonymous=True)'},
    )
    # Exclude zero from the set because an IP address with the host address of zero may cause complications.
    assert 1 <= int(stdout) <= 65534
