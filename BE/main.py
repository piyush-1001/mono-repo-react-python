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


def _get_ml_model():
    """Lazily train and return the ML model to avoid race conditions on import."""
    if not getattr(_get_ml_model, "_trained", False):
        ml_model.fit(TRAINING_TEXTS, TRAINING_LABELS)
        _get_ml_model._trained = True
    return ml_model


def simple_ai_analysis(text: str):
    words = [word.strip(".,!?;:'\"()[]{}") for word in text.lower().split()]
    words = [word for word in words if word]

    NEGATION_PREFIXES = {"not", "never", "no", "hardly", "barely", "scarcely", "without"}
    NEGATION_WINDOW = 3

    positive_score = 0
    negative_score = 0
    negated_positive = False
    negated_negative = False

    for i, word in enumerate(words):
        is_negated = i > 0 and words[max(0, i - NEGATION_WINDOW):i] and any(
            w in NEGATION_PREFIXES for w in words[max(0, i - NEGATION_WINDOW):i]
        )

        if word in POSITIVE_WORDS:
            if is_negated:
                negative_score += 1
            else:
                positive_score += 1
        elif word in NEGATIVE_WORDS:
            if is_negated:
                positive_score += 1
            else:
                negative_score += 1

    if positive_score > negative_score:
        sentiment = "positive"
    elif negative_score > positive_score:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    max_score = max(positive_score, negative_score)
    confidence = round(max_score / max(len(words), 1) * 100, 1) if max_score > 0 else 0.0
    keywords = list(set(words) & (POSITIVE_WORDS | NEGATIVE_WORDS))[:5]

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "keywords": keywords if keywords else ["no strong signal"],
        "word_count": len(words),
        "prediction": f"The model detects a mostly {sentiment} tone in the text.",
    }


def ml_predict_text(text: str):
    model = _get_ml_model()
    proba = model.predict_proba([text])[0]
    max_idx = proba.argmax()
    label = model.classes_[max_idx]
    return {
        "label": label,
        "confidence": round(float(proba[max_idx]) * 100, 2),
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
