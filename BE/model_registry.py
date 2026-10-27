"""The catalogue of models this API exposes, in one place.

/api/models used to be a hand-written list inside main.py: adding an endpoint
meant adding a dictionary to that list, and nothing checked that the two
agreed. A model could be listed and not exist, or exist and not be listed, and
the frontend - which renders the list - would not find out until someone
clicked the entry.

This module is the list. main.py serves it verbatim and then verifies that
every entry has a matching route, so the catalogue cannot describe an endpoint
that is not there.
"""

from typing import get_args, get_origin

from schemas import (
    ClusterRequest,
    ExportRequest,
    GenerateRequest,
    KeywordRequest,
    MessageRequest,
    RankRequest,
    SimilarityRequest,
    TopicsRequest,
)

# Each entry names the endpoint, the method, and the model class that describes
# its input. `request_model` is None for the endpoints that take no input.
MODELS = [
    {
        "id": "sentiment",
        "name": "Keyword Sentiment Analysis",
        "endpoint": "/api/sentiment",
        "method": "POST",
        "description": "Scores a text as positive, negative or neutral.",
        "request_model": MessageRequest,
    },
    {
        "id": "spam",
        "name": "Naive Bayes Spam Classifier",
        "endpoint": "/api/predict",
        "method": "POST",
        "description": "Multinomial naive Bayes trained on a spam/ham corpus.",
        "request_model": MessageRequest,
    },
    {
        "id": "similarity",
        "name": "TF-IDF Cosine Similarity",
        "endpoint": "/api/similarity",
        "method": "POST",
        "description": "Compares two texts term-by-term with TF-IDF weighting.",
        "request_model": SimilarityRequest,
    },
    {
        "id": "generate",
        "name": "Markov Text Generator",
        "endpoint": "/api/generate",
        "method": "POST",
        "description": "Generates text from a bigram Markov chain.",
        "request_model": GenerateRequest,
    },
    {
        "id": "cluster",
        "name": "K-Means Document Clustering",
        "endpoint": "/api/cluster",
        "method": "POST",
        "description": "Groups documents by cosine distance over TF-IDF vectors.",
        "request_model": ClusterRequest,
    },
    {
        "id": "rank-tasks",
        "name": "Task Priority Ranker",
        "endpoint": "/api/rank-tasks",
        "method": "POST",
        "description": "Scores tasks by priority, status, age and urgent wording.",
        "request_model": RankRequest,
    },
    {
        "id": "rank-stored-tasks",
        "name": "Stored Task Ranker",
        "endpoint": "/api/tasks/ranked",
        "method": "GET",
        "description": "Reads the Node.js task store and ranks it in one call.",
        "request_model": None,
    },
    {
        "id": "export-tasks",
        "name": "Ranking Export",
        "endpoint": "/api/tasks/export",
        "method": "POST",
        "description": "Ranks posted tasks and returns them as CSV or Markdown.",
        "request_model": ExportRequest,
    },
    {
        "id": "topics",
        "name": "LSA Topic Model",
        "endpoint": "/api/topics",
        "method": "POST",
        "description": "Extracts latent topics from a set of documents.",
        "request_model": TopicsRequest,
    },
    {
        "id": "keywords",
        "name": "TF-IDF Keyword Extractor",
        "endpoint": "/api/keywords",
        "method": "POST",
        "description": "Pulls the terms that carry each document's meaning.",
        "request_model": KeywordRequest,
    },
    {
        "id": "insights",
        "name": "Task Board Insights",
        "endpoint": "/api/insights",
        "method": "GET",
        "description": "Summarises the stored board: ages, mix and what to do next.",
        "request_model": None,
    },
]


def _type_name(annotation):
    """A form-friendly name for a Python annotation.

    The frontend renders one control per parameter, so it needs to know whether
    a value is a line of text, a number, a checkbox, a list of lines or a piece
    of JSON. Everything that is not obviously one of those is called JSON, which
    the frontend parses - a wrong guess there produces a validation error the
    user can read, which is better than sending a string where a list belongs.
    """
    origin = get_origin(annotation)

    if origin is list:
        item_types = get_args(annotation)
        if item_types and item_types[0] is str:
            return "text-list"
        return "json"
    if origin is dict:
        return "json"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation is str:
        return "text"

    # Optional[str] and friends: the member that is not NoneType decides.
    members = [arg for arg in get_args(annotation) if arg is not type(None)]
    if len(members) == 1:
        return _type_name(members[0])
    return "json"


def _parameters(request_model):
    """Describe a model's input as a list of fields a form can render."""
    if request_model is None:
        return []

    fields = []
    for name, field in request_model.model_fields.items():
        fields.append(
            {
                "name": name,
                "type": _type_name(field.annotation),
                "required": field.is_required(),
                "default": field.get_default(call_default_factory=True),
                "description": field.description or "",
            }
        )
    return fields


def catalogue():
    """The catalogue as the frontend consumes it."""
    entries = []
    for model in MODELS:
        entry = {key: value for key, value in model.items() if key != "request_model"}
        entry["parameters"] = _parameters(model["request_model"])
        entries.append(entry)
    return entries


def endpoints():
    """The (method, path) pairs the catalogue claims, for the route check."""
    return {(model["method"], model["endpoint"]) for model in MODELS}
