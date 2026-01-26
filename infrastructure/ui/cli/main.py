import click
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import service contracts and DTOs
from application.contracts.form_comparator_service import FormComparatorService
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from application.dtos import ComparisonResultDTO

@click.group()
@click.pass_context
def cli(ctx):
    """XLSForm Data Source Tools CLI."""
    # This group serves as the entry point for all subcommands.
    # Services from the IoC container are passed via ctx.obj.
    pass

@cli.command("compare-sql")
@click.option('--country', required=True, help='Country code (e.g., RCI, MALI).')
@click.option('--github-form', required=True, help='XLSForm name in GitHub (without .xlsx extension).')
@click.option('--bigquery-view', required=True, help='Full BigQuery view ID (e.g., project.dataset.view_name).')
@click.pass_context
def compare_sql(ctx, country, github_form, bigquery_view):
    """Compares an XLSForm from GitHub with a BigQuery SQL view."""
    form_comparator_service: FormComparatorService = ctx.obj['form_comparator_service']
    code_repository: CodeRepository = ctx.obj['code_repository']
    data_warehouse_repository: DataWarehouseRepository = ctx.obj['data_warehouse_repository']

    click.echo(f"Comparing XLSForm '{github_form}' from GitHub with BigQuery view '{bigquery_view}' for country '{country}'...")

    try:
        # 1. Fetch XLSForm content from GitHub
        xls_path_prefix = "muso-mali/forms/app/" if country.upper() == "MALI" else "muso-cdi/forms/app/"
        xls_path = f"{xls_path_prefix}{github_form}.xlsx"
        xls_content = code_repository.download_file(branch="master", file_path=xls_path)
        click.echo(f"Successfully downloaded '{github_form}.xlsx' from GitHub.")

        # 2. Fetch SQL content from BigQuery
        project_id, dataset_id, view_id = bigquery_view.split('.')
        sql_content = data_warehouse_repository.get_view_query(project_id, dataset_id, view_id)
        click.echo(f"Successfully fetched SQL for view '{bigquery_view}'.")

        # 3. Perform comparison
        result_dto: ComparisonResultDTO = form_comparator_service.compare_form_with_sql(
            xls_content=xls_content,
            sql_content=sql_content.encode('utf-8'), # Ensure it's bytes for the service
            country_code=country
        )

        # 4. Print results
        click.echo("\n--- Comparison Results ---")
        if result_dto.not_founds:
            click.secho("❌ Not Found (Critical):", fg="red")
            for item in result_dto.not_founds:
                click.echo(f"  - Element: {item.element_name}, Path: {item.json_path}")
        if result_dto.not_found_bm_elements:
            click.secho("ℹ️ Not Found `_bm` Elements (RCI Only):", fg="blue")
            for item in result_dto.not_found_bm_elements:
                click.echo(f"  - Element: {item.element_name}, Path: {item.json_path}")
        if result_dto.founds:
            click.secho("✅ Found in SQL:", fg="green")
            for item in result_dto.founds:
                click.echo(f"  - Element: {item.element_name}, Path: {item.json_path}, Count: {item.count}, Lines: {item.lines}")
        
        if not result_dto.founds and not result_dto.not_founds and not result_dto.not_found_bm_elements:
            click.secho("No discrepancies found and no elements to compare.", fg="green")

    except Exception as e:
        click.secho(f"Error during comparison: {e}", fg="red", err=True)
        sys.exit(1)

def build_ui(
    form_comparator_service: FormComparatorService,
    code_repository: CodeRepository,
    data_warehouse_repository: DataWarehouseRepository,
    # Add other services as needed for future CLI commands
    **kwargs # Catch any extra services not explicitly used by the CLI for now
):
    """
    Entry point for the CLI UI. This function is called by the IoC container.
    It stores the services in the Click context and invokes the CLI.
    """
    # Store services in the Click context object
    # This allows sub-commands to access them via @click.pass_context
    ctx = click.Context(cli, obj={
        'form_comparator_service': form_comparator_service,
        'code_repository': code_repository,
        'data_warehouse_repository': data_warehouse_repository,
        # Add other services here as they become relevant to CLI commands
    })
    
    # Invoke the CLI command group. This will parse sys.argv and call the appropriate sub-command.
    ctx.invoke(cli)
