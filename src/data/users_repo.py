# src/data/users_repo.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import hashlib


from data.db import get_connection


@dataclass
class User:
    id: int
    username: str
    password_hash: str


class UsersRepo:
    """
    Kullanıcı tabloları için Repository.
    - create_user  : yeni kullanıcı oluşturur
    - get_by_username : kullanıcıyı isme göre bulur
    - verify_login : login kontrolü (username + password)
    """

    def __init__(self) -> None:
        self.conn = get_connection()

    # -------- yardımcı --------
    def _hash_password(self, password: str) -> str:
        # Basit SHA-256 hash. (Gerçek projede salt vs. eklenir.)
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _row_to_model(self, row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
        )

    # -------- CRUD benzeri metodlar --------
    def create_user(self, username: str, password: str) -> User:
        cur = self.conn.cursor()
        password_hash = self._hash_password(password)

        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        self.conn.commit()

        user_id = cur.lastrowid
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        return self._row_to_model(row)

    def get_by_username(self, username: str) -> Optional[User]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def verify_login(self, username: str, password: str) -> Optional[User]:
        """
        Kullanıcı adı + şifre ile giriş:
        Hash eşleşirse User döner, yoksa None.
        """
        user = self.get_by_username(username)
        if user is None:
            return None

        if user.password_hash == self._hash_password(password):
            return user
        return None
