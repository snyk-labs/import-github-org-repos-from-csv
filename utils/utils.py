import csv
import json
import shutil
from typing import List, Dict
import typer
from datetime import date
import subprocess
import os

from apis.snykApi import create_snyk_org, get_snyk_org_data, get_snyk_orgs, get_org_integrations

current_directory = os.getcwd()

def read_csv_file(csv_file_path: str) -> List[Dict[str, str]]:
    """
    Read the CSV file and return its contents as a list of dictionaries.
    """
    try:
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            return list(csv_reader)
    except FileNotFoundError:
        typer.echo(f"Error: Could not find CSV file at {csv_file_path}")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error reading CSV file: {str(e)}")
        raise typer.Exit(code=1) 
    
# Write snyk-created-orgs.json file
def writeJsonFile(orgDataObject, index):
    fileName = f'snyk-created-orgs-{index}.json'
    try:
        with open(fileName, 'w') as json_file:
            json.dump(orgDataObject, json_file, indent=4)
    except:
        print('Failed to create json file.')
        
def find_org_data_files():
    org_data_files_path = []
    org_data_file_name = 'snyk-created-orgs-'
    matching_files = [f for f in os.listdir(current_directory) if f.startswith(org_data_file_name)]

    # print("Files that start with '{}':".format(org_data_file_name))
    for file in matching_files:
        file_path = current_directory + '/' + file
        org_data_files_path.append(file_path)
    return org_data_files_path

def find_log_files():
    log_files = [f for f in os.listdir(current_directory) if f.endswith('.log')]
    log_file_data = []
    for file in log_files:
        file_path = current_directory + '/' + file
        log_file_data.append(file_path)
    return log_file_data

# Split large import data file into smaller batches and return list of new file paths.
def split_import_data_file(file_path: str, batch_size: int = 1000) -> tuple[List[str], str | None]:
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        targets = data['targets']
        if len(targets) <= batch_size:
            return ([file_path], None)
            
        # Split targets into batches
        batched_files = []
        for i in range(0, len(targets), batch_size):
            batch = targets[i:i + batch_size]
            batch_file_name = f'github-enterprise-import-targets-batch-{i//batch_size + 1}.json'
            batch_data = {'targets': batch}
            
            with open(batch_file_name, 'w') as f:
                json.dump(batch_data, f, indent=2)
            batched_files.append(os.path.join(current_directory, batch_file_name))
        
        # Get the orgId from first target in first batch for reference
        org_id = targets[0]['orgId']
        print(f'Here is the orgId in split_import_data_file method: {org_id}')
        return (batched_files, org_id)
        
    except Exception as e:
        print(f'Error splitting import data file: {str(e)}')
        return ([], None)

def find_import_data_file():
    import_data_file_name = 'github-enterprise-import-targets.json'
    matching_file = [f for f in os.listdir(current_directory) if f.startswith(import_data_file_name)]
    print(f'Here is the length of the import file list: {len(matching_file)}')
    if len(matching_file) >= 1:
        matching_file = current_directory + '/' + matching_file[0]
        return matching_file
    else:
        return None
    
def find_matching_org_id(org_data: dict, group_org_data: list, index: int) -> str | None:
    org_name = org_data['attributes']['name']
    indexed_name = f"{org_name}-{index}"
    
    for group_org in group_org_data:
        if group_org['attributes']['name'] == indexed_name:
            return group_org['id']
    
    return None   

def import_repos(org_data_files_path, snyk_api_import_name, snyk_api_tenant, group_id, source_org_id):
    group_org_data = get_snyk_orgs(group_id, snyk_api_tenant)
    for org_data_file_path in org_data_files_path:
        print(org_data_file_path)
        org_data_value = f'--orgsData={org_data_file_path}'
        # Run snyk-api-import import:data command
        subprocess.run(f'SNYK_API=https:/{snyk_api_tenant}/v1 {current_directory}/{snyk_api_import_name} import:data {org_data_value} --source=github-enterprise --integrationType=github-enterprise', shell=True)
        
        # Find and split import data file if needed
        import_file_path = find_import_data_file()
        if import_file_path:
            import_files = split_import_data_file(import_file_path)
            print(f'Here is the import files: {import_files}')
            
            if import_files[1] != None:
                org_data = get_snyk_org_data(import_files[1], snyk_api_tenant)              
                
                # Process each batch file
                for index, batch_file in enumerate(import_files[0]):
                    print(f'Processing batch file number: {index}.  File name: {batch_file}')
                    if index > 0:
                        matching_org_id = find_matching_org_id(org_data, group_org_data, index + 1)
                        if matching_org_id == None:
                            print(f'No matching orgId found for {org_data["attributes"]["name"]} - {index + 1} \n Creating new org...')
                            # Create new org and get orgId.  Then add orgId to batch file and import
                            new_org_data = create_snyk_org(org_data, source_org_id, index + 1, group_id, snyk_api_tenant)
                            matching_org_id = new_org_data['id']
                            
                            print(f'Adding new orgId {matching_org_id} to batch file {batch_file}')
                            # subprocess.run(f'DEBUG=* SNYK_API=https:/{snyk_api_tenant}/v1  {current_directory}/{snyk_api_import_name} import --file={batch_file}', shell=True)
                            integrations = get_org_integrations(matching_org_id, snyk_api_tenant)
                            update_batch_file_ids(batch_file, matching_org_id, integrations)
                            subprocess.run(f'SNYK_API=https:/{snyk_api_tenant}/v1  {current_directory}/{snyk_api_import_name} import --file={batch_file}', shell=True)
                        else:
                            # Add orgId to batch file and import
                            print(f'Found matching orgId {matching_org_id} for {org_data["attributes"]["name"]} - {index + 1} \n Adding orgId to batch file {batch_file}')
                            integrations = get_org_integrations(matching_org_id, snyk_api_tenant)
                            # subprocess.run(f'DEBUG=* SNYK_API=https:/{snyk_api_tenant}/v1  {current_directory}/{snyk_api_import_name} import --file={batch_file}', shell=True)
                            update_batch_file_ids(batch_file, matching_org_id, integrations)
                            subprocess.run(f'SNYK_API=https:/{snyk_api_tenant}/v1  {current_directory}/{snyk_api_import_name} import --file={batch_file}', shell=True)
            else:
                print(f'Importing data file {import_file_path}')
                # subprocess.run(f'DEBUG=* SNYK_API=https:/{snyk_api_tenant}/v1  {current_directory}/{snyk_api_import_name} import --file={batch_file}', shell=True)
                subprocess.run(f'SNYK_API=https:/{snyk_api_tenant}/v1  {current_directory}/{snyk_api_import_name} import --file={import_file_path}', shell=True)
                    
        else:
            print('No import file found.')

def clean_up(list_of_files, switch):
    today_date = date.today()
    formatted_date = today_date.strftime("%m%d%Y")
    
    # Define folder names based on switch value
    match switch:
        case "json":
            folder_name = f'json-files-dir-{formatted_date}'
        case "log":
            folder_name = f'log-files-dir-{formatted_date}'
        case "import":
            folder_name = f'import-files-dir-{formatted_date}'
        case _:
            print("Invalid switch value")
            return

    file_name_counter = 2
    making_directory = True

    # Create the new directory
    while making_directory:
        if os.path.exists(current_directory + '/' + folder_name):
            try:
                os.makedirs(current_directory + '/' + folder_name + '-run#' + str(file_name_counter))
                new_dir_path = current_directory + '/' + folder_name + '-run#' + str(file_name_counter)
                making_directory = False
            except:
                file_name_counter = file_name_counter + 1
        else:
            os.makedirs(current_directory + '/' + folder_name)
            new_dir_path = current_directory + '/' + folder_name
            making_directory = False

    # Move files to the new directory
    for file in list_of_files:
        # Check if the file exists
        if os.path.isfile(file):
            # Strip out file name
            split = file.split('/')
            file_name = split[(len(split)-1)]
            # Move the file
            shutil.move(file, os.path.join(new_dir_path, file_name))
        else:
            print(f"File {file} does not exist")

def find_batch_import_data_files():
    """Find all GitHub Enterprise import target files in the current directory."""
    import_data_file_name = 'github-enterprise-import-targets'
    matching_files = [os.path.join(current_directory, f) for f in os.listdir(current_directory) 
                     if f.startswith(import_data_file_name) and f.endswith('.json')]
    
    if not matching_files:
        print('No import files found')
        return []
        
    return matching_files


def update_batch_file_ids(batch_file_path: str, org_id: str, integrations: dict) -> None:
    # Get GitHub Enterprise integration ID
    github_enterprise_id = integrations.get('github-enterprise')
    if not github_enterprise_id:
        raise ValueError("GitHub Enterprise integration ID not found in integrations response")

    try:
        with open(batch_file_path, 'r') as file:
            data = json.load(file)
        
        if not isinstance(data, dict) or 'targets' not in data:
            raise ValueError("Invalid batch file format: missing 'targets' key")

        # Update both orgId and integrationId for all targets
        for target in data['targets']:
            target['orgId'] = org_id
            target['integrationId'] = github_enterprise_id

        with open(batch_file_path, 'w') as file:
            json.dump(data, file, indent=2)
            
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in batch file: {str(e)}")
    except IOError as e:
        raise IOError(f"Error accessing batch file: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error updating batch file: {str(e)}")
