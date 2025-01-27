import typer
from apis.snykApi import get_org_integrations, get_snyk_orgs
from utils.utils import clean_up, find_log_files, find_org_data_files, import_repos, read_csv_file, writeJsonFile
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
    )
):
    """
    Process the CSV file containing GitHub organization mappings and create organization data for Snyk API import.
    """
    # Read the CSV file
    csv_data = read_csv_file(csv_file_path)
    typer.echo(f"Successfully read CSV file with {len(csv_data)} entries")
    
    snykApiImportOrgDataObject = []
    
    try:
        # Get all organizations using the githubapi module from apis package
        github_orgs = list_organizations(github_token)
        
        # Get all organizations using the snykapi module from apis package
        snyk_orgs = get_snyk_orgs(group_id)

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
            snykIntegrations = get_org_integrations(match['snyk_org_id'])
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
        print(f"Error in writing to json file: {str(e)}")
        raise typer.Exit(1)
    
    # Find the json files
    try:
        org_data_files_path = find_org_data_files()
    except Exception as e:
        print(f"Error in finding json files: {str(e)}")
        raise typer.Exit(1)
    
    # Import the json files
    try:
        import_repos(org_data_files_path, snyk_api_import_name)
    except Exception as e:
        print(f"Error in importing repos: {str(e)}")
        raise typer.Exit(1)
    
    # Clean up the json and log files
    try:
        clean_up(org_data_files_path, True)
        log_files_path = find_log_files()
        clean_up(log_files_path, False)
    except Exception as e:
        print(f"Error in cleaning up json files: {str(e)}")
        raise typer.Exit(1)
        
if __name__ == "__main__":
    app()
