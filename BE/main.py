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
    "good", "great", "excellent", "happy", "love", "amazing", "fast", "smart", "nice",
    "success", "support", "helpful", "smooth", "easy", "positive", "improve", "better"
}
NEGATIVE_WORDS = {
    "bad", "slow", "issue", "problem", "error", "poor", "hate", "worst", "broken",
    "difficult", "confusing", "negative", "fail", "weak"
}


def simple_ai_analysis(text: str):
    words = [word.strip(".,!?;:'\"()[]{}") for word in text.lower().split()]
    words = [word for word in words if word]

    positive_score = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_score = sum(1 for word in words if word in NEGATIVE_WORDS)

    if positive_score > negative_score:
        sentiment = "positive"
    elif negative_score > positive_score:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    confidence = round(max(positive_score, negative_score) / max(len(words), 1) * 100, 1)
    keywords = [word for word in words if word in POSITIVE_WORDS or word in NEGATIVE_WORDS][:5]

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "keywords": keywords if keywords else ["no strong signal"],
        "word_count": len(words),
        "prediction": f"The model detects a mostly {sentiment} tone in the text.",
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
        "reply": f"AI review: {analysis['prediction']}",
        "original_message": payload.message,
        "analysis": analysis,
    }
