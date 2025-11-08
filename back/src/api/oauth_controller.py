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

    # OAuth URLs
    GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

    # Scopes
    GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    LOGIN_SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]

    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

    def validate(self):
        """Check if OAuth is configured."""
        return bool(self.client_id and self.client_secret)

    def get_redirect_uri(self, request: Request, endpoint: str = 'callback') -> str:
        """Generate redirect URI based on request context."""
        scheme = request.url.scheme
        host = request.url.hostname
        port = request.url.port

        if port and port not in [80, 443]:
            base_url = f"{scheme}://{host}:{port}"
        else:
            base_url = f"{scheme}://{host}"

        return f"{base_url}/auth/google/{endpoint}"

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

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    'code': code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """Get user info from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return response.json()


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

    redirect_uri = oauth_config.get_redirect_uri(request, 'login/callback')
    logger.info(f"Using redirect URI for login: {redirect_uri}")

    # Build authorization URL for login
    params = {
        'client_id': oauth_config.client_id,
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
    redirect_uri = oauth_config.get_redirect_uri(request, 'login/callback')

    try:
        token_data = await oauth_config.exchange_code_for_tokens(code, redirect_uri)
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=token_exchange_failed")

    access_token = token_data.get('access_token')
    if not access_token:
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_access_token")

    # Get user info from Google
    try:
        userinfo = await oauth_config.get_user_info(access_token)
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

    redirect_uri = oauth_config.get_redirect_uri(request, 'callback')

    # Build authorization URL
    params = {
        'client_id': oauth_config.client_id,
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
    redirect_uri = oauth_config.get_redirect_uri(request, 'callback')

    try:
        token_data = await oauth_config.exchange_code_for_tokens(code, redirect_uri)
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
        userinfo = await oauth_config.get_user_info(access_token)
        email = userinfo.get('email', 'gmail')
    except Exception as e:
        logger.warning(f"Could not get user email: {str(e)}")
        email = 'gmail'

    secret_repository = PostgreSQLSecretRepository()
    secret_service = SecretService(secret_repository)

    # Prepare credentials data
    credentials_data = {
        'client_id': oauth_config.client_id,
        'client_secret': oauth_config.client_secret,
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
