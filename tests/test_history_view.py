"""HistoryView 组件测试"""

from unittest.mock import MagicMock, patch

import pytest

textual = pytest.importorskip("textual", reason="Textual is required for HistoryView tests")

from textual.app import App, ComposeResult

from trans_cli.tui.views.history import HistoryView
from trans_cli.tui.widgets.history_item import HistoryItem
from trans_cli.tui.state import AppState
from trans_cli.history import HistoryEntry


class HistoryViewApp(App):
    """测试应用"""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield HistoryView(state=self.state)


def make_mock_state() -> AppState:
    """创建 mock 状态"""
    translator = MagicMock()
    config = MagicMock()
    return AppState(translator=translator, config=config)


def make_mock_entries(count: int = 3) -> list[HistoryEntry]:
    """创建 mock 历史记录"""
    return [
        HistoryEntry(
            input_text=f"Hello {i}",
            output_text=f"你好 {i}",
            from_code="en",
            to_code="zh",
            created_at=f"2026-04-30T12:00:{i:02d}",
        )
        for i in range(count)
    ]


@pytest.mark.asyncio
@patch("trans_cli.tui.views.history.load_history")
async def test_history_view_compose(mock_load_history):
    """测试 HistoryView 组合"""
    mock_load_history.return_value = make_mock_entries()
    state = make_mock_state()

    async with HistoryViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(HistoryView)
        assert view is not None

        # 检查搜索框
        search_input = pilot.app.query_one("#history-search")
        assert search_input is not None

        # 检查列表
        list_view = pilot.app.query_one("#history-list")
        assert list_view is not None


@pytest.mark.asyncio
@patch("trans_cli.tui.views.history.load_history")
async def test_history_view_load(mock_load_history):
    """测试加载历史记录"""
    entries = make_mock_entries(5)
    mock_load_history.return_value = entries
    state = make_mock_state()

    async with HistoryViewApp(state).run_test() as pilot:
        list_view = pilot.app.query_one("#history-list")
        # 等待加载完成
        await pilot.pause()
        assert len(list_view.children) == 5


@pytest.mark.asyncio
@patch("trans_cli.tui.views.history.load_history")
async def test_history_view_empty(mock_load_history):
    """测试空历史记录"""
    mock_load_history.return_value = []
    state = make_mock_state()

    async with HistoryViewApp(state).run_test() as pilot:
        list_view = pilot.app.query_one("#history-list")
        await pilot.pause()
        assert len(list_view.children) == 0


@pytest.mark.asyncio
@patch("trans_cli.tui.views.history.search_history")
@patch("trans_cli.tui.views.history.load_history")
async def test_history_view_search(mock_load_history, mock_search_history):
    """测试搜索功能"""
    mock_load_history.return_value = make_mock_entries(3)
    mock_search_history.return_value = make_mock_entries(1)
    state = make_mock_state()

    async with HistoryViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(HistoryView)

        # 初始加载
        await pilot.pause()
        list_view = pilot.app.query_one("#history-list")
        assert len(list_view.children) == 3

        # 触发搜索
        view.action_search_history()
        search_input = pilot.app.query_one("#history-search")
        search_input.value = "Hello 0"
        await pilot.pause()

        # 搜索被调用
        mock_search_history.assert_called()


@pytest.mark.asyncio
@patch("trans_cli.tui.views.history.load_history")
async def test_history_view_refresh(mock_load_history):
    """测试刷新功能"""
    mock_load_history.return_value = make_mock_entries(2)
    state = make_mock_state()

    async with HistoryViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(HistoryView)
        await pilot.pause()

        # 刷新
        view.action_refresh_history()
        await pilot.pause()

        # load_history 被调用至少两次（on_mount + refresh）
        assert mock_load_history.call_count >= 2


@pytest.mark.asyncio
@patch("trans_cli.tui.views.history.load_history")
async def test_history_item_compose(mock_load_history):
    """测试 HistoryItem 组件"""
    entry = HistoryEntry(
        input_text="Hello world",
        output_text="你好世界",
        from_code="en",
        to_code="zh",
        created_at="2026-04-30T12:00:00",
    )
    mock_load_history.return_value = [entry]
    state = make_mock_state()

    async with HistoryViewApp(state).run_test() as pilot:
        await pilot.pause()
        # 检查 HistoryItem 存在
        items = pilot.app.query(HistoryItem)
        assert len(items) == 1
        assert items[0].entry.input_text == "Hello world"
        assert items[0].entry.output_text == "你好世界"
