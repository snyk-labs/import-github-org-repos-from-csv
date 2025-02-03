import csv
import json
import shutil
from typing import List, Dict
import typer
from datetime import date
import subprocess
import os

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

def find_import_data_file():
    import_data_file_name = 'github-enterprise-import-targets.json'
    matching_file = [f for f in os.listdir(current_directory) if f.startswith(import_data_file_name)]
    print(matching_file)
    print(f'Here is the length of the import file list: {len(matching_file)}')
    if len(matching_file) >= 1:
        matching_file = current_directory + '/' + matching_file[0]
        return matching_file
    else:
        return None   

def import_repos(org_data_files_path, snyk_api_import_name, snyk_token):
    for org_data_file_path in org_data_files_path:
        print(org_data_file_path)
        org_data_value = f'--orgsData={org_data_file_path}'
        # Run snyk-api-import import:data command
        subprocess.run(f'SNYK_TOKEN={snyk_token} SNYK_API=https:/api.us.snyk.io/v1 {current_directory}/{snyk_api_import_name} import:data {org_data_value} --source=github-enterprise --integrationType=github-enterprise', shell=True)
        # Find github-import-targets.json and run import
        import_file_path = find_import_data_file()
        subprocess.run(f'DEBUG=* SNYK_TOKEN={snyk_token} SNYK_API=https:/api.us.snyk.io/v1  {current_directory}/{snyk_api_import_name} import --file={import_file_path}', shell=True)
        
def clean_up(list_of_files, switch):
    today_date = date.today()
    formatted_date = today_date.strftime("%m%d%Y")
    folder_name_json_files = f'json-files-dir-{formatted_date}'
    folder_name_log_files = f'log-files-dir-{formatted_date}'
    file_name_counter = 2
    making_directory = True

    # Create the new directory
    if switch:
        while making_directory:
            if os.path.exists(current_directory + '/' + folder_name_json_files):
                try:
                    os.makedirs(current_directory + '/' + folder_name_json_files + '-run#' + str(file_name_counter))
                    new_dir_path = current_directory + '/' + folder_name_json_files + '-run#' + str(file_name_counter)
                    making_directory = False
                except:
                    file_name_counter = file_name_counter + 1
            else:
                os.makedirs(current_directory + '/' + folder_name_json_files)
                new_dir_path = current_directory + '/' + folder_name_json_files
                making_directory = False
    else:
        while making_directory:
            if os.path.exists(current_directory + '/' + folder_name_log_files):
                try:
                    os.makedirs(current_directory + '/' + folder_name_log_files + '-run#' + str(file_name_counter))
                    new_dir_path = current_directory + '/' + folder_name_log_files + '-run#' + str(file_name_counter)
                    making_directory = False
                except:
                    file_name_counter = file_name_counter + 1
            else:
                os.makedirs(current_directory + '/' + folder_name_log_files)
                new_dir_path = current_directory + '/' + folder_name_log_files
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
