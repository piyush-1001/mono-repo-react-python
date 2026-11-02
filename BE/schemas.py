"""Request models for the HTTP API.

They live here rather than in main.py so the model registry can publish each
model's input schema: the React app renders its forms from that schema, and a
form generated from a model class cannot describe a different model.

The vocabulary of a task is not open-ended. A status the ranker does not know
is not rejected but silently treated as "pending", and a priority it does not
know as "medium" - so an accepted-but-unknown value is a task that is stored,
displayed and scored as something it is not. The Literal types below make that
a 422 at the edge instead of a quiet downgrade further in.
"""

from typing import Literal

from pydantic import BaseModel, Field

from task_fields import PRIORITIES, STATUSES

Status = Literal["pending", "in-progress", "done"]
Priority = Literal["high", "medium", "low"]

# Literal needs its members written out at import time, so the lists above
# cannot be derived from the tuples in task_fields. This check is what keeps
# the two from drifting apart when the ranker's weights change.
if set(Status.__args__) != set(STATUSES):
    raise RuntimeError(
        f"Status {Status.__args__} does not match the ranker's vocabulary {STATUSES}"
    )
if set(Priority.__args__) != set(PRIORITIES):
    raise RuntimeError(
        f"Priority {Priority.__args__} does not match the ranker's vocabulary {PRIORITIES}"
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
    status: Status = "pending"
    priority: Priority = "medium"
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


class KeywordRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    top_terms: int = Field(default=8, ge=1, le=25)
    # Per-document keywords as well as the corpus-wide ones. Off by default
    # because a corpus of a hundred documents returns a hundred lists.
    per_document: bool = False
