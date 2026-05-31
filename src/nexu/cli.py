from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from .blueprint import build_blueprint
from .bundle import build_capsule_bundle
from .capsule import create_capsule, list_capsules
from .diff import diff_capsule
from .drift import check_source_drift
from .export_prompt import export_iteration_prompt
from .freeze import freeze_project
from .init_project import init_project
from .iterate import iterate_capsule
from .cinema import generate_cinema_player
from .journal import append_journal, read_journal
from .plan import build_iteration_plan
from .orchestrate import build_capsule_orchestration
from .mcp_server import MCP_TOOLS, run_mcp_stdio
from .report import build_capsule_report
from .review import build_review_packet
from .runtime import build_capsule_runtime
from .paths import project_root
from .promote import build_promotion_plan
from .status import capsule_status
from .verify import verify_capsule

app = typer.Typer(help="nexu — Visual Intent Contract Orchestrator.")
capsule_app = typer.Typer(help="Create, iterate, verify and promote project capsules.")
mcp_app = typer.Typer(help="Expose nexu as an MCP tool service for IDE agents.")
app.add_typer(capsule_app, name="capsule")
app.add_typer(mcp_app, name="mcp")
console = Console()


def _print_yaml(data: object) -> None:
    import yaml

    console.print(Syntax(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), "yaml"))


def _relative_to_root(root: Path, path: str | Path) -> Path:
    return Path(path).relative_to(root)


@app.command()
def init(path: Annotated[str, typer.Argument(help="Project root.")] = ".") -> None:
    """Initialize nexu files in a project."""
    root = project_root(path)
    created = init_project(root)
    if not created:
        console.print("[green]nexu already initialized.[/green]")
        return
    for item in created:
        console.print(f"[green]created[/green] {item.relative_to(root)}")


@app.command()
def freeze(
    path: Annotated[str, typer.Argument(help="Project root.")] = ".",
    name: Annotated[str, typer.Option("--name", "-n", help="Snapshot name.")] = "baseline",
    include: Annotated[list[str] | None, typer.Option("--include", "-i", help="Glob include.")] = None,
) -> None:
    """Freeze a lightweight hash snapshot of the current project."""
    root = project_root(path)
    snapshot = freeze_project(root, name=name, include=include)
    console.print(f"[green]snapshot[/green] {snapshot.id}")
    console.print(f"files: {len(snapshot.files)}")
    if snapshot.git_sha:
        console.print(f"git: {snapshot.git_sha[:12]}")


@capsule_app.command("create")
def capsule_create(
    path: Annotated[str, typer.Argument(help="Project root.")] = ".",
    name: Annotated[str, typer.Option("--name", "-n", help="Capsule name.")] = "capsule",
    domain: Annotated[str, typer.Option("--domain", "-d", help="Domain name.")] = "general",
    include: Annotated[list[str] | None, typer.Option("--include", "-i", help="Glob include pattern.")] = None,
    route: Annotated[list[str] | None, typer.Option("--route", help="UI route covered by capsule.")] = None,
    endpoint: Annotated[list[str] | None, typer.Option("--endpoint", help="Endpoint covered by capsule.")] = None,
    snapshot: Annotated[str | None, typer.Option("--snapshot", help="Source snapshot id.")] = None,
) -> None:
    """Create an isolated capsule from selected project files."""
    root = project_root(path)
    capsule = create_capsule(
        root,
        name,
        domain=domain,
        include=include,
        routes=route,
        endpoints=endpoint,
        snapshot_id=snapshot,
    )
    build_blueprint(root, capsule.name)
    console.print(f"[green]capsule created[/green] {capsule.name}")
    console.print(f"location: .nexu/capsules/{capsule.name}")
    console.print(f"baseline files: {len(capsule.baseline_files)}")


@capsule_app.command("list")
def capsule_list(path: Annotated[str, typer.Argument(help="Project root.")] = ".") -> None:
    """List local capsules."""
    root = project_root(path)
    names = list_capsules(root)
    if not names:
        console.print("[yellow]No capsules found.[/yellow]")
        return
    table = Table("Capsule")
    for name in names:
        table.add_row(name)
    console.print(table)


@capsule_app.command("status")
def capsule_status_command(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
) -> None:
    """Show capsule status, latest iteration, diff counters and verification summary."""
    root = project_root(path)
    status = capsule_status(root, name)
    console.print(f"[bold]{status['name']}[/bold] ({status['type']})")
    console.print(f"domain: {status['domain']}")
    console.print(f"latest iteration: {status['latest_iteration']}")
    files = status["files"]
    table = Table("Counter", "Value")
    for key, value in files.items():
        table.add_row(key, str(value))
    console.print(table)
    if status.get("verification"):
        verification = status["verification"]
        console.print(f"verification: {verification.get('status')} score={verification.get('score')}")


@capsule_app.command("iterate")
def capsule_iterate(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    steps: Annotated[int, typer.Option("--steps", "-s", help="How many planned iterations to create.")] = 1,
    goal: Annotated[str, typer.Option("--goal", "-g", help="Iteration goal.")] = "Evolve capsule safely.",
    cinema: Annotated[bool, typer.Option("--cinema", "-c", help="Start interactive Nexu editor (visual approval).")] = False,
) -> None:
    """Create planned S1..Sn iteration folders and prompts."""
    root = project_root(path)
    created = iterate_capsule(root, name, steps=steps, goal=goal)
    append_journal(root, name, "iterate.planned", f"Planned {len(created)} iteration(s).", data={"goal": goal, "iterations": created})
    console.print(f"[green]created iterations[/green] {', '.join(created)}")
    if cinema:
        player_path = generate_cinema_player(root, name)
        console.print(f"[bold green]🎬 Nexu ready:[/bold green] {player_path}")


@capsule_app.command("blueprint")
def capsule_blueprint(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    print_yaml: Annotated[bool, typer.Option("--print/--no-print", help="Print generated YAML.")] = False,
) -> None:
    """Generate a UI/API/test blueprint from capsule selection and Intract contracts."""
    root = project_root(path)
    blueprint = build_blueprint(root, name)
    console.print(f"[green]blueprint[/green] .nexu/capsules/{name}/blueprints/blueprint.yaml")
    if print_yaml:
        _print_yaml(blueprint)


@capsule_app.command("export-prompt")
def capsule_export_prompt(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    iteration: Annotated[str | None, typer.Option("--iteration", "-i", help="Iteration id, e.g. S3.")] = None,
) -> None:
    """Export an LLM-ready prompt constrained by capsule contracts and blueprint."""
    root = project_root(path)
    export = export_iteration_prompt(root, name, iteration=iteration)
    console.print(f"[green]prompt exported[/green] {_relative_to_root(root, export.path)}")


@capsule_app.command("diff")
def capsule_diff(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
) -> None:
    """Compare capsule src files against the frozen baseline lock."""
    root = project_root(path)
    report = diff_capsule(root, name)
    table = Table("Kind", "Count")
    table.add_row("added", str(len(report.added)))
    table.add_row("modified", str(len(report.modified)))
    table.add_row("deleted", str(len(report.deleted)))
    table.add_row("unchanged", str(len(report.unchanged)))
    console.print(table)


@capsule_app.command("drift")
def capsule_drift(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
) -> None:
    """Check whether the original source files changed since capsule creation."""
    root = project_root(path)
    report = check_source_drift(root, name)
    color = "green" if report["status"] == "pass" else "yellow"
    console.print(f"status: [{color}]{report['status']}[/]")
    console.print(f"changed: {len(report['changed'])}")
    console.print(f"missing: {len(report['missing'])}")


@capsule_app.command("verify")
def capsule_verify(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
) -> None:
    """Verify a capsule against basic intent-contract gates."""
    root = project_root(path)
    report = verify_capsule(root, name)
    if report.status == "pass":
        color = "green"
    elif report.status == "fail":
        color = "red"
    else:
        color = "yellow"
    console.print(f"status: [{color}]{report.status}[/]")
    console.print(f"score: {report.score:.2f}")
    table = Table("Gate", "Status", "Message")
    for finding in report.findings:
        table.add_row(finding.code, finding.status, finding.message)
    console.print(table)


@capsule_app.command("plan")
def capsule_plan(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    steps: Annotated[int, typer.Option("--steps", "-s", help="Forecast horizon.")] = 10,
    goal: Annotated[str, typer.Option("--goal", "-g", help="High-level iteration goal.")] = "",
    print_yaml: Annotated[bool, typer.Option("--print/--no-print", help="Print generated YAML.")] = False,
) -> None:
    """Create a deterministic S1..Sn capsule iteration plan."""
    root = project_root(path)
    plan = build_iteration_plan(root, name, steps=steps, goal=goal)
    console.print(f"[green]iteration plan[/green] .nexu/capsules/{name}/plan/iteration-plan.yaml")
    console.print(f"steps: {len(plan['steps'])}")
    if print_yaml:
        _print_yaml(plan)


@capsule_app.command("runtime")
def capsule_runtime(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
) -> None:
    """Build a static HTML runtime/mock for the isolated capsule."""
    root = project_root(path)
    runtime = build_capsule_runtime(root, name)
    console.print(f"[green]runtime built[/green] {_relative_to_root(root, runtime['index'])}")
    console.print(f"data: {_relative_to_root(root, runtime['data'])}")


@capsule_app.command("report")
def capsule_report(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
) -> None:
    """Build Markdown/HTML/YAML report with verification evidence."""
    root = project_root(path)
    report = build_capsule_report(root, name)
    console.print(f"[green]report built[/green] {_relative_to_root(root, report['markdown'])}")
    console.print(f"html: {_relative_to_root(root, report['html'])}")
    console.print(f"status: {report['status']} score={report['score']:.3f}")


@capsule_app.command("journal")
def capsule_journal(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    limit: Annotated[int, typer.Option("--limit", "-n", help="How many latest entries to show.")] = 20,
) -> None:
    """Show capsule event journal."""
    root = project_root(path)
    entries = read_journal(root, name)[-limit:]
    table = Table("#", "Event", "Message", "Created")
    for entry in entries:
        table.add_row(str(entry.get("index", "")), str(entry.get("event", "")), str(entry.get("message", "")), str(entry.get("created_at", "")))
    console.print(table)


@capsule_app.command("orchestrate")
def capsule_orchestrate(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    steps: Annotated[int, typer.Option("--steps", "-s", help="Forecast/orchestration horizon.")] = 10,
    goal: Annotated[str, typer.Option("--goal", "-g", help="High-level orchestration goal.")] = "",
    call_llm: Annotated[bool, typer.Option("--call-llm/--offline", help="Call configured LiteLLM provider instead of offline deterministic orchestration.")] = False,
    model: Annotated[str | None, typer.Option("--model", "-m", help="Model override for orchestration.")] = None,
) -> None:
    """Build an offline or LLM-assisted orchestration plan for capsule evolution."""
    root = project_root(path)
    result = build_capsule_orchestration(root, name, steps=steps, goal=goal, call_llm=call_llm, model=model)
    console.print(f"[green]orchestration built[/green] {_relative_to_root(root, result['markdown'])}")
    console.print(f"prompt: {_relative_to_root(root, result['prompt'])}")
    console.print(f"mode: {result['mode']} steps={result['steps']}")


@capsule_app.command("review")
def capsule_review(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    iteration: Annotated[str | None, typer.Option("--iteration", "-i", help="Iteration id, e.g. S3.")] = None,
    call_llm: Annotated[bool, typer.Option("--call-llm/--offline", help="Call configured LiteLLM provider instead of offline deterministic review.")] = False,
    model: Annotated[str | None, typer.Option("--model", "-m", help="Model override for LLM review.")] = None,
) -> None:
    """Build an evidence-based review packet for human or optional LLM review."""
    root = project_root(path)
    review = build_review_packet(root, name, iteration=iteration, call_llm=call_llm, model=model)
    console.print(f"[green]review built[/green] {_relative_to_root(root, review['markdown'])}")
    console.print(f"prompt: {_relative_to_root(root, review['prompt'])}")
    console.print(f"decision: {review['decision']} status={review['status']} score={review['score']:.3f}")


@capsule_app.command("bundle")
def capsule_bundle(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    include_src: Annotated[bool, typer.Option("--include-src/--no-src", help="Include copied capsule source files in the bundle.")] = True,
) -> None:
    """Build a portable ZIP bundle with capsule context, evidence and prompts."""
    root = project_root(path)
    bundle = build_capsule_bundle(root, name, include_src=include_src)
    console.print(f"[green]bundle built[/green] {_relative_to_root(root, bundle['path'])}")
    console.print(f"files: {bundle['file_count']}")


@capsule_app.command("promote")
def capsule_promote(
    name: Annotated[str, typer.Argument(help="Capsule name.")],
    path: Annotated[str, typer.Option("--path", "-p", help="Project root.")] = ".",
    dry_run: Annotated[bool, typer.Option("--dry-run/--apply", help="Only create a promotion plan.")] = True,
) -> None:
    """Build a promotion plan for copying capsule changes back to the source project."""
    root = project_root(path)
    plan = build_promotion_plan(root, name)
    console.print(f"[green]promotion plan[/green] .nexu/capsules/{name}/promotion-plan.yaml")
    console.print(f"files to review: {len(plan['files_to_review'])}")
    if not dry_run:
        from .promote import apply_promotion_plan
        try:
            apply_promotion_plan(root, plan)
            console.print("[green]Promotion applied successfully![/green] Files have been copied to the source project.")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise typer.Exit(code=1)


@mcp_app.command("tools")
def mcp_tools() -> None:
    """List nexu MCP tools exposed by the stdio service."""
    table = Table("Tool", "Description")
    for tool in MCP_TOOLS:
        table.add_row(str(tool["name"]), str(tool.get("description", "")))
    console.print(table)


@mcp_app.command("serve")
def mcp_serve(
    path: Annotated[str, typer.Option("--path", "-p", help="Project root available to the MCP server.")] = ".",
    transport: Annotated[str, typer.Option("--transport", help="Transport. MVP supports stdio.")] = "stdio",
) -> None:
    """Run a conservative MCP-compatible JSON-RPC stdio service for nexu tools."""
    root = project_root(path)
    if transport != "stdio":
        raise typer.BadParameter("MVP supports only --transport stdio")
    # Do not print banners here: MCP stdio must be clean JSON-RPC.
    run_mcp_stdio(root)
