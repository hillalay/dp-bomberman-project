from commands.base import Command

class MoveCommand(Command):
    def __init__(self, player, dx: int, dy: int):
        self.player = player
        self.dx = dx
        self.dy = dy

    def execute(self) -> None:
        self.player.move_dir.x = self.dx
        self.player.move_dir.y = self.dy

class StopMoveCommand(Command):
    def __init__(self, player, axis: str):
        self.player = player
        self.axis = axis  # "x" / "y"

    def execute(self) -> None:
        if self.axis == "x":
            self.player.move_dir.x = 0
        elif self.axis == "y":
            self.player.move_dir.y = 0
