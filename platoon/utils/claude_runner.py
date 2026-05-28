"""Thin async wrapper around the claude CLI."""
from __future__ import annotations
import asyncio
from typing import Optional


async def run_claude(
    prompt: str,
    *,
    system: Optional[str] = None,
    model: str = "claude-sonnet-4-6",
    allow_web_search: bool = False,
    effort: Optional[str] = None,
    timeout: int = 300,
) -> str:
    cmd = ["claude", "-p", "--model", model]
    if system:
        cmd.extend(["--system-prompt", system])
    if allow_web_search:
        cmd.extend(["--allowedTools", "WebSearch"])
    if effort:
        cmd.extend(["--effort", effort])
    cmd.append(prompt)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"claude CLI timed out after {timeout}s")

    if proc.returncode != 0:
        err = (stderr or b"").decode()[:500]
        raise RuntimeError(f"claude CLI exit {proc.returncode}: {err}")

    return stdout.decode()
