# Create snyk-created-orgs.json based off of Snyk and GitHub Organization Names

This script will search your GitHub organizations for any matching Snyk organization based off of GitHub organization mapping in a csv.  If matches are found, it will generate snyk-created-orgs.json which will be used to import repos into Snyk.

## Requirements

Python version 3.9.5, 3.10.0

Download [snyk-api-import](https://github.com/snyk/snyk-api-import/releases), make the file executable, and place the file in the root directory of this repo.

## Required Environment Variables

[SNYK_TOKEN](https://docs.snyk.io/getting-started/how-to-obtain-and-authenticate-with-your-snyk-api-token)

SNYK_LOG_PATH - This needs to be the full path to the root directory of this repo.

## Script Arguments

csv-file-path - Path to the csv file with GitHub organization data.

[github-token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

[group-id](https://docs.snyk.io/snyk-admin/groups-and-organizations/groups/group-general-settings)

[snyk-api-import-name](https://github.com/snyk/snyk-api-import/releases) - Name of the Snyk API import binary in root directory 



## Running
```bash
git clone https://github.com/snyk-labs/import-gitlab-repo-from-csv.git
pip install -r requirements.txt
python3 index.py --csv-file-path=FULL-PATH-TO-CSV-File --github-token=GITHUB-TOKEN --group-id=SNYK-GROUP-ID --snyk-api-import-name=snyk-api-import
```

## Example run command
python3 index.py --csv-file-path=FULL-PATH-TO-CSV-File --github-token=GITHUB-TOKEN --group-id=SNYK-GROUP-ID --snyk-api-import-name=snyk-api-import
