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

    def get_notifications_count(self) -> int:
        """
        Get count of unread notifications.
        GitHub notifications include: mentions, comments on issues/PRs, reviews, etc.

        Returns:
            Number of unread notifications (up to 100 for performance)
        """
        try:
            notification_count = 0
            page = 1
            per_page = 100
            max_count = 100  # Limit to 100 for performance

            while notification_count < max_count:
                response = self.session.get(
                    f"{self.BASE_URL}/notifications",
                    params={
                        'all': False,  # Only unread
                        'per_page': per_page,
                        'page': page
                    }
                )
                response.raise_for_status()

                notifications = response.json()
                page_count = len(notifications)
                notification_count += page_count

                # If we got fewer than per_page, we've reached the end
                if page_count < per_page:
                    break

                # Check if there are more pages from Link header
                link_header = response.headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break

                page += 1

                # Safety limit
                if notification_count >= max_count:
                    break

            logger.debug(f"Retrieved GitHub notifications count: {notification_count}")
            return min(notification_count, max_count)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting GitHub notifications count: {str(e)}")
            # Return 0 on error instead of raising
            return 0
