"""Latent Semantic Analysis (LSA) topic model over the existing TF-IDF space.

This is the third text-analysis model in the backend, alongside the naive Bayes
classifier and the k-means clusterer in ml_models.py. LSA goes a step further
than raw TF-IDF: it compresses the document/term matrix into a few latent
topics, so two documents that never share a literal word can still be close
because they use the same topic.

Implementation notes:

  - Standard library only, like the rest of the backend. The corpus here is a
    handful of short task titles, so a dense matrix is cheap and much easier to
    read than a sparse one.
  - The decomposition uses deflated orthogonal power iteration on M^T M to get
    the top-k right singular vectors. That is a plain eigen-decomposition of a
    small symmetric matrix - no numpy, and deterministic given the same corpus.
  - Documents are projected into topic space by multiplying their TF-IDF vector
    with the right singular vectors, which means a brand new (unseen) text can
    be projected and compared with the training documents directly.

Typical use:

    model = LsaTopicModel(["fix login bug", "add password reset", ...], k=2)
    model.topics()                 # keywords + top documents per topic
    model.transform("reset password")   # latent vector for a new string
    model.similarity("reset password")  # nearest known documents
"""

import math

from ml_models import vectorizer

MAX_ITERATIONS = 100
CONVERGENCE_TOLERANCE = 1e-9


def _mat_vec(rows, vector):
    """Multiply every row of the matrix by `vector`."""
    return [sum(row[i] * vector[i] for i in range(len(vector))) for row in rows]


def _matT_vec(rows, vector, n_terms):
    """Multiply the transpose of the matrix by `vector`."""
    return [
        sum(row[t] * weight for row, weight in zip(rows, vector))
        for t in range(n_terms)
    ]


def _norm(vector):
    return math.sqrt(sum(value * value for value in vector))


def _dot(vector_a, vector_b):
    return sum(a * b for a, b in zip(vector_a, vector_b))


def _orthogonalize(vector, basis):
    """Remove the components of `basis` from `vector` (Gram-Schmidt)."""
    for basis_vector in basis:
        projection = _dot(vector, basis_vector)
        vector = [
            value - projection * component
            for value, component in zip(vector, basis_vector)
        ]
    return vector


def _deterministic_seed(n_terms, component):
    """A stable, non-degenerate starting vector.

    Power iteration must not start orthogonal to the target eigenvector, and it
    must not start at zero. A smooth irrational-ish ramp satisfies both without
    needing a random number generator, which keeps results reproducible.
    """
    vector = [
        math.sin(1.37 * (component + 1) + 0.7 * index) + 1.0
        for index in range(n_terms)
    ]
    magnitude = _norm(vector)
    if magnitude == 0.0:
        return [1.0 / math.sqrt(n_terms)] * n_terms
    return [value / magnitude for value in vector]


class LsaTopicModel:
    """Rank-k truncated SVD of the TF-IDF document/term matrix."""

    def __init__(self, corpus, k=2, iterations=MAX_ITERATIONS):
        if not corpus:
            raise ValueError("LSA needs at least one document")

        sparse_rows = [vectorizer.vector(text) for text in corpus]
        self.terms = sorted({term for row in sparse_rows for term in row})
        self.n_docs = len(corpus)
        self.n_terms = len(self.terms)

        # Dense term vectors in a fixed term order, so a row can be multiplied
        # against a term-space vector directly.
        self.rows = [
            [row.get(term, 0.0) for term in self.terms] for row in sparse_rows
        ]

        # A rank-k approximation cannot exceed the matrix' own rank.
        self.k = max(1, min(k, self.n_docs, self.n_terms))
        self.right_vectors = []  # term-space directions (one per topic)
        self.singular_values = []
        self._fit(iterations)

    # ---------------------------------------------------------------- SVD

    def _fit(self, iterations):
        rows = [list(row) for row in self.rows]  # deflation mutates a copy

        for component in range(self.k):
            vector = _deterministic_seed(self.n_terms, component)
            previous = list(self.right_vectors)

            for _ in range(iterations):
                left = _mat_vec(rows, vector)
                candidate = _matT_vec(rows, left, self.n_terms)
                candidate = _orthogonalize(candidate, previous)

                magnitude = _norm(candidate)
                if magnitude < CONVERGENCE_TOLERANCE:
                    # Nothing left in this direction; the matrix ran out of rank.
                    return
                candidate = [value / magnitude for value in candidate]

                shift = _norm([a - b for a, b in zip(candidate, vector)])
                vector = candidate
                if shift < CONVERGENCE_TOLERANCE:
                    break

            left = _mat_vec(rows, vector)
            sigma = _norm(left)
            if sigma < CONVERGENCE_TOLERANCE:
                return

            self.right_vectors.append(vector)
            self.singular_values.append(sigma)

            # Deflate so the next component finds the following topic.
            left_unit = [value / sigma for value in left]
            rows = [
                [
                    row[t] - sigma * left_unit[i] * vector[t]
                    for t in range(self.n_terms)
                ]
                for i, row in enumerate(rows)
            ]

    # ------------------------------------------------------------- public

    def topics(self, top_terms=5, top_documents=3):
        """Describe each latent topic by its strongest terms and documents."""
        topics = []
        weights = self.projection_weights()
        for topic, vector in enumerate(self.right_vectors):
            ranked_terms = sorted(
                zip(self.terms, vector), key=lambda pair: abs(pair[1]), reverse=True
            )
            ranked_docs = sorted(
                range(self.n_docs), key=lambda i: abs(weights[i][topic]), reverse=True
            )
            topics.append(
                {
                    "topic": topic,
                    "singular_value": round(self.singular_values[topic], 4),
                    "keywords": [
                        {"term": term, "weight": round(weight, 4)}
                        for term, weight in ranked_terms[:top_terms]
                    ],
                    "documents": [
                        {"index": i, "weight": round(weights[i][topic], 4)}
                        for i in ranked_docs[:top_documents]
                    ],
                }
            )
        return topics

    def projection_weights(self):
        """Topic weight of every training document: shape (n_docs, k)."""
        return [self._project_row(row) for row in self.rows]

    def transform(self, text):
        """Project an arbitrary string into topic space."""
        vector = vectorizer.vector(text)
        row = [vector.get(term, 0.0) for term in self.terms]
        return self._project_row(row)

    def similarity(self, text, top_n=3):
        """Nearest training documents to `text`, by cosine in topic space."""
        query = self.transform(text)
        weights = self.projection_weights()
        scored = [
            {
                "index": i,
                "similarity": round(self._cosine(query, doc) * 100, 1),
            }
            for i, doc in enumerate(weights)
        ]
        scored.sort(key=lambda item: item["similarity"], reverse=True)
        return {
            "query": text,
            "latent_vector": [round(value, 4) for value in query],
            "matches": scored[:top_n],
        }

    # ------------------------------------------------------------ helpers

    def _project_row(self, row):
        """Project one TF-IDF row onto the retained term-space directions."""
        return [_dot(row, vector) for vector in self.right_vectors]

    @staticmethod
    def _cosine(vector_a, vector_b):
        dot = _dot(vector_a, vector_b)
        magnitude = _norm(vector_a) * _norm(vector_b)
        if magnitude == 0.0:
            return 0.0
        return dot / magnitude


def lsa_topics(corpus, k=2, top_terms=5):
    """Convenience wrapper mirroring the other model callables."""
    model = LsaTopicModel(corpus, k=k)
    return {
        "k": model.k,
        "documents": len(corpus),
        "terms": model.n_terms,
        "topics": model.topics(top_terms=top_terms),
    }
