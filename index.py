from typing import Annotated
import typer
from apis.snykApi import get_org_integrations, get_snyk_orgs
from utils.utils import clean_up, find_log_files, find_org_data_files, import_repos, read_csv_file, writeJsonFile, find_batch_import_data_files
from apis.githubapi import list_organizations

app = typer.Typer()

@app.command(name="run-snyk-api-import")
def run_snyk_api_import(
    csv_file_path: str = typer.Option(
        ...,
        "--csv-file-path",
        help="Path to the CSV file containing GitHub organization mappings",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    github_token: str = typer.Option(
        ...,
        "--github-token",
        help="GitHub personal access token for authentication",
        envvar="GITHUB_TOKEN"
    ),
    group_id: str = typer.Option(
        ...,
        "--group-id",
        help="Snyk group ID",
        envvar="SNYK_GROUP_ID"
    ),
    snyk_api_import_name: str = typer.Option(
        ...,
        "--snyk-api-import-name",
        help="Name of the Snyk API import binary in root directory https://github.com/snyk/snyk-api-import/releases",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    snyk_api_tenant: str = typer.Option(
        "api.us.snyk.io",  # Set default value
        "--snyk-api-tenant",
        help="Snyk API tenant listed here: https://docs.snyk.io/snyk-api/rest-api/about-the-rest-api.  Example: api.snyk.io, api.us.snyk.io, api.eu.snyk.io, api.au.snyk.io.  Default: api.us.snyk.io",
        envvar="SNYK_API"
    ),
    snyk_source_org_id: str = typer.Option(
        ...,
        "--snyk-source-org-id",
        help="Snyk source org ID",
        envvar="SNYK_SOURCE_ORG_ID"
    ),
    use_github_cloud_app_integration: bool = typer.Option(
        False,
        "--use-github-cloud-app-integration",
        help="Use the GitHub Cloud App integration for the import if it exists. Default: False",
        is_flag=True,
        envvar="USE_GITHUB_CLOUD_APP_INTEGRATION"
    )
):
    """
    Process the CSV file containing GitHub organization mappings and create organization data for Snyk API import.
    """
    # Validate snyk_api_tenant
    valid_tenants = ["api.snyk.io", "api.us.snyk.io", "api.eu.snyk.io", "api.au.snyk.io"]
    if snyk_api_tenant not in valid_tenants:
        typer.echo(f"Error: Invalid Snyk API tenant. Must be one of: {', '.join(valid_tenants)}")
        raise typer.Exit(1)
    
    # Read the CSV file
    csv_data = read_csv_file(csv_file_path)
    typer.echo(f"Successfully read CSV file with {len(csv_data)} entries")
    
    snykApiImportOrgDataObject = []
    
    try:
        # Get all organizations using the githubapi module from apis package
        github_orgs = list_organizations(github_token)
        print("Collected GitHub orgs")
    except Exception as e:
        print(f"Error in collecting GitHub orgs: {str(e)}")
        raise typer.Exit(1)
        
    try:
        # Get all organizations using the snykapi module from apis package
        snyk_orgs = get_snyk_orgs(group_id, snyk_api_tenant)
        print("Collected Snyk orgs")
    except Exception as e:
        print(f"Error in collecting Snyk orgs: {str(e)}")
        raise typer.Exit(1)

    # Create lookup dictionaries
    github_org_dict = {org['login']: org for org in github_orgs}
    snyk_org_dict = {}
    for org in snyk_orgs:
    # Add entry with slug as key
        snyk_org_dict[org['attributes']['slug']] = org
        # Add entry with name as key
        snyk_org_dict[org['attributes']['name']] = org
        
        # Store matches
        matches = []
    try:
        # Compare CSV entries with both GitHub and Snyk orgs
        for row in csv_data:
            github_org_name = row['GitHub-Org-Name']
            snyk_org = row['Snyk-Org-Name']
            
            # Check if we have matches in both GitHub and Snyk
            if (github_org_name in github_org_dict and 
                snyk_org in snyk_org_dict):
                matches.append({
                    'github_org_name': github_org_name,
                    'snyk_org_id': snyk_org_dict[snyk_org]['id']
                })
        
        for match in matches:
            snykIntegrations = get_org_integrations(match['snyk_org_id'], snyk_api_tenant)
            newSnykApiImportOrgDataObject = {
                    "name": match['github_org_name'],
                    "orgId": match['snyk_org_id'],
                    "integrations": snykIntegrations,
                    "groupId": group_id
                }
            snykApiImportOrgDataObject.append(newSnykApiImportOrgDataObject)
            
    except Exception as e:
        print(f"Error in processing: {str(e)}")
        raise typer.Exit(1)
    
    # Write the snykApiImportOrgDataObject to a json file
    try:
        for index, orgData in enumerate(snykApiImportOrgDataObject):
            snykApiImportOrgDataObject = {"orgData": [orgData]}
            writeJsonFile(snykApiImportOrgDataObject, index)
    except Exception as e:
        print(f"Error in creating org data json files: {str(e)}")
        raise typer.Exit(1)
    
    # Find the json files
    try:
        org_data_files_path = find_org_data_files()
    except Exception as e:
        print(f"Error in finding org data json files: {str(e)}")
        raise typer.Exit(1)
    
    # Import the json files
    try:
        import_repos(org_data_files_path, snyk_api_import_name, snyk_api_tenant, group_id, snyk_source_org_id, use_github_cloud_app_integration)
    except Exception as e:
        print(f"Error in importing repos: {str(e)} \n Continuing with cleanup...")
    
    # Clean up the json and log files
    try:
        clean_up(org_data_files_path, 'json')
        log_files_path = find_log_files()
        clean_up(log_files_path, 'log')
        import_files_path = find_batch_import_data_files()
        clean_up(import_files_path, 'import')
    except Exception as e:
        print(f"Error in cleaning up json files: {str(e)}")
        raise typer.Exit(1)
        
if __name__ == "__main__":
    app()
