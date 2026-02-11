"""
Centralized path config. Uses HOWISSTAT_ROOT env var if set, else repo root derived from this file.
"""
import os

# Repo root: from env or derived from main/config.py location
_ROOT = os.getenv("HOWISSTAT_ROOT")
if not _ROOT:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = _ROOT


def path(*parts: str) -> str:
    """Path relative to repo root. E.g. path('data', 'player_id2player_info.json')"""
    return os.path.join(ROOT, *parts)
