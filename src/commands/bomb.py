from commands.base import Command

class PlaceBombCommand(Command):
    def __init__(self, world):
        self.world = world

    def execute(self) -> None:
        self.world.place_bomb()
