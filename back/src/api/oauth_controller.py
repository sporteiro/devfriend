import json
import logging
import os
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
import httpx

from src.middleware.auth_middleware import get_current_user_id
from src.models.integration import IntegrationUpdate
from src.models.secret import SecretCreate
from src.models.user import User
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository
from src.repositories.postgresql_user_repository import PostgreSQLUserRepository
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.services.integration_service import IntegrationService
from src.services.secret_service import SecretService
from src.utils.security import create_access_token, hash_password


logger = logging.getLogger(__name__)
router = APIRouter()


class OAuthConfig:
    """Centralized OAuth configuration and helper methods."""

    # OAuth URLs - Google
    GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

    # OAuth URLs - GitHub
    GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
    GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
    GITHUB_USERINFO_URL = 'https://api.github.com/user'

    # OAuth URLs - Slack
    SLACK_AUTH_URL = 'https://slack.com/oauth/v2/authorize'
    SLACK_TOKEN_URL = 'https://slack.com/api/oauth.v2.access'
    SLACK_USERINFO_URL = 'https://slack.com/api/users.identity'

    # Scopes
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    LOGIN_SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    GITHUB_SCOPES = ['repo', 'read:user', 'notifications']
    SLACK_SCOPES = ['channels:read', 'chat:write', 'users:read', 'users:read.email']

    def __init__(self):
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.github_client_id = os.getenv('GITHUB_CLIENT_ID')
        self.github_client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        self.slack_client_id = os.getenv('SLACK_CLIENT_ID')
        self.slack_client_secret = os.getenv('SLACK_CLIENT_SECRET')

    def validate_google(self):
        """Check if Google OAuth is configured."""
        return bool(self.google_client_id and self.google_client_secret)

    def validate_github(self):
        """Check if GitHub OAuth is configured."""
        return bool(self.github_client_id and self.github_client_secret)

    def validate_slack(self):
        """Check if Slack OAuth is configured."""
        return bool(self.slack_client_id and self.slack_client_secret)

    def validate(self):
        """Check if OAuth is configured (for backward compatibility - checks Google)."""
        return self.validate_google()

    def get_redirect_uri(self, request: Request, provider: str = 'google', endpoint: str = 'callback') -> str:
        """Generate redirect URI based on request context or environment variable.

        Priority:
        1. {PROVIDER}_REDIRECT_URI environment variable (e.g., GITHUB_REDIRECT_URI) - REQUIRED for GitHub/Slack
        2. BACKEND_URL environment variable + /auth/{provider}/{endpoint}
        3. Dynamic generation from request (only for Google, not recommended for GitHub/Slack)

        NOTE: GitHub and Slack only allow ONE redirect URI per app, so you MUST set the
        environment variable to match exactly what's configured in their OAuth apps.
        """
        # First, try to use environment variable for the specific provider
        # This is REQUIRED for GitHub and Slack since they only allow one redirect URI
        env_var_name = f"{provider.upper()}_REDIRECT_URI"
        env_redirect_uri = os.getenv(env_var_name)
        if env_redirect_uri:
            logger.info(f"Using {env_var_name} from environment: {env_redirect_uri}")
            return env_redirect_uri

        # Second, try to use BACKEND_URL if available
        backend_url = os.getenv('BACKEND_URL')
        if backend_url:
            redirect_uri = f"{backend_url.rstrip('/')}/auth/{provider}/{endpoint}"
            logger.info(f"Using BACKEND_URL from environment: {redirect_uri}")
            return redirect_uri

        # For GitHub and Slack, warn if no environment variable is set
        if provider in ['github', 'slack']:
            logger.warning(
                f"No {env_var_name} or BACKEND_URL set for {provider}. "
                f"GitHub/Slack only allow ONE redirect URI per app. "
                f"Please set {env_var_name} to match your OAuth app configuration."
            )

        # Fallback: Generate based on request
        # NOTE: This may not match your GitHub/Slack OAuth app configuration!
        scheme = request.url.scheme
        host = request.url.hostname
        port = request.url.port

        # For localhost, always include port if it's not standard
        if host in ['localhost', '127.0.0.1']:
            if port and port not in [80, 443]:
                base_url = f"{scheme}://{host}:{port}"
            else:
                # Default to 8888 for localhost if no port specified
                base_url = f"http://localhost:8888"
        else:
            # For remote/production, use standard ports or include port if non-standard
            if port and port not in [80, 443]:
                base_url = f"{scheme}://{host}:{port}"
            else:
                base_url = f"{scheme}://{host}"

        redirect_uri = f"{base_url}/auth/{provider}/{endpoint}"
        logger.warning(f"Generated redirect_uri dynamically: {redirect_uri}. "
                      f"For {provider}, ensure this matches your OAuth app configuration!")
        return redirect_uri

    def get_frontend_url(self, request: Request) -> str:
        """Get frontend URL for redirects."""
        frontend_url = os.getenv('FRONTEND_URL')
        if frontend_url:
            return frontend_url

        scheme = request.url.scheme
        host = request.url.hostname
        if host in ['localhost', '127.0.0.1']:
            return 'http://localhost:88'
        return f"{scheme}://{host}"

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str, provider: str = 'google') -> dict:
        """Exchange authorization code for tokens."""
        if provider == 'google':
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.GOOGLE_TOKEN_URL,
                    data={
                        'code': code,
                        'client_id': self.google_client_id,
                        'client_secret': self.google_client_secret,
                        'redirect_uri': redirect_uri,
                        'grant_type': 'authorization_code'
                    }
                )
                response.raise_for_status()
                return response.json()
        elif provider == 'github':
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.GITHUB_TOKEN_URL,
                    data={
                        'code': code,
                        'client_id': self.github_client_id,
                        'client_secret': self.github_client_secret,
                        'redirect_uri': redirect_uri
                    },
                    headers={'Accept': 'application/json'}
                )
                response.raise_for_status()
                return response.json()
        elif provider == 'slack':
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.SLACK_TOKEN_URL,
                    data={
                        'code': code,
                        'client_id': self.slack_client_id,
                        'client_secret': self.slack_client_secret,
                        'redirect_uri': redirect_uri
                    }
                )
                response.raise_for_status()
                return response.json()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def get_user_info(self, access_token: str, provider: str = 'google') -> dict:
        """Get user info from OAuth provider."""
        if provider == 'google':
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.GOOGLE_USERINFO_URL,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                return response.json()
        elif provider == 'github':
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.GITHUB_USERINFO_URL,
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Accept': 'application/vnd.github+json'
                    }
                )
                response.raise_for_status()
                return response.json()
        elif provider == 'slack':
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.SLACK_USERINFO_URL,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                return response.json()
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Initialize config once
oauth_config = OAuthConfig()


def get_db_config():
    """Get database configuration."""
    return {
        "host": os.getenv("DB_HOST", "postgres"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "devfriend"),
        "user": os.getenv("DB_USER", "devfriend"),
        "password": os.getenv("DB_PASSWORD", "devfriend"),
    }


@router.get("/auth/google/login")
async def authorize_google_login(request: Request):
    """
    Initiate Google OAuth flow for login.
    Uses credentials from environment variables.
    Returns the Google OAuth authorization URL.
    """
    if not oauth_config.validate():
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )

    redirect_uri = oauth_config.get_redirect_uri(request, 'google', 'login/callback')
    logger.info(f"Using redirect URI for login: {redirect_uri}")

    # Build authorization URL for login
    params = {
        'client_id': oauth_config.google_client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(oauth_config.LOGIN_SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
    }

    auth_url = f"{oauth_config.GOOGLE_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating Google login OAuth URL with redirect_uri: {redirect_uri}")

    return {"auth_url": auth_url, "redirect_uri": redirect_uri}


@router.get("/auth/google/login/callback")
async def google_login_callback(
    request: Request,
    code: str = Query(...),
    error: str = Query(None)
):
    """
    Handle Google OAuth callback for login.
    Creates or logs in user and returns JWT token.
    """
    frontend_url = oauth_config.get_frontend_url(request)

    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error={error}")

    if not code:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_code")

    if not oauth_config.validate():
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=config_error")

    # Exchange code for tokens
    redirect_uri = oauth_config.get_redirect_uri(request, 'google', 'login/callback')

    try:
        token_data = await oauth_config.exchange_code_for_tokens(code, redirect_uri, 'google')
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=token_exchange_failed")

    access_token = token_data.get('access_token')
    if not access_token:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_access_token")

    # Get user info from Google
    try:
        userinfo = await oauth_config.get_user_info(access_token, 'google')
        google_email = userinfo.get('email')
        google_name = userinfo.get('name', '')
    except Exception as e:
        logger.error(f"Could not get user info from Google: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=userinfo_failed")

    if not google_email:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_email")

    # Check if user exists, create if not
    db_config = get_db_config()
    user_repository = PostgreSQLUserRepository(**db_config)
    auth_service = AuthService(user_repository)

    # Check if user exists
    existing_user = auth_service.get_user_by_email(google_email)

    if existing_user:
        user = existing_user
        logger.info(f"Logging in existing user {user.id} via Google OAuth")
    else:
        # Create new user
        random_password = secrets.token_urlsafe(32)
        password_hash = hash_password(random_password)
        new_user = User(email=google_email, password_hash=password_hash)
        user = user_repository.save(new_user)
        logger.info(f"Created new user {user.id} via Google OAuth")

    # Generate JWT token
    token_data = {"sub": str(user.id), "email": user.email}
    jwt_token = create_access_token(token_data)

    # Redirect to frontend with token
    logger.info(f"Redirecting to frontend: {frontend_url}")
    return RedirectResponse(
        url=f"{frontend_url}/?oauth_login_success=true&token={jwt_token}"
    )


@router.get("/auth/google/authorize")
async def authorize_google(
    request: Request,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Initiate Google OAuth flow for Gmail integration.
    Uses credentials from environment variables (simplified - no secret_id needed).
    Returns the Google OAuth authorization URL.
    """
    if not oauth_config.validate():
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )

    redirect_uri = oauth_config.get_redirect_uri(request, 'google', 'callback')

    # Build authorization URL
    params = {
        'client_id': oauth_config.google_client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(oauth_config.GMAIL_SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': str(current_user_id)
    }

    auth_url = f"{oauth_config.GOOGLE_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating OAuth URL for Gmail integration for user {current_user_id} with redirect_uri: {redirect_uri}")

    return {"auth_url": auth_url, "redirect_uri": redirect_uri}


@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None)
):
    """
    Handle Google OAuth callback.
    Exchanges authorization code for tokens and saves refresh_token.
    """
    frontend_url = oauth_config.get_frontend_url(request)

    if error:
        logger.error(f"Google OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth authorization failed: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    # Parse state: user_id
    try:
        user_id = int(state)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if not oauth_config.validate():
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured")

    # Exchange code for tokens
    redirect_uri = oauth_config.get_redirect_uri(request, 'google', 'callback')

    try:
        token_data = await oauth_config.exchange_code_for_tokens(code, redirect_uri, 'google')
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange authorization code: {str(e)}"
        )

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')

    if not refresh_token:
        logger.warning("No refresh_token received. This may happen if user already authorized.")
        # Try to get existing refresh_token from user's secrets
        secret_repository = PostgreSQLSecretRepository()
        secrets = secret_repository.find_by_user(user_id)
        gmail_secret = None

        for secret in secrets:
            if secret.service_type.lower() in ['gmail', 'email']:
                try:
                    creds = json.loads(secret.encrypted_value)
                    if creds.get('refresh_token'):
                        gmail_secret = secret
                        break
                except:
                    continue

        if gmail_secret:
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&secret_id={gmail_secret.id}&message=already_authorized"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="No refresh_token received. Please revoke access in Google Account settings (https://myaccount.google.com/permissions) and try again."
            )

    # Get user's email from Google to name the secret
    try:
        userinfo = await oauth_config.get_user_info(access_token, 'google')
        email = userinfo.get('email', 'gmail')
    except Exception as e:
        logger.warning(f"Could not get user email: {str(e)}")
        email = 'gmail'

    secret_repository = PostgreSQLSecretRepository()
    secret_service = SecretService(secret_repository)

    # Prepare credentials data
    credentials_data = {
        'client_id': oauth_config.google_client_id,
        'client_secret': oauth_config.google_client_secret,
        'refresh_token': refresh_token,
        'redirect_uri': redirect_uri
    }

    secret_data = SecretCreate(
        name=f"Gmail - {email}",
        service_type='gmail',
        datos_secrets=credentials_data
    )

    try:
        saved_secret = secret_service.create_secret(user_id, secret_data)
        logger.info(f"Saved Gmail credentials for user {user_id}")
        secret_id = saved_secret.id
    except Exception as e:
        logger.error(f"Error creating secret: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create secret: {str(e)}")

    # Automatically create or update the email integration
    if secret_id:
        email_service = EmailService(user_id)
        integration_service = IntegrationService(user_id)

        try:
            # Check if user already has a Gmail integration
            existing_integrations = integration_service.get_integrations('gmail')

            if existing_integrations and len(existing_integrations) > 0:
                # Update existing integration with new secret_id
                existing_integration = existing_integrations[0]
                integration_id = existing_integration.get('id')

                logger.info(f"Updating integration {integration_id} with secret_id {secret_id}")
                update_data = IntegrationUpdate(secret_id=secret_id)
                integration = integration_service.update_integration(integration_id, update_data)
            else:
                # Create new integration
                logger.info(f"Creating new Gmail integration for user {user_id} with secret_id {secret_id}")
                integration_data = {'credential_id': secret_id}
                try:
                    integration = email_service.create_email_integration(integration_data)
                    logger.info(f"Successfully created integration {integration.get('id')} for user {user_id}")
                except Exception as create_error:
                    logger.error(f"Error creating integration: {str(create_error)}", exc_info=True)
                    raise

            logger.info(f"Gmail integration ready: {integration.get('id')} for user {user_id}")

            logger.info(f"Redirecting to frontend after Gmail OAuth: {frontend_url}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&integration_id={integration.get('id')}"
            )

        except Exception as integration_error:
            logger.error(f"Error creating/updating integration after OAuth: {str(integration_error)}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}&warning=integration_failed"
            )
    else:
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}"
        )


# ============================================================================
# GitHub OAuth Endpoints
# ============================================================================

@router.get("/auth/github/authorize")
async def authorize_github(
    request: Request,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Initiate GitHub OAuth flow for GitHub integration.
    Uses credentials from environment variables.
    Returns the GitHub OAuth authorization URL.
    """
    if not oauth_config.validate_github():
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth credentials not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables."
        )

    redirect_uri = oauth_config.get_redirect_uri(request, 'github', 'callback')

    # Build authorization URL
    params = {
        'client_id': oauth_config.github_client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(oauth_config.GITHUB_SCOPES),
        'state': str(current_user_id),
        'allow_signup': 'true'
    }

    auth_url = f"{oauth_config.GITHUB_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating OAuth URL for GitHub integration for user {current_user_id} with redirect_uri: {redirect_uri}")

    return {"auth_url": auth_url, "redirect_uri": redirect_uri}


@router.get("/auth/github/callback")
async def github_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None)
):
    """
    Handle GitHub OAuth callback.
    Exchanges authorization code for tokens and saves access_token.
    """
    frontend_url = oauth_config.get_frontend_url(request)

    if error:
        logger.error(f"GitHub OAuth error: {error}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error={error}")

    if not code:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_code")

    # Parse state: user_id
    try:
        user_id = int(state)
    except (ValueError, TypeError):
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=invalid_state")

    if not oauth_config.validate_github():
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=config_error")

    # Exchange code for tokens
    redirect_uri = oauth_config.get_redirect_uri(request, 'github', 'callback')

    try:
        token_data = await oauth_config.exchange_code_for_tokens(code, redirect_uri, 'github')
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=token_exchange_failed")

    access_token = token_data.get('access_token')
    if not access_token:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_access_token")

    # Get user info from GitHub to name the secret
    try:
        userinfo = await oauth_config.get_user_info(access_token, 'github')
        github_username = userinfo.get('login', 'github')
    except Exception as e:
        logger.warning(f"Could not get user info from GitHub: {str(e)}")
        github_username = 'github'

    secret_repository = PostgreSQLSecretRepository()
    secret_service = SecretService(secret_repository)

    # Prepare credentials data
    credentials_data = {
        'access_token': access_token,
        'client_id': oauth_config.github_client_id,
        'client_secret': oauth_config.github_client_secret,
        'redirect_uri': redirect_uri
    }

    secret_data = SecretCreate(
        name=f"GitHub - {github_username}",
        service_type='github',
        datos_secrets=credentials_data
    )

    try:
        saved_secret = secret_service.create_secret(user_id, secret_data)
        logger.info(f"Saved GitHub credentials for user {user_id}")
        secret_id = saved_secret.id
    except Exception as e:
        logger.error(f"Error creating secret: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=secret_creation_failed")

    # Automatically create or update the GitHub integration
    if secret_id:
        from src.services.github_service import GitHubService
        github_service = GitHubService(user_id)
        integration_service = IntegrationService(user_id)

        try:
            # Check if user already has a GitHub integration
            existing_integrations = integration_service.get_integrations('github')

            if existing_integrations and len(existing_integrations) > 0:
                # Update existing integration with new secret_id
                existing_integration = existing_integrations[0]
                integration_id = existing_integration.get('id')

                logger.info(f"Updating integration {integration_id} with secret_id {secret_id}")
                update_data = IntegrationUpdate(secret_id=secret_id)
                integration = integration_service.update_integration(integration_id, update_data)
            else:
                # Create new integration
                logger.info(f"Creating new GitHub integration for user {user_id} with secret_id {secret_id}")
                integration_data = {'credential_id': secret_id}
                try:
                    integration = github_service.create_github_integration(integration_data)
                    logger.info(f"Successfully created integration {integration.get('id')} for user {user_id}")
                except Exception as create_error:
                    logger.error(f"Error creating integration: {str(create_error)}", exc_info=True)
                    raise

            logger.info(f"GitHub integration ready: {integration.get('id')} for user {user_id}")

            logger.info(f"Redirecting to frontend after GitHub OAuth: {frontend_url}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&integration_id={integration.get('id')}"
            )

        except Exception as integration_error:
            logger.error(f"Error creating/updating integration after OAuth: {str(integration_error)}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}&warning=integration_failed"
            )
    else:
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}"
        )


# ============================================================================
# Slack OAuth Endpoints
# ============================================================================

@router.get("/auth/slack/authorize")
async def authorize_slack(
    request: Request,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Initiate Slack OAuth flow for Slack integration.
    Uses credentials from environment variables.
    Returns the Slack OAuth authorization URL.
    """
    if not oauth_config.validate_slack():
        raise HTTPException(
            status_code=500,
            detail="Slack OAuth credentials not configured. Please set SLACK_CLIENT_ID and SLACK_CLIENT_SECRET environment variables."
        )

    redirect_uri = oauth_config.get_redirect_uri(request, 'slack', 'callback')

    # Build authorization URL
    params = {
        'client_id': oauth_config.slack_client_id,
        'redirect_uri': redirect_uri,
        'scope': ','.join(oauth_config.SLACK_SCOPES),
        'state': str(current_user_id)
    }

    auth_url = f"{oauth_config.SLACK_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating OAuth URL for Slack integration for user {current_user_id} with redirect_uri: {redirect_uri}")

    return {"auth_url": auth_url, "redirect_uri": redirect_uri}


@router.get("/auth/slack/callback")
async def slack_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None)
):
    """
    Handle Slack OAuth callback.
    Exchanges authorization code for tokens and saves access_token.
    """
    frontend_url = oauth_config.get_frontend_url(request)

    if error:
        logger.error(f"Slack OAuth error: {error}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error={error}")

    if not code:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_code")

    # Parse state: user_id
    try:
        user_id = int(state)
    except (ValueError, TypeError):
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=invalid_state")

    if not oauth_config.validate_slack():
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=config_error")

    # Exchange code for tokens
    redirect_uri = oauth_config.get_redirect_uri(request, 'slack', 'callback')

    try:
        token_response = await oauth_config.exchange_code_for_tokens(code, redirect_uri, 'slack')
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=token_exchange_failed")

    # Slack OAuth v2 returns data in a different format
    if not token_response.get('ok'):
        error_msg = token_response.get('error', 'unknown_error')
        logger.error(f"Slack OAuth error: {error_msg}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error={error_msg}")

    # Extract tokens from Slack response
    # Slack OAuth v2 returns: { ok: true, authed_user: { access_token }, access_token: bot_token, team: {...} }
    authed_user = token_response.get('authed_user', {})
    user_access_token = authed_user.get('access_token')  # User token
    bot_token = token_response.get('access_token')  # Bot token is in the root
    team_info = token_response.get('team', {})
    workspace_name = team_info.get('name', 'slack')

    # Use bot_token as primary, fallback to user token
    access_token = bot_token or user_access_token

    if not access_token:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_access_token")

    secret_repository = PostgreSQLSecretRepository()
    secret_service = SecretService(secret_repository)

    # Prepare credentials data
    credentials_data = {
        'bot_token': bot_token or access_token,
        'access_token': user_access_token or access_token,
        'client_id': oauth_config.slack_client_id,
        'client_secret': oauth_config.slack_client_secret,
        'redirect_uri': redirect_uri,
        'team_id': team_info.get('id'),
        'team_name': workspace_name
    }

    secret_data = SecretCreate(
        name=f"Slack - {workspace_name}",
        service_type='slack',
        datos_secrets=credentials_data
    )

    try:
        saved_secret = secret_service.create_secret(user_id, secret_data)
        logger.info(f"Saved Slack credentials for user {user_id}")
        secret_id = saved_secret.id
    except Exception as e:
        logger.error(f"Error creating secret: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=secret_creation_failed")

    # Automatically create or update the Slack integration
    if secret_id:
        from src.services.slack_service import SlackService
        slack_service = SlackService(user_id)
        integration_service = IntegrationService(user_id)

        try:
            # Check if user already has a Slack integration
            existing_integrations = integration_service.get_integrations('slack')

            if existing_integrations and len(existing_integrations) > 0:
                # Update existing integration with new secret_id
                existing_integration = existing_integrations[0]
                integration_id = existing_integration.get('id')

                logger.info(f"Updating integration {integration_id} with secret_id {secret_id}")
                update_data = IntegrationUpdate(secret_id=secret_id)
                integration = integration_service.update_integration(integration_id, update_data)
            else:
                # Create new integration using SlackService (similar to GitHub)
                logger.info(f"Creating new Slack integration for user {user_id} with secret_id {secret_id}")
                integration_data = {'credential_id': secret_id}
                try:
                    integration = slack_service.create_slack_integration(integration_data)
                    logger.info(f"Successfully created integration {integration.get('id')} for user {user_id}")
                except Exception as create_error:
                    logger.error(f"Error creating integration: {str(create_error)}", exc_info=True)
                    raise

            logger.info(f"Slack integration ready: {integration.get('id')} for user {user_id}")

            logger.info(f"Redirecting to frontend after Slack OAuth: {frontend_url}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&integration_id={integration.get('id')}"
            )

        except Exception as integration_error:
            logger.error(f"Error creating/updating integration after OAuth: {str(integration_error)}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}&warning=integration_failed"
            )
    else:
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}"
        )
