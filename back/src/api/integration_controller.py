from fastapi import APIRouter, Depends, HTTPException, Query

from src.middleware.auth_middleware import get_current_user_id
from src.models.integration import IntegrationCreate, IntegrationUpdate
from src.models.user import User
from src.services.integration_service import IntegrationService

router = APIRouter()

@router.get("/integrations")
async def get_integrations(
    service_type: str = Query(default=None, description="Filtrar por tipo de servicio"),
    current_user: User = Depends(get_current_user_id)
):
    """
    Obtener todas las integraciones del usuario actual, opcionalmente filtrando por service_type
    """
    try:
        integration_service = IntegrationService(current_user)
        integrations = await integration_service.get_user_integrations(service_type)
        return integrations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{integration_id}")
async def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user_id)
):
    """
    Obtener una integración específica del usuario actual
    """
    try:
        integration_service = IntegrationService(current_user.id)
        integration = await integration_service.get_integration(integration_id)
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        return integration
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations")
async def create_integration(
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_current_user_id)
):
    """
    Crear una nueva integración
    """
    try:
        integration_service = IntegrationService(current_user)
        new_integration = await integration_service.create_integration(integration_data)
        return new_integration
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/integrations/{integration_id}")
async def update_integration(
    integration_id: int,
    update_data: IntegrationUpdate,
    current_user: User = Depends(get_current_user_id)
):
    """
    Actualizar una integración
    """
    try:
        integration_service = IntegrationService(current_user)
        updated_integration = await integration_service.update_integration(integration_id, update_data)
        if not updated_integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        return updated_integration
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user_id)
):
    """
    Eliminar una integración
    """
    try:
        integration_service = IntegrationService(current_user)
        success = await integration_service.delete_integration(integration_id)
        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")
        return {"message": "Integration deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))