"""Small, dependency-free machine-learning models used by the API.

Everything here is implemented with the Python standard library only, so the
backend keeps its current install footprint while still exposing real ML
algorithms:

  - NaiveBayesClassifier : multinomial naive Bayes with Laplace smoothing
                           (trained spam/ham detector)
  - TfidfVectorizer      : TF-IDF term weighting + cosine similarity
  - MarkovTextGenerator  : bigram Markov-chain text generation
  - kmeans_cluster       : k-means clustering over TF-IDF vectors
"""

import math
import random
import re
from collections import Counter, defaultdict

WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text: str):
    return WORD_RE.findall(text.lower())


# ============================ Naive Bayes ============================

# Hand-labeled corpus: "spam" vs "ham". Replace/extend to improve accuracy.
# Note: This corpus should be extended or replaced with a larger dataset
# in production to improve model robustness against adversarial inputs.
TRAINING_CORPUS = [
    ("Win a free iPhone now click here to claim your prize", "spam"),
    ("Congratulations you have been selected for a cash prize call now", "spam"),
    ("Buy cheap meds online no prescription needed discount pills", "spam"),
    ("URGENT your account will be suspended verify password immediately", "spam"),
    ("Make 5000 per week working from home guaranteed income", "spam"),
    ("Limited offer cheapest deals on pills and vitamins buy today", "spam"),
    ("You won a free vacation claim your free ticket within 24 hours", "spam"),
    ("Free entry to win cash text WIN to our number now", "spam"),
    ("Increase your bank balance with this one weird money trick act fast", "spam"),
    ("Best pills discount buy now limited stock free shipping", "spam"),
    ("Hey are we still meeting for lunch tomorrow at noon", "ham"),
    ("The project deadline moved to Friday please review the report", "ham"),
    ("Happy birthday hope you have a great day with your family", "ham"),
    ("Can you send me the meeting notes from this morning", "ham"),
    ("I fixed the API bug and pushed the update to production", "ham"),
    ("Let's grab coffee after class and go over the study plan", "ham"),
    ("The doctor appointment for next week is confirmed for 3pm", "ham"),
    ("Thanks for the helpful feedback on my code it really improved it", "ham"),
    ("Weekend trip plans flight booked hotel reserved great weather", "ham"),
    ("Reminder team standup at 10 bring the revenue report for review", "ham"),
]


class NaiveBayesClassifier:
    """Multinomial naive Bayes with Laplace smoothing."""

    def __init__(self):
        self.class_doc_counts = Counter()
        self.class_word_counts = defaultdict(Counter)
        self.class_total_words = Counter()
        self.vocab = set()
        self.total_docs = 0

    def fit(self, documents):
        for text, label in documents:
            tokens = tokenize(text)
            self.class_doc_counts[label] += 1
            self.class_word_counts[label].update(tokens)
            self.class_total_words[label] += len(tokens)
            self.vocab.update(tokens)
            self.total_docs += 1

    def predict(self, text: str):
        tokens = tokenize(text)
        vocab_size = len(self.vocab)

        log_scores = {}
        for label in self.class_doc_counts:
            total = self.class_total_words[label]
            score = math.log(self.class_doc_counts[label] / self.total_docs)
            for token in tokens:
                count = self.class_word_counts[label][token]
                score += math.log((count + 1) / (total + vocab_size))
            log_scores[label] = score

        # softmax over log-scores -> normalized probabilities
        best = max(log_scores.values())
        exp = {label: math.exp(s - best) for label, s in log_scores.items()}
        norm = sum(exp.values())
        probabilities = {
            label: round(value / norm * 100, 1) for label, value in exp.items()
        }
        label = max(log_scores, key=log_scores.get)

        return {
            "label": label,
            "probabilities": probabilities,
            "word_count": len(tokens),
            "model": "multinomial-naive-bayes",
        }


spam_classifier = NaiveBayesClassifier()
spam_classifier.fit(TRAINING_CORPUS)


# ============================ TF-IDF similarity ============================

# Background corpus for document frequencies, so idf does not degenerate
# when only two short texts are compared.
IDF_CORPUS = [text for text, _ in TRAINING_CORPUS] + [
    "machine learning models learn patterns from data using training and prediction",
    "the software developer built a fast api with python and react for the web app",
    "healthy food and daily exercise improve wellness and business productivity",
    "students study education topics and learn about travel destinations",
]


class TfidfVectorizer:
    """Term frequency / inverse document frequency vectorizer."""

    def __init__(self, corpus):
        documents = [tokenize(doc) for doc in corpus]
        self.n_docs = len(documents)
        doc_freq = Counter()
        for doc in documents:
            doc_freq.update(set(doc))
        self.idf = {
            term: math.log((self.n_docs + 1) / (df + 1)) + 1
            for term, df in doc_freq.items()
        }
        self.default_idf = math.log(self.n_docs + 1) + 1

    def vector(self, text: str):
        tokens = tokenize(text)
        counts = Counter(tokens)
        total = max(len(tokens), 1)
        return {
            term: (count / total) * self.idf.get(term, self.default_idf)
            for term, count in counts.items()
        }


vectorizer = TfidfVectorizer(IDF_CORPUS)


def cosine_similarity(vec_a, vec_b):
    common = set(vec_a) & set(vec_b)
    dot = sum(vec_a[term] * vec_b[term] for term in common)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def text_similarity(text_a: str, text_b: str):
    vec_a = vectorizer.vector(text_a)
    vec_b = vectorizer.vector(text_b)
    sim = cosine_similarity(vec_a, vec_b)

    if sim > 0.6:
        verdict = "very similar"
    elif sim > 0.3:
        verdict = "somewhat similar"
    else:
        verdict = "mostly unrelated"

    return {
        "similarity": round(sim * 100, 1),
        "shared_terms": sorted(set(vec_a) & set(vec_b))[:10],
        "verdict": verdict,
    }


# ============================ Markov text generation ============================

GENERATION_TRAINING_TEXT = """
Machine learning teaches computers to learn from data. Sentiment analysis detects
tone in text. Neural networks recognize patterns that humans find difficult.
Text classification sorts documents into categories. Modern AI systems combine
statistics with software engineering. Natural language processing helps machines
read like people. FastAPI serves machine learning models to web apps. Good data
makes better models. Better models make smarter products. Smarter products help
people every day. React displays predictions in a friendly interface. Python runs
the analysis behind the scenes.
"""


class MarkovTextGenerator:
    """Bigram Markov-chain text generator."""

    def __init__(self, text: str):
        self.transitions = defaultdict(list)
        tokens = tokenize(text)
        for first, second in zip(tokens, tokens[1:]):
            self.transitions[first].append(second)
        self.words = list(self.transitions)

    def generate(self, seed: str = "", max_words: int = 30, seed_value: int = None):
        """Generate text using bigram Markov chain.

        Args:
            seed: Initial words to start the chain
            max_words: Maximum number of words to generate
            seed_value: Optional random seed for reproducible output
        """
        if seed_value is not None:
            random.seed(seed_value)

        seed_tokens = tokenize(seed)
        if seed_tokens and seed_tokens[-1] in self.transitions:
            chain = list(seed_tokens)
            seed_used = True
        else:
            chain = [random.choice(self.words)]
            seed_used = False

        current = chain[-1]
        while len(chain) < max_words:
            nxt = self.transitions.get(current)
            if not nxt:
                break
            current = random.choice(nxt)
            chain.append(current)

        sentence = " ".join(chain)
        text = sentence[0].upper() + sentence[1:] + "."
        return {"text": text, "seed_used": seed_used, "word_count": len(chain)}


markov_generator = MarkovTextGenerator(GENERATION_TRAINING_TEXT)


# ============================ K-Means clustering ============================

def _euclidean(vec_a, vec_b):
    terms = set(vec_a) | set(vec_b)
    return math.sqrt(sum((vec_a.get(t, 0.0) - vec_b.get(t, 0.0)) ** 2 for t in terms))


def _mean_vector(vectors):
    if not vectors:
        return {}
    terms = set().union(*(set(v) for v in vectors))
    return {t: sum(v.get(t, 0.0) for v in vectors) / len(vectors) for t in terms}


def _top_terms(centroid, n=3):
    ranked = sorted(centroid.items(), key=lambda kv: kv[1], reverse=True)
    return [term for term, _ in ranked[:n]]


def kmeans_cluster(texts, k=2, iterations=20):
    vectors = [vectorizer.vector(t) for t in texts]
    n = len(vectors)
    k = max(1, min(k, n))

    # Deterministic init: evenly spaced documents.
    centroids = [dict(vectors[i * n // k]) for i in range(k)]

    assignments = [-1] * n
    for _ in range(iterations):
        new_assignments = [
            min(range(k), key=lambda c: _euclidean(v, centroids[c])) for v in vectors
        ]
        if new_assignments == assignments:
            break
        assignments = new_assignments
        for c in range(k):
            centroids[c] = _mean_vector(
                [vectors[i] for i in range(n) if assignments[i] == c]
            )

    clusters = []
    for c in range(k):
        members = [i for i in range(n) if assignments[i] == c]
        clusters.append(
            {"cluster": c, "members": members, "keywords": _top_terms(centroids[c])}
        )

    return {"k": k, "assignments": assignments, "clusters": clusters}
