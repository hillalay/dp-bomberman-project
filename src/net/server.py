from __future__ import annotations
import socket
import threading
import queue
from typing import Dict, Any, Tuple, List

from net.protocol import send_json, recv_json


class GameServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.listener: socket.socket | None = None
        self.clients: Dict[int, socket.socket] = {}
        self._lock = threading.Lock()

        self.running = False
        self.inbox: "queue.Queue[Tuple[int, Dict[str, Any]]]" = queue.Queue()

    def start(self) -> None:
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((self.host, self.port))
        self.listener.listen(2)

        self.running = True
        print(f"[Server] Listening on {self.host}:{self.port}")

        # 2 client bekle
        for pid in (1, 2):
            conn, addr = self.listener.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            with self._lock:
                self.clients[pid] = conn

            print(f"[Server] Client {pid} connected: {addr}")
            send_json(conn, {"type": "WELCOME", "player_id": pid})

            t = threading.Thread(target=self._reader, args=(pid, conn), daemon=True)
            t.start()

    def _reader(self, pid: int, conn: socket.socket) -> None:
        try:
            while self.running:
                msg = recv_json(conn)  # blocking
                self.inbox.put((pid, msg))
        except Exception as e:
            print(f"[Server] reader stopped pid={pid}: {repr(e)}")
        finally:
            # cleanup
            with self._lock:
                old = self.clients.pop(pid, None)
            try:
                if old is not None:
                    old.close()
            except Exception:
                pass

    def poll_inputs(self) -> List[Tuple[int, Dict[str, Any]]]:
        out: List[Tuple[int, Dict[str, Any]]] = []
        while True:
            try:
                out.append(self.inbox.get_nowait())
            except queue.Empty:
                break
        return out

    def broadcast(self, payload: Dict[str, Any]) -> None:
        # bağlantısı kopanları listeden düş
        dead: List[int] = []
        with self._lock:
            items = list(self.clients.items())

        for pid, conn in items:
            try:
                send_json(conn, payload)
            except Exception as e:
                print(f"[Server] send failed pid={pid}: {repr(e)}")
                dead.append(pid)

        if dead:
            with self._lock:
                for pid in dead:
                    c = self.clients.pop(pid, None)
                    try:
                        if c:
                            c.close()
                    except Exception:
                        pass
