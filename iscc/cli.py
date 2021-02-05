# -*- coding: utf-8 -*-
import json
import sys
from loguru import logger as log
import typer
import iscc
from pathlib import Path
from typing import Optional


app = typer.Typer()

Parg = typer.Argument(..., help="Path to file or folder (default: currend dir)")
Debug = typer.Option(False, "--debug", "-d", help="Show debug output.")
Verbose = typer.Option(0, "--verbose", "-v", count=True)


@app.callback()
def init(debug: bool = Debug):
    if debug:
        log.add(sys.stderr)
        log.info("Debug messages activated!")


@app.command()
def explain(icode: str):
    """Decode ISCC to human readable format."""
    code = iscc.Code(icode)
    typer.echo(code.explain)


@app.command("iscc")
def main(path: Path, verbose: int = Verbose):
    """Generate ISCC for file(s)."""
    for file in files(path):
        try:
            result = iscc.code_iscc(file)
            if verbose == 0:
                typer.echo(f"ISCC:{result['iscc']}")
            elif verbose == 1:
                typer.echo(f"ISCC:{result['iscc']},{result['filename']}")
            elif verbose == 2:
                typer.echo(result)
            else:
                typer.echo(json.dumps(result, indent=2))
        except Exception as e:
            log.error(e)


def files(path: Optional[Path]):
    """Build a list of files from a path"""

    if path is None:
        return list(f for f in Path.cwd().glob("*") if f.is_file())
    elif path.is_file():
        return [path]
    elif path.is_dir():
        return list(f for f in path.glob("*") if f.is_file())
    else:
        typer.Abort("Nothing to do.")


if __name__ == "__main__":
    app()
