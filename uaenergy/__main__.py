"""
A CLI interface for the package.
"""

import click

from .scraping import main as cli_scraping


@click.group()
def cli():
    """
    Combined CLI for uaenergy for scraping and text mining.
    """
    pass


cli.add_command(cli_scraping, "scraping")
cli()
