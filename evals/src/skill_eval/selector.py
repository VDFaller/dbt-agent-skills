"""Interactive selection widgets for CLI using Textual."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Input, OptionList, SelectionList
from textual.widgets.option_list import Option
from textual.widgets.selection_list import Selection


@dataclass
class RunInfo:
    """Information about a run for display in selector.

    Display format: '2026-01-30-120000 | 3 scenarios | graded | $0.75'
    """

    path: Path
    name: str
    scenario_count: int
    graded: bool
    total_cost: float | None

    @classmethod
    def from_path(cls, path: Path) -> RunInfo:
        """Create RunInfo from a run directory path."""
        name = path.name
        scenario_count = sum(
            1 for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")
        )

        grades_file = path / "grades.yaml"
        graded = grades_file.exists()

        # Calculate total cost from metadata files
        total_cost: float | None = None
        cost_sum = 0.0
        has_cost = False
        for metadata_file in path.glob("**/metadata.yaml"):
            try:
                with metadata_file.open() as f:
                    metadata = yaml.safe_load(f)
                    if metadata and metadata.get("total_cost_usd"):
                        cost_sum += float(metadata["total_cost_usd"])
                        has_cost = True
            except (yaml.YAMLError, ValueError, TypeError):
                pass
        if has_cost:
            total_cost = cost_sum

        return cls(
            path=path,
            name=name,
            scenario_count=scenario_count,
            graded=graded,
            total_cost=total_cost,
        )

    def display_text(self) -> str:
        """Format for display in selector."""
        parts = [self.name, f"{self.scenario_count} scenario(s)"]
        if self.graded:
            parts.append("graded")
        if self.total_cost is not None:
            parts.append(f"${self.total_cost:.2f}")
        return " | ".join(parts)


@dataclass
class ScenarioInfo:
    """Information about a scenario for display in selector.

    Display format: 'my-scenario | 2 skill sets | Description...'
    """

    path: Path
    name: str
    description: str
    skill_set_count: int

    @classmethod
    def from_path(cls, path: Path) -> ScenarioInfo:
        """Create ScenarioInfo from a scenario directory path."""
        name = path.name

        # Count skill sets
        skill_sets_file = path / "skill-sets.yaml"
        skill_set_count = 0
        if skill_sets_file.exists():
            try:
                with skill_sets_file.open() as f:
                    data = yaml.safe_load(f)
                    skill_set_count = len(data.get("sets", []))
            except yaml.YAMLError:
                pass

        # Get description from scenario.md
        description = ""
        scenario_md = path / "scenario.md"
        if scenario_md.exists():
            try:
                content = scenario_md.read_text()
                # Use first non-empty line as description
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        description = line[:60] + "..." if len(line) > 60 else line
                        break
            except (OSError, UnicodeDecodeError):
                pass

        return cls(
            path=path,
            name=name,
            description=description,
            skill_set_count=skill_set_count,
        )

    def display_text(self) -> str:
        """Format for display in selector."""
        parts = [self.name, f"{self.skill_set_count} skill set(s)"]
        if self.description:
            parts.append(self.description)
        return " | ".join(parts)


def is_interactive() -> bool:
    """Check if running in interactive mode (TTY)."""
    return sys.stdin.isatty()


class RunSelectorApp(App[Path | None]):
    """Single-selection app for choosing a run."""

    BINDINGS = [
        ("escape", "quit", "Cancel"),
        ("enter", "select", "Select"),
        ("/", "focus_search", "Search"),
    ]

    def __init__(self, runs: list[RunInfo], title: str = "Select a run") -> None:
        super().__init__()
        self.runs = runs
        self.title_text = title
        self._selected: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Type to filter...", id="search")
        yield OptionList(
            *[Option(run.display_text(), id=run.name) for run in self.runs],
            id="options",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        self.title = "skill-eval"
        self.sub_title = self.title_text
        # Focus the option list by default
        self.query_one("#options", OptionList).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter options as user types."""
        query = event.value.lower()
        option_list = self.query_one("#options", OptionList)
        option_list.clear_options()

        for run in self.runs:
            if query in run.display_text().lower():
                option_list.add_option(Option(run.display_text(), id=run.name))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """When Enter is pressed in search, focus the list."""
        self.query_one("#options", OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection via Enter or double-click."""
        selected_name = str(event.option.id)
        for run in self.runs:
            if run.name == selected_name:
                self._selected = run.path
                break
        self.exit(self._selected)

    async def action_quit(self) -> None:
        self.exit(None)

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_select(self) -> None:
        option_list = self.query_one("#options", OptionList)
        if option_list.highlighted is not None:
            option = option_list.get_option_at_index(option_list.highlighted)
            selected_name = str(option.id)
            for run in self.runs:
                if run.name == selected_name:
                    self._selected = run.path
                    break
        self.exit(self._selected)


class ScenarioSelectorApp(App[list[Path]]):
    """Multi-selection app for choosing scenarios."""

    BINDINGS = [
        ("escape", "quit", "Cancel"),
        ("enter", "confirm", "Confirm selection"),
        ("a", "select_all", "Select all"),
        ("/", "focus_search", "Search"),
    ]

    def __init__(
        self, scenarios: list[ScenarioInfo], title: str = "Select scenarios"
    ) -> None:
        super().__init__()
        self.scenarios = scenarios
        self.title_text = title
        # Track selections across filtering
        self._selected_names: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Type to filter...", id="search")
        yield SelectionList[str](
            *[
                Selection(scenario.display_text(), scenario.name, initial_state=False)
                for scenario in self.scenarios
            ],
            id="selections",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "tokyo-night"
        self.title = "skill-eval"
        self.sub_title = self.title_text
        # Focus the selection list by default
        self.query_one("#selections", SelectionList).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter options as user types, preserving selections."""
        query = event.value.lower()
        selection_list = self.query_one("#selections", SelectionList)

        # Save current selections before clearing
        self._selected_names.update(selection_list.selected)

        selection_list.clear_options()

        for scenario in self.scenarios:
            if query in scenario.display_text().lower():
                is_selected = scenario.name in self._selected_names
                selection_list.add_option(
                    Selection(
                        scenario.display_text(), scenario.name, initial_state=is_selected
                    )
                )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """When Enter is pressed in search, focus the list."""
        self.query_one("#selections", SelectionList).focus()

    async def action_quit(self) -> None:
        self.exit([])

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_confirm(self) -> None:
        selection_list = self.query_one("#selections", SelectionList)
        # Combine currently visible selections with previously saved ones
        all_selected = self._selected_names.union(selection_list.selected)
        selected_paths = [s.path for s in self.scenarios if s.name in all_selected]
        self.exit(selected_paths)

    def action_select_all(self) -> None:
        selection_list = self.query_one("#selections", SelectionList)
        selection_list.select_all()


def select_run(runs: list[Path], title: str = "Select a run") -> Path | None:
    """Show interactive selector for a single run.

    Args:
        runs: List of run directory paths
        title: Title to display in the selector

    Returns:
        Selected run path, or None if cancelled
    """
    if not runs:
        return None

    # Single run available - skip selector
    if len(runs) == 1:
        return runs[0]

    run_infos = [RunInfo.from_path(run) for run in runs]
    # Sort by name descending (most recent first)
    run_infos.sort(key=lambda r: r.name, reverse=True)

    app = RunSelectorApp(run_infos, title)
    return app.run()


def select_scenarios(
    scenarios: list[Path], title: str = "Select scenarios"
) -> list[Path]:
    """Show interactive selector for multiple scenarios.

    Args:
        scenarios: List of scenario directory paths
        title: Title to display in the selector

    Returns:
        List of selected scenario paths (empty if cancelled)
    """
    if not scenarios:
        return []

    scenario_infos = [ScenarioInfo.from_path(s) for s in scenarios]
    # Sort alphabetically by name
    scenario_infos.sort(key=lambda s: s.name)

    app = ScenarioSelectorApp(scenario_infos, title)
    result = app.run()
    return result if result is not None else []
