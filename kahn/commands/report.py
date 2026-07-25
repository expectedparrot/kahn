from __future__ import annotations

import html
import json
from pathlib import Path

import typer
from jinja2 import Template

from ..renderer import render_markdown
from ..store import KahnError
from .common import HumanOption, ProjectDirOption, QuietOption, fail, finish, should_emit_json, store_for

app = typer.Typer(help="Generate and render reports.")

SUMMARY_TEMPLATE = Template(
    """# {{ meta.focal_question }}

Domain: {{ meta.domain }}
Horizon: {{ meta.horizon }}

## Scenarios
{% for scenario in scenarios %}
- **{{ scenario.name }}**: {{ scenario.tagline }}
{% endfor %}

## Strategic Options
{% for option in options %}
- **{{ option.name }}**
{% endfor %}
"""
)

RECOMMENDATIONS_TEMPLATE = Template(
    """# Robust Recommendations

{% for item in rankings %}
- **{{ item.name }}** ({{ "%.2f"|format(item.score) }}){% if item.hedging %} hedging option{% endif %}
{% endfor %}
"""
)


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{font-family:sans-serif;max-width:900px;margin:2em auto;padding:0 1em;color:#222}}
  h1,h2,h3{{color:#333}}
  table{{border-collapse:collapse;width:100%;margin:1em 0}}
  th,td{{border:1px solid #ccc;padding:.5em 1em;text-align:left}}
  th{{background:#f0f0f0}}
  .robust{{color:green;font-weight:bold}}
  .fragile{{color:#c00}}
  .acceptable{{color:#888}}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _build_html_report(summary: str, recommendations: str, strategy: dict, signals: dict) -> str:
    def _pre(text: str) -> str:
        return f"<pre>{html.escape(text)}</pre>"

    scenario_ids = list(next(iter(strategy.values()), {}).keys()) if strategy else []
    matrix_rows = ""
    for option_id, evals in strategy.items():
        cells = "".join(
            f'<td class="{html.escape(evals.get(sc, ""))}">{ html.escape(evals.get(sc, "-")) }</td>'
            for sc in scenario_ids
        )
        matrix_rows += f"<tr><td><b>{html.escape(option_id)}</b></td>{cells}</tr>\n"
    sc_headers = "".join(f"<th>{html.escape(sc)}</th>" for sc in scenario_ids)
    matrix_html = (
        f"<h2>Strategy Matrix</h2>"
        f"<table><tr><th>Option</th>{sc_headers}</tr>{matrix_rows}</table>"
        if strategy else ""
    )

    signal_rows = ""
    for scenario_id, data in signals.items():
        for sig in data.get("signals", []):
            signal_rows += (
                f"<tr><td>{html.escape(scenario_id)}</td>"
                f"<td>{html.escape(sig.get('description', ''))}</td>"
                f"<td>{html.escape(sig.get('observable_in', ''))}</td></tr>\n"
            )
    signals_html = (
        f"<h2>Signal Dashboard</h2>"
        f"<table><tr><th>Scenario</th><th>Signal</th><th>Observable In</th></tr>{signal_rows}</table>"
        if signals else ""
    )

    title_line = summary.splitlines()[0].lstrip("#").strip() if summary else "kahn Report"
    body = (
        f"<h1>{html.escape(title_line)}</h1>"
        f"<h2>Summary</h2>{_pre(summary)}"
        f"<h2>Recommendations</h2>{_pre(recommendations)}"
        f"{matrix_html}"
        f"{signals_html}"
    )
    return _HTML_TEMPLATE.format(title=html.escape(title_line), body=body)


@app.command("generate")
def generate_report(
    force: bool = typer.Option(False, "--force"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "report generate"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    warnings: list[str] = []
    try:
        meta = store.read_meta()
        if meta.phase not in ("option_evaluation", "complete"):
            raise KahnError("PHASE_REQUIRED", "Current phase must be option_evaluation or complete to generate reports.")
        scenarios = store.list_scenarios()
        options = store.list_options()
        scenario_ids = {scenario.id for scenario in scenarios}
        rankings = []
        strategy_matrix = {}
        signal_dashboard = {}
        for option in options:
            performance = store.get_option_performance(option.id)
            missing = sorted(scenario_ids - set(performance.evaluations))
            if missing:
                raise KahnError(
                    "DEPENDENCY_MISSING",
                    "All options must be evaluated against all scenarios before report generation.",
                    context=f"{option.id} missing evaluations for: {', '.join(missing)}",
                )
            strategy_matrix[option.id] = {scenario_id: evaluation.rating for scenario_id, evaluation in performance.evaluations.items()}
            rankings.append({"id": option.id, "name": option.name, "score": performance.robustness_score, "hedging": option.hedging_value})
        rankings.sort(key=lambda item: item["score"], reverse=True)
        for scenario in scenarios:
            signals = store.get_scenario_signals(scenario.id)
            signal_dashboard[scenario.id] = signals.model_dump(mode="json")
            if len(signals.signals) < 3:
                warnings.append(f"{scenario.id} has fewer than 3 signals.")
        output_dir = store.root / "output"
        existing = [output_dir / name for name in ["summary.md", "strategy_matrix.json", "robust_recommendations.md", "signal_dashboard.json"]]
        if any(path.exists() for path in existing) and not force:
            raise KahnError("ALREADY_EXISTS", "Output files already exist.", hint="Pass `--force` to regenerate.")
        (output_dir / "summary.md").write_text(SUMMARY_TEMPLATE.render(meta=meta, scenarios=scenarios, options=options))
        (output_dir / "strategy_matrix.json").write_text(json.dumps(strategy_matrix, indent=2) + "\n")
        (output_dir / "robust_recommendations.md").write_text(RECOMMENDATIONS_TEMPLATE.render(rankings=rankings))
        (output_dir / "signal_dashboard.json").write_text(json.dumps(signal_dashboard, indent=2) + "\n")
    except KahnError as err:
        fail(command, err, json_flag)
    payload = {"output_dir": str(store.root / "output")}
    if json_flag:
        finish(command, payload, warnings=warnings)
        return
    if not quiet:
        from ..renderer import render_kv_panel

        render_kv_panel("Report generated", [("Output", str(store.root / "output")), ("Warnings", "; ".join(warnings) or "none")])


@app.command("show")
def show_report(
    section: str = typer.Option("summary", "--section"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "report show"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    mapping = {
        "summary": store.root / "output" / "summary.md",
        "strategy": store.root / "output" / "strategy_matrix.json",
        "recommendations": store.root / "output" / "robust_recommendations.md",
        "signals": store.root / "output" / "signal_dashboard.json",
    }
    valid_sections = ", ".join(sorted(mapping.keys()))
    try:
        path = mapping[section]
        content = path.read_text()
    except KeyError:
        fail(
            command,
            KahnError(
                "VALIDATION_FAILED",
                f"Unknown report section '{section}'.",
                hint=f"Valid sections: {valid_sections}",
            ),
            json_flag,
        )
    except FileNotFoundError as err:
        fail(command, KahnError("ID_NOT_FOUND", "Report output not found.", context=str(mapping.get(section))), json_flag)
    if json_flag:
        finish(command, {"section": section, "content": content})
        return
    if not quiet:
        if path.suffix == ".md":
            render_markdown(content)
        else:
            from ..renderer import console

            console.print_json(content)


@app.command("export")
def export_report(
    format: str = typer.Option("markdown", "--format"),
    output: Path | None = typer.Option(None, "--output"),
    project_dir: Path | None = ProjectDirOption,
    human: bool = HumanOption,
    quiet: bool = QuietOption,
) -> None:
    command = "report export"
    json_flag = should_emit_json(human)
    store = store_for(project_dir)
    valid_formats = "markdown, json, html"
    if format not in ("markdown", "json", "html"):
        fail(command, KahnError("VALIDATION_FAILED", f"Unknown export format '{format}'.", hint=f"Valid formats: {valid_formats}"), json_flag)
    try:
        summary = (store.root / "output" / "summary.md").read_text()
        recommendations = (store.root / "output" / "robust_recommendations.md").read_text()
        strategy = json.loads((store.root / "output" / "strategy_matrix.json").read_text())
        signals = json.loads((store.root / "output" / "signal_dashboard.json").read_text())
        if format == "json":
            payload = json.dumps({"summary": summary, "recommendations": recommendations, "strategy": strategy, "signals": signals}, indent=2)
        elif format == "html":
            payload = _build_html_report(summary, recommendations, strategy, signals)
        else:
            payload = f"{summary}\n\n{recommendations}\n"
        if output:
            output.write_text(payload)
    except FileNotFoundError as err:
        fail(command, KahnError("ID_NOT_FOUND", "Report output not found.", context=str(err)), json_flag)
    result = {"format": format, "output": str(output) if output else None, "content": payload}
    if json_flag:
        finish(command, result)
        return
    if output:
        if not quiet:
            from ..renderer import render_kv_panel

            render_kv_panel("Report exported", [("Format", format), ("Output", str(output))])
    elif not quiet:
        if format == "json":
            from ..renderer import console

            console.print_json(payload)
        elif format == "html":
            from ..renderer import console

            console.print(payload)
        else:
            render_markdown(payload)
