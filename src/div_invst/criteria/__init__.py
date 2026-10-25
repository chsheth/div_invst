"""Screening criteria engine. Importing this package registers every criterion; see engine.py for the run."""
from . import analysts, chowder, portfolio, quality, valuation  # noqa: F401  (registration)
from .base import FAIL, NA, PASS, REGISTRY, UNKNOWN, Result
from .config import load_config
from .engine import evaluate, rank, screen

__all__ = ["FAIL", "NA", "PASS", "REGISTRY", "UNKNOWN", "Result", "evaluate", "load_config", "rank", "screen"]
