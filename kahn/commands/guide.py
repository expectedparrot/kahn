from __future__ import annotations

import typer

from ..docs import load_doc
from ..renderer import render_markdown
from .common import HumanOption, finish, should_emit_json

app = typer.Typer(help="Read the agent workflow guide.")


@app.command("guide")
def guide_command(human: bool = HumanOption) -> None:
    """Show the authoritative end-to-end agent workflow."""
    markdown = load_doc("agent-workflow")
    if should_emit_json(human):
        finish("guide", {"topic": "agent-workflow", "markdown": markdown}, next_steps=["kahn next"])
        return
    render_markdown(markdown)
