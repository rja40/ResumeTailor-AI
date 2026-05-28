"""ResumeTailor — entry point. Dispatches to the theme selected by `UI_THEME` in .env.

Available themes (set in .env):
  UI_THEME=terminal   → dark Vercel/Geist look, mono headings, violet accent
  UI_THEME=minimal    → Linear/Notion: light, serif headings, card-based
  UI_THEME=workspace  → Cursor/IDE-style two-column layout (inputs + live preview)
  UI_THEME=wizard     → 3-step guided flow with a progress bar
"""
from __future__ import annotations

from src.config import settings
from src.ui.themes import REGISTRY


theme_module = REGISTRY.get(settings.ui_theme, REGISTRY["terminal"])
theme_module.render()
