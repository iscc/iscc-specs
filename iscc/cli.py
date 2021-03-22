# -*- coding: utf-8 -*-
import json
import sys
from loguru import logger as log
import typer
import iscc
from pathlib import Path
from typing import Optional
from codetiming import Timer


app = typer.Typer()

Parg = typer.Argument(..., help="Path to file or folder (default: currend dir)")
Debug = typer.Option(False, "--debug", "-d", help="Show debug output.")
Verbose = typer.Option(0, "--verbose", "-v", count=True)


@app.command()
def explain(icode: str):
    """Decode ISCC to human readable format."""
    code = iscc.Code(icode)
    typer.echo(code.explain)


@app.command()
def distance(a: str, b: str):
    """Calculate hamming distance of codes"""
    codes_a = iscc.decompose(a)
    codes_b = iscc.decompose(b)
    for a, b in zip(codes_a, codes_b):
        typer.echo(
            f"Distance {a.maintype.name}: {a.code} - {b.code} = {iscc.distance(a, b)} bits"
        )


@app.command()
def decompose(icode: str):
    """Decompose ISCC into its components"""
    codes = iscc.decompose(icode)
    typer.echo(f'ISCC:{"-".join(c.code for c in codes)}')


@app.command("iscc")
def main(
    path: Path, verbose: int = Verbose, debug: bool = Debug, granular: bool = False
):
    """Generate ISCC for file(s)."""
    if debug:
        log.add(sys.stderr)
        log.info("Debug messages activated!")
    for file in files(path):
        try:
            with Timer(text="ISCC generation time: {:0.4f} seconds", logger=log.info):
                result = iscc.code_iscc(file, all_granular=granular)
            if not isinstance(result, dict):
                typer.echo(f"no result for {file.name} ({result})")
                continue
            if verbose == 0:
                typer.echo(f"ISCC:{result['iscc']}")
            elif verbose == 1:
                typer.echo(f"ISCC:{result['iscc']},{result['filename']}")
            elif verbose == 2:
                typer.echo(result)
            else:
                typer.echo(json.dumps(result, indent=2))
        except Exception as e:
            log.error(f"{file.name} failed with: {str(e).strip()}")


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
