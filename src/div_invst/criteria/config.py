"""Load config/criteria.toml."""
import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "criteria.toml"


def load_config(path: Path | None = None) -> dict:
    with open(path or CONFIG_PATH, "rb") as f:
        return tomllib.load(f)
