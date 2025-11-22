import pytest
import os
import sys

# Add src to path to import the constants
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.constants import (
    GOOGLE_AUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL,
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GITHUB_AUTH_URL, GITHUB_TOKEN_URL, GITHUB_USERINFO_URL,
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET,
    SLACK_AUTH_URL, SLACK_TOKEN_URL, SLACK_USERINFO_URL,
    SLACK_CLIENT_ID, SLACK_CLIENT_SECRET,
    GMAIL_SCOPES, LOGIN_SCOPES, GITHUB_SCOPES, SLACK_SCOPES,
    FRONTEND_URL, BACKEND_URL
)


class TestConstants:

    def test_google_urls_have_valid_values(self):
        """Test that Google OAuth URLs have valid values"""
        assert GOOGLE_AUTH_URL == 'https://accounts.google.com/o/oauth2/v2/auth'
        assert GOOGLE_TOKEN_URL == 'https://oauth2.googleapis.com/token'
        assert GOOGLE_USERINFO_URL == 'https://www.googleapis.com/oauth2/v2/userinfo'

    def test_github_urls_have_valid_values(self):
        """Test that GitHub OAuth URLs have valid values"""
        assert GITHUB_AUTH_URL == 'https://github.com/login/oauth/authorize'
        assert GITHUB_TOKEN_URL == 'https://github.com/login/oauth/access_token'
        assert GITHUB_USERINFO_URL == 'https://api.github.com/user'

    def test_slack_urls_have_valid_values(self):
        """Test that Slack OAuth URLs have valid values"""
        assert SLACK_AUTH_URL == 'https://slack.com/oauth/v2/authorize'
        assert SLACK_TOKEN_URL == 'https://slack.com/api/oauth.v2.access'
        assert SLACK_USERINFO_URL == 'https://slack.com/api/users.identity'

    def test_gmail_scopes_have_values(self):
        """Test that Gmail scopes have values"""
        assert len(GMAIL_SCOPES) > 0
        assert 'https://www.googleapis.com/auth/gmail.readonly' in GMAIL_SCOPES
        assert isinstance(GMAIL_SCOPES[0], str)
        assert len(GMAIL_SCOPES[0]) > 0

    def test_login_scopes_have_values(self):
        """Test that login scopes have values"""
        assert len(LOGIN_SCOPES) == 3
        assert 'openid' in LOGIN_SCOPES
        assert 'https://www.googleapis.com/auth/userinfo.email' in LOGIN_SCOPES
        assert 'https://www.googleapis.com/auth/userinfo.profile' in LOGIN_SCOPES

        for scope in LOGIN_SCOPES:
            assert isinstance(scope, str)
            assert len(scope) > 0

    def test_github_scopes_have_values(self):
        """Test that GitHub scopes have values"""
        assert len(GITHUB_SCOPES) == 3
        assert 'repo' in GITHUB_SCOPES
        assert 'read:user' in GITHUB_SCOPES
        assert 'notifications' in GITHUB_SCOPES

        for scope in GITHUB_SCOPES:
            assert isinstance(scope, str)
            assert len(scope) > 0

    def test_slack_scopes_have_values(self):
        """Test that Slack scopes have values"""
        assert len(SLACK_SCOPES) == 7
        expected_scopes = [
            'channels:read', 'channels:history', 'team:read',
            'groups:read', 'groups:history', 'im:history', 'mpim:history'
        ]

        for scope in expected_scopes:
            assert scope in SLACK_SCOPES

        for scope in SLACK_SCOPES:
            assert isinstance(scope, str)
            assert len(scope) > 0

    def test_frontend_backend_urls_have_values(self):
        """Test that frontend and backend URLs have values"""
        assert FRONTEND_URL is not None
        assert BACKEND_URL is not None
        assert len(FRONTEND_URL) > 0
        assert len(BACKEND_URL) > 0
        assert FRONTEND_URL.startswith('http')
        assert BACKEND_URL.startswith('http')

    def test_all_urls_are_accessible_format(self):
        """Test that all URLs have accessible format"""
        urls = [
            GOOGLE_AUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL,
            GITHUB_AUTH_URL, GITHUB_TOKEN_URL, GITHUB_USERINFO_URL,
            SLACK_AUTH_URL, SLACK_TOKEN_URL, SLACK_USERINFO_URL,
            FRONTEND_URL, BACKEND_URL
        ]

        for url in urls:
            assert url.startswith('https://') or url.startswith('http://')
            assert '.' in url or 'localhost' in url
            assert len(url) > 10

    def test_scopes_lists_are_not_empty(self):
        """Test that all scope lists are not empty"""
        scope_lists = [GMAIL_SCOPES, LOGIN_SCOPES, GITHUB_SCOPES, SLACK_SCOPES]

        for scope_list in scope_lists:
            assert len(scope_list) > 0
            assert isinstance(scope_list, list)
            for scope in scope_list:
                assert isinstance(scope, str)
                assert len(scope) > 2

    def test_oauth_credentials_are_loaded_from_env(self):
        """Test that OAuth credentials are loaded from environment variables"""
        # These can be None in testing environment, but verify they match env vars
        assert GOOGLE_CLIENT_ID == os.getenv('GOOGLE_CLIENT_ID')
        assert GOOGLE_CLIENT_SECRET == os.getenv('GOOGLE_CLIENT_SECRET')
        assert GITHUB_CLIENT_ID == os.getenv('GITHUB_CLIENT_ID')
        assert GITHUB_CLIENT_SECRET == os.getenv('GITHUB_CLIENT_SECRET')
        assert SLACK_CLIENT_ID == os.getenv('SLACK_CLIENT_ID')
        assert SLACK_CLIENT_SECRET == os.getenv('SLACK_CLIENT_SECRET')

    @pytest.mark.skipif(
        not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'),
        reason="OAuth credentials not configured in environment"
    )
    def test_oauth_credentials_are_configured_in_production(self):
        """Test that OAuth credentials are configured (only runs in production)"""
        assert GOOGLE_CLIENT_ID is not None and len(GOOGLE_CLIENT_ID) > 0
        assert GOOGLE_CLIENT_SECRET is not None and len(GOOGLE_CLIENT_SECRET) > 0
        # assert GITHUB_CLIENT_ID is not None and len(GITHUB_CLIENT_ID) > 0
        # assert GITHUB_CLIENT_SECRET is not None and len(GITHUB_CLIENT_SECRET) > 0
        # assert SLACK_CLIENT_ID is not None and len(SLACK_CLIENT_ID) > 0
        # assert SLACK_CLIENT_SECRET is not None and len(SLACK_CLIENT_SECRET) > 0
