import json
import logging
from typing import Any, Dict, List, Optional

from src.repositories.postgresql_integration_repository import (
    PostgreSQLIntegrationRepository,
)

logger = logging.getLogger(__name__)

class IntegrationRepository(PostgreSQLIntegrationRepository):
    def __init__(self):
        super().__init__()
    
    def get_user_integrations(self, user_id: int, service_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtener todas las integraciones de un usuario
        """
        try:
            if service_type:
                query = """
                    SELECT * FROM integrations 
                    WHERE user_id = %s AND service_type = %s
                    ORDER BY created_at DESC
                """
                result = self.fetch_all(query, user_id, service_type)
            else:
                query = """
                    SELECT * FROM integrations 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """
                result = self.fetch_all(query, user_id)
            return result
        except Exception as e:
            logger.error(f"Error getting integrations for user {user_id}: {str(e)}")
            raise e

    def get_integration(self, integration_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener una integración específica del usuario
        """
        try:
            query = "SELECT * FROM integrations WHERE id = %s AND user_id = %s"
            result = self.fetch_one(query, integration_id, user_id)
            return result
        except Exception as e:
            logger.error(f"Error getting integration {integration_id}: {str(e)}")
            raise e

    def create_integration(self, integration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear una nueva integración
        """
        try:
            print(f"🔍 Creating integration with data: {integration_data}")
            
            # INSERT sin RETURNING
            query = """
                INSERT INTO integrations 
                (user_id, secret_id, service_type, config, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """
            config_json = json.dumps(integration_data.get('config')) if integration_data.get('config') else None
            
            self.execute(
                query,
                integration_data['user_id'],
                integration_data.get('secret_id'),
                integration_data['service_type'],
                config_json,
                integration_data.get('is_active', True)
            )
            
            print("🔍 Insert executed, now fetching the last inserted integration")
            
            # Consulta para obtener la integración recién insertada
            fetch_query = """
                SELECT * FROM integrations 
                WHERE user_id = %s AND service_type = %s
                ORDER BY id DESC LIMIT 1
            """
            result = self.fetch_one(
                fetch_query,
                integration_data['user_id'],
                integration_data['service_type']
            )
            
            print(f"🔍 Fetch result: {result}")
            return result
        except Exception as e:
            print(f"🔥 Error in create_integration: {e}")
            logger.error(f"Error creating integration: {str(e)}")
            raise e


    def update_integration(self, integration_id: int, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Actualizar una integración
        """
        try:
            # Verificar que la integración pertenece al usuario
            integration = self.get_integration(integration_id, user_id)
            if not integration:
                return None

            set_parts = []
            params = []
            param_count = 1

            for field, value in update_data.items():
                if value is not None:
                    set_parts.append(f"{field} = %s")  # Cambiado a %s
                    params.append(value)

            if not set_parts:
                return integration

            set_parts.append("updated_at = NOW()")
            params.extend([integration_id, user_id])

            query = f"""
                UPDATE integrations 
                SET {', '.join(set_parts)}
                WHERE id = %s AND user_id = %s
                RETURNING *
            """
            result = self.fetch_one(query, *params)
            return result
        except Exception as e:
            logger.error(f"Error updating integration {integration_id}: {str(e)}")
            raise e

    def delete_integration(self, integration_id: int, user_id: int) -> bool:
        """
        Eliminar una integración
        """
        try:
            # Verificar que la integración pertenece al usuario
            integration = self.get_integration(integration_id, user_id)
            if not integration:
                return False

            query = "DELETE FROM integrations WHERE id = %s AND user_id = %s"
            self.execute(query, integration_id, user_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting integration {integration_id}: {str(e)}")
            raise e