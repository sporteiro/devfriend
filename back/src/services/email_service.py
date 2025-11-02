import json
import logging

from src.models.integration import IntegrationCreate
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository
from src.services.integration_service import IntegrationService

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.integration_service = IntegrationService(user_id)
        self.secret_repository = PostgreSQLSecretRepository()

    def get_email_integrations(self):
        """
        Obtener integraciones de email del usuario
        """
        logger.debug(f"🔍 Getting email integrations for user {self.user_id}")
        try:
            logger.debug("📞 Calling integration_service.get_integrations...")
            integrations = self.integration_service.get_integrations('gmail')
            logger.debug(f"✅ Found {len(integrations)} integrations")
            return integrations
        except Exception as e:
            logger.error(f"❌ Error in get_email_integrations: {str(e)}", exc_info=True)
            raise e

    def create_email_integration(self, integration_data: dict):
        """
        Crear una nueva integración de email
        """
        try:
            # Verificar que la credencial existe y pertenece al usuario
            credential_id = integration_data.get('credential_id')
            if credential_id:
                credential = self.secret_repository.find_by_id(credential_id)
                if not credential:
                    raise Exception("Credential not found or access denied")
                if credential and credential.user_id != self.user_id:
                    raise Exception("Credential not found or access denied")

            integration_create = IntegrationCreate(
                user_id=self.user_id,
                secret_id=credential_id,
                service_type='gmail',
                config={
                    'email_address': 'user@gmail.com',
                    'status': 'connected'
                }
            )
            
            new_integration = self.integration_service.create_integration(integration_create)
            return new_integration
            
        except Exception as e:
            logger.error(f"Error creating email integration for user {self.user_id}: {str(e)}")
            raise e

    def get_emails(self, integration_id: int):
        """
        Obtener emails de una integración de Gmail
        """
        try:
            # Verificar que la integración existe y es de tipo gmail
            integration = self.integration_service.get_integration(integration_id)
            if not integration or integration.get('service_type') != 'gmail':
                raise Exception("Email integration not found")

            # TODO: Conectar a Gmail API usando las credenciales del secret
            # Por ahora devolvemos datos mock
            return [
                {
                    'id': 'msg_1',
                    'sender': 'John Doe <john@example.com>',
                    'subject': 'Meeting tomorrow 10:00',
                    'preview': 'Hi, let\'s meet tomorrow at 10:00 to discuss...',
                    'date': '2024-01-15T10:00:00Z',
                    'read': False
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting emails for integration {integration_id}: {str(e)}")
            raise e

    def sync_emails(self, integration_id: int):
        """
        Sincronizar emails de Gmail
        """
        try:
            # Verificar que la integración existe
            integration = self.integration_service.get_integration(integration_id)
            if not integration or integration.get('service_type') != 'gmail':
                raise Exception("Email integration not found")

            # TODO: Implementar sincronización real con Gmail API
            logger.info(f"Syncing emails for Gmail integration {integration_id}")
            
        except Exception as e:
            logger.error(f"Error syncing emails for integration {integration_id}: {str(e)}")
            raise e

    def get_email_stats(self, integration_id: int):
        """
        Obtener estadísticas de email
        """
        try:
            # Verificar que la integración existe
            integration = self.integration_service.get_integration(integration_id)
            if not integration or integration.get('service_type') != 'gmail':
                raise Exception("Email integration not found")

            # TODO: Obtener estadísticas reales de Gmail API
            return {
                'total_emails': 150,
                'unread_count': 3,
                'last_sync': '2024-01-15T10:00:00Z'
            }
            
        except Exception as e:
            logger.error(f"Error getting email stats for integration {integration_id}: {str(e)}")
            raise e