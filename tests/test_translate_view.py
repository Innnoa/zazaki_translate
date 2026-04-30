"""TranslateView 组件测试"""

from unittest.mock import MagicMock

import pytest

textual = pytest.importorskip("textual", reason="Textual is required for TranslateView tests")

from trans_cli.tui.views.translate import TranslateView, TranslationError
from trans_cli.tui.state import AppState

from textual.app import App, ComposeResult


class TranslateViewApp(App):
    """测试应用"""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield TranslateView(state=self.state)


def make_mock_state() -> AppState:
    """创建 mock 状态"""
    translator = MagicMock()
    config = MagicMock()
    config.default_direction = "zh-en"
    config.save_history = False
    return AppState(translator=translator, config=config)


@pytest.mark.asyncio
async def test_translate_view_compose():
    """测试 TranslateView 组合"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)
        assert view is not None

        # 检查输入框
        input_widget = pilot.app.query_one("#source-input")
        assert input_widget is not None

        # 检查输出区域
        output_widget = pilot.app.query_one("#translation-output")
        assert output_widget is not None


@pytest.mark.asyncio
async def test_translate_view_clear():
    """测试清空功能"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)

        # 设置输入
        input_widget = pilot.app.query_one("#source-input")
        input_widget.text = "Hello"

        # 执行清空
        view.action_clear_input()

        # 验证清空
        assert input_widget.text == ""


@pytest.mark.asyncio
async def test_translate_view_direction_display():
    """测试语言方向显示"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)

        # 检查初始方向显示
        direction_btn = pilot.app.query_one("#lang-direction")
        assert "zh" in str(direction_btn.label)
        assert "en" in str(direction_btn.label)


@pytest.mark.asyncio
async def test_translate_view_swap_direction():
    """测试交换语言方向"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)

        # 记录初始方向
        initial_from = state.from_code
        initial_to = state.to_code

        # 执行交换
        view.action_swap_direction()

        # 验证方向已交换
        assert state.from_code == initial_to
        assert state.to_code == initial_from


@pytest.mark.asyncio
async def test_translate_view_empty_input():
    """测试空输入翻译"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)

        # 空输入时翻译应该被跳过
        view.action_translate()

        # 翻译不应进行
        assert state.translation_in_progress is False


@pytest.mark.asyncio
async def test_translate_view_toggle_focus():
    """测试焦点切换"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)

        # 切换焦点
        view.action_toggle_focus()

        # 再次切换
        view.action_toggle_focus()


def test_translation_error():
    """测试 TranslationError 异常"""
    error = TranslationError("test error")
    assert str(error) == "test error"
    assert isinstance(error, Exception)
