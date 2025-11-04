import json
import logging
import os
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from src.middleware.auth_middleware import get_current_user_id
from src.models.user import User
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository
from src.services.secret_service import SecretService

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth 2.0 configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
GOOGLE_LOGIN_SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']

# OAuth endpoints
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'


def get_redirect_uri(request: Request) -> str:
    """
    Get the redirect URI based on the current environment.
    Works for both localhost and production (Render.com).
    """
    # Get the base URL from the request
    scheme = request.url.scheme
    host = request.url.hostname
    port = request.url.port
    
    # If port is 80 or 443, don't include it (standard HTTP/HTTPS)
    if port and port not in [80, 443]:
        base_url = f"{scheme}://{host}:{port}"
    else:
        base_url = f"{scheme}://{host}"
    
    redirect_uri = f"{base_url}/auth/google/callback"
    logger.debug(f"Using redirect URI: {redirect_uri}")
    return redirect_uri


@router.get("/auth/google/login")
async def authorize_google_login(request: Request):
    """
    Initiate Google OAuth flow for login.
    Uses credentials from environment variables.
    Returns the Google OAuth authorization URL.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )

    # Build redirect URI for login callback
    scheme = request.url.scheme
    host = request.url.hostname
    port = request.url.port
    
    if port and port not in [80, 443]:
        base_url = f"{scheme}://{host}:{port}"
    else:
        base_url = f"{scheme}://{host}"
    
    redirect_uri = f"{base_url}/auth/google/login/callback"
    logger.info(f"Using redirect URI for login: {redirect_uri}")
    
    # Build authorization URL for login
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(GOOGLE_LOGIN_SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating Google login OAuth URL with redirect_uri: {redirect_uri}")
    
    return {"auth_url": auth_url, "redirect_uri": redirect_uri}  # Also return redirect_uri for debugging


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
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )

    redirect_uri = get_redirect_uri(request)
    
    # Build authorization URL
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(GOOGLE_SCOPES),
        'response_type': 'code',
        'access_type': 'offline',  # Required to get refresh_token
        'prompt': 'consent',  # Force consent screen to ensure refresh_token
        'state': str(current_user_id)  # Pass user_id in state
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generating OAuth URL for Gmail integration for user {current_user_id} with redirect_uri: {redirect_uri}")
    
    # Return JSON with the URL instead of redirecting
    return {"auth_url": auth_url, "redirect_uri": redirect_uri}  # Also return redirect_uri for debugging


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
    if error:
        logger.error(f"Google OAuth error: {error}")
        raise HTTPException(
            status_code=400,
            detail=f"OAuth authorization failed: {error}"
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Authorization code not provided"
        )

    # Parse state: user_id (simplified - always use env vars)
    try:
        user_id = int(state)
        secret_id = None  # Always None now - we use env vars
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter"
        )

    # Always use environment variables (simplified)
    client_id = GOOGLE_CLIENT_ID
    client_secret = GOOGLE_CLIENT_SECRET
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth credentials not configured"
        )
    
    # Exchange code for tokens
    redirect_uri = get_redirect_uri(request)
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
            )
            token_response.raise_for_status()
            token_data = token_response.json()
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
            # Update existing secret with new access_token if needed
            # But we can't update without the refresh_token, so redirect to success
            frontend_url = os.getenv('FRONTEND_URL')
            if not frontend_url:
                scheme = request.url.scheme
                host = request.url.hostname
                if host == 'localhost' or host == '127.0.0.1':
                    frontend_url = 'http://localhost:88'
                else:
                    frontend_url = f"{scheme}://{host}:88"
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
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
            email = userinfo.get('email', 'gmail')
    except Exception as e:
        logger.warning(f"Could not get user email: {str(e)}")
        email = 'gmail'

    secret_repository = PostgreSQLSecretRepository()
    secret_service = SecretService(secret_repository)
    
    # Always create new secret (simplified - no updating existing)
    from src.models.secret import SecretCreate

    # Prepare credentials data
    credentials_data = {
        'client_id': client_id,
        'client_secret': client_secret,
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
    
    # Automatically create or update the email integration with the saved secret (only if secret was updated)
    if secret_id:
        from src.models.integration import IntegrationUpdate
        from src.services.email_service import EmailService
        from src.services.integration_service import IntegrationService
        
        email_service = EmailService(user_id)
        integration_service = IntegrationService(user_id)
        
        try:
            # Check if user already has a Gmail integration
            existing_integrations = integration_service.get_integrations('gmail')
            
            if existing_integrations and len(existing_integrations) > 0:
                # Update existing integration with new secret_id
                existing_integration = existing_integrations[0]
                integration_id = existing_integration.get('id')
                
                # Update integration with the secret_id
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
            
            # Return success page or redirect to frontend
            frontend_url = os.getenv('FRONTEND_URL')
            if not frontend_url:
                scheme = request.url.scheme
                host = request.url.hostname
                if host == 'localhost' or host == '127.0.0.1':
                    frontend_url = 'http://localhost:88'
                else:
                    frontend_url = f"{scheme}://{host}:88"
            
            logger.info(f"Redirecting to frontend after Gmail OAuth: {frontend_url}")
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&integration_id={integration.get('id')}"
            )
        except Exception as integration_error:
            logger.error(f"Error creating/updating integration after OAuth: {str(integration_error)}")
            # Still redirect to success, user can manually connect
            frontend_url = os.getenv('FRONTEND_URL')
            if not frontend_url:
                scheme = request.url.scheme
                host = request.url.hostname
                if host == 'localhost' or host == '127.0.0.1':
                    frontend_url = 'http://localhost:88'
                else:
                    frontend_url = f"{scheme}://{host}:88"
            return RedirectResponse(
                url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}&warning=integration_failed"
            )
    else:
        # No secret_id means secret was created (not updated), redirect to success
        frontend_url = os.getenv('FRONTEND_URL')
        if not frontend_url:
            scheme = request.url.scheme
            host = request.url.hostname
            if host == 'localhost' or host == '127.0.0.1':
                frontend_url = 'http://localhost:88'
            else:
                frontend_url = f"{scheme}://{host}:88"
        return RedirectResponse(
            url=f"{frontend_url}/?oauth_success=true&secret_id={secret_id}"
        )


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
    def get_frontend_url():
        frontend_url = os.getenv('FRONTEND_URL')
        if not frontend_url:
            scheme = request.url.scheme
            host = request.url.hostname
            if host == 'localhost' or host == '127.0.0.1':
                return 'http://localhost:88'
            else:
                return f"{scheme}://{host}:88"
        return frontend_url
    
    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse(
            url=f"{get_frontend_url()}/?oauth_error={error}"
        )

    if not code:
        return RedirectResponse(
            url=f"{get_frontend_url()}/?oauth_error=no_code"
        )

    # Always use environment variables
    client_id = GOOGLE_CLIENT_ID
    client_secret = GOOGLE_CLIENT_SECRET
    
    if not client_id or not client_secret:
        return RedirectResponse(
            url=f"{get_frontend_url()}/?oauth_error=config_error"
        )
    
    # Exchange code for tokens
    redirect_uri = get_redirect_uri(request).replace('/auth/google/callback', '/auth/google/login/callback')
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
            )
            token_response.raise_for_status()
            token_data = token_response.json()
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        return RedirectResponse(
            url=f"{get_frontend_url()}/?oauth_error=token_exchange_failed"
        )

    access_token = token_data.get('access_token')
    
    if not access_token:
        return RedirectResponse(
            url=f"{get_frontend_url()}/?oauth_error=no_access_token"
        )

    # Get user info from Google
    try:
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
            google_email = userinfo.get('email')
            google_name = userinfo.get('name', '')
    except Exception as e:
        logger.error(f"Could not get user info from Google: {str(e)}")
        return RedirectResponse(
            url=f"{get_frontend_url()}/?oauth_error=userinfo_failed"
        )

    if not google_email:
        return RedirectResponse(
            url=f"{get_frontend_url()}/?oauth_error=no_email"
        )

    # Check if user exists, create if not
    import os
    import secrets

    from src.repositories.postgresql_user_repository import PostgreSQLUserRepository
    from src.services.auth_service import AuthService
    from src.utils.security import create_access_token, hash_password
    
    db_config = {
        "host": os.getenv("DB_HOST", "postgres"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "devfriend"),
        "user": os.getenv("DB_USER", "devfriend"),
        "password": os.getenv("DB_PASSWORD", "devfriend"),
    }
    
    user_repository = PostgreSQLUserRepository(**db_config)
    auth_service = AuthService(user_repository)
    
    # Check if user exists
    existing_user = auth_service.get_user_by_email(google_email)
    
    if existing_user:
        # User exists, log them in
        user = existing_user
        logger.info(f"Logging in existing user {user.id} via Google OAuth")
    else:
        # Create new user (no password for OAuth users - they can't login with password)
        from src.models.user import User

        # Generate a random password hash for OAuth users (they can't login with password)
        random_password = secrets.token_urlsafe(32)
        password_hash = hash_password(random_password)
        
        new_user = User(email=google_email, password_hash=password_hash)
        user = user_repository.save(new_user)
        logger.info(f"Created new user {user.id} via Google OAuth")
    
    # Generate JWT token
    token_data = {"sub": str(user.id), "email": user.email}
    jwt_token = create_access_token(token_data)
    
    # Redirect to frontend with token
    logger.info(f"Redirecting to frontend: {get_frontend_url()}")
    return RedirectResponse(
        url=f"{get_frontend_url()}/?oauth_login_success=true&token={jwt_token}"
    )

