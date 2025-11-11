import logging
from typing import Any, Dict, List, Optional

import requests


logger = logging.getLogger(__name__)

class SlackClient:
    """
    Slack API client for authenticating and fetching channels, messages, and user data.
    """

    BASE_URL = "https://slack.com/api"

    def __init__(self, bot_token: str):
        """
        Initialize Slack client with bot token.

        Args:
            bot_token: Slack bot token (xoxb-...)
        """
        self.bot_token = bot_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to Slack API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., 'users.info')
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON as dict
        """
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=kwargs.get('params', {}))
            else:
                response = self.session.post(url, json=kwargs.get('json', {}))

            response.raise_for_status()
            data = response.json()

            if not data.get('ok'):
                error = data.get('error', 'unknown_error')
                logger.error(f"Slack API error: {error}")
                raise Exception(f"Slack API error: {error}")

            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making Slack API request: {str(e)}")
            raise Exception(f"Slack API error: {str(e)}")

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get the authenticated bot's user information.
        """
        try:
            response = self._make_request('GET', 'auth.test')
            return response
        except Exception as e:
            logger.error(f"Error fetching Slack user info: {str(e)}")
            raise

    def get_channels(self, exclude_archived: bool = True) -> List[Dict[str, Any]]:
        """
        Get list of channels in the workspace.

        Args:
            exclude_archived: Whether to exclude archived channels (default: True)

        Returns:
            List of channels
        """
        try:
            params = {'exclude_archived': exclude_archived}
            response = self._make_request('GET', 'conversations.list', params=params)
            return response.get('channels', [])
        except Exception as e:
            logger.error(f"Error fetching Slack channels: {str(e)}")
            raise

    def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 100,
        oldest: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a specific channel.

        Args:
            channel_id: Channel ID (e.g., 'C1234567890')
            limit: Maximum number of messages to return (default: 100, max: 1000)
            oldest: Timestamp of oldest message to include (optional)

        Returns:
            List of messages
        """
        try:
            params = {
                'channel': channel_id,
                'limit': min(limit, 1000)  # Slack API max is 1000
            }
            if oldest:
                params['oldest'] = oldest

            response = self._make_request('GET', 'conversations.history', params=params)
            return response.get('messages', [])
        except Exception as e:
            logger.error(f"Error fetching Slack channel messages: {str(e)}")
            raise

    def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get workspace/team information.
        """
        try:
            response = self._make_request('GET', 'team.info')
            return response.get('team', {})
        except Exception as e:
            logger.error(f"Error fetching Slack workspace info: {str(e)}")
            raise

    def get_users(self) -> List[Dict[str, Any]]:
        """
        Get list of users in the workspace.
        """
        try:
            response = self._make_request('GET', 'users.list')
            return response.get('members', [])
        except Exception as e:
            logger.error(f"Error fetching Slack users: {str(e)}")
            raise
