#!/usr/bin/env python3
"""OSINT Platoon — CLI entry point."""
import asyncio
import click
from platoon.orchestrator import Orchestrator
from platoon.utils.logger import init_logger


@click.command()
@click.option("--target", required=True, help="Target: domain, company name, email, username")
@click.option(
    "--type", "target_type",
    type=click.Choice(["domain", "person", "company", "email", "username"]),
    default="domain",
    show_default=True,
    help="Target type",
)
@click.option(
    "--depth",
    type=click.Choice(["hasty", "deliberate", "detailed"]),
    default="deliberate",
    show_default=True,
    help="Recon depth (hasty=fast/shallow, deliberate=balanced, detailed=thorough)",
)
@click.option(
    "--max-iterations", default=2, show_default=True,
    help="Maximum replan-and-reconvene iterations",
)
@click.option(
    "--dry-run", is_flag=True, default=False,
    help="Run METT-TC analysis only — no squads dispatched",
)
@click.option(
    "--log-dir", default="logs", show_default=True,
    help="Directory for JSONL mission logs",
)
def main(target, target_type, depth, max_iterations, dry_run, log_dir):
    """OSINT Platoon — ATP 3-21.8 multi-agent intelligence collection."""
    log = init_logger(log_dir=log_dir)
    click.echo(f"[PLATOON] Mission: {target} | type={target_type} | depth={depth}")
    click.echo(f"[PLATOON] Log: {log_dir}/mission_{log.mission_id}.jsonl")

    orchestrator = Orchestrator(max_iterations=max_iterations)

    if dry_run:
        click.echo("[PLATOON] Dry-run mode — METT-TC plan only")
        plan = asyncio.run(orchestrator.dry_run(target, target_type, depth))
        click.echo(plan)
        return

    click.echo("[PLATOON] Dispatching squads...")
    salute = asyncio.run(orchestrator.run_mission(target, target_type, depth))

    click.echo("\n" + "=" * 60)
    click.echo(f"SALUTE REPORT — {salute.subject}")
    click.echo("=" * 60)
    click.echo(f"Subject  : {salute.subject}")
    click.echo(f"Activity : {salute.activity}")
    click.echo(f"Location : {salute.location}")
    click.echo(f"Unit/Org : {salute.unit_org}")
    click.echo(f"Exposure : {salute.exposure}")
    click.echo(f"Confidence: {salute.confidence:.0%}")
    click.echo()
    click.echo("Executive Summary:")
    click.echo(salute.executive_summary)
    click.echo()
    click.echo("Key Findings:")
    for i, finding in enumerate(salute.key_findings[:10], 1):
        click.echo(f"  {i}. {finding}")

    if salute.timeline:
        click.echo()
        click.echo("Timeline:")
        for entry in salute.timeline:
            click.echo(f"  {entry.date}: {entry.event}")

    click.echo()
    click.echo(f"[PLATOON] Report saved to reports/")
    click.echo(f"[PLATOON] Log: {log_dir}/mission_{log.mission_id}.jsonl")


if __name__ == "__main__":
    main()
