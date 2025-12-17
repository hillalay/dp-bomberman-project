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
    def add_game_result(self, user_id: int, score: int, won: bool) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scores (user_id, score, won)
                VALUES (?, ?, ?)
                """,
                (user_id, int(score), 1 if won else 0),
            )

    def get_stats(self, user_id: int) -> Dict[str, int]:
        with get_connection() as conn:
            cur = conn.execute(
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

    def get_leaderboard(self, limit: int = 10) -> List[ScoreEntry]:
        with get_connection() as conn:
            cur = conn.execute(
                """
                SELECT u.username, s.score, s.won, s.played_at
                FROM scores s
                JOIN users u ON u.id = s.user_id
                ORDER BY s.score DESC, s.played_at ASC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cur.fetchall()

        return [
            ScoreEntry(
                username=r["username"],
                score=r["score"],
                won=bool(r["won"]),
                played_at=r["played_at"],
            )
            for r in rows
        ]
