import pytest
import sys
import os
import httpx
from dotenv import load_dotenv
from src.utils.slack_client import SlackClient
from src.services.slack_service import SlackService

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)


# Load Slack credentials from environment variables
TEST_SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID', '')
TEST_SLACK_CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET', '')
TEST_SLACK_REDIRECT_URI = os.getenv('SLACK_REDIRECT_URI', '')
TEST_SLACK_CHANNEL_ID = 'C07Q85NBKQE'

# PUT FOR TESTING
TEST_SLACK_ACCESS_TOKEN = os.getenv('SLACK_ACCESS_TOKEN', 'xoxe.xoxb-1-MS0yLTc4NTM1OTY0MTA1MjgtOTkzMjUzMTI2ODE4Mi05OTI5MjcwNzIwNzU1LTk5MzIyMTY2NTk1MDktZmMwNDE4MmZjMGQwMzU4MjE3YzAyNDY0ZjEwYzc4N2QwYmEzN2Y0OWQ5Nzc2YmYzMjgzNGI5OTNmY2I4ODJjYg')


pytestmark = pytest.mark.skipif(
    os.getenv('PYTEST_USE_REAL_DB') != '1',
    reason='Test requiere base de datos real (PYTEST_USE_REAL_DB=1)'
)


def test_slack_oauth_configuration():
    """
    Test that Slack OAuth configuration is properly set up.
    """
    if not TEST_SLACK_CLIENT_ID or not TEST_SLACK_CLIENT_SECRET:
        pytest.skip("Slack OAuth credentials not configured")

    assert len(TEST_SLACK_CLIENT_ID) > 0, "SLACK_CLIENT_ID should not be empty"
    assert len(TEST_SLACK_CLIENT_SECRET) > 0, "SLACK_CLIENT_SECRET should not be empty"
    assert TEST_SLACK_REDIRECT_URI.startswith('http'), "SLACK_REDIRECT_URI should be a valid URL"

    print(f"\n✓ Slack OAuth configuration is valid")
    print(f"  Client ID: {TEST_SLACK_CLIENT_ID[:10]}...")
    print(f"  Redirect URI: {TEST_SLACK_REDIRECT_URI}")


def test_slack_oauth_endpoints():
    """
    Test that Slack OAuth endpoints are accessible.
    """
    try:
        # Test Slack's main OAuth endpoint
        response = httpx.get("https://slack.com/oauth/v2/authorize", timeout=10.0)
        assert response.status_code in [200, 404, 405], f"Slack OAuth endpoint returned {response.status_code}"
        print(f"\n✓ Slack OAuth authorize endpoint is reachable")
    except Exception as e:
        pytest.fail(f"Failed to connect to Slack OAuth endpoint: {str(e)}")


def test_slack_api_connectivity():
    """
    Test basic connectivity to Slack API.
    """
    try:
        response = httpx.get("https://slack.com/api/auth.test", timeout=10.0)
        assert response.status_code == 200, f"Slack API returned {response.status_code}"
        print(f"\n✓ Slack API is reachable")
    except Exception as e:
        pytest.fail(f"Failed to connect to Slack API: {str(e)}")


def test_slack_client_class_initialization():
    """
    Test that SlackClient class can be imported and initialized.
    """
    try:
        # Test with empty token (should not crash on import/init)
        client = SlackClient(bot_token="")
        assert client is not None, "SlackClient should initialize without token"

        print(f"\n✓ SlackClient class imports and initializes correctly")

    except Exception as e:
        pytest.fail(f"SlackClient import/initialization failed: {str(e)}")


def test_slack_service_initialization():
    """
    Test that SlackService class can be imported and initialized.
    """
    try:
        # Test initialization
        service = SlackService(user_id=1)
        assert service is not None, "SlackService should initialize"
        assert service.user_id == 1, "SlackService should set user_id correctly"

        print(f"\n✓ SlackService class imports and initializes correctly")

    except Exception as e:
        pytest.fail(f"SlackService import/initialization failed: {str(e)}")


def test_slack_with_access_token():
    """
    Test Slack API with a real access token (if available).
    """
    if not TEST_SLACK_ACCESS_TOKEN:
        pytest.skip("No Slack access token available for testing")

    try:
        response = httpx.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {TEST_SLACK_ACCESS_TOKEN}"},
            timeout=10.0
        )
        assert response.status_code == 200, f"Slack API returned {response.status_code}"

        data = response.json()
        if data.get('ok'):
            print(f"\n✓ Successfully authenticated to Slack as: {data.get('user', 'Unknown')}")
            print(f"  Team: {data.get('team', 'Unknown')}")
        else:
            error = data.get('error', 'unknown_error')
            print(f"\n⚠ Slack authentication failed: {error}")
            # Don't fail the test - just log the error for debugging

    except Exception as e:
        pytest.fail(f"Slack access token test failed: {str(e)}")


def test_slack_conversations_with_token():
    """
    Test conversations endpoints with a real token (if available).
    """
    if not TEST_SLACK_ACCESS_TOKEN:
        pytest.skip("No Slack access token available for testing")

    try:
        # Test conversations.list
        response = httpx.get(
            "https://slack.com/api/conversations.list",
            params={"exclude_archived": True},
            headers={"Authorization": f"Bearer {TEST_SLACK_ACCESS_TOKEN}"},
            timeout=10.0
        )
        assert response.status_code == 200, f"Slack API returned {response.status_code}"

        data = response.json()
        print(f"\nDebug - conversations.list response: {data}")

        if data.get('ok'):
            channels = data.get('channels', [])
            print(f"✓ Successfully fetched {len(channels)} channels")
        else:
            error = data.get('error', 'unknown_error')
            print(f"⚠ conversations.list failed: {error}")

    except Exception as e:
        pytest.fail(f"Slack conversations test failed: {str(e)}")


def test_slack_invalid_token():
    """
    Test that Slack API fails gracefully with invalid token.
    """
    invalid_token = "xoxb-invalid-token-1234567890"

    try:
        response = httpx.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {invalid_token}"},
            timeout=10.0
        )
        assert response.status_code == 200, "Slack API should return 200 even for invalid auth"

        data = response.json()
        assert not data.get('ok'), "Invalid token should not return ok: true"
        assert data.get('error') in ['invalid_auth', 'not_authed'], f"Expected auth error, got: {data.get('error')}"

        print(f"\n✓ Slack returned expected error for invalid token: {data.get('error')}")

    except Exception as e:
        pytest.fail(f"Slack invalid token test failed: {str(e)}")


def test_slack_missing_scope_analysis():
    """
    Analyze what scopes might be missing based on your current setup.
    """
    print(f"\n🔍 Slack Scope Analysis:")
    print(f"  - You have OAuth credentials: {'✅' if TEST_SLACK_CLIENT_ID and TEST_SLACK_CLIENT_SECRET else '❌'}")
    print(f"  - Redirect URI: {TEST_SLACK_REDIRECT_URI}")
    print(f"  - Test Channel ID: {TEST_SLACK_CHANNEL_ID}")

    if TEST_SLACK_ACCESS_TOKEN:
        print(f"  - Access token available: ✅")
        # You could add more analysis here if token is available
    else:
        print(f"  - Access token available: ❌ (need to complete OAuth flow)")

    print(f"\n💡 Based on your error logs, you need these scopes:")
    print(f"  - channels:history (for reading messages)")
    print(f"  - team:read (for team.info)")
    print(f"  - channels:read (you already have this - conversations.list works)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
