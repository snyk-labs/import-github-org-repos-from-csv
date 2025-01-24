import json
import requests
from requests.exceptions import HTTPError
import time

from helpers.helper import get_snyk_token

SNYK_TOKEN = get_snyk_token()

restHeaders = {'Content-Type': 'application/vnd.api+json', 'Authorization': f'token {SNYK_TOKEN}'}
v1Headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': f'token {SNYK_TOKEN}'}
rest_version = '2024-10-15'

# Create a request method
def create_request_method(method):
    methods = {
        'GET': requests.get,
        'POST': requests.post,
        'PUT': requests.put,
        'DELETE': requests.delete,
        'PATCH': requests.patch,
    }

    http_method = methods.get(method.upper())
    
    return http_method

# Paginate through Snyk's API endpoints with retry and backoff
def pagination_snyk_rest_endpoint(method, url, *args):
    retries = 3
    delay = 5
    http_method = create_request_method(method)
    if any(args):
        for attempt in range(retries):
            try:
                api_response = http_method(url, headers=restHeaders, data=json.dumps(args[0]))
                api_response.raise_for_status()
                return api_response
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    print("All attempts failed.")
                    raise
    else:
        has_next_link = True
        data = []
        while has_next_link:
            for attempt in range(retries):
                try:
                    api_response = http_method(url, headers=restHeaders)
                    api_data = api_response.json()['data']
                    data.extend(api_data)
                    # If the response status is 429, handle the rate limit
                    if api_response.status_code == 429:
                        print(f"Rate limit exceeded. Waiting for 60 seconds.")
                        time.sleep(61)
                        continue
                except requests.RequestException as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        print("All attempts failed.")
                        raise
                
                # Check if next page exist and set url if it does.  If not, exit and return issuesData
                try:
                    api_response.json()['links']['next']
                    url = 'https://api.snyk.io' + api_response.json()['links']['next']
                except:
                    has_next_link = False
                    return data
                

def get_org_integrations(orgId, orgName = 'No Name provided'):
    # print(f"Collecting organization integrations for {orgName}")
    url = f'https://api.snyk.io/v1/org/{orgId}/integrations'

    try:
        integrationsApiResponse = requests.get(url, headers=v1Headers)
        return integrationsApiResponse.json()
    except HTTPError as exc:
        # Raise an error
        print("Snyk Integrations endpoint failed.")
        print(exc)


def get_snyk_orgs(groupId):
    print("Collecting organization IDs")
    url = f'https://api.snyk.io/rest/groups/{groupId}/orgs?version={rest_version}&limit=100'
    hasNextLink = True
    orgs = []

    while hasNextLink:
        try:
            orgApiResponse = requests.get(url, headers=restHeaders)
            orgData = orgApiResponse.json()['data']
            orgs.extend(orgData)
        except:
            print("Orgs endpoint call failed.")
            print(orgApiResponse)
        
        # Check if next page exist and set url if it does.  If not, exit and return issuesData
        try:
            orgApiResponse.json()['links']['next']
            url = 'https://api.snyk.io' + orgApiResponse.json()['links']['next']
        except:
            hasNextLink = False
            return orgs
        
# Get all snyk targets in org.
def get_snyk_targets(org_id):
    url = f'https://api.snyk.io/rest/orgs/{org_id}/targets?version={rest_version}&limit=100'
    
    target_data = pagination_snyk_rest_endpoint('GET', url)
    
    return target_data

def delete_target(org_id, target_id):
    url = f'https://api.snyk.io/rest/orgs/{org_id}/targets/{target_id}?version={rest_version}'
    
    response = requests.delete(url, headers=restHeaders)
    
    return response