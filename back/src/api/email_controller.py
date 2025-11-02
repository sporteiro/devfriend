from fastapi import APIRouter, Depends, HTTPException

from src.middleware.auth_middleware import get_current_user_id
from src.models.user import User
from src.services.email_service import EmailService
from src.services.integration_service import IntegrationService

router = APIRouter()

@router.get("/email/integrations")
def get_email_integrations(current_user_id: int = Depends(get_current_user_id)):
    """
    Obtener las integraciones de email del usuario
    """
    try:
        print(f"🎯 DEBUG: Entering endpoint, user_id: {current_user_id}")
        email_service = EmailService(current_user_id)
        print("🎯 DEBUG: EmailService created")
        integrations = email_service.get_email_integrations()
        print(f"🎯 DEBUG: Got {len(integrations)} integrations")
        return integrations
    except Exception as e:
        print(f"🔥 ERROR in endpoint: {e}")
        import traceback
        print(f"🔥 TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email/integrations")
def create_email_integration(integration_data: dict, current_user: User = Depends(get_current_user_id)):
    print(f'integration_data: {integration_data}')
    """
    Create a new email integration
    """
    try:
        email_service = EmailService(current_user)
        integration = email_service.create_email_integration(integration_data)
        return integration
    except Exception as e:
        print(f'error creating email integration ACA: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/email/integrations/{integration_id}")
def delete_email_integration(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Eliminar una integración de email
    """
    try:
        integration_service = IntegrationService(current_user)
        success = integration_service.delete_integration(integration_id)
        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")
        return {"message": "Email integration deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/integrations/{integration_id}/emails")
def get_emails(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Obtener emails de una integración
    """
    try:
        email_service = EmailService(current_user)
        emails = email_service.get_emails(integration_id)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/email/integrations/{integration_id}/sync")
def sync_emails(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Sincronizar emails de una integración
    """
    try:
        email_service = EmailService(current_user)
        email_service.sync_emails(integration_id)
        return {"message": "Email sync started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/integrations/{integration_id}/stats")
def get_email_stats(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Obtener estadísticas de email
    """
    try:
        email_service = EmailService(current_user)
        stats = email_service.get_email_stats(integration_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))