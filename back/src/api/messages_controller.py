import traceback

from fastapi import APIRouter, Depends, HTTPException, Query

from src.middleware.auth_middleware import get_current_user_id
from src.models.user import User
from src.services.integration_service import IntegrationService
from src.services.slack_service import SlackService


router = APIRouter()

@router.get("/messages/integrations")
def get_slack_integrations(current_user_id: int = Depends(get_current_user_id)):
    """
    Get Slack integrations for the user
    """
    try:
        print(f"DEBUG: Entering Slack endpoint, user_id: {current_user_id}")
        slack_service = SlackService(current_user_id)
        print("DEBUG: SlackService created")
        integrations = slack_service.get_slack_integrations()
        print(f"DEBUG: Got {len(integrations)} integrations")
        return integrations
    except Exception as e:
        print(f"ERROR in Slack endpoint: {e}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/integrations")
def create_slack_integration(integration_data: dict, current_user: User = Depends(get_current_user_id)):
    print(f'slack_integration_data: {integration_data}')
    """
    Create a new Slack integration
    """
    try:
        slack_service = SlackService(current_user)
        integration = slack_service.create_slack_integration(integration_data)
        return integration
    except Exception as e:
        print(f'Error creating Slack integration: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/messages/integrations/{integration_id}")
def delete_slack_integration(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Delete a Slack integration
    """
    try:
        integration_service = IntegrationService(current_user)
        success = integration_service.delete_integration(integration_id)
        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")
        return {"message": "Slack integration deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/integrations/{integration_id}/channels")
def get_channels(
    integration_id: int,
    current_user: User = Depends(get_current_user_id)
):
    """
    Get channels from a Slack integration
    """
    try:
        slack_service = SlackService(current_user)
        channels = slack_service.get_channels(integration_id)
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/integrations/{integration_id}/messages")
def get_messages(
    integration_id: int,
    current_user: User = Depends(get_current_user_id),
    channel_id: str = Query(default=None, description="Channel ID to filter messages"),
    max_results: int = Query(default=100, ge=1, le=1000, description="Maximum number of messages to return")
):
    """
    Get messages from a Slack integration
    """
    try:
        slack_service = SlackService(current_user)
        messages = slack_service.get_messages(integration_id, channel_id=channel_id, max_results=max_results)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/integrations/{integration_id}/workspace")
def get_workspace_info(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Get Slack workspace information from integration
    """
    try:
        slack_service = SlackService(current_user)
        workspace_info = slack_service.get_workspace_info(integration_id)
        return workspace_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/integrations/{integration_id}/sync")
def sync_slack(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Sync Slack data from an integration
    """
    try:
        slack_service = SlackService(current_user)
        slack_service.sync_slack(integration_id)
        return {"message": "Slack sync started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/integrations/{integration_id}/stats")
def get_slack_stats(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Get Slack statistics
    """
    try:
        slack_service = SlackService(current_user)
        stats = slack_service.get_slack_stats(integration_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
