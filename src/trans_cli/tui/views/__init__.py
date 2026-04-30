"""TUI 视图模块"""

from trans_cli.tui.views.history import HistoryView
from trans_cli.tui.views.models import ModelsView
from trans_cli.tui.views.settings import SettingsView
from trans_cli.tui.views.translate import TranslateView

__all__ = ["HistoryView", "ModelsView", "SettingsView", "TranslateView"]
