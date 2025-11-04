import base64
import json
import logging
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailClient:
    """
    Gmail API client for authenticating and retrieving emails.
    Uses OAuth 2.0 with refresh token for authentication.
    """

    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, credentials_data: Dict[str, Any]):
        """
        Initialize Gmail client with credentials.
        
        Args:
            credentials_data: Dictionary containing:
                - client_id: Google OAuth client ID
                - client_secret: Google OAuth client secret
                - refresh_token: OAuth refresh token
                - redirect_uri: Optional redirect URI
        """
        self.credentials_data = credentials_data
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """
        Authenticate with Gmail API using refresh token.
        """
        try:
            creds = Credentials(
                token=None,
                refresh_token=self.credentials_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.credentials_data.get('client_id'),
                client_secret=self.credentials_data.get('client_secret'),
                scopes=self.SCOPES
            )

            # Refresh the token to get a new access token
            if creds.expired or not creds.valid:
                creds.refresh(Request())

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.debug("Gmail API client authenticated successfully")

        except Exception as e:
            logger.error(f"Error authenticating with Gmail API: {str(e)}")
            raise Exception(f"Failed to authenticate with Gmail: {str(e)}")

    def get_messages(self, max_results: int = 10, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of email messages.
        
        Args:
            max_results: Maximum number of messages to return (default: 10)
            query: Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
        
        Returns:
            List of message dictionaries with id, threadId, and snippet
        """
        try:
            if not self.service:
                raise Exception("Gmail service not initialized")

            # List messages
            messages_list = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()

            messages = messages_list.get('messages', [])
            logger.debug(f"Retrieved {len(messages)} messages from Gmail")
            return messages

        except HttpError as e:
            logger.error(f"Gmail API error getting messages: {str(e)}")
            raise Exception(f"Failed to get messages from Gmail: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            raise

    def get_message_details(self, message_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific message.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Dictionary with message details including headers, body, etc.
        """
        try:
            if not self.service:
                raise Exception("Gmail service not initialized")

            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return self._parse_message(message)

        except HttpError as e:
            logger.error(f"Gmail API error getting message details: {str(e)}")
            raise Exception(f"Failed to get message details: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting message details: {str(e)}")
            raise

    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gmail message format into our application format.
        
        Args:
            message: Raw Gmail API message object
        
        Returns:
            Parsed message dictionary
        """
        payload = message.get('payload', {})
        headers = payload.get('headers', [])

        # Extract headers
        headers_dict = {h['name']: h['value'] for h in headers}
        
        # Get subject
        subject = headers_dict.get('Subject', '')
        
        # Get sender
        sender = headers_dict.get('From', '')
        
        # Get date
        date = headers_dict.get('Date', '')
        
        # Get body
        body = self._extract_body(payload)
        
        # Get labels (to determine if read)
        labels = message.get('labelIds', [])
        is_read = 'UNREAD' not in labels

        return {
            'id': message.get('id'),
            'thread_id': message.get('threadId'),
            'sender': sender,
            'subject': subject,
            'preview': body[:200] if body else '',
            'date': date,
            'read': is_read,
            'snippet': message.get('snippet', '')
        }

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract text body from message payload.
        
        Args:
            payload: Message payload from Gmail API
        
        Returns:
            Plain text body
        """
        body = ''
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
        else:
            # Single part message
            if payload.get('mimeType') == 'text/plain':
                data = payload.get('body', {}).get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

        return body

    def get_profile(self) -> Dict[str, Any]:
        """
        Get Gmail user profile information.
        
        Returns:
            Dictionary with email address and other profile info
        """
        try:
            if not self.service:
                raise Exception("Gmail service not initialized")

            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'email_address': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0)
            }

        except HttpError as e:
            logger.error(f"Gmail API error getting profile: {str(e)}")
            raise Exception(f"Failed to get Gmail profile: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            raise

