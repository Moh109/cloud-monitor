"""Console reporter using rich for a readable terminal summary."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..models import ScanResult, Severity, Status
from ..scoring import compute_score

_SEVERITY_STYLE = {
    Severity.CRITICAL: "bold white on red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
    Severity.INFORMATIONAL: "dim",
}

_GRADE_STYLE = {"A": "bold green", "B": "green", "C": "yellow", "D": "red", "F": "bold red"}


def render_console(result: ScanResult, console: Console | None = None) -> None:
    console = console or Console()
    score = compute_score(result)

    grade_style = _GRADE_STYLE.get(score.grade, "white")
    header = (
        f"[b]CloudGuard[/b] posture report\n"
        f"Account: {result.account_id or 'n/a'}   Regions: {', '.join(result.regions)}\n\n"
        f"[{grade_style}]Score {score.score}/100  (Grade {score.grade})[/]\n"
        f"Passed {score.passed_controls}  |  Failed {score.failed_controls}  |  "
        f"Errored {score.errored_controls}"
    )
    console.print(Panel(header, title="Security Posture", expand=False))

    # Failing findings, most severe first.
    failed = sorted(result.failed, key=lambda f: (f.severity.rank, f.check_id))
    if not failed:
        console.print("[green]No failing controls. ✓[/green]")
        return

    table = Table(title="Failing Controls", show_lines=False, expand=True)
    table.add_column("Severity", no_wrap=True)
    table.add_column("Check", no_wrap=True)
    table.add_column("Resource", overflow="fold")
    table.add_column("Title", overflow="fold")

    for f in failed:
        style = _SEVERITY_STYLE.get(f.severity, "white")
        table.add_row(
            f"[{style}]{f.severity.value}[/]",
            f.check_id,
            f.resource_id,
            f.title,
        )
    console.print(table)

    if result.errored:
        console.print(
            f"[yellow]{len(result.errored)} check(s) errored - see JSON report.[/yellow]"
        )
