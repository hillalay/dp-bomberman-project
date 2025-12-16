from typing import Optional
from commands.base import Command

class CommandInvoker:
    def execute(self, cmd: Optional[Command]) -> None:
        if cmd is None:
            return
        cmd.execute()
