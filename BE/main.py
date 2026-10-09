from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from config import POSITIVE_WORDS, NEGATIVE_WORDS, TRAINING_TEXTS, TRAINING_LABELS

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

ml_model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression(max_iter=1000)),
])


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
