from core.game import Game
from data.db import init_db
init_db()


def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
