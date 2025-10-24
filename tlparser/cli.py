import json
import os
import shutil
import sys
from contextlib import nullcontext

import click

from tlparser.config import Configuration
from tlparser.utils import Utils
from tlparser.viz import Viz

DEFAULT_WD = "workingdir"
DEFAULT_STATI = ["OK"]
DEFAULT_ORDER = ["INV", "LTL", "MTLb", "MITL", "TPTL", "CTLS", "STL"]
DEFAULT_COLOR = [
    "#687dd6",
    "#56ac67",
    "#ba543d",
    "#20d8fd",
    "#8750a6",
    "#696969",
    "#ac9c3d",
]
COLOR_PALETTE = dict(zip(DEFAULT_ORDER, DEFAULT_COLOR))


def get_working_directory(custom_working_dir=None):
    """Get or create the working directory"""

    script_location = os.path.dirname(os.path.abspath(__file__))
    working_dir = (
        os.path.join(script_location, DEFAULT_WD)
        if custom_working_dir is None
        else custom_working_dir
    )

    # Check if the working directory exists
    if not os.path.exists(working_dir):
        # Create the working directory and notify the user
        os.makedirs(working_dir, exist_ok=True)
        click.echo(f"Working directory ['{working_dir}'] has been created.")
    else:
        click.echo(f"Using existing working directory: [{working_dir}]")

    return working_dir


@click.group()
@click.version_option()
def cli():
    """Temporal Logic Parser"""


@cli.command(name="digest")
@click.argument("json_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    default=None,
    help="Path to the output directory.",
)
@click.option(
    "--extended",
    is_flag=True,
    help="Include Spot-based extended columns when Spot CLI tools are available.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show Spot CLI progress when using --extended.",
)
def digest_file(json_file, output, extended, verbose):
    """Processes the JSON file and outputs a CSV"""
    working_dir = get_working_directory(output)
    config = Configuration(
        file_data_in=json_file,
        folder_data_out=working_dir,
        only_with_status=DEFAULT_STATI,
        logic_order=DEFAULT_ORDER,
    )
    util = Utils(config)
    label = "Spot classification" if extended else "Processing formulas"

    def progress_factory(total: int):
        if total <= 0:
            return nullcontext()
        return click.progressbar(length=total, label=label, show_pos=True)

    formulas = util.read_formulas_from_json(
        extended=extended,
        verbose=verbose,
        progress_factory=progress_factory,
    )
    if util.warnings:
        for warning in util.warnings:
            click.echo(warning, err=True)
    out_file = util.write_to_excel(formulas)
    click.echo(f"Processed {json_file} and saved results to {out_file}")

    if util.spot_issues:
        issue_path = os.path.splitext(out_file)[0] + "_errors.md"
        util.save_spot_issue_report(issue_path)
        count = len(util.spot_issues)
        click.echo(
            f"{count} out of {len(formulas)} formulae reported Spot issues; see {issue_path}",
            err=True,
        )

    util.echo_spot_summary(util.spot_issues, total=len(formulas))


@cli.command(name="evaluate")
@click.argument("formula_tokens", nargs=-1)
@click.option(
    "--extended",
    is_flag=True,
    help="Include Spot-based extended columns when Spot CLI tools are available.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show Spot CLI progress when using --extended.",
)
@click.option(
    "--text",
    "requirement_text",
    default=None,
    help="Optional requirement text to include when computing stats.",
)
def evaluate_formula(formula_tokens, extended, verbose, requirement_text):
    """Analyze a single formula and print the statistics."""
    if not formula_tokens:
        raise click.UsageError("Provide a formula to evaluate.")

    formula = " ".join(formula_tokens).strip()

    config = Configuration(logic_order=DEFAULT_ORDER)
    util = Utils(config)
    stats = util.analyze_single_formula(
        formula,
        extended=extended,
        requirement_text=requirement_text,
        verbose=verbose,
    )

    click.echo("Digest results for provided formula:\n")
    click.echo(formula)
    if requirement_text:
        click.echo("")
        click.echo("Requirement text:")
        click.echo(requirement_text)
    click.echo("")
    click.echo(json.dumps(stats.as_serializable(), indent=2, sort_keys=True))

    if util.warnings:
        for warning in util.warnings:
            click.echo(warning, err=True)
    util.echo_spot_summary(util.spot_issues, total=1)


@cli.command(name="visualize")
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Path to the Excel file"
)
@click.option(
    "--latest",
    "-l",
    is_flag=True,
    help="Use the latest Excel file in the working directory",
)
@click.option(
    "--selfonly",
    "-s",
    is_flag=True,
    help="Only focus on natural formalizations (omitting projections)",
)
@click.option(
    "--plot",
    "-p",
    type=click.Choice(
        [
            "hist",
            "viol",
            "viol_req",
            "pair",
            "pair_req",
            "ops",
            "chord",
            "sankey",
            "dag",
            "all",
        ],
        case_sensitive=False,
    ),
    multiple=True,
    help="Specify the plot types to generate",
)
def visualize_data(file, latest, selfonly, plot):
    """Creates a PDF plot from the Excel file"""

    if not (file or latest):
        click.echo("You must provide either --file or --latest.")
        return
    if file and latest:
        latest = False

    working_dir = get_working_directory()
    config = Configuration(
        folder_data_out=working_dir,
        logic_order=DEFAULT_ORDER,
        color_palette=COLOR_PALETTE,
    )
    util = Utils(config)

    # If --latest is used, find the latest file
    if latest:
        file = util.get_latest_excel(config.folder_data_out)
        if len(file) == 0:
            click.echo("No Excel files found in the working directory.")
            return
        click.echo(f"Using latest file: {file}")

    # Read the Excel file
    viz = Viz(config, file, selfonly)
    plot_methods = {
        "hist": viz.plot_histogram,
        "viol": lambda: viz.plot_violin_engcompl(palette_index=1),
        "viol_req": lambda: viz.plot_violin_reqtext(palette_index=0),
        "pair": viz.plot_pairplot,
        "pair_req": lambda: viz.plot_pairplot_reqwords(include_trend=True),
        "ops": viz.plot_operator_bars,
        "chord": viz.plot_chord,
        "sankey": viz.plot_sankey,
        "dag": viz.plot_dag_interactive,
    }

    if "all" in plot or not plot:
        plot = plot_methods.keys()
    for pt in plot:
        click.echo(f"Generating {pt} plot...")
        plot_methods[pt]()

    click.echo("Plot generation completed.")


@cli.command(name="cleanup")
def cleanup_folder():
    """Empties the working folder except JSON files"""
    working_dir = get_working_directory()
    files_to_delete = [f for f in os.listdir(working_dir) if not f.endswith(".json")]
    file_count = len(files_to_delete)

    if file_count == 0:
        click.echo("No files to clean up in the working directory.")
        return

    # Prompt user for confirmation
    if click.confirm(
        f"Execution of this command will remove {file_count} files inside of '{working_dir}'."
        + "\nDo you want to proceed?",
        default=False,
    ):
        for filename in files_to_delete:
            file_path = os.path.join(working_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                click.echo(f"Failed to delete {file_path}. Reason: {e}")

        click.echo(
            f"Cleaned up {file_count} files from the working directory: {working_dir}"
        )
    else:
        click.echo("Cleanup operation aborted.")


@click.command()
def check_spot():
    """Report Spot tool availability and exit non-zero if missing."""
    try:
        from tlparser.spot_tools import print_spot_status
    except Exception:
        click.echo(
            "Spot status check unavailable (missing Spot helper functions).", err=True
        )
        sys.exit(2)
    sys.exit(print_spot_status())
