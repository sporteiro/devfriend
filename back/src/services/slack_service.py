from datetime import datetime
import json
import logging

from src.models.integration import IntegrationCreate
from src.models.user import User
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository
from src.services.integration_service import IntegrationService
from src.utils.slack_client import SlackClient


logger = logging.getLogger(__name__)

class SlackService:
    def __init__(self, user_id):
        # Accept both User object or int
        if isinstance(user_id, User):
            self.user_id = user_id.id
        else:
            self.user_id = user_id
        self.integration_service = IntegrationService(self.user_id)
        self.secret_repository = PostgreSQLSecretRepository()

    def get_slack_integrations(self):
        """
        Get Slack integrations for the user
        """
        logger.debug(f"Getting Slack integrations for user {self.user_id}")
        try:
            logger.debug("Calling integration_service.get_integrations...")
            integrations = self.integration_service.get_integrations('slack')
            logger.debug(f"Found {len(integrations)} integrations")

            # Map integration data to include workspace_name and status from config
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
                mapped['workspace_name'] = config.get('workspace_name', 'unknown')
                mapped['status'] = config.get('status', 'unknown')
                mapped['provider'] = 'slack'
                mapped['team_id'] = config.get('team_id')

                # Also extract last_sync if available
                if 'last_sync' in config:
                    mapped['last_sync'] = config.get('last_sync')

                logger.debug(f"Mapped integration {mapped.get('id')}: workspace_name={mapped.get('workspace_name')}, status={mapped.get('status')}")
                mapped_integrations.append(mapped)

            logger.info(f"Returning {len(mapped_integrations)} mapped integrations")
            return mapped_integrations
        except Exception as e:
            logger.error(f"Error in get_slack_integrations: {str(e)}", exc_info=True)
            raise e

    def create_slack_integration(self, integration_data: dict):
        """
        Create a new Slack integration
        """
        try:
            # Verify that the credential exists and belongs to the user
            credential_id = integration_data.get('credential_id')
            logger.info(f"Creating Slack integration for user {self.user_id} with credential_id {credential_id}")

            if credential_id:
                credential = self.secret_repository.find_by_id(credential_id)
                if not credential:
                    logger.error(f"Credential {credential_id} not found")
                    raise Exception("Credential not found or access denied")
                if credential.user_id != self.user_id:
                    logger.error(f"Credential {credential_id} belongs to user {credential.user_id}, but current user is {self.user_id}")
                    raise Exception("Credential not found or access denied")

                # Get real Slack workspace info from Slack API
                try:
                    credentials_data = json.loads(credential.encrypted_value)
                    logger.debug(f"Credentials parsed for credential {credential_id}, has bot_token: {'bot_token' in credentials_data}")

                    bot_token = credentials_data.get('bot_token') or credentials_data.get('access_token')
                    if not bot_token:
                        raise Exception("No bot_token or access_token found in credentials")

                    slack_client = SlackClient(bot_token)
                    workspace_info = slack_client.get_workspace_info()
                    workspace_name = workspace_info.get('name', 'unknown')
                    team_id = workspace_info.get('id')
                    status = 'connected'
                    logger.info(f"Successfully connected to Slack API, workspace: {workspace_name}")
                except Exception as e:
                    logger.warning(f"Could not connect to Slack API during creation: {str(e)}", exc_info=True)
                    workspace_name = 'unknown'
                    team_id = None
                    status = 'error'
            else:
                logger.warning("No credential_id provided, creating integration without credentials")
                workspace_name = 'unknown'
                team_id = None
                status = 'pending'

            integration_create = IntegrationCreate(
                user_id=self.user_id,
                secret_id=credential_id,
                service_type='slack',
                config={
                    'workspace_name': workspace_name,
                    'team_id': team_id,
                    'status': status
                }
            )

            logger.info(f"Calling integration_service.create_integration for user {self.user_id}")
            new_integration = self.integration_service.create_integration(integration_create)
            logger.info(f"Successfully created integration {new_integration.get('id')} for user {self.user_id}")
            return new_integration

        except Exception as e:
            logger.error(f"Error creating Slack integration for user {self.user_id}: {str(e)}", exc_info=True)
            raise e

    def _get_slack_client(self, integration_id: int) -> SlackClient:
        """
        Get Slack client for an integration.

        Args:
            integration_id: Integration ID

        Returns:
            SlackClient instance
        """
        # Get integration
        integration = self.integration_service.get_integration(integration_id)
        if not integration or integration.get('service_type') != 'slack':
            raise Exception("Slack integration not found")

        logger.debug(f"Integration {integration_id} data: {integration}")

        # Get secret
        secret_id = integration.get('secret_id')
        logger.debug(f"Raw secret_id from integration: {secret_id} (type: {type(secret_id)})")
        if not secret_id:
            logger.error(f"Integration {integration_id} has no secret_id configured")
            raise Exception("No credentials configured for this integration. Please reconnect your Slack account.")

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
            logger.warning(f"Secret {secret_id} not found in database. Integration may be orphaned. Looking for valid Slack secret...")
            # List all secrets for this user to find a valid Slack secret
            all_secrets = self.secret_repository.find_by_user(self.user_id)
            slack_secrets = [s for s in all_secrets if 'slack' in s.service_type.lower()]

            if slack_secrets and len(slack_secrets) > 0:
                # Use the most recent Slack secret
                valid_secret_id = slack_secrets[0].id
                logger.info(f"Found valid Slack secret {valid_secret_id}. Updating integration {integration_id} to use it.")

                # Update integration with valid secret_id
                from src.models.integration import IntegrationUpdate
                update_data = IntegrationUpdate(secret_id=valid_secret_id)
                updated_integration = self.integration_service.update_integration(integration_id, update_data)

                # Refresh integration data to get updated secret_id
                integration = self.integration_service.get_integration(integration_id)
                logger.info(f"Updated integration {integration_id} to use secret_id {valid_secret_id}")

                # Get the full secret with decrypted value
                secret = self.secret_repository.find_by_id(valid_secret_id)
                if not secret:
                    raise Exception(f"Could not retrieve secret {valid_secret_id} after updating integration")
            else:
                logger.error(f"User {self.user_id} has no Slack secrets available")
                raise Exception(
                    f"Credentials not found (secret_id: {secret_id}). "
                    "No Slack credentials available. Please connect your Slack account via OAuth."
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
            raise Exception(f"Invalid credentials format in secret {secret.id}. Please reconnect your Slack account via OAuth.")
        except Exception as e:
            logger.error(f"Error processing credentials for secret {secret.id}: {str(e)}", exc_info=True)
            raise

        # Validate required fields
        bot_token = credentials_data.get('bot_token') or credentials_data.get('access_token')
        if not bot_token:
            logger.error(f"Secret {secret.id} is missing bot_token or access_token. Available keys: {list(credentials_data.keys())}")
            raise Exception("Missing bot_token or access_token in Slack credentials. Please reconnect your Slack account.")

        # Create Slack client
        return SlackClient(bot_token)

    def get_channels(self, integration_id: int):
        """
        Get channels from a Slack integration

        Args:
            integration_id: Integration ID

        Returns:
            List of channels
        """
        try:
            # Get Slack client
            slack_client = self._get_slack_client(integration_id)

            # Get channels
            channels = slack_client.get_channels(exclude_archived=True)

            logger.info(f"Retrieved {len(channels)} channels for integration {integration_id}")
            return channels

        except Exception as e:
            logger.error(f"Error getting channels for integration {integration_id}: {str(e)}")
            raise e

    def get_messages(self, integration_id: int, channel_id: str = None, max_results: int = 100):
        """
        Get messages from a Slack integration

        Args:
            integration_id: Integration ID
            channel_id: Optional channel ID to filter messages
            max_results: Maximum number of messages to return (default: 100)

        Returns:
            List of messages
        """
        try:
            # Get Slack client
            slack_client = self._get_slack_client(integration_id)

            if channel_id:
                # Get messages from specific channel
                messages = slack_client.get_channel_messages(channel_id, limit=max_results)
            else:
                # Get messages from all channels (get first channel as default)
                channels = slack_client.get_channels(exclude_archived=True)
                if channels:
                    # Get messages from the first channel
                    first_channel = channels[0]
                    messages = slack_client.get_channel_messages(first_channel['id'], limit=max_results)
                else:
                    messages = []

            logger.info(f"Retrieved {len(messages)} messages for integration {integration_id}")
            return messages

        except Exception as e:
            logger.error(f"Error getting messages for integration {integration_id}: {str(e)}")
            raise e

    def get_workspace_info(self, integration_id: int):
        """
        Get Slack workspace information from integration

        Args:
            integration_id: Integration ID

        Returns:
            Workspace information
        """
        try:
            # Get Slack client
            slack_client = self._get_slack_client(integration_id)

            # Get workspace info
            workspace_info = slack_client.get_workspace_info()

            logger.info(f"Retrieved Slack workspace info for integration {integration_id}")
            return workspace_info

        except Exception as e:
            logger.error(f"Error getting workspace info for integration {integration_id}: {str(e)}")
            raise e

    def sync_slack(self, integration_id: int):
        """
        Sync Slack data - triggers a refresh of data from Slack API.
        """
        try:
            # Get Slack client to verify connection
            slack_client = self._get_slack_client(integration_id)

            # Get workspace info to verify connection works
            workspace_info = slack_client.get_workspace_info()
            logger.info(
                f"Syncing Slack data for integration {integration_id}. "
                f"Workspace: {workspace_info.get('name')}, "
                f"ID: {workspace_info.get('id')}"
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
                config['workspace_name'] = workspace_info.get('name', 'unknown')
                config['team_id'] = workspace_info.get('id')

                from src.models.integration import IntegrationUpdate
                update_data = IntegrationUpdate(config=config)
                self.integration_service.update_integration(integration_id, update_data)

            return {"message": "Slack sync completed successfully"}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error syncing Slack for integration {integration_id}: {error_msg}")

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

    def get_slack_stats(self, integration_id: int):
        """
        Get Slack statistics

        Returns:
            Dictionary with Slack statistics
        """
        try:
            # Get Slack client
            slack_client = self._get_slack_client(integration_id)

            # Get workspace info for basic info
            workspace_info = slack_client.get_workspace_info()

            # Get channels for counts
            channels = slack_client.get_channels(exclude_archived=True)
            public_channels = [ch for ch in channels if not ch.get('is_private', False)] if channels else []
            private_channels = [ch for ch in channels if ch.get('is_private', False)] if channels else []

            # Get users count
            users = slack_client.get_users()
            active_users = [u for u in users if not u.get('deleted', False)] if users else []

            # Get integration for last_sync
            integration = self.integration_service.get_integration(integration_id)
            config = integration.get('config', {}) if integration else {}
            if isinstance(config, str):
                config = json.loads(config)
            if not isinstance(config, dict):
                config = {}
            last_sync = config.get('last_sync', None)

            return {
                'workspace_name': workspace_info.get('name', ''),
                'workspace_id': workspace_info.get('id', ''),
                'public_channels_count': len(public_channels),
                'private_channels_count': len(private_channels),
                'total_channels_count': len(channels) if channels else 0,
                'active_users_count': len(active_users),
                'total_users_count': len(users) if users else 0,
                'last_sync': last_sync
            }

        except Exception as e:
            logger.error(f"Error getting Slack stats for integration {integration_id}: {str(e)}")
            raise e
