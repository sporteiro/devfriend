import traceback

from fastapi import APIRouter, Depends, HTTPException, Query

from src.middleware.auth_middleware import get_current_user_id
from src.models.user import User
from src.services.github_service import GitHubService
from src.services.integration_service import IntegrationService


router = APIRouter()

@router.get("/github/integrations")
def get_github_integrations(current_user_id: int = Depends(get_current_user_id)):
    """
    Get GitHub integrations for the user
    """
    try:
        print(f"DEBUG: Entering GitHub endpoint, user_id: {current_user_id}")
        github_service = GitHubService(current_user_id)
        print("DEBUG: GitHubService created")
        integrations = github_service.get_github_integrations()
        print(f"DEBUG: Got {len(integrations)} integrations")
        return integrations
    except Exception as e:
        print(f"ERROR in GitHub endpoint: {e}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/github/integrations")
def create_github_integration(integration_data: dict, current_user: User = Depends(get_current_user_id)):
    print(f'github_integration_data: {integration_data}')
    """
    Create a new GitHub integration
    """
    try:
        github_service = GitHubService(current_user)
        integration = github_service.create_github_integration(integration_data)
        return integration
    except Exception as e:
        print(f'Error creating GitHub integration: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/github/integrations/{integration_id}")
def delete_github_integration(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Delete a GitHub integration
    """
    try:
        integration_service = IntegrationService(current_user)
        success = integration_service.delete_integration(integration_id)
        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")
        return {"message": "GitHub integration deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/github/integrations/{integration_id}/repos")
def get_repos(
    integration_id: int,
    current_user: User = Depends(get_current_user_id),
    max_results: int = Query(default=50, ge=1, le=500, description="Maximum number of repos to return"),
    visibility: str = Query(default="all", description="Repository visibility: 'all', 'public', or 'private'")
):
    """
    Get repositories from a GitHub integration
    """
    try:
        github_service = GitHubService(current_user)
        repos = github_service.get_repos(integration_id, max_results=max_results, visibility=visibility)
        return repos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/github/integrations/{integration_id}/user")
def get_github_user(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Get GitHub user profile from integration
    """
    try:
        github_service = GitHubService(current_user)
        user_profile = github_service.get_user_profile(integration_id)
        return user_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/github/integrations/{integration_id}/sync")
def sync_github(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Sync GitHub data from an integration
    """
    try:
        github_service = GitHubService(current_user)
        github_service.sync_github(integration_id)
        return {"message": "GitHub sync started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/github/integrations/{integration_id}/stats")
def get_github_stats(integration_id: int, current_user: User = Depends(get_current_user_id)):
    """
    Get GitHub statistics
    """
    try:
        github_service = GitHubService(current_user)
        stats = github_service.get_github_stats(integration_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
