from github.MainClass import Github
from typing import List

def list_organizations(github_token: str) -> List[dict]:
    """
    Fetch all organizations for the authenticated user using the GitHub API client.
    
    Args:
        github_token (str): GitHub personal access token
    
    Returns:
        List[dict]: List of organization dictionaries containing id, name, login, and url
    """
    try:
        # Initialize the GitHub client
        github_client = Github(github_token)
        
        # Get authenticated user's organizations
        orgs = github_client.get_user().get_orgs()
        
        # Convert organization objects to dictionaries
        org_list = [
            {
                'id': org.id,
                'name': org.name,  # Full/display name of the organization
                'login': org.login,  # Organization's username/login
                'url': org.html_url
            }
            for org in orgs
        ]
        
        return org_list
        
    except Exception as e:
        raise Exception(f"Failed to fetch organizations: {str(e)}") 