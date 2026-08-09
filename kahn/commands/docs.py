from __future__ import annotations

import typer

from ..docs import DOCS, load_doc, search_docs
from ..renderer import console, render_markdown, table
from .common import HumanOption, finish, should_emit_json

app = typer.Typer(help="Read built-in documentation.")


@app.command("list")
def docs_list(human: bool = HumanOption) -> None:
    command = "docs list"
    json_flag = should_emit_json(human)
    topics = [{"topic": k, "title": v["title"], "summary": v["summary"]} for k, v in DOCS.items()]
    if json_flag:
        finish(command, {"topics": topics})
        return
    tbl = table("Topic", "Title", "Summary")
    for row in topics:
        tbl.add_row(row["topic"], row["title"], row["summary"])
    console.print(tbl)


@app.command("show")
def docs_show(topic: str, human: bool = HumanOption) -> None:
    command = "docs show"
    json_flag = should_emit_json(human)
    if topic not in DOCS:
        from ..store import KahnError

        err = KahnError(
            "UNKNOWN_TOPIC",
            f"No doc '{topic}'.",
            hint="Run `kahn docs list` to see available topics.",
        )
        from .common import fail

        fail(command, err, json_flag)
    text = load_doc(topic)
    if json_flag:
        finish(command, {"topic": topic, "title": DOCS[topic]["title"], "markdown": text})
        return
    render_markdown(text)


@app.command("search")
def docs_search(query: str, human: bool = HumanOption) -> None:
    command = "docs search"
    json_flag = should_emit_json(human)
    matches = search_docs(query)
    if json_flag:
        finish(command, {"query": query, "matches": matches})
        return
    if not matches:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return
    tbl = table("Topic", "Score", "Snippet")
    for m in matches:
        tbl.add_row(m["topic"], str(m["score"]), (m.get("snippet") or "")[:80])
    console.print(tbl)
