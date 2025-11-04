import logging

from repositories.postgresql_repository import PostgreSQLRepository

logger = logging.getLogger(__name__)

class EmailRepository(PostgreSQLRepository):
    def __init__(self):
        super().__init__()
    
    async def get_user_integrations(self, user_id: int):
        """
        Get all email integrations for a user
        """
        try:
            query = """
                SELECT * FROM email_integrations 
                WHERE user_id = $1
                ORDER BY created_at DESC
            """
            result = await self.fetch_all(query, user_id)
            return result
        except Exception as e:
            logger.error(f"Error getting email integrations for user {user_id}: {str(e)}")
            raise e

    async def get_integration(self, integration_id: int, user_id: int):
        """
        Get a specific integration for the user
        """
        try:
            query = "SELECT * FROM email_integrations WHERE id = $1 AND user_id = $2"
            result = await self.fetch_one(query, integration_id, user_id)
            return result
        except Exception as e:
            logger.error(f"Error getting integration {integration_id}: {str(e)}")
            raise e

    async def create_integration(self, integration_data: dict):
        """
        Create a new email integration
        """
        try:
            query = """
                INSERT INTO email_integrations 
                (user_id, provider, credential_id, email_address, status)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """
            result = await self.fetch_one(
                query,
                integration_data['user_id'],
                integration_data['provider'],
                integration_data['credential_id'],
                integration_data['email_address'],
                integration_data['status']
            )
            return result
        except Exception as e:
            logger.error(f"Error creating email integration: {str(e)}")
            raise e

    async def delete_integration(self, integration_id: int):
        """
        Delete an email integration
        """
        try:
            query = "DELETE FROM email_integrations WHERE id = $1"
            await self.execute(query, integration_id)
        except Exception as e:
            logger.error(f"Error deleting email integration {integration_id}: {str(e)}")
            raise e

    async def update_integration_status(self, integration_id: int, status: str):
        """
        Update the status of an integration
        """
        try:
            query = "UPDATE email_integrations SET status = $1, updated_at = NOW() WHERE id = $2"
            await self.execute(query, status, integration_id)
        except Exception as e:
            logger.error(f"Error updating integration status {integration_id}: {str(e)}")
            raise e

    async def update_last_sync(self, integration_id: int):
        """
        Update the last sync time
        """
        try:
            query = "UPDATE email_integrations SET last_sync = NOW(), updated_at = NOW() WHERE id = $1"
            await self.execute(query, integration_id)
        except Exception as e:
            logger.error(f"Error updating last sync for integration {integration_id}: {str(e)}")
            raise e