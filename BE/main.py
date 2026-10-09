from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import Counter
import re

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


# ============== Sentiment Analysis ==============
POSITIVE_WORDS = {
    "good", "great", "excellent", "happy", "love", "amazing", "fast", "smart", "nice",
    "success", "support", "helpful", "smooth", "easy", "positive", "improve", "better",
    "awesome", "fantastic", "wonderful", "perfect", "brilliant", "outstanding"
}
NEGATIVE_WORDS = {
    "bad", "slow", "issue", "problem", "error", "poor", "hate", "worst", "broken",
    "difficult", "confusing", "negative", "fail", "weak", "terrible", "awful", "horrible",
    "useless", "disappointing", "annoying", "frustrating"
}


def simple_ai_analysis(text: str):
    """Keyword-based sentiment analysis"""
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


# ============== Text Classification ==============
CATEGORY_KEYWORDS = {
    "technology": ["software", "computer", "app", "code", "developer", "api", "web", "data", "ai", "ml", "machine"],
    "business": ["company", "sales", "revenue", "profit", "market", "customer", "business", "strategy"],
    "health": ["health", "doctor", "medical", "patient", "hospital", "treatment", "symptom", "wellness"],
    "education": ["school", "student", "teacher", "learning", "course", "education", "study", "class"],
    "food": ["food", "eat", "restaurant", "meal", "cook", "recipe", "dish", "taste", "delicious"],
    "travel": ["travel", "trip", "flight", "hotel", "vacation", "destination", "tourist", "visit"],
}


def classify_text(text: str):
    """Simple keyword-based text classification"""
    words = set(word.lower().strip(".,!?;:'\"()[]{}") for word in text.split())

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for word in words if word in keywords)
        scores[category] = score

    top_category = max(scores, key=scores.get) if max(scores.values()) > 0 else "general"

    return {
        "category": top_category,
        "scores": scores,
        "confidence": round(scores[top_category] / max(len(words), 1) * 100, 1) if scores[top_category] > 0 else 0
    }


# ============== Named Entity Recognition (Simple) ==============
def extract_entities(text: str):
    """Simple rule-based entity extraction"""
    # Capitalized words (potential proper nouns)
    capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)

    # Numbers
    numbers = re.findall(r'\b\d+\.?\d*\b', text)

    # Emails
    emails = re.findall(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)

    # URLs
    urls = re.findall(r'https?://\S+', text)

    # Capitalized sequences (names, places)
    proper_nouns = [w for w in capitalized if len(w) > 2][:10]

    return {
        "emails": emails,
        "urls": urls,
        "numbers": numbers[:5],
        "proper_nouns": proper_nouns,
        "entity_count": len(emails) + len(urls) + len(numbers) + len(proper_nouns)
    }


# ============== Text Statistics ==============
def analyze_text_stats(text: str):
    """Calculate various text statistics"""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    char_count = len(text)
    word_count = len(words)
    sentence_count = max(len(sentences), 1)
    avg_word_length = sum(len(w) for w in words) / max(word_count, 1)
    avg_sentence_length = word_count / max(sentence_count, 1)

    # Word frequency
    word_freq = Counter(word.lower().strip(".,!?;:'\"()[]{}") for word in words if len(word) > 2)
    top_words = word_freq.most_common(10)

    return {
        "characters": char_count,
        "words": word_count,
        "sentences": sentence_count,
        "avg_word_length": round(avg_word_length, 2),
        "avg_sentence_length": round(avg_sentence_length, 2),
        "top_words": dict(top_words),
        "unique_words": len(word_freq)
    }


# ============== Text Summarization (Simple) ==============
def summarize_text(text: str, max_sentences=2):
    """Simple extractive summarization"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    # Score sentences by word count and keyword presence
    scored = []
    for sent in sentences:
        score = len(sent.split())
        # Boost if contains important words
        sent_lower = sent.lower()
        score += sum(5 for cat_words in CATEGORY_KEYWORDS.values()
                     if any(w in sent_lower for w in cat_words))
        scored.append((score, sent))

    scored.sort(reverse=True)
    top_sentences = [s[1] for s in scored[:max_sentences]]

    return " ".join(top_sentences)


# ============== API Endpoints ==============
@app.get("/")
def read_root():
    return {"message": "AI/ML Smart App API is running", "version": "2.0"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/message")
def send_message(payload: MessageRequest):
    """Full AI analysis endpoint"""
    analysis = simple_ai_analysis(payload.message)
    classification = classify_text(payload.message)
    entities = extract_entities(payload.message)
    stats = analyze_text_stats(payload.message)
    summary = summarize_text(payload.message)

    return {
        "reply": f"AI Analysis: {analysis['prediction']}",
        "original_message": payload.message,
        "analysis": analysis,
        "classification": classification,
        "entities": entities,
        "statistics": stats,
        "summary": summary
    }


@app.post("/api/sentiment")
def sentiment_analysis(payload: MessageRequest):
    """Sentiment analysis only"""
    return simple_ai_analysis(payload.message)


@app.post("/api/classify")
def text_classification(payload: MessageRequest):
    """Text classification only"""
    return classify_text(payload.message)


@app.post("/api/entities")
def entity_extraction(payload: MessageRequest):
    """Named entity extraction only"""
    return extract_entities(payload.message)


@app.post("/api/stats")
def text_statistics(payload: MessageRequest):
    """Text statistics only"""
    return analyze_text_stats(payload.message)


@app.post("/api/summarize")
def text_summarization(payload: MessageRequest):
    """Text summarization only"""
    return {
        "summary": summarize_text(payload.message),
        "original_length": len(payload.message.split())
    }
