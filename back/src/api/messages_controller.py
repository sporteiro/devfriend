import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from src.middleware.auth_middleware import get_current_user_id
from src.models.user import User
from src.services.integration_service import IntegrationService
from src.services.slack_service import SlackService


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/messages/integrations")
def get_slack_integrations(current_user_id: int = Depends(get_current_user_id)):
    """
    Get Slack integrations for the user
    """
    try:
        logger.debug(f"Getting Slack integrations for user {current_user_id}")
        slack_service = SlackService(current_user_id)
        integrations = slack_service.get_slack_integrations()
        logger.debug(f"Retrieved {len(integrations)} Slack integrations")
        return integrations
    except Exception as e:
        logger.error(f"Error getting Slack integrations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages/integrations")
def create_slack_integration(integration_data: dict, current_user: User = Depends(get_current_user_id)):
    """
    Create a new Slack integration
    """
    try:
        logger.debug(f"Creating Slack integration for user {current_user.id}")
        slack_service = SlackService(current_user)
        integration = slack_service.create_slack_integration(integration_data)
        return integration
    except Exception as e:
        logger.error(f"Error creating Slack integration: {str(e)}", exc_info=True)
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
