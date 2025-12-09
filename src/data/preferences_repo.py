# src/data/preferences_repo.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from data.db import get_connection


@dataclass
class Preferences:
    id: int
    user_id: int
    theme: str
    music_volume: float
    sfx_volume: float
    music_muted: bool
    sfx_muted: bool


class PreferencesRepo:
    """
    Kullanıcıya ait preferences kaydını yönetir.
    - get_or_create_for_user(user_id)
    - update_for_user(...)
    """

    def __init__(self) -> None:
        self.conn = get_connection()

    def _row_to_model(self, row) -> Preferences:
        return Preferences(
            id=row["id"],
            user_id=row["user_id"],
            theme=row["theme"],
            music_volume=row["music_volume"],
            sfx_volume=row["sfx_volume"],
            music_muted=bool(row["music_muted"]),
            sfx_muted=bool(row["sfx_muted"]),
        )

    def get_or_create_for_user(self, user_id: int) -> Preferences:
        """
        Eğer kullanıcıya ait preferences satırı varsa getirir,
        yoksa varsayılanlarla oluşturur.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, theme, music_volume, sfx_volume, music_muted, sfx_muted
            FROM preferences
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if row is not None:
            return self._row_to_model(row)

        # Yoksa yeni oluştur
        cur.execute(
            """
            INSERT INTO preferences (user_id)
            VALUES (?)
            """,
            (user_id,),
        )
        self.conn.commit()
        new_id = cur.lastrowid

        cur.execute(
            """
            SELECT id, user_id, theme, music_volume, sfx_volume, music_muted, sfx_muted
            FROM preferences
            WHERE id = ?
            """,
            (new_id,),
        )
        row = cur.fetchone()
        return self._row_to_model(row)

    def update_for_user(
        self,
        user_id: int,
        *,
        theme: Optional[str] = None,
        music_volume: Optional[float] = None,
        sfx_volume: Optional[float] = None,
        music_muted: Optional[bool] = None,
        sfx_muted: Optional[bool] = None,
    ) -> Preferences:
        """
        Parametrelerden gelen değerleri günceller (None olanlar dokunulmaz),
        güncel Preferences objesini geri döner.
        """
        cur = self.conn.cursor()

        # Dinamik UPDATE query kur
        fields = []
        params = []

        if theme is not None:
            fields.append("theme = ?")
            params.append(theme)
        if music_volume is not None:
            fields.append("music_volume = ?")
            params.append(music_volume)
        if sfx_volume is not None:
            fields.append("sfx_volume = ?")
            params.append(sfx_volume)
        if music_muted is not None:
            fields.append("music_muted = ?")
            params.append(1 if music_muted else 0)
        if sfx_muted is not None:
            fields.append("sfx_muted = ?")
            params.append(1 if sfx_muted else 0)

        if fields:
            params.append(user_id)
            query = f"""
                UPDATE preferences
                SET {", ".join(fields)}
                WHERE user_id = ?
            """
            cur.execute(query, tuple(params))
            self.conn.commit()

        # Güncel halini geri dön
        cur.execute(
            """
            SELECT id, user_id, theme, music_volume, sfx_volume, music_muted, sfx_muted
            FROM preferences
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return self._row_to_model(row)
        # Eski koda uyumluluk için: update_preferences -> update_for_user
    def update_preferences(
        self,
        user_id: int,
        *,
        theme: Optional[str] = None,
        music_volume: Optional[float] = None,
        sfx_volume: Optional[float] = None,
        music_muted: Optional[bool] = None,
        sfx_muted: Optional[bool] = None,
    ) -> Preferences:
        """
        Eski OptionsState kodu update_preferences ismini kullanıyorsa
        bozulmasın diye bu wrapper'ı ekliyoruz.
        """
        return self.update_for_user(
            user_id=user_id,
            theme=theme,
            music_volume=music_volume,
            sfx_volume=sfx_volume,
            music_muted=music_muted,
            sfx_muted=sfx_muted,
        )

