import logging
import sys


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth_controller import router as auth_router
from src.api.email_controller import router as email_router
from src.api.github_controller import router as github_router
from src.api.integration_controller import router as integration_router
from src.api.note_controller import router as note_router
from src.api.oauth_controller import router as oauth_router
from src.api.secret_controller import router as secret_router


app = FastAPI(title="DevFriend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(oauth_router, tags=["OAuth"])
app.include_router(note_router, tags=["Notes"])
app.include_router(secret_router, tags=["Secrets"])
app.include_router(integration_router, tags=["Integrations"])
app.include_router(email_router, tags=["Email"])
app.include_router(github_router, tags=["Github"])

@app.get("/")
async def root():
    return {"message": "DevFriend is ON"}
