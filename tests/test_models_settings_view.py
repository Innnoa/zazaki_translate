"""ModelsView 和 SettingsView 组件测试"""

from unittest.mock import MagicMock, patch

import pytest

textual = pytest.importorskip("textual", reason="Textual is required for view tests")

from textual.app import App, ComposeResult

from trans_cli.tui.views.models import ModelsView
from trans_cli.tui.views.settings import SettingsView
from trans_cli.tui.state import AppState
from trans_cli.config import TransConfig


class ModelsViewApp(App):
    """ModelsView 测试应用"""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield ModelsView(state=self.state)


class SettingsViewApp(App):
    """SettingsView 测试应用"""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield SettingsView(state=self.state)


def make_mock_state(**config_overrides) -> AppState:
    """创建 mock 状态"""
    translator = MagicMock()
    config = TransConfig(**config_overrides)
    return AppState(translator=translator, config=config)


# ---------------------------------------------------------------------------
# ModelsView tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch("trans_cli.tui.views.models.get_model_statuses")
async def test_models_view_compose(mock_get_statuses):
    """测试 ModelsView 组合"""
    mock_get_statuses.return_value = []
    state = make_mock_state()

    async with ModelsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(ModelsView)
        assert view is not None

        # 检查表格
        table = pilot.app.query_one("#models-table")
        assert table is not None

        # 检查安装按钮
        install_btn = pilot.app.query_one("#install-all")
        assert install_btn is not None


@pytest.mark.asyncio
@patch("trans_cli.tui.views.models.get_model_statuses")
async def test_models_view_refresh(mock_get_statuses):
    """测试刷新模型"""
    from trans_cli.model_status import ModelPairStatus

    mock_get_statuses.return_value = [
        ModelPairStatus("zh", "en", "installed", ""),
        ModelPairStatus("en", "zh", "missing", "Run `trans --install-models` first."),
    ]
    state = make_mock_state()

    async with ModelsViewApp(state).run_test() as pilot:
        table = pilot.app.query_one("#models-table")
        await pilot.pause()

        # 应有两行数据
        assert table.row_count == 2

        view = pilot.app.query_one(ModelsView)
        view.action_refresh_models()
        await pilot.pause()

        # refresh 被调用至少两次（on_mount + refresh）
        assert mock_get_statuses.call_count >= 2


@pytest.mark.asyncio
@patch("trans_cli.tui.views.models.install_default_models")
@patch("trans_cli.tui.views.models.get_model_statuses")
async def test_models_view_install(mock_get_statuses, mock_install):
    """测试安装模型"""
    mock_get_statuses.return_value = []
    state = make_mock_state()

    async with ModelsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(ModelsView)
        view.action_install_models()
        mock_install.assert_called_once()


@pytest.mark.asyncio
@patch("trans_cli.tui.views.models.get_model_statuses")
async def test_models_view_status_display(mock_get_statuses):
    """测试模型状态显示"""
    from trans_cli.model_status import ModelPairStatus

    mock_get_statuses.return_value = [
        ModelPairStatus("zh", "en", "installed", ""),
        ModelPairStatus("en", "zh", "missing", "Not available"),
    ]
    state = make_mock_state()

    async with ModelsViewApp(state).run_test() as pilot:
        table = pilot.app.query_one("#models-table")
        await pilot.pause()

        assert table.row_count == 2


# ---------------------------------------------------------------------------
# SettingsView tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_settings_view_compose():
    """测试 SettingsView 组合"""
    state = make_mock_state()

    async with SettingsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(SettingsView)
        assert view is not None

        # 检查主题选择
        theme_select = pilot.app.query_one("#theme-select")
        assert theme_select is not None

        # 检查方向选择
        direction_select = pilot.app.query_one("#direction-select")
        assert direction_select is not None

        # 检查历史开关
        history_switch = pilot.app.query_one("#history-switch")
        assert history_switch is not None

        # 检查保存按钮
        save_btn = pilot.app.query_one("#save-btn")
        assert save_btn is not None


@pytest.mark.asyncio
async def test_settings_view_defaults():
    """测试默认值反映配置"""
    state = make_mock_state(theme="latte", default_direction="en-zh", save_history=False)

    async with SettingsViewApp(state).run_test() as pilot:
        theme_select = pilot.app.query_one("#theme-select")
        direction_select = pilot.app.query_one("#direction-select")
        history_switch = pilot.app.query_one("#history-switch")

        assert theme_select.value == "latte"
        assert direction_select.value == "en-zh"
        assert history_switch.value is False


@pytest.mark.asyncio
@patch("trans_cli.tui.views.settings.save_config")
async def test_settings_view_save(mock_save_config):
    """测试保存设置"""
    state = make_mock_state()

    async with SettingsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(SettingsView)
        view.action_save_settings()

        mock_save_config.assert_called_once()
        saved_config = mock_save_config.call_args[0][0]
        assert isinstance(saved_config, TransConfig)


@pytest.mark.asyncio
@patch("trans_cli.tui.views.settings.save_config")
async def test_settings_view_save_updates_state(mock_save_config):
    """测试保存设置后更新 state"""
    state = make_mock_state()

    async with SettingsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(SettingsView)

        # 修改主题选择
        theme_select = pilot.app.query_one("#theme-select")
        theme_select.value = "frappe"

        view.action_save_settings()

        # state.config 应被更新为新实例
        assert state.config.theme == "frappe"


@pytest.mark.asyncio
@patch("trans_cli.tui.views.settings.save_config", side_effect=OSError("read-only"))
async def test_settings_view_save_failure(mock_save_config):
    """测试保存失败"""
    state = make_mock_state()

    async with SettingsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(SettingsView)
        # 不应抛出异常
        view.action_save_settings()
