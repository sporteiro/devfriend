from datetime import datetime
import json
import logging

from src.models.integration import IntegrationCreate
from src.models.user import User
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository
from src.services.integration_service import IntegrationService
from src.utils.gmail_client import GmailClient


logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, user_id):
        # Accept both User object or int
        if isinstance(user_id, User):
            self.user_id = user_id.id
        else:
            self.user_id = user_id
        self.integration_service = IntegrationService(self.user_id)
        self.secret_repository = PostgreSQLSecretRepository()

    def get_email_integrations(self):
        """
        Get email integrations for the user
        """
        logger.debug(f"Getting email integrations for user {self.user_id}")
        try:
            logger.debug("Calling integration_service.get_integrations...")
            integrations = self.integration_service.get_integrations('gmail')
            logger.debug(f"Found {len(integrations)} integrations")

            # Map integration data to include email_address and status from config
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
                mapped['email_address'] = config.get('email_address', 'unknown@gmail.com')
                mapped['status'] = config.get('status', 'unknown')
                mapped['provider'] = 'gmail'

                # Also extract last_sync if available
                if 'last_sync' in config:
                    mapped['last_sync'] = config.get('last_sync')

                # Get unread count if integration is connected
                unread_count = 0
                if mapped.get('status') == 'connected' and integration.get('id'):
                    try:
                        gmail_client = self._get_gmail_client(integration.get('id'))
                        unread_count = gmail_client.get_unread_count()
                        logger.debug(f"Integration {integration.get('id')} has {unread_count} unread messages")
                    except Exception as e:
                        logger.warning(f"Could not get unread count for integration {integration.get('id')}: {str(e)}")
                        unread_count = 0

                mapped['unread_count'] = unread_count

                logger.debug(f"Mapped integration {mapped.get('id')}: email_address={mapped.get('email_address')}, status={mapped.get('status')}, unread_count={unread_count}")
                mapped_integrations.append(mapped)

            logger.info(f"Returning {len(mapped_integrations)} mapped integrations")
            return mapped_integrations
        except Exception as e:
            logger.error(f"Error in get_email_integrations: {str(e)}", exc_info=True)
            raise e

    def create_email_integration(self, integration_data: dict):
        """
        Create a new email integration
        """
        try:
            # Verify that the credential exists and belongs to the user
            credential_id = integration_data.get('credential_id')
            logger.info(f"Creating email integration for user {self.user_id} with credential_id {credential_id}")

            if credential_id:
                credential = self.secret_repository.find_by_id(credential_id)
                if not credential:
                    logger.error(f"Credential {credential_id} not found")
                    raise Exception("Credential not found or access denied")
                if credential.user_id != self.user_id:
                    logger.error(f"Credential {credential_id} belongs to user {credential.user_id}, but current user is {self.user_id}")
                    raise Exception("Credential not found or access denied")

                # Get real email address from Gmail API
                try:
                    credentials_data = json.loads(credential.encrypted_value)
                    logger.debug(f"Credentials parsed for credential {credential_id}, has refresh_token: {'refresh_token' in credentials_data}")

                    gmail_client = GmailClient(credentials_data)
                    profile = gmail_client.get_profile()
                    email_address = profile.get('email_address', 'unknown@gmail.com')
                    status = 'connected'
                    logger.info(f"Successfully connected to Gmail API, email: {email_address}")
                except Exception as e:
                    logger.warning(f"Could not connect to Gmail API during creation: {str(e)}", exc_info=True)
                    email_address = 'unknown@gmail.com'
                    status = 'error'
            else:
                logger.warning("No credential_id provided, creating integration without credentials")
                email_address = 'unknown@gmail.com'
                status = 'pending'

            integration_create = IntegrationCreate(
                user_id=self.user_id,
                secret_id=credential_id,
                service_type='gmail',
                config={
                    'email_address': email_address,
                    'status': status
                }
            )

            logger.info(f"Calling integration_service.create_integration for user {self.user_id}")
            new_integration = self.integration_service.create_integration(integration_create)
            logger.info(f"Successfully created integration {new_integration.get('id')} for user {self.user_id}")
            return new_integration

        except Exception as e:
            logger.error(f"Error creating email integration for user {self.user_id}: {str(e)}", exc_info=True)
            raise e

    def _get_gmail_client(self, integration_id: int) -> GmailClient:
        """
        Get Gmail client for an integration.

        Args:
            integration_id: Integration ID

        Returns:
            GmailClient instance
        """
        # Get integration
        integration = self.integration_service.get_integration(integration_id)
        if not integration or integration.get('service_type') != 'gmail':
            raise Exception("Email integration not found")

        logger.debug(f"Integration {integration_id} data: {integration}")

        # Get secret
        secret_id = integration.get('secret_id')
        logger.debug(f"Raw secret_id from integration: {secret_id} (type: {type(secret_id)})")
        if not secret_id:
            logger.error(f"Integration {integration_id} has no secret_id configured")
            raise Exception("No credentials configured for this integration. Please reconnect your Gmail account.")

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
            logger.warning(f"Secret {secret_id} not found in database. Integration may be orphaned. Looking for valid Gmail secret...")
            # List all secrets for this user to find a valid Gmail secret
            all_secrets = self.secret_repository.find_by_user(self.user_id)
            gmail_secrets = [s for s in all_secrets if 'gmail' in s.service_type.lower() or 'email' in s.service_type.lower()]

            if gmail_secrets and len(gmail_secrets) > 0:
                # Use the most recent Gmail secret
                valid_secret_id = gmail_secrets[0].id
                logger.info(f"Found valid Gmail secret {valid_secret_id}. Updating integration {integration_id} to use it.")

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
                logger.error(f"User {self.user_id} has no Gmail secrets available")
                raise Exception(
                    f"Credentials not found (secret_id: {secret_id}). "
                    "No Gmail credentials available. Please connect your Gmail account via OAuth."
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
            raise Exception(f"Invalid credentials format in secret {secret.id}. Please reconnect your Gmail account via OAuth.")
        except Exception as e:
            logger.error(f"Error processing credentials for secret {secret.id}: {str(e)}", exc_info=True)
            raise

        # Validate required fields
        if 'refresh_token' not in credentials_data:
            logger.error(f"Secret {secret.id} is missing refresh_token. Available keys: {list(credentials_data.keys())}")

            # Check if we have client_id and client_secret to initiate OAuth
            if 'client_id' in credentials_data and 'client_secret' in credentials_data:
                raise Exception(
                    f"Missing refresh_token. Please authorize Gmail access. "
                    f"Go to /auth/google/authorize?secret_id={secret.id} to complete OAuth authorization."
                )
            else:
                raise Exception(
                    "Missing refresh_token and OAuth credentials (client_id, client_secret). "
                    "Please add Gmail credentials first."
                )

        required_fields = ['client_id', 'client_secret', 'refresh_token']
        for field in required_fields:
            if field not in credentials_data:
                raise Exception(f"Missing required credential field: {field}")

        # Create Gmail client
        return GmailClient(credentials_data)

    def get_emails(self, integration_id: int, max_results: int = 50, query: str = None):
        """
        Get emails from a Gmail integration

        Args:
            integration_id: Integration ID
            max_results: Maximum number of emails to return (default: 50)
            query: Optional Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')

        Returns:
            List of email messages
        """
        try:
            # Get Gmail client
            gmail_client = self._get_gmail_client(integration_id)

            # Get message list
            messages = gmail_client.get_messages(max_results=max_results, query=query)

            # Get detailed information for each message
            email_list = []
            for msg in messages:
                try:
                    message_details = gmail_client.get_message_details(msg['id'])
                    email_list.append(message_details)
                except Exception as e:
                    logger.warning(f"Error getting details for message {msg.get('id')}: {str(e)}")
                    continue

            logger.info(f"Retrieved {len(email_list)} emails for integration {integration_id}")
            return email_list

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error getting emails for integration {integration_id}: {error_msg}")

            # Check if error is about Gmail API not enabled
            if 'Gmail API has not been used' in error_msg or 'it is disabled' in error_msg or 'accessNotConfigured' in error_msg:
                raise Exception(
                    "Gmail API is not enabled in your Google Cloud project. "
                    "Please enable it at: https://console.developers.google.com/apis/api/gmail.googleapis.com/overview "
                    "Then wait a few minutes and try again."
                )
            raise e

    def sync_emails(self, integration_id: int):
        """
        Sync Gmail emails - triggers a refresh of emails from Gmail API.
        This method can be extended to store emails in a local cache/database.
        """
        try:
            # Get Gmail client to verify connection
            gmail_client = self._get_gmail_client(integration_id)

            # Get profile to verify connection works
            profile = gmail_client.get_profile()
            logger.info(
                f"Syncing emails for Gmail integration {integration_id}. "
                f"Email: {profile.get('email_address')}, "
                f"Total messages: {profile.get('messages_total', 0)}"
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

                from src.models.integration import IntegrationUpdate
                update_data = IntegrationUpdate(config=config)
                self.integration_service.update_integration(integration_id, update_data)

            return {"message": "Email sync completed successfully"}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error syncing emails for integration {integration_id}: {error_msg}")

            # Update integration status to error only if it's not a credentials issue
            # (credentials errors should be handled by the user reconnecting)
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
