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


POSITIVE_WORDS = {
    "good", "great", "excellent", "happy", "love", "amazing", "fast", "smart", "nice", "success",
    "support", "helpful", "smooth", "easy", "positive", "improve", "better"
}
NEGATIVE_WORDS = {
    "bad", "slow", "issue", "problem", "error", "poor", "hate", "worst", "broken", "difficult",
    "confusing", "negative", "fail", "weak"
}


def simple_ai_analysis(text: str):
    cleaned = text.lower()
    words = [word.strip(".,!?;:'\"()[]{}") for word in cleaned.split()]
    words = [w for w in words if w]

    positive_score = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_score = sum(1 for word in words if word in NEGATIVE_WORDS)

    sentiment = "neutral"
    if positive_score > negative_score:
        sentiment = "positive"
    elif negative_score > positive_score:
        sentiment = "negative"

    confidence = round(max(positive_score, negative_score) / max(len(words), 1) * 100, 1)
    keyword_hits = [w for w in words if w in POSITIVE_WORDS or w in NEGATIVE_WORDS]

    if not keyword_hits:
        keyword_hits = ["no strong signal detected"]

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "keywords": keyword_hits[:5],
        "word_count": len(words),
        "prediction": "The model detects a mostly {} tone in the text.".format(sentiment),
    }


@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/message")
def send_message(payload: MessageRequest):
    analysis = simple_ai_analysis(payload.message)
    return {
        "reply": f"AI model review: {analysis['prediction']}",
        "original_message": payload.message,
        "analysis": analysis,
    }
