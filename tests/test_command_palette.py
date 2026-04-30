"""CommandPalette 组件测试"""

import pytest

textual = pytest.importorskip("textual", reason="Textual is required for CommandPalette tests")

from textual.app import App, ComposeResult
from textual.widgets import Input, ListView

from trans_cli.tui.widgets.command_palette import Command, CommandPalette, DEFAULT_COMMANDS


class CommandPaletteApp(App):
    """测试应用"""

    def compose(self) -> ComposeResult:
        yield CommandPalette()


@pytest.mark.asyncio
async def test_command_dataclass():
    """测试 Command 数据类"""
    cmd = Command(
        name="test",
        description="Test command",
        shortcut="T",
        action=lambda app: None,
    )
    assert cmd.name == "test"
    assert cmd.description == "Test command"
    assert cmd.shortcut == "T"
    assert callable(cmd.action)


@pytest.mark.asyncio
async def test_default_commands_exist():
    """测试默认命令列表非空且包含导航和主题命令"""
    assert len(DEFAULT_COMMANDS) > 0

    names = [cmd.name for cmd in DEFAULT_COMMANDS]
    # 导航命令
    assert "translate" in names
    assert "history" in names
    assert "models" in names
    assert "settings" in names
    # 主题命令
    assert "theme latte" in names
    assert "theme frappe" in names
    assert "theme macchiato" in names
    assert "theme mocha" in names


@pytest.mark.asyncio
async def test_command_palette_compose():
    """测试 CommandPalette 组合"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)
        assert palette is not None

        # 检查输入框
        input_widget = pilot.app.query_one("#command-input")
        assert input_widget is not None

        # 检查列表
        list_view = pilot.app.query_one("#command-list")
        assert list_view is not None


@pytest.mark.asyncio
async def test_command_palette_default_commands():
    """测试默认命令加载"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)

        # 应加载 DEFAULT_COMMANDS
        assert len(palette.commands) == len(DEFAULT_COMMANDS)
        assert len(palette.filtered_commands) == len(DEFAULT_COMMANDS)


@pytest.mark.asyncio
async def test_command_palette_filter():
    """测试命令过滤"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)

        # 输入过滤
        input_widget = pilot.app.query_one("#command-input")
        input_widget.value = "trans"
        await pilot.pause()

        # 验证过滤结果
        assert len(palette.filtered_commands) > 0
        assert all(
            "trans" in cmd.name.lower() or "trans" in cmd.description.lower()
            for cmd in palette.filtered_commands
        )


@pytest.mark.asyncio
async def test_command_palette_filter_no_match():
    """测试无匹配过滤"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)

        input_widget = pilot.app.query_one("#command-input")
        input_widget.value = "zzzznonexistent"
        await pilot.pause()

        assert len(palette.filtered_commands) == 0


@pytest.mark.asyncio
async def test_command_palette_filter_case_insensitive():
    """测试大小写不敏感过滤"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)

        input_widget = pilot.app.query_one("#command-input")
        input_widget.value = "Translate"
        await pilot.pause()

        assert len(palette.filtered_commands) > 0
        assert any("translate" in cmd.name for cmd in palette.filtered_commands)


@pytest.mark.asyncio
async def test_command_palette_filter_by_description():
    """测试按描述过滤"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)

        input_widget = pilot.app.query_one("#command-input")
        input_widget.value = "Theme"
        await pilot.pause()

        assert len(palette.filtered_commands) > 0
        assert all(
            "theme" in cmd.name.lower() or "theme" in cmd.description.lower()
            for cmd in palette.filtered_commands
        )


@pytest.mark.asyncio
async def test_command_palette_custom_commands():
    """测试自定义命令列表"""
    custom = [
        Command("foo", "Foo action", "F", lambda app: None),
        Command("bar", "Bar action", "B", lambda app: None),
    ]

    class CustomApp(App):
        def compose(self) -> ComposeResult:
            yield CommandPalette(commands=custom)

    async with CustomApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)
        assert len(palette.commands) == 2
        assert palette.commands[0].name == "foo"


@pytest.mark.asyncio
async def test_command_palette_cancel():
    """测试取消操作（escape 键）"""
    dismissed_with = []

    class CancelApp(App):
        def on_mount(self) -> None:
            def on_dismiss(result):
                dismissed_with.append(result)
            self.push_screen(CommandPalette(), on_dismiss)

    async with CancelApp().run_test() as pilot:
        await pilot.pause()
        # 按 escape 关闭
        await pilot.press("escape")
        await pilot.pause()
        assert dismissed_with == [None]


@pytest.mark.asyncio
async def test_command_palette_select():
    """测试选择命令（enter 键）"""
    dismissed_with = []

    class SelectApp(App):
        def on_mount(self) -> None:
            def on_dismiss(result):
                dismissed_with.append(result)
            self.push_screen(CommandPalette(), on_dismiss)

    async with SelectApp().run_test() as pilot:
        await pilot.pause()
        # 按 enter 选择第一条命令
        await pilot.press("enter")
        await pilot.pause()
        assert len(dismissed_with) == 1
        # 应返回第一个命令
        assert dismissed_with[0] is not None
        assert isinstance(dismissed_with[0], Command)
        assert dismissed_with[0].name == "translate"
