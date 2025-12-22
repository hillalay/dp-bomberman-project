from __future__ import annotations
import json
import socket
import struct
from typing import Any, Dict

_HDR = struct.Struct("!I")  # 4-byte length, network endian


def _recv_exact(conn: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    return buf


def send_json(conn: socket.socket, payload: Dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    conn.sendall(_HDR.pack(len(data)) + data)


def recv_json(conn: socket.socket) -> Dict[str, Any]:
    (length,) = _HDR.unpack(_recv_exact(conn, _HDR.size))
    data = _recv_exact(conn, length)
    return json.loads(data.decode("utf-8"))
