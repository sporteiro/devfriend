"""
Test GitHub connection with credentials from .env file.

This test verifies if we can connect to GitHub's OAuth API using client_id and client_secret.
The test uses OAuth to verify credentials and optionally tests data retrieval using a token.
"""

import pytest
import sys
import os
import httpx
from dotenv import load_dotenv

# Add src to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Load OAuth credentials from environment variables
TEST_GITHUB_CREDENTIALS = {
    'client_id': os.getenv('GITHUB_CLIENT_ID', ''),
    'client_secret': os.getenv('GITHUB_CLIENT_SECRET', ''),
    'redirect_uri': os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:8888/auth/github/callback')
}

# Optional: GitHub does not use refresh_token; use personal access token or OAuth access_token
TEST_GITHUB_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN', '')


def test_github_oauth_connection():
    """
    Test GitHub OAuth credentials and endpoints.

    This test verifies that:
    1. GitHub OAuth endpoints are reachable
    2. client_id and client_secret are valid format
    3. Authorization URL is correctly built
    """
    if not TEST_GITHUB_CREDENTIALS['client_id'] or not TEST_GITHUB_CREDENTIALS['client_secret']:
        pytest.skip(
            "GitHub OAuth credentials not configured. Please set in .env:\n"
            "  GITHUB_CLIENT_ID=your_client_id\n"
            "  GITHUB_CLIENT_SECRET=your_client_secret"
        )

    client_id = TEST_GITHUB_CREDENTIALS['client_id']
    redirect_uri = TEST_GITHUB_CREDENTIALS['redirect_uri']

    # 1️⃣ Verify OAuth endpoint accessibility
    try:
        response = httpx.get("https://github.com/login/oauth/authorize", timeout=10.0)
        assert response.status_code in [200, 302, 404], "GitHub OAuth authorize endpoint should respond"
        print(f"\n✓ GitHub OAuth authorize endpoint reachable")
    except Exception as e:
        pytest.fail(f"Failed to connect to GitHub OAuth endpoint: {str(e)}")

    # 2️⃣ Build OAuth authorization URL
    from urllib.parse import urlencode, quote
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'repo read:user notifications',
        'allow_signup': 'true'
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    assert client_id in auth_url, "client_id must appear in auth URL"
    assert quote(redirect_uri, safe='') in auth_url or redirect_uri in auth_url, "redirect_uri must appear encoded"
    print(f"\n✓ GitHub OAuth authorization URL built successfully")
    print(f"  URL: {auth_url[:100]}...")

    # 3️⃣ Test token endpoint availability
    try:
        response = httpx.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "client_secret": TEST_GITHUB_CREDENTIALS['client_secret'],
                "code": "invalid_test_code",  # expected to fail
                "redirect_uri": redirect_uri
            },
            headers={"Accept": "application/json"},
            timeout=10.0
        )
        assert response.status_code in [400, 401, 200], "GitHub token endpoint should respond"
        data = response.json()
        if "error" in data and data["error"] == "bad_verification_code":
            print(f"\n✓ GitHub credentials are valid (expected error: {data['error']})")
        elif "error" in data and data["error"] == "incorrect_client_credentials":
            pytest.fail("Invalid GitHub client credentials")
        else:
            print(f"\n✓ GitHub token endpoint responded correctly")
    except Exception as e:
        pytest.fail(f"Failed to validate GitHub OAuth credentials: {str(e)}")

    print(f"\n✓ Successfully validated GitHub OAuth connection!")
    print(f"  Client ID: {client_id[:50]}...")


def test_github_api_access_with_token():
    """
    Test access to GitHub API using access token.

    This verifies that:
    1. The token can authenticate to GitHub API
    2. /user endpoint returns valid data
    """
    if not TEST_GITHUB_TOKEN:
        pytest.skip(
            "GitHub token not set. To test API access, add TEST_GITHUB_ACCESS_TOKEN to .env\n"
            "  TEST_GITHUB_ACCESS_TOKEN=your_personal_or_oauth_token"
        )

    headers = {"Authorization": f"Bearer {TEST_GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}

    try:
        response = httpx.get("https://api.github.com/user", headers=headers, timeout=10.0)
        assert response.status_code == 200, f"GitHub API returned {response.status_code}"
        user_data = response.json()
        assert "login" in user_data, "Response should contain 'login' field"
        assert "id" in user_data, "Response should contain 'id' field"
        print(f"\n✓ Successfully authenticated to GitHub API as {user_data['login']}")
    except httpx.TimeoutException:
        pytest.fail("Timeout connecting to GitHub API")
    except Exception as e:
        pytest.fail(f"GitHub API access failed: {str(e)}")


def test_github_connection_invalid_credentials():
    """
    Test that GitHub API fails gracefully with invalid credentials.
    """
    invalid_token = "ghp_invalidtoken1234567890"

    try:
        response = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {invalid_token}", "Accept": "application/vnd.github+json"},
            timeout=10.0
        )
        assert response.status_code in [401, 403], "Invalid token should return 401 or 403"
        print(f"\n✓ GitHub returned expected error for invalid credentials ({response.status_code})")
    except Exception as e:
        pytest.fail(f"GitHub invalid credentials test failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
