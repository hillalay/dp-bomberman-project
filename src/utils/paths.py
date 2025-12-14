from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # dp-bomberman-project
ASSETS_DIR = PROJECT_ROOT / "assets"

def asset_path(*parts: str) -> str:
    return str(ASSETS_DIR.joinpath(*parts))
