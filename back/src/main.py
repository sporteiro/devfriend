from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth_controller import router as auth_router
from src.api.note_controller import router as note_router

app = FastAPI(title="DevFriend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(note_router, tags=["Notes"])


@app.get("/")
async def root():
    return {"message": "Hello, Dockerized FastAPI!"}
