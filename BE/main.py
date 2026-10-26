from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from corpus_prep import MIN_DOCUMENTS, prepare
from lsa_topic_model import lsa_topics
from ml_models import (
    spam_classifier,
    text_similarity,
    markov_generator,
    kmeans_cluster,
)
from task_export import export_filename, to_csv, to_markdown
from task_ranker import rank_tasks
from task_store import TaskStoreError, fetch_tasks

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


class TaskItem(BaseModel):
    id: int
    title: str
    status: str = "pending"
    priority: str = "medium"
    created_at: str | None = None


class RankRequest(BaseModel):
    tasks: list[TaskItem] = Field(min_length=1)


class TopicsRequest(BaseModel):
    # min_length rejects an empty array only. The real floor is content-based -
    # two documents that are not all whitespace - and belongs to corpus_prep,
    # whose error says which of the posted items were blank rather than
    # "expected 2 items".
    texts: list[str] = Field(min_length=1)
    topics: int = Field(default=2, ge=1, le=5)
    top_terms: int = Field(default=5, ge=1, le=15)


class ExportRequest(BaseModel):
    tasks: list[TaskItem] = Field(min_length=1)
    format: str = "csv"
    title: str = "Task ranking"


# Anything else is a 400 rather than a fallback to csv: a caller that asks for
# "xlsx" and quietly receives CSV learns about it by opening the file.
EXPORT_FORMATS = ("csv", "markdown")


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
            {
                "id": "rank-tasks",
                "name": "Task Priority Ranker",
                "endpoint": "/api/rank-tasks",
                "method": "POST",
                "description": "Scores tasks by priority, status, age and urgent wording.",
            },
            {
                "id": "rank-stored-tasks",
                "name": "Stored Task Ranker",
                "endpoint": "/api/tasks/ranked",
                "method": "GET",
                "description": "Reads the Node.js task store and ranks it in one call.",
            },
            {
                "id": "export-tasks",
                "name": "Ranking Export",
                "endpoint": "/api/tasks/export",
                "method": "POST",
                "description": "Ranks posted tasks and returns them as CSV or Markdown.",
            },
            {
                "id": "topics",
                "name": "LSA Topic Model",
                "endpoint": "/api/topics",
                "method": "POST",
                "description": "Extracts latent topics from a set of documents.",
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


@app.post("/api/rank-tasks")
def rank_task_list(payload: RankRequest):
    """Rank tasks from the Node.js store by urgency (see task_ranker.py)."""
    return rank_tasks([task.model_dump() for task in payload.tasks])


@app.get("/api/tasks/ranked")
def rank_stored_tasks():
    """Fetch the tasks from the Node.js store and rank them in one call.

    The caller sends nothing, which is the point: a phone asking "what should I
    do next" should not first pull every task and post the whole list back.

    502 when the store cannot be read. The ranker itself is healthy, so a 4xx
    would blame a request that was fine, and 500 would read as a bug in this
    service. `detail` carries the reason, which is the distinction callers care
    about more than the code.
    """
    try:
        tasks = fetch_tasks()
    except TaskStoreError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    # An empty store is an answer rather than a failure, so it is ranked rather
    # than reported: the response shape is unchanged and "nothing to do" is true.
    return rank_tasks(tasks)


@app.post("/api/tasks/export")
def export_task_ranking(payload: ExportRequest):
    """Rank the posted tasks and return them as CSV or Markdown (see task_export.py)."""
    requested = payload.format.strip().lower()
    if requested not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"format must be one of: {', '.join(EXPORT_FORMATS)}",
        )

    ranked = rank_tasks([task.model_dump() for task in payload.tasks])["ranked"]

    if requested == "markdown":
        # Inline rather than as an attachment: Markdown gets pasted into a README,
        # so a download would be an extra step on the way to a copy.
        return Response(
            content=to_markdown(ranked, title=payload.title),
            media_type="text/markdown",
        )

    # CSV arrives as a download because a spreadsheet opens a .csv far better than
    # a browser does, and the filename is timestamped so exports stack instead of
    # replacing each other in the downloads folder.
    filename = export_filename("task-ranking")
    return Response(
        content=to_csv(ranked),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/topics")
def discover_topics(payload: TopicsRequest):
    """LSA topic extraction over the posted documents (see lsa_topic_model.py)."""
    corpus = prepare(payload.texts)
    if not corpus.usable:
        # 400 with the reason prepare() collected: "five documents, all empty"
        # is the caller's to fix, and LsaTopicModel's own ValueError for an empty
        # corpus would reach them as a 500 saying "LSA needs at least one
        # document" about documents they did send.
        raise HTTPException(
            status_code=400,
            detail=(
                f"need at least {MIN_DOCUMENTS} non-empty documents "
                f"({'; '.join(corpus.notes) or f'received {corpus.received}'})"
            ),
        )

    result = lsa_topics(
        corpus.documents, k=payload.topics, top_terms=payload.top_terms
    )
    # lsa_topics reports the documents it fitted; the received count and the notes
    # say how much of what was posted that left out.
    result["received"] = corpus.received
    result["notes"] = corpus.notes
    return result
