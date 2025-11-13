from game.game import Game

def main():
    # Game singleton'ı oluştur ve çalıştır
    game = Game(width=800, height=600)
    game.run()

if __name__ == "__main__":
    main()
