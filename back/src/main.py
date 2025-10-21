from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.note_controller import router as note_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

app.include_router(note_router)

@app.get("/")
async def root():
    return {"message": "Hello, Dockerized FastAPI!"}
