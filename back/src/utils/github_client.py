import logging
from typing import Any, Dict, Optional

import requests


logger = logging.getLogger(__name__)

class GitHubClient:
    """
    GitHub API client for authenticating and fetching user or repository data.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: str):
        """
        Initialize GitHub client with personal or OAuth access token.

        Args:
            access_token: GitHub personal access token or OAuth token.
        """
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "DevFriendApp"
        })

    def get_user(self) -> Dict[str, Any]:
        """
        Get the authenticated user's GitHub profile information.
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/user")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching GitHub user profile: {str(e)}")
            raise Exception(f"GitHub API error: {str(e)}")

    def get_repos(self, visibility: str = "all") -> Dict[str, Any]:
        """
        Get list of repositories for the authenticated user.

        Args:
            visibility: 'all', 'public', or 'private' (default: 'all')
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/user/repos", params={"visibility": visibility})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching GitHub repositories: {str(e)}")
            raise Exception(f"GitHub API error: {str(e)}")

    def get_repo_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get details for a specific repository.

        Args:
            owner: Repository owner username
            repo: Repository name
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/repos/{owner}/{repo}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching GitHub repo details: {str(e)}")
            raise Exception(f"GitHub API error: {str(e)}")
