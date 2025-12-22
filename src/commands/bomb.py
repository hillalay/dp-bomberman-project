from commands.base import Command

class PlaceBombCommand(Command):
    def __init__(self, world, owner):
        self.world = world
        self.owner = owner

    def execute(self) -> None:
        if self.owner is None or not getattr(self.owner, "alive", True):
            return  # ölü oyuncu bombalayamaz
        self.world.place_bomb(self.owner)
