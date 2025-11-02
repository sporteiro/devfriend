import logging

from src.models.integration import IntegrationCreate, IntegrationUpdate
from src.repositories.integration_repository import IntegrationRepository
from src.repositories.postgresql_secret_repository import PostgreSQLSecretRepository

logger = logging.getLogger(__name__)

class IntegrationService:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.integration_repository = IntegrationRepository()
        self.secret_repository = PostgreSQLSecretRepository()

    def get_integrations(self, service_type: str = None):
        """
        Obtener integraciones del usuario
        """
        logger.debug(f"🔍 IntegrationService.get_integrations for user {self.user_id}")
        try:
            integrations = self.integration_repository.get_user_integrations(
                self.user_id, service_type
            )
            logger.debug(f"✅ IntegrationService found {len(integrations)} integrations")
            return integrations
        except Exception as e:
            logger.error(f"❌ Error in IntegrationService.get_integrations: {str(e)}", exc_info=True)
            raise e

    def get_integration(self, integration_id: int):
        """
        Obtener una integración específica
        """
        try:
            integration = self.integration_repository.get_integration(
                integration_id, self.user_id
            )
            return integration
        except Exception as e:
            logger.error(f"Error getting integration {integration_id}: {str(e)}")
            raise e

    def create_integration(self, integration_data: IntegrationCreate):
        """
        Crear una nueva integración
        """
        try:
            # Verificar que el secret_id pertenece al usuario si se proporciona
            if integration_data.secret_id:
                secret = self.secret_repository.find_by_id(integration_data.secret_id)
                # if secret and secret.user_id != self.user_id:
                #    raise Exception("Secret not found or access denied")
                # else:
                #     raise Exception("Secret not found or access denied")

            # Crear la integración
            integration_dict = integration_data.model_dump()
            integration_dict['user_id'] = self.user_id
            
            new_integration = self.integration_repository.create_integration(
                integration_dict
            )
            return new_integration
            
        except Exception as e:
            logger.error(f"Error creating integration for user {self.user_id}: {str(e)}")
            raise e

    def update_integration(self, integration_id: int, update_data: IntegrationUpdate):
        """
        Actualizar una integración
        """
        try:
            # Verificar que el secret_id pertenece al usuario si se proporciona
            if update_data.secret_id:
                secret = self.secret_repository.get_secret(
                    update_data.secret_id, self.user_id
                )
                if not secret:
                    raise Exception("Secret not found or access denied")

            update_dict = update_data.model_dump(exclude_unset=True)
            updated_integration = self.integration_repository.update_integration(
                integration_id, self.user_id, update_dict
            )
            return updated_integration
            
        except Exception as e:
            logger.error(f"Error updating integration {integration_id}: {str(e)}")
            raise e

    def delete_integration(self, integration_id: int):
        """
        Eliminar una integración
        """
        try:
            success = self.integration_repository.delete_integration(
                integration_id, self.user_id
            )
            return success
        except Exception as e:
            logger.error(f"Error deleting integration {integration_id}: {str(e)}")
            raise e