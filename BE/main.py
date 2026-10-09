from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

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

TRAINING_TEXTS = [
    "I love this product and it works great",
    "This is amazing and very helpful",
    "The app is fast and smooth to use",
    "I am happy with the support and service",
    "This is good and easy to understand",
    "The feature is poor and very slow",
    "I have a problem with the login screen",
    "This is bad and confusing",
    "There is an issue with the dashboard",
    "The experience was awful and weak",
    "The interface is clean and better than before",
    "The tool feels excellent and very smart",
]
TRAINING_LABELS = [
    "positive", "positive", "positive", "positive", "positive",
    "negative", "negative", "negative", "negative", "negative",
    "positive", "positive",
]

ml_model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", LogisticRegression(max_iter=1000)),
])
ml_model.fit(TRAINING_TEXTS, TRAINING_LABELS)


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


def ml_predict_text(text: str):
    prediction = ml_model.predict([text])[0]
    probability = max(ml_model.predict_proba([text])[0])
    return {
        "label": prediction,
        "confidence": round(float(probability) * 100, 2),
        "model": "logistic_regression",
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
    ml_result = ml_predict_text(payload.message)
    return {
        "reply": f"AI review: {analysis['prediction']}",
        "original_message": payload.message,
        "analysis": analysis,
        "ml_prediction": ml_result,
    }


@app.post("/api/ml/predict")
def predict_ml(payload: MessageRequest):
    return {
        "input": payload.message,
        "ml_prediction": ml_predict_text(payload.message),
    }
