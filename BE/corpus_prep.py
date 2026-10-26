"""Bound what a text model is asked to fit, and say what was changed.

The clustering and topic endpoints fit a model over whatever documents the caller
posted. Both models cost time in proportion to documents x terms - k-means
recomputes centroids over the whole TF-IDF space, and lsa_topic_model runs up to
MAX_ITERATIONS power-iteration sweeps - so without a ceiling here the caller sets
the server's per-request cost, from a browser, where pasting a whole log file is
one Ctrl-V away.

A silent cap would be its own problem: the response would claim two topics over
"20 documents" when 200 were posted. So every edit is reported in `notes`, and
endpoints pass that through rather than hiding it.

Standard library only; nothing here imports FastAPI, so the same guard can be
used from a script or a test.
"""

from typing import NamedTuple

# Ceilings, not measurements. A task board has tens of titles, so nothing real
# is near these and a request that is is only ever a paste that got away.
MAX_DOCUMENTS = 200
MAX_DOCUMENT_CHARACTERS = 4000

# Below this there is no comparison to be made: one document gives a matrix of
# rank 1, so k clamps to 1 and every similarity against it is 1.0. k-means has
# the same floor, which is why ClusterRequest already declares min_length=2.
MIN_DOCUMENTS = 2


class PreparedCorpus(NamedTuple):
    """The corpus to fit, plus what it took to get there.

    `received` is the raw count the caller posted, kept separate from
    `len(documents)` so an endpoint can report both rather than quietly
    reconciling them.
    """

    documents: list[str]
    received: int
    notes: list[str]

    @property
    def dropped(self) -> int:
        return max(self.received - len(self.documents), 0)

    @property
    def usable(self) -> bool:
        return len(self.documents) >= MIN_DOCUMENTS


def prepare(texts, max_documents=MAX_DOCUMENTS, max_characters=MAX_DOCUMENT_CHARACTERS):
    """Clean, cap and describe a corpus before a model fits it.

    Pydantic's min_length counts array items, not content: five empty strings
    passes validation and then raises ValueError from inside the model, which
    reaches the caller as a 500 for what is really a bad request. This is the
    check that looks at what was actually sent.
    """
    documents = []
    truncated = 0

    for text in texts:
        # One space per run of whitespace, which also strips the leading and
        # trailing ends. Pasted task titles arrive with the newlines of whatever
        # table they were copied from, and the vectorizer treats "a\n b" and
        # "a b" as the same terms only after this folding.
        cleaned = " ".join(text.split())
        if not cleaned:
            continue
        if len(cleaned) > max_characters:
            cleaned = cleaned[:max_characters].rstrip()
            truncated += 1
        documents.append(cleaned)

    notes = []

    empty = len(texts) - len(documents)
    if empty:
        notes.append(f"{empty} empty document(s) ignored")
    if truncated:
        notes.append(f"{truncated} document(s) cut to {max_characters} characters")

    # Truncation happens before the count cap, so a request of 300 short
    # documents is capped on document count rather than on character budget.
    if len(documents) > max_documents:
        notes.append(
            f"fitted the first {max_documents} of {len(documents)} documents"
        )
        documents = documents[:max_documents]

    if not documents:
        notes.append("nothing left to fit")

    # Identical documents are deliberately not deduplicated: topics() reports the
    # documents closest to each topic by index into this list, so removing an
    # entry would silently renumber every citation in the response.
    return PreparedCorpus(documents=documents, received=len(texts), notes=notes)
