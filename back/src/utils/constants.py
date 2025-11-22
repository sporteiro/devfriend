# OAuth URLs - Google
import os


GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# OAuth URLs - GitHub
GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USERINFO_URL = 'https://api.github.com/user'
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')

# OAuth URLs - Slack
SLACK_AUTH_URL = 'https://slack.com/oauth/v2/authorize'
SLACK_TOKEN_URL = 'https://slack.com/api/oauth.v2.access'
SLACK_USERINFO_URL = 'https://slack.com/api/users.identity'
SLACK_CLIENT_ID = os.getenv('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET = os.getenv('SLACK_CLIENT_SECRET')

# Scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
LOGIN_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
GITHUB_SCOPES = ['repo', 'read:user', 'notifications']
SLACK_SCOPES = scopes = [
    'channels:read',
    'channels:history',
    'team:read',
    'groups:read',
    'groups:history',
    'im:history',
    'mpim:history'
]
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:88')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8888')
