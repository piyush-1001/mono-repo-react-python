from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml_models import (
    spam_classifier,
    text_similarity,
    markov_generator,
    kmeans_cluster,
)

app = FastAPI(title="AI/ML Smart App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str


class SimilarityRequest(BaseModel):
    text_a: str
    text_b: str


class GenerateRequest(BaseModel):
    seed: str = ""
    max_words: int = Field(default=30, ge=1, le=100)


class ClusterRequest(BaseModel):
    texts: list[str] = Field(min_length=2)
    k: int = Field(default=2, ge=1, le=10)


# ============== Sentiment Analysis (keyword-based) ==============
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


# ============== API Endpoints ==============
@app.get("/")
def read_root():
    return {"message": "AI/ML Smart App API is running", "version": "2.0"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/models")
def list_models():
    """Catalogue of the models exposed by this API, consumed by the frontend."""
    return {
        "models": [
            {
                "id": "sentiment",
                "name": "Keyword Sentiment Analysis",
                "endpoint": "/api/sentiment",
                "method": "POST",
                "description": "Scores a text as positive, negative or neutral.",
            },
            {
                "id": "spam",
                "name": "Naive Bayes Spam Classifier",
                "endpoint": "/api/predict",
                "method": "POST",
                "description": "Multinomial naive Bayes trained on a spam/ham corpus.",
            },
            {
                "id": "similarity",
                "name": "TF-IDF Cosine Similarity",
                "endpoint": "/api/similarity",
                "method": "POST",
                "description": "Compares two texts term-by-term with TF-IDF weighting.",
            },
            {
                "id": "generate",
                "name": "Markov Text Generator",
                "endpoint": "/api/generate",
                "method": "POST",
                "description": "Generates text from a bigram Markov chain.",
            },
            {
                "id": "cluster",
                "name": "K-Means Document Clustering",
                "endpoint": "/api/cluster",
                "method": "POST",
                "description": "Groups documents by cosine distance over TF-IDF vectors.",
            },
        ]
    }


@app.post("/api/message")
def send_message(payload: MessageRequest):
    """Keyword sentiment analysis (used by the frontend analyzer)."""
    analysis = simple_ai_analysis(payload.message)
    return {
        "reply": f"AI review: {analysis['prediction']}",
        "original_message": payload.message,
        "analysis": analysis,
    }


@app.post("/api/sentiment")
def sentiment_analysis(payload: MessageRequest):
    """Sentiment analysis only."""
    return simple_ai_analysis(payload.message)


@app.post("/api/predict")
def predict_spam(payload: MessageRequest):
    """Multinomial naive Bayes spam/ham classifier (see ml_models.py)."""
    return spam_classifier.predict(payload.message)


@app.post("/api/similarity")
def similarity(payload: SimilarityRequest):
    """TF-IDF vectorization + cosine similarity between two texts."""
    return text_similarity(payload.text_a, payload.text_b)


@app.post("/api/generate")
def generate_text(payload: GenerateRequest):
    """Bigram Markov-chain text generation."""
    return markov_generator.generate(payload.seed, payload.max_words)


@app.post("/api/cluster")
def cluster_documents(payload: ClusterRequest):
    """K-means clustering over TF-IDF vectors of the given documents."""
    if payload.k > len(payload.texts):
        raise HTTPException(
            status_code=400,
            detail=f"k={payload.k} is larger than the number of documents ({len(payload.texts)})",
        )
    return kmeans_cluster(payload.texts, k=payload.k)
