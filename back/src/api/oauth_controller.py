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
from src.utils.constants import (
    BACKEND_URL,
    FRONTEND_URL,
    GITHUB_AUTH_URL,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_SCOPES,
    GITHUB_TOKEN_URL,
    GITHUB_USERINFO_URL,
    GMAIL_SCOPES,
    GOOGLE_AUTH_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    LOGIN_SCOPES,
    SLACK_AUTH_URL,
    SLACK_CLIENT_ID,
    SLACK_CLIENT_SECRET,
    SLACK_SCOPES,
    SLACK_TOKEN_URL,
    SLACK_USERINFO_URL,
)
from src.utils.get_db_config import GetDBConfig
from src.utils.security import create_access_token, hash_password


logger = logging.getLogger(__name__)
router = APIRouter()


class OAuthConfig:

    def validate_google(self):
        """Check if Google OAuth is configured."""
        return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

    def validate_github(self):
        """Check if GitHub OAuth is configured."""
        return bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)

    def validate_slack(self):
        """Check if Slack OAuth is configured."""
        return bool(SLACK_CLIENT_ID and SLACK_CLIENT_SECRET)

    def validate(self):
        """Check if OAuth is configured (for backward compatibility - checks Google)."""
        return self.validate_google()

    def get_redirect_uri_static(self, provider: str = 'google', endpoint: str = 'callback') -> str:
        """
        Get redirect URI from environment variables only (no request needed).
        For GitHub and Slack, REQUIRES {PROVIDER}_REDIRECT_URI to be set (no fallbacks).
        """
        env_var_name = f"{provider.upper()}_REDIRECT_URI"
        env_redirect_uri = os.getenv(env_var_name)

        # For GitHub and Slack, the redirect URI MUST be set in environment variable
        # No fallbacks allowed - it's fixed and must match OAuth app configuration
        if provider in ['github', 'slack']:
            if not env_redirect_uri:
                raise ValueError(
                    f"{env_var_name} environment variable is required for {provider}. "
                    f"GitHub/Slack only allow ONE redirect URI per app, so it must be set exactly."
                )
            return env_redirect_uri

        # For Google, allow fallbacks
        if env_redirect_uri:
            return env_redirect_uri

        backend_url = os.getenv('BACKEND_URL')
        if backend_url:
            return f"{backend_url.rstrip('/')}/auth/{provider}/{endpoint}"

        # Fallback: return a placeholder (only for Google)
        return f"https://your-backend-url/auth/{provider}/{endpoint}"

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
                base_url = BACKEND_URL
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
        frontend_url = FRONTEND_URL
        if frontend_url:
            return frontend_url

        scheme = request.url.scheme
        host = request.url.hostname
        if host in ['localhost', '127.0.0.1']:
            return FRONTEND_URL
        return f"{scheme}://{host}"

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str, provider: str = 'google', client_id: str = None, client_secret: str = None) -> dict:
        """
        Exchange authorization code for tokens.
        If client_id and client_secret are provided, use those; otherwise use environment variables.
        """
        if provider == 'google':
            cid = client_id or GOOGLE_CLIENT_ID
            csec = client_secret or GOOGLE_CLIENT_SECRET
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        'code': code,
                        'client_id': cid,
                        'client_secret': csec,
                        'redirect_uri': redirect_uri,
                        'grant_type': 'authorization_code'
                    }
                )
                response.raise_for_status()
                return response.json()
        elif provider == 'github':
            cid = client_id or GITHUB_CLIENT_ID
            csec = client_secret or GITHUB_CLIENT_SECRET
            logger.info(f"GitHub token exchange: client_id length={len(cid) if cid else 0}, client_secret length={len(csec) if csec else 0}, redirect_uri={redirect_uri}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GITHUB_TOKEN_URL,
                    data={
                        'code': code,
                        'client_id': cid,
                        'client_secret': csec,
                        'redirect_uri': redirect_uri
                    },
                    headers={'Accept': 'application/json'}
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"GitHub token exchange response keys: {list(result.keys())}")
                if 'error' in result:
                    logger.error(f"GitHub token exchange error: {result}")
                return result
        elif provider == 'slack':
            cid = client_id or SLACK_CLIENT_ID
            csec = client_secret or SLACK_CLIENT_SECRET
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SLACK_TOKEN_URL,
                    data={
                        'code': code,
                        'client_id': cid,
                        'client_secret': csec,
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
                    GOOGLE_USERINFO_URL,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                return response.json()
        elif provider == 'github':
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    GITHUB_USERINFO_URL,
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
                    SLACK_USERINFO_URL,
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                response.raise_for_status()
                return response.json()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def get_dynamic_credentials(self, user_id: int, provider: str) -> dict:
        """
        Get client_id and client_secret from user's secrets of the given provider type.
        Falls back to environment variables if not found.
        """
        from src.repositories.postgresql_secret_repository import (
            PostgreSQLSecretRepository,
        )
        repo = PostgreSQLSecretRepository()

        secrets = repo.find_all_by_type_decrypted(user_id, provider)
        for s in secrets:
            try:
                datos = json.loads(s.encrypted_value) if isinstance(s.encrypted_value, str) else s.encrypted_value
                logger.debug(f"Secret {s.id} decrypted data keys: {list(datos.keys()) if isinstance(datos, dict) else 'not a dict'}")
                cid = datos.get('client_id')
                csec = datos.get('client_secret')
                if cid and csec:
                    cid_clean = str(cid).strip()
                    csec_clean = str(csec).strip()
                    logger.info(f"Using user-saved {provider} credentials from secret {s.id} for user {user_id}: client_id={cid_clean[:10]}... (len={len(cid_clean)}), client_secret=*** (len={len(csec_clean)})")
                    return {'client_id': cid_clean, 'client_secret': csec_clean}
            except Exception as e:
                logger.error(f"Error parsing secret {s.id}: {str(e)}", exc_info=True)
                continue

        logger.info(f"Using environment variables for {provider}")
        if provider == 'gmail':
            cid = str(GOOGLE_CLIENT_ID).strip() if GOOGLE_CLIENT_ID else None
            csec = str(GOOGLE_CLIENT_SECRET).strip() if GOOGLE_CLIENT_SECRET else None
            return {'client_id': cid, 'client_secret': csec}
        elif provider == 'github':
            cid = str(GITHUB_CLIENT_ID).strip() if GITHUB_CLIENT_ID else None
            csec = str(GITHUB_CLIENT_SECRET).strip() if GITHUB_CLIENT_SECRET else None
            logger.info(f"Env GitHub credentials: client_id={cid[:10] if cid else None}... (len={len(cid) if cid else 0}), client_secret=*** (len={len(csec) if csec else 0})")
            return {'client_id': cid, 'client_secret': csec}
        elif provider == 'slack':
            cid = str(SLACK_CLIENT_ID).strip() if SLACK_CLIENT_ID else None
            csec = str(SLACK_CLIENT_SECRET).strip() if SLACK_CLIENT_SECRET else None
            return {'client_id': cid, 'client_secret': csec}
        return {'client_id': None, 'client_secret': None}


# Initialize config once
oauth_config = OAuthConfig()


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
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(LOGIN_SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
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
    db_config = GetDBConfig().get_db_config()
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
    Uses client_id/client_secret from secrets if available, otherwise from .env
    """
    creds = oauth_config.get_dynamic_credentials(current_user_id, 'gmail')
    redirect_uri = oauth_config.get_redirect_uri(request, 'google', 'callback')
    if not creds['client_id'] or not creds['client_secret']:
        raise HTTPException(status_code=500, detail="Google OAuth client_id/client_secret not configured.")

    params = {
        'client_id': creds['client_id'],
        'redirect_uri': redirect_uri,
        'scope': ' '.join(GMAIL_SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': str(current_user_id)
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating OAuth URL for Gmail integration for user {current_user_id} (dynamic client_id)")
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

    # Exchange code for tokens - use same credentials as authorization
    redirect_uri = oauth_config.get_redirect_uri(request, 'google', 'callback')
    creds = oauth_config.get_dynamic_credentials(user_id, 'gmail')

    try:
        token_data = await oauth_config.exchange_code_for_tokens(
            code, redirect_uri, 'google',
            client_id=creds['client_id'],
            client_secret=creds['client_secret']
        )
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
    # redirect_uri is NOT saved - it's always fixed in environment variable
    credentials_data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token
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
    Uses client_id/client_secret from secrets if available, otherwise from .env
    """
    creds = oauth_config.get_dynamic_credentials(current_user_id, 'github')
    # Always use static redirect URI from environment (fixed, never dynamic)
    redirect_uri = oauth_config.get_redirect_uri_static('github', 'callback')
    if not creds['client_id'] or not creds['client_secret']:
        raise HTTPException(status_code=500, detail="GitHub OAuth client_id/client_secret not configured.")
    params = {
        'client_id': creds['client_id'],
        'redirect_uri': redirect_uri,
        'scope': ' '.join(GITHUB_SCOPES),
        'state': str(current_user_id),
        'allow_signup': 'true'
    }
    auth_url = f"{GITHUB_AUTH_URL}?{urlencode(params)}"
    logger.info(f"GitHub OAuth URL for user {current_user_id}: client_id={creds['client_id'][:10]}..., redirect_uri={redirect_uri}")
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
    try:
        frontend_url = oauth_config.get_frontend_url(request)
        logger.info(f"GitHub OAuth callback received: code={code[:10]}..., state={state}, error={error}")

        if error:
            logger.error(f"GitHub OAuth error: {error}")
            return RedirectResponse(url=f"{frontend_url}/?oauth_error={error}")

        if not code:
            logger.error("GitHub OAuth callback: no code provided")
            return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_code")

        # Parse state: user_id
        try:
            user_id = int(state)
            logger.info(f"GitHub OAuth callback for user {user_id}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid state parameter: {state}, error: {str(e)}")
            return RedirectResponse(url=f"{frontend_url}/?oauth_error=invalid_state")

        # Validate credentials (either from secrets or env)
        creds = oauth_config.get_dynamic_credentials(user_id, 'github')
        if not creds['client_id'] or not creds['client_secret']:
            logger.error(f"GitHub OAuth credentials not configured for user {user_id}")
            return RedirectResponse(url=f"{frontend_url}/?oauth_error=config_error")

        # Exchange code for tokens - use same credentials as authorization
        # Always use static redirect URI from environment (fixed, never dynamic)
        redirect_uri = oauth_config.get_redirect_uri_static('github', 'callback')
        logger.info(f"Exchanging code for tokens with redirect_uri: {redirect_uri}")

        try:
            token_data = await oauth_config.exchange_code_for_tokens(
                code, redirect_uri, 'github',
                client_id=creds['client_id'],
                client_secret=creds['client_secret']
            )
            logger.info(f"Token exchange response: {token_data}")
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}", exc_info=True)
            return RedirectResponse(url=f"{frontend_url}/?oauth_error=token_exchange_failed")

        access_token = token_data.get('access_token')
        if not access_token:
            logger.error(f"No access_token in token response. Full response: {token_data}")
            return RedirectResponse(url=f"{frontend_url}/?oauth_error=no_access_token")

        # Get user info from GitHub to name the secret
        try:
            userinfo = await oauth_config.get_user_info(access_token, 'github')
            github_username = userinfo.get('login', 'github')
            logger.info(f"Got GitHub user info: {github_username}")
        except Exception as e:
            logger.warning(f"Could not get user info from GitHub: {str(e)}")
            github_username = 'github'

        secret_repository = PostgreSQLSecretRepository()
        secret_service = SecretService(secret_repository)

        # Prepare credentials data - use the same credentials that were used for authorization
        # redirect_uri is NOT saved - it's always fixed in environment variable
        credentials_data = {
            'access_token': access_token,
            'client_id': creds['client_id'],
            'client_secret': creds['client_secret']
        }

        secret_data = SecretCreate(
            name=f"GitHub - {github_username}",
            service_type='github',
            datos_secrets=credentials_data
        )

        try:
            saved_secret = secret_service.create_secret(user_id, secret_data)
            logger.info(f"Saved GitHub credentials for user {user_id}, secret_id: {saved_secret.id}")
            secret_id = saved_secret.id
        except Exception as e:
            logger.error(f"Error creating secret: {str(e)}", exc_info=True)
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
                logger.error(f"Error creating/updating integration after OAuth: {str(integration_error)}", exc_info=True)
                return RedirectResponse(
                    url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}&warning=integration_failed"
                )
        else:
            logger.warning(f"No secret_id after saving credentials for user {user_id}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}"
            )
    except Exception as e:
        logger.error(f"Unexpected error in GitHub callback: {str(e)}", exc_info=True)
        frontend_url = oauth_config.get_frontend_url(request) if 'frontend_url' not in locals() else frontend_url
        return RedirectResponse(url=f"{frontend_url}/?oauth_error=unexpected_error")


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
    Uses client_id/client_secret from secrets if available, otherwise from .env
    """
    creds = oauth_config.get_dynamic_credentials(current_user_id, 'slack')
    # Always use static redirect URI from environment (fixed, never dynamic)
    redirect_uri = oauth_config.get_redirect_uri_static('slack', 'callback')
    if not creds['client_id'] or not creds['client_secret']:
        raise HTTPException(status_code=500, detail="Slack OAuth client_id/client_secret not configured.")
    params = {
        'client_id': creds['client_id'],
        'redirect_uri': redirect_uri,
        'scope': ','.join(SLACK_SCOPES),
        'state': str(current_user_id)
    }
    auth_url = f"{SLACK_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating OAuth URL for Slack integration for user {current_user_id} (dynamic client_id)")
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

    # Exchange code for tokens - use same credentials as authorization
    # Always use static redirect URI from environment (fixed, never dynamic)
    redirect_uri = oauth_config.get_redirect_uri_static('slack', 'callback')
    creds = oauth_config.get_dynamic_credentials(user_id, 'slack')

    try:
        token_response = await oauth_config.exchange_code_for_tokens(
            code, redirect_uri, 'slack',
            client_id=creds['client_id'],
            client_secret=creds['client_secret']
        )
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
    # redirect_uri is NOT saved - it's always fixed in environment variable
    credentials_data = {
        'bot_token': bot_token or access_token,
        'access_token': user_access_token or access_token,
        'client_id': SLACK_CLIENT_ID,
        'client_secret': SLACK_CLIENT_SECRET,
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


@router.get("/oauth/redirect-uris")
async def get_redirect_uris():
    """
    Get configured redirect URIs for OAuth providers.
    Returns the redirect URIs that will be used for each provider.
    """
    return {
        "google": oauth_config.get_redirect_uri_static('google', 'callback'),
        "github": oauth_config.get_redirect_uri_static('github', 'callback'),
        "slack": oauth_config.get_redirect_uri_static('slack', 'callback')
    }
