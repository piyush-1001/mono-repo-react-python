"""The words that carry a document's meaning.

TF-IDF weighs every term by how often it appears in a document and how rare it
is across the corpus. The similarity model in ml_models.py uses that weighting
to compare two documents; the same weighting applied to one document at a time
answers a different question - not "how similar are these" but "what is this
about".

Standard library plus the tokenizer and vectorizer from ml_models.py, so the
vocabulary of a term is exactly the one the rest of the models use.
"""

from collections import Counter

from ml_models import TfidfVectorizer, tokenize

# A short English stopword list. Not exhaustive on purpose: a long list starts
# dropping words that carry meaning in a task title ("to", "for" and "with" are
# all words in "rewrite the login flow with a timer"), and a title is a
# sentence fragment rather than prose.
STOPWORDS = frozenset(
    """
    a an and are as at be been being but by can could did do does doing done
    for from had has have he her here hers him his how i if in into is it its
    me my of on once only or other our ours out over own same she should so some
    such than that the their theirs them then there these they this those to
    too under until up very was we were what when where which while who whom
    why will with would you your yours
    don't doesn't isn't aren't wasn't weren't
    """.split()
)


def _term_weights(text, idf, default_idf):
    """(term, tf-idf) pairs for one document, stopwords removed.

    The raw term count is used rather than the vectorizer's length-normalised
    weight: a keyword list is about which words matter, and normalising by
    document length flattens exactly the difference between a word that appears
    once in a long title and one that appears three times.
    """
    counts = Counter(tokenize(text))
    return [
        (term, count * idf.get(term, default_idf))
        for term, count in counts.items()
        if term not in STOPWORDS and len(term) > 1
    ]


def _ranked(pairs, top_n):
    """The highest-scoring pairs, ties broken alphabetically for a stable list."""
    ordered = sorted(pairs, key=lambda pair: (-pair[1], pair[0]))
    return [
        {"term": term, "weight": round(weight, 4)}
        for term, weight in ordered[:top_n]
    ]


def document_keywords(text, idf, default_idf, top_n=8):
    """The keywords of a single document."""
    return _ranked(_term_weights(text, idf, default_idf), top_n)


def corpus_keywords(documents, top_n=10, vectorizer=None):
    """The terms that matter across the whole corpus.

    Each term's score is the sum of its tf-idf over every document, so a term
    that is both frequent and rare elsewhere keeps its place: "api" in a
    document about an API is common, and common, and therefore uninteresting,
    which is what idf is for.

    The vectorizer is optional so a caller that already built one - to score
    the documents individually - does not pay for a second, identical fit.
    """
    vectorizer = vectorizer or TfidfVectorizer(documents)
    totals = Counter()
    for text in documents:
        for term, weight in _term_weights(text, vectorizer.idf, vectorizer.default_idf):
            totals[term] += weight
    return _ranked(totals.items(), top_n)


def extract(texts, top_n=8, per_document=False):
    """Keyword extraction over a set of documents.

    `texts` is expected to be the cleaned corpus, not the raw request: the
    caller runs corpus_prep.prepare first, so empty documents are not counted
    and the idf is computed over the documents that are actually there.
    """
    # One fit of the corpus, shared by the corpus-wide and the per-document
    # scores, so both are measured against the same idf.
    vectorizer = TfidfVectorizer(texts)

    result = {
        "documents": len(texts),
        "corpus": corpus_keywords(texts, top_n=top_n, vectorizer=vectorizer),
    }

    if per_document:
        result["per_document"] = [
            {
                "index": index,
                "keywords": document_keywords(
                    text, vectorizer.idf, vectorizer.default_idf, top_n=top_n
                ),
            }
            for index, text in enumerate(texts)
        ]

    return result
