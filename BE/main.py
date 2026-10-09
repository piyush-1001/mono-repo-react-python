from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Simple One Page App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str


@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/message")
def send_message(payload: MessageRequest):
    return {
        "reply": f"Hello from FastAPI! You sent: {payload.message}",
        "original_message": payload.message,
    }
