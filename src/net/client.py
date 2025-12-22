from __future__ import annotations
import socket
import threading
import queue
from typing import Any, Dict, Optional

from net.protocol import send_json, recv_json


class GameClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.conn: socket.socket | None = None
        self.running = False

        self.player_id: int | None = None
        self._inbox: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self._last_snapshot: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()

    def connect(self) -> None:
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.host, self.port))
        self.conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # welcome al
        welcome = recv_json(self.conn)
        if welcome.get("type") != "WELCOME":
            raise RuntimeError(f"Expected WELCOME, got {welcome}")
        self.player_id = int(welcome["player_id"])
        print(f"[Client] connected as player_id: {self.player_id}")

        self.running = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        assert self.conn is not None
        try:
            while self.running:
                msg = recv_json(self.conn)
                t = msg.get("type")
                if t == "SNAPSHOT":
                    with self._lock:
                        self._last_snapshot = msg.get("data", {})
                else:
                    self._inbox.put(msg)
        except Exception as e:
            print("[Client] reader stopped:", repr(e))
        finally:
            self.running = False
            try:
                if self.conn:
                    self.conn.close()
            except Exception:
                pass

    def send_input(self, action: str, data: Dict[str, Any]) -> None:
        if not self.conn or not self.running:
            return
        try:
            send_json(self.conn, {"type": "INPUT", "action": action, "data": data})
        except OSError as e:
            print("[Client] send_input failed:", repr(e))
            self.running = False
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def get_snapshot(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            snap = self._last_snapshot
            self._last_snapshot = None
        return snap
