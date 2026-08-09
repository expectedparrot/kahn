from __future__ import annotations

import typer

from .commands.docs import app as docs_app
from .commands.force import app as force_app
from .commands.guide import app as guide_app
from .commands.ingest import app as ingest_app
from .commands.init import app as init_app
from .commands.job import app as job_app
from .commands.next import app as next_app
from .commands.option import app as option_app
from .commands.phase import app as phase_app
from .commands.report import app as report_app
from .commands.scenario import app as scenario_app
from .commands.snapshot import app as snapshot_app
from .commands.status import app as status_app
from .commands.uncertainty import app as uncertainty_app
from .commands.validate import app as validate_app

app = typer.Typer(help="Strategic scenario planning CLI.")
app.add_typer(init_app)
app.add_typer(status_app)
app.add_typer(guide_app)
app.add_typer(next_app)
app.add_typer(force_app, name="force")
app.add_typer(uncertainty_app, name="uncertainty")
app.add_typer(scenario_app, name="scenario")
app.add_typer(phase_app, name="phase")
app.add_typer(option_app, name="option")
app.add_typer(report_app, name="report")
app.add_typer(validate_app)
app.add_typer(snapshot_app, name="snapshot")
app.add_typer(docs_app, name="docs")
app.add_typer(job_app, name="job")
app.add_typer(ingest_app, name="ingest")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
