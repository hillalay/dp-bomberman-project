# src/data/scores_repo.py

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict

from data.db import get_connection


@dataclass
class ScoreEntry:
    username: str
    score: int
    won: bool
    played_at: str


class ScoresRepo:
    """
    Oyun sonuçlarını tutan Repository.
    Buradan:
      - Game statistics (wins, losses, total_games)
      - High scores (leaderboard)
    hepsini çıkarabiliyoruz.
    """

    def __init__(self) -> None:
        self.conn = get_connection()

    # -------- oyun sonucu ekleme --------
    def add_game_result(self, user_id: int, score: int, won: bool) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO scores (user_id, score, won)
            VALUES (?, ?, ?)
            """,
            (user_id, score, 1 if won else 0),
        )
        self.conn.commit()

    # -------- istatistikler (wins/losses/total) --------
    def get_stats(self, user_id: int) -> Dict[str, int]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN won = 0 THEN 1 ELSE 0 END) AS losses,
                COUNT(*) AS total_games
            FROM scores
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cur.fetchone()

        if row is None:
            return {"wins": 0, "losses": 0, "total_games": 0}

        return {
            "wins": row["wins"] or 0,
            "losses": row["losses"] or 0,
            "total_games": row["total_games"] or 0,
        }

    # -------- leaderboard --------
    def get_leaderboard(self, limit: int = 10) -> List[ScoreEntry]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT u.username, s.score, s.won, s.played_at
            FROM scores s
            JOIN users u ON u.id = s.user_id
            ORDER BY s.score DESC, s.played_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()

        result: List[ScoreEntry] = []
        for r in rows:
            result.append(
                ScoreEntry(
                    username=r["username"],
                    score=r["score"],
                    won=bool(r["won"]),
                    played_at=r["played_at"],
                )
            )
        return result
