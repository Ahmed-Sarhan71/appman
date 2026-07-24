"""AppMan — Textual Linux Application Manager."""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Input, Static


from . import backends
PKG_SOURCE = "pacman"  # ponytail: flatpak support when needed


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    elif n < 1024**2:
        return f"{n / 1024:.0f} KiB"
    elif n < 1024**3:
        return f"{n / 1024**2:.1f} MiB"
    return f"{n / 1024**3:.2f} GiB"


class DetailPanel(Static):
    """Right-side detail pane for the selected package."""

    def show(self, pkg: backends.Package | None) -> None:
        if pkg is None:
            self.update("")
            return
        lines = [
            f"[bold]{pkg.name}[/bold]",
            f"Version:  {pkg.version}",
            f"Source:   {PKG_SOURCE}",
            f"Category: {pkg.category}",
            f"Size:     {_fmt_size(pkg.installed_size)}",
            f"Reason:   {'explicit' if pkg.install_reason == 0 else 'dependency'}",
        ]
        if pkg.url:
            lines.append(f"Homepage: {pkg.url}")
        if pkg.description:
            lines.append(f"\n{pkg.description}")
        self.update("\n".join(lines))


class AppMan(App):
    TITLE = "AppMan"
    CSS = """
    Screen { layout: horizontal; }
    #main-col { width: 1fr; height: 100%; }
    #detail-col { width: 36; min-width: 28; height: 100%; border-left: solid $primary; padding: 1; }
    #search { dock: top; margin: 0 0 1 0; }
    DataTable { height: 1fr; }
    DetailPanel { overflow-y: auto; }
    """

    BINDINGS = [
        Binding("f5", "refresh", "Refresh"),
        Binding("u", "uninstall", "Uninstall"),
        Binding("o", "open_url", "Homepage"),
        Binding("c", "copy_name", "Copy name"),
        Binding("/", "focus_search", "Search"),
        Binding("q", "quit", "Quit"),
        Binding("escape", "escape", ""),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._all_packages: list[backends.Package] = []
        self._selected_pkg: backends.Package | None = None
        self._sort_reverse = False
        self._current_query = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="main-col"):
            yield Input(placeholder="Search packages…", id="search")
            yield DataTable(id="table")
        with Vertical(id="detail-col"):
            yield DetailPanel(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Version", "Category", "Disk Size", "Source")
        self.load_packages()
        self.query_one("#search", Input).focus()

    @work(thread=True)
    def load_packages(self) -> None:
        pkgs = backends.filtered_packages()
        self.call_from_thread(self._populate_table, pkgs)

    def _populate_table(self, pkgs: list[backends.Package]) -> None:
        self._all_packages = pkgs
        table = self.query_one("#table", DataTable)
        table.clear()
        for p in pkgs:
            table.add_row(
                p.name, p.version, p.category,
                _fmt_size(p.installed_size), PKG_SOURCE,
                key=p.name,
            )
        self.query_one("#detail", DetailPanel).show(None)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = event.row_key.value
        for p in self._all_packages:
            if p.name == key:
                self._selected_pkg = p
                self.query_one("#detail", DetailPanel).show(p)
                return

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.label.plain == "Disk Size":
            self._sort_reverse = not self._sort_reverse
            self._all_packages.sort(
                key=lambda p: p.installed_size, reverse=self._sort_reverse,
            )
            self._filter(self._current_query)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filter(event.value)

    def _filter(self, query: str) -> None:
        self._current_query = query
        q = query.strip().lower()
        table = self.query_one("#table", DataTable)
        table.clear()
        for p in self._all_packages:
            if q in p.name.lower() or q in p.description.lower() or q in p.category.lower():
                table.add_row(
                    p.name, p.version, p.category,
                    _fmt_size(p.installed_size), PKG_SOURCE,
                    key=p.name,
                )

    def action_refresh(self) -> None:
        self._sort_reverse = False
        pkgs = backends.refresh_cache()
        self._all_packages = backends.filtered_packages(pkgs)
        self._populate_table(self._all_packages)

    def action_uninstall(self) -> None:
        pkg = self._selected_pkg
        if pkg is None:
            return
        self.exit(f"sudo pacman -Rns {pkg.name}")
        # ponytail: in-app sudo prompt when Textual handles suspend/resume better

    def action_open_url(self) -> None:
        pkg = self._selected_pkg
        if pkg is None or not pkg.url:
            return
        webbrowser.open(pkg.url)

    def action_copy_name(self) -> None:
        pkg = self._selected_pkg
        if pkg is None:
            return
        # ponytail: only wl-copy; fallback to xclip/xsel when needed
        for tool, args in [("wl-copy", []), ("xclip", ["-selection", "c"]), ("xsel", ["-ib"])]:
            if Path(f"/usr/bin/{tool}").exists():
                subprocess.run([tool, *args, pkg.name], check=False)
                break

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_escape(self) -> None:
        inp = self.query_one("#search", Input)
        if inp.has_focus:
            inp.value = ""
            self.query_one("#table", DataTable).focus()


def main() -> None:
    app = AppMan()
    result = app.run()
    if result and isinstance(result, str):
        print(f"Run: {result} | Press Enter to execute, Ctrl+C to cancel")
        try:
            input()
            subprocess.run(result.split(), check=False)
        except (KeyboardInterrupt, EOFError):
            pass


if __name__ == "__main__":
    main()
