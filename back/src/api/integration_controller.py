from fastapi import APIRouter, Depends, HTTPException, Query

from src.middleware.auth_middleware import get_current_user_id
from src.models.integration import IntegrationCreate, IntegrationUpdate
from src.models.user import User
from src.services.integration_service import IntegrationService

router = APIRouter()

@router.get("/integrations")
def get_integrations(
    service_type: str = Query(default=None, description="Filter by service type"),
    current_user: User = Depends(get_current_user_id)
):
    """
    Get all integrations for the current user, optionally filtered by service_type
    """
    try:
        integration_service = IntegrationService(current_user)
        integrations = integration_service.get_integrations(service_type)
        return integrations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integrations/{integration_id}")
def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user_id)
):
    """
    Get a specific integration for the current user
    """
    try:
        integration_service = IntegrationService(current_user.id)
        integration = integration_service.get_integration(integration_id)
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        return integration
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations")
def create_integration(
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_current_user_id)
):
    """
    Create a new integration
    """
    try:
        integration_service = IntegrationService(current_user)
        new_integration = integration_service.create_integration(integration_data)
        return new_integration
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/integrations/{integration_id}")
def update_integration(
    integration_id: int,
    update_data: IntegrationUpdate,
    current_user: User = Depends(get_current_user_id)
):
    """
    Update an integration
    """
    try:
        integration_service = IntegrationService(current_user)
        updated_integration = integration_service.update_integration(integration_id, update_data)
        if not updated_integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        return updated_integration
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/integrations/{integration_id}")
def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user_id)
):
    """
    Delete an integration
    """
    try:
        integration_service = IntegrationService(current_user)
        success = integration_service.delete_integration(integration_id)
        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")
        return {"message": "Integration deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))