"""Each theme exposes a single `render()` function that owns the whole page."""
from . import terminal, minimal, workspace, wizard

REGISTRY = {
    "terminal": terminal,
    "minimal": minimal,
    "workspace": workspace,
    "wizard": wizard,
}

__all__ = ["terminal", "minimal", "workspace", "wizard", "REGISTRY"]
