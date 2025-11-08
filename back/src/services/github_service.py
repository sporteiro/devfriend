from datetime import datetime
import json
import logging

from src.models.integration import IntegrationCreate
from src.models.user import User
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository
from src.services.integration_service import IntegrationService
from src.utils.github_client import GitHubClient


logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, user_id):
        # Accept both User object or int
        if isinstance(user_id, User):
            self.user_id = user_id.id
        else:
            self.user_id = user_id
        self.integration_service = IntegrationService(self.user_id)
        self.secret_repository = PostgreSQLSecretRepository()

    def get_github_integrations(self):
        """
        Get GitHub integrations for the user
        """
        logger.debug(f"Getting GitHub integrations for user {self.user_id}")
        try:
            logger.debug("Calling integration_service.get_integrations...")
            integrations = self.integration_service.get_integrations('github')
            logger.debug(f"Found {len(integrations)} integrations")

            # Map integration data to include github_username and status from config
            mapped_integrations = []
            for integration in integrations:
                mapped = dict(integration)
                config = integration.get('config', {})

                # Handle config if it's a string (JSON)
                if isinstance(config, str):
                    try:
                        config = json.loads(config) if config else {}
                    except:
                        config = {}
                elif config is None:
                    config = {}

                logger.debug(f"Integration {integration.get('id')} config: {config}")

                # Extract fields from config to top level for frontend compatibility
                mapped['github_username'] = config.get('github_username', 'unknown')
                mapped['status'] = config.get('status', 'unknown')
                mapped['provider'] = 'github'

                # Also extract last_sync if available
                if 'last_sync' in config:
                    mapped['last_sync'] = config.get('last_sync')

                logger.debug(f"Mapped integration {mapped.get('id')}: github_username={mapped.get('github_username')}, status={mapped.get('status')}")
                mapped_integrations.append(mapped)

            logger.info(f"Returning {len(mapped_integrations)} mapped integrations")
            return mapped_integrations
        except Exception as e:
            logger.error(f"Error in get_github_integrations: {str(e)}", exc_info=True)
            raise e

    def create_github_integration(self, integration_data: dict):
        """
        Create a new GitHub integration
        """
        try:
            # Verify that the credential exists and belongs to the user
            credential_id = integration_data.get('credential_id')
            logger.info(f"Creating GitHub integration for user {self.user_id} with credential_id {credential_id}")

            if credential_id:
                credential = self.secret_repository.find_by_id(credential_id)
                if not credential:
                    logger.error(f"Credential {credential_id} not found")
                    raise Exception("Credential not found or access denied")
                if credential.user_id != self.user_id:
                    logger.error(f"Credential {credential_id} belongs to user {credential.user_id}, but current user is {self.user_id}")
                    raise Exception("Credential not found or access denied")

                # Get real GitHub username from GitHub API
                try:
                    credentials_data = json.loads(credential.encrypted_value)
                    logger.debug(f"Credentials parsed for credential {credential_id}, has access_token: {'access_token' in credentials_data}")

                    github_client = GitHubClient(credentials_data['access_token'])
                    user_profile = github_client.get_user()
                    github_username = user_profile.get('login', 'unknown')
                    status = 'connected'
                    logger.info(f"Successfully connected to GitHub API, username: {github_username}")
                except Exception as e:
                    logger.warning(f"Could not connect to GitHub API during creation: {str(e)}", exc_info=True)
                    github_username = 'unknown'
                    status = 'error'
            else:
                logger.warning("No credential_id provided, creating integration without credentials")
                github_username = 'unknown'
                status = 'pending'

            integration_create = IntegrationCreate(
                user_id=self.user_id,
                secret_id=credential_id,
                service_type='github',
                config={
                    'github_username': github_username,
                    'status': status
                }
            )

            logger.info(f"Calling integration_service.create_integration for user {self.user_id}")
            new_integration = self.integration_service.create_integration(integration_create)
            logger.info(f"Successfully created integration {new_integration.get('id')} for user {self.user_id}")
            return new_integration

        except Exception as e:
            logger.error(f"Error creating GitHub integration for user {self.user_id}: {str(e)}", exc_info=True)
            raise e

    def _get_github_client(self, integration_id: int) -> GitHubClient:
        """
        Get GitHub client for an integration.

        Args:
            integration_id: Integration ID

        Returns:
            GitHubClient instance
        """
        # Get integration
        integration = self.integration_service.get_integration(integration_id)
        if not integration or integration.get('service_type') != 'github':
            raise Exception("GitHub integration not found")

        logger.debug(f"Integration {integration_id} data: {integration}")

        # Get secret
        secret_id = integration.get('secret_id')
        logger.debug(f"Raw secret_id from integration: {secret_id} (type: {type(secret_id)})")
        if not secret_id:
            logger.error(f"Integration {integration_id} has no secret_id configured")
            raise Exception("No credentials configured for this integration. Please reconnect your GitHub account.")

        logger.debug(f"Looking for secret_id {secret_id} (type: {type(secret_id)}) for user {self.user_id}")

        # Ensure secret_id is an integer
        if secret_id is not None:
            try:
                secret_id = int(secret_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid secret_id type: {type(secret_id)}, value: {secret_id}")
                raise Exception(f"Invalid secret_id format: {secret_id}")

        secret = self.secret_repository.find_by_id(secret_id)
        if not secret:
            logger.warning(f"Secret {secret_id} not found in database. Integration may be orphaned. Looking for valid GitHub secret...")
            # List all secrets for this user to find a valid GitHub secret
            all_secrets = self.secret_repository.find_by_user(self.user_id)
            github_secrets = [s for s in all_secrets if 'github' in s.service_type.lower()]

            if github_secrets and len(github_secrets) > 0:
                # Use the most recent GitHub secret
                valid_secret_id = github_secrets[0].id
                logger.info(f"Found valid GitHub secret {valid_secret_id}. Updating integration {integration_id} to use it.")

                # Update integration with valid secret_id
                from src.models.integration import IntegrationUpdate
                update_data = IntegrationUpdate(secret_id=valid_secret_id)
                updated_integration = self.integration_service.update_integration(integration_id, update_data)

                # Refresh integration data to get updated secret_id
                integration = self.integration_service.get_integration(integration_id)
                logger.info(f"Updated integration {integration_id} to use secret_id {valid_secret_id}")

                # Get the full secret with decrypted value (find_by_user returns masked values)
                secret = self.secret_repository.find_by_id(valid_secret_id)
                if not secret:
                    raise Exception(f"Could not retrieve secret {valid_secret_id} after updating integration")
            else:
                logger.error(f"User {self.user_id} has no GitHub secrets available")
                raise Exception(
                    f"Credentials not found (secret_id: {secret_id}). "
                    "No GitHub credentials available. Please connect your GitHub account via OAuth."
                )

        if secret.user_id != self.user_id:
            logger.error(f"Secret {secret_id} belongs to user {secret.user_id}, but current user is {self.user_id}")
            raise Exception("Credentials access denied")

        # Decrypt and parse credentials
        try:
            encrypted_value = secret.encrypted_value
            logger.debug(f"Secret {secret.id} encrypted_value type: {type(encrypted_value)}, length: {len(str(encrypted_value)) if encrypted_value else 0}")

            if not encrypted_value:
                logger.error(f"Secret {secret.id} has empty encrypted_value")
                raise Exception("Secret encrypted_value is empty. The credential may be corrupted.")

            # Try to parse as JSON
            if isinstance(encrypted_value, str):
                logger.debug(f"Parsing JSON string for secret {secret.id} (length: {len(encrypted_value)})")
                if encrypted_value.strip() == '':
                    raise Exception("Encrypted value is an empty string")
                credentials_data = json.loads(encrypted_value)
            elif isinstance(encrypted_value, dict):
                logger.debug(f"Using dict directly for secret {secret.id}")
                credentials_data = encrypted_value
            else:
                logger.error(f"Invalid encrypted_value type for secret {secret.id}: {type(encrypted_value)}")
                raise Exception(f"Invalid encrypted_value type: {type(encrypted_value)}")

            logger.debug(f"Successfully parsed credentials for secret {secret.id}, keys: {list(credentials_data.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse credentials JSON for secret {secret.id}: {str(e)}")
            logger.error(f"Encrypted value preview (first 200 chars): {str(encrypted_value)[:200] if encrypted_value else 'None'}")
            raise Exception(f"Invalid credentials format in secret {secret.id}. Please reconnect your GitHub account via OAuth.")
        except Exception as e:
            logger.error(f"Error processing credentials for secret {secret.id}: {str(e)}", exc_info=True)
            raise

        # Validate required fields
        if 'access_token' not in credentials_data:
            logger.error(f"Secret {secret.id} is missing access_token. Available keys: {list(credentials_data.keys())}")
            raise Exception("Missing access_token in GitHub credentials. Please reconnect your GitHub account.")

        # Create GitHub client
        return GitHubClient(credentials_data['access_token'])

    def get_repos(self, integration_id: int, max_results: int = 50, visibility: str = "all"):
        """
        Get repositories from a GitHub integration

        Args:
            integration_id: Integration ID
            max_results: Maximum number of repos to return (default: 50)
            visibility: Repository visibility: 'all', 'public', or 'private'

        Returns:
            List of repositories
        """
        try:
            # Get GitHub client
            github_client = self._get_github_client(integration_id)

            # Get repositories
            repos = github_client.get_repos(visibility=visibility)

            # Limit results
            limited_repos = repos[:max_results] if repos else []

            logger.info(f"Retrieved {len(limited_repos)} repos for integration {integration_id}")
            return limited_repos

        except Exception as e:
            logger.error(f"Error getting repos for integration {integration_id}: {str(e)}")
            raise e

    def get_user_profile(self, integration_id: int):
        """
        Get GitHub user profile from integration

        Args:
            integration_id: Integration ID

        Returns:
            GitHub user profile data
        """
        try:
            # Get GitHub client
            github_client = self._get_github_client(integration_id)

            # Get user profile
            user_profile = github_client.get_user()

            logger.info(f"Retrieved GitHub user profile for integration {integration_id}")
            return user_profile

        except Exception as e:
            logger.error(f"Error getting user profile for integration {integration_id}: {str(e)}")
            raise e

    def sync_github(self, integration_id: int):
        """
        Sync GitHub data - triggers a refresh of data from GitHub API.
        """
        try:
            # Get GitHub client to verify connection
            github_client = self._get_github_client(integration_id)

            # Get user profile to verify connection works
            user_profile = github_client.get_user()
            logger.info(
                f"Syncing GitHub data for integration {integration_id}. "
                f"Username: {user_profile.get('login')}, "
                f"Name: {user_profile.get('name', 'N/A')}"
            )

            # Update integration config with last sync time
            integration = self.integration_service.get_integration(integration_id)
            if integration:
                config = integration.get('config', {})
                if isinstance(config, str):
                    import json
                    config = json.loads(config)
                if not isinstance(config, dict):
                    config = {}

                config['last_sync'] = datetime.utcnow().isoformat()
                config['status'] = 'connected'
                config['github_username'] = user_profile.get('login', 'unknown')

                from src.models.integration import IntegrationUpdate
                update_data = IntegrationUpdate(config=config)
                self.integration_service.update_integration(integration_id, update_data)

            return {"message": "GitHub sync completed successfully"}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error syncing GitHub for integration {integration_id}: {error_msg}")

            # Update integration status to error only if it's not a credentials issue
            if "credentials" not in error_msg.lower() and "not found" not in error_msg.lower():
                try:
                    integration = self.integration_service.get_integration(integration_id)
                    if integration:
                        config = integration.get('config', {})
                        if isinstance(config, str):
                            import json
                            config = json.loads(config)
                        if not isinstance(config, dict):
                            config = {}

                        config['status'] = 'error'
                        from src.models.integration import IntegrationUpdate
                        update_data = IntegrationUpdate(config=config)
                        self.integration_service.update_integration(integration_id, update_data)
                except:
                    pass
            raise e

    def get_github_stats(self, integration_id: int):
        """
        Get GitHub statistics

        Returns:
            Dictionary with GitHub statistics
        """
        try:
            # Get GitHub client
            github_client = self._get_github_client(integration_id)

            # Get user profile for basic info
            user_profile = github_client.get_user()

            # Get repositories for counts
            repos = github_client.get_repos(visibility='all')
            public_repos = [repo for repo in repos if repo.get('private') is False] if repos else []
            private_repos = [repo for repo in repos if repo.get('private') is True] if repos else []

            # Get integration for last_sync
            integration = self.integration_service.get_integration(integration_id)
            config = integration.get('config', {}) if integration else {}
            if isinstance(config, str):
                config = json.loads(config)
            if not isinstance(config, dict):
                config = {}
            last_sync = config.get('last_sync', None)

            return {
                'username': user_profile.get('login', ''),
                'name': user_profile.get('name', ''),
                'public_repos_count': len(public_repos),
                'private_repos_count': len(private_repos),
                'total_repos_count': len(repos) if repos else 0,
                'followers': user_profile.get('followers', 0),
                'following': user_profile.get('following', 0),
                'last_sync': last_sync
            }

        except Exception as e:
            logger.error(f"Error getting GitHub stats for integration {integration_id}: {str(e)}")
            raise e
