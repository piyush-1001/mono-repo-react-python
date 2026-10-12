import express from 'express';
import cors from 'cors';

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

// ============================================================
// Helpers
// ============================================================

const tokenize = (text) =>
  text.toLowerCase().match(/[a-z0-9']+/g) || [];

const logFactorial = (n) => {
  if (n <= 1) return 0;
  let r = 0;
  for (let i = 2; i <= n; i++) r += Math.log(i);
  return r;
};

// ============================================================
// 1. Sentiment Analysis  (keyword-based)
// ============================================================

const POSITIVE_WORDS = new Set([
  'good', 'great', 'excellent', 'happy', 'love', 'amazing', 'fast', 'smart',
  'nice', 'success', 'support', 'helpful', 'smooth', 'easy', 'positive',
  'improve', 'better', 'awesome', 'fantastic', 'wonderful', 'perfect',
]);
const NEGATIVE_WORDS = new Set([
  'bad', 'slow', 'issue', 'problem', 'error', 'poor', 'hate', 'worst',
  'broken', 'difficult', 'confusing', 'negative', 'fail', 'weak', 'terrible',
  'awful', 'horrible', 'useless', 'disappointing', 'annoying', 'frustrating',
]);

function analyzeSentiment(text) {
  const words = tokenize(text);
  const pos = words.filter((w) => POSITIVE_WORDS.has(w)).length;
  const neg = words.filter((w) => NEGATIVE_WORDS.has(w)).length;
  const sentiment = pos > neg ? 'positive' : neg > pos ? 'negative' : 'neutral';
  const confidence = Math.round((Math.max(pos, neg) / Math.max(words.length, 1)) * 100, 1);
  const keywords = words.filter((w) => POSITIVE_WORDS.has(w) || NEGATIVE_WORDS.has(w)).slice(0, 5);

  return {
    sentiment,
    confidence,
    keywords: keywords.length ? keywords : ['no strong signal'],
    word_count: words.length,
    prediction: `The model detects a mostly ${sentiment} tone in the text.`,
  };
}

// ============================================================
// 2. Naive Bayes Spam/Ham Classifier
// ============================================================

const TRAINING_CORPUS = [
  ['Win a free iPhone now click here to claim your prize', 'spam'],
  ['Congratulations you have been selected for a cash prize call now', 'spam'],
  ['Buy cheap meds online no prescription needed discount pills', 'spam'],
  ['URGENT your account will be suspended verify password immediately', 'spam'],
  ['Make 5000 per week working from home guaranteed income', 'spam'],
  ['Limited offer cheapest deals on pills and vitamins buy today', 'spam'],
  ['You won a free vacation claim your free ticket within 24 hours', 'spam'],
  ['Free entry to win cash text WIN to our number now', 'spam'],
  ['Increase your bank balance with this one weird money trick act fast', 'spam'],
  ['Best pills discount buy now limited stock free shipping', 'spam'],
  ['Hey are we still meeting for lunch tomorrow at noon', 'ham'],
  ['The project deadline moved to Friday please review the report', 'ham'],
  ['Happy birthday hope you have a great day with your family', 'ham'],
  ['Can you send me the meeting notes from this morning', 'ham'],
  ['I fixed the API bug and pushed the update to production', 'ham'],
  ["Let's grab coffee after class and go over the study plan", 'ham'],
  ['The doctor appointment for next week is confirmed for 3pm', 'ham'],
  ['Thanks for the helpful feedback on my code it really improved it', 'ham'],
  ['Weekend trip plans flight booked hotel reserved great weather', 'ham'],
  ['Reminder team standup at 10 bring the revenue report for review', 'ham'],
];

class NaiveBayesClassifier {
  constructor() {
    this.classDocCounts = {};      // label -> doc count
    this.classWordCounts = {};     // label -> { word -> count }
    this.classTotalWords = {};     // label -> total word count
    this.vocab = new Set();
    this.totalDocs = 0;
  }

  fit(corpus) {
    for (const [text, label] of corpus) {
      const tokens = tokenize(text);
      this.classDocCounts[label] = (this.classDocCounts[label] || 0) + 1;
      this.classWordCounts[label] = this.classWordCounts[label] || {};
      this.classTotalWords[label] = (this.classTotalWords[label] || 0) + tokens.length;
      for (const t of tokens) {
        this.classWordCounts[label][t] = (this.classWordCounts[label][t] || 0) + 1;
        this.vocab.add(t);
      }
      this.totalDocs++;
    }
  }

  predict(text) {
    const tokens = tokenize(text);
    const vocabSize = this.vocab.size;
    const logScores = {};

    for (const label of Object.keys(this.classDocCounts)) {
      const total = this.classTotalWords[label];
      let score = Math.log(this.classDocCounts[label] / this.totalDocs);
      for (const token of tokens) {
        const count = this.classWordCounts[label][token] || 0;
        score += Math.log((count + 1) / (total + vocabSize));
      }
      logScores[label] = score;
    }

    const best = Math.max(...Object.values(logScores));
    const expScores = Object.fromEntries(
      Object.entries(logScores).map(([k, v]) => [k, Math.exp(v - best)])
    );
    const norm = Object.values(expScores).reduce((a, b) => a + b, 0);
    const probabilities = Object.fromEntries(
      Object.entries(expScores).map(([k, v]) => [k, Math.round((v / norm) * 100, 1)])
    );

    const label = Object.entries(logScores).reduce((a, b) => (b[1] > a[1] ? b : a))[0];

    return { label, probabilities, word_count: tokens.length, model: 'multinomial-naive-bayes' };
  }
}

const spamClassifier = new NaiveBayesClassifier();
spamClassifier.fit(TRAINING_CORPUS);

// ============================================================
// 3. TF-IDF + Cosine Similarity
// ============================================================

const IDF_CORPUS = [
  ...TRAINING_CORPUS.map(([t]) => t),
  'machine learning models learn patterns from data using training and prediction',
  'the software developer built a fast api with python and react for the web app',
  'healthy food and daily exercise improve wellness and business productivity',
  'students study education topics and learn about travel destinations',
];

class TfidfVectorizer {
  constructor(corpus) {
    const docs = corpus.map((t) => tokenize(t));
    this.nDocs = docs.length;
    this.idf = {};
    const docFreq = {};
    for (const doc of docs) {
      for (const t of new Set(doc)) docFreq[t] = (docFreq[t] || 0) + 1;
    }
    for (const [term, df] of Object.entries(docFreq)) {
      this.idf[term] = Math.log((this.nDocs + 1) / (df + 1)) + 1;
    }
    this.defaultIdf = Math.log(this.nDocs + 1) + 1;
  }

  vector(text) {
    const tokens = tokenize(text);
    const counts = {};
    for (const t of tokens) counts[t] = (counts[t] || 0) + 1;
    const total = Math.max(tokens.length, 1);
    return Object.fromEntries(
      Object.entries(counts).map(([term, count]) => [
        term,
        (count / total) * (this.idf[term] ?? this.defaultIdf),
      ])
    );
  }
}

const cosineSimilarity = (a, b) => {
  const common = Object.keys(a).filter((t) => t in b);
  const dot = common.reduce((s, t) => s + a[t] * b[t], 0);
  const magA = Math.sqrt(Object.values(a).reduce((s, v) => s + v * v, 0));
  const magB = Math.sqrt(Object.values(b).reduce((s, v) => s + v * v, 0));
  if (!magA || !magB) return 0;
  return dot / (magA * magB);
};

const vectorizer = new TfidfVectorizer(IDF_CORPUS);

function textSimilarity(textA, textB) {
  const vecA = vectorizer.vector(textA);
  const vecB = vectorizer.vector(textB);
  const sim = cosineSimilarity(vecA, vecB);
  const verdict = sim > 0.6 ? 'very similar' : sim > 0.3 ? 'somewhat similar' : 'mostly unrelated';
  const shared = Object.keys(vecA).filter((t) => t in vecB).slice(0, 10);
  return { similarity: Math.round(sim * 100, 1), shared_terms: shared, verdict };
}

// ============================================================
// 4. Markov Chain Text Generator
// ============================================================

const GENERATION_TEXT = `
machine learning teaches computers to learn from data. sentiment analysis detects
tone in text. neural networks recognize patterns that humans find difficult.
text classification sorts documents into categories. modern ai systems combine
statistics with software engineering. natural language processing helps machines
read like people. fastapi serves machine learning models to web apps. good data
makes better models. better models make smarter products. smarter products help
people every day. react displays predictions in a friendly interface. python runs
the analysis behind the scenes. javascript runs in the browser making web apps
interactive. node serves the backend with express and handles api requests.
`.trim();

class MarkovGenerator {
  constructor(text) {
    this.transitions = {};
    const tokens = tokenize(text);
    for (let i = 0; i < tokens.length - 1; i++) {
      const [a, b] = [tokens[i], tokens[i + 1]];
      this.transitions[a] = this.transitions[a] || [];
      this.transitions[a].push(b);
    }
    this.words = Object.keys(this.transitions);
  }

  generate(seed = '', maxWords = 30) {
    const seedTokens = tokenize(seed);
    let chain;
    let seedUsed;
    if (seedTokens.length && this.transitions[seedTokens.at(-1)]) {
      chain = [...seedTokens];
      seedUsed = true;
    } else {
      chain = [this.words[Math.floor(Math.random() * this.words.length)]];
      seedUsed = false;
    }
    let current = chain.at(-1);
    while (chain.length < maxWords) {
      const next = this.transitions[current];
      if (!next) break;
      current = next[Math.floor(Math.random() * next.length)];
      chain.push(current);
    }
    const sentence = chain.join(' ');
    return {
      text: sentence[0].toUpperCase() + sentence.slice(1) + '.',
      seed_used: seedUsed,
      word_count: chain.length,
    };
  }
}

const markovGenerator = new MarkovGenerator(GENERATION_TEXT);

// ============================================================
// 5. K-Means Clustering
// ============================================================

const euclidean = (a, b) => {
  const terms = new Set([...Object.keys(a), ...Object.keys(b)]);
  return Math.sqrt([...terms].reduce((s, t) => s + (a[t] - b[t]) ** 2, 0));
};

const meanVector = (vectors) => {
  if (!vectors.length) return {};
  const terms = [...new Set(vectors.flatMap((v) => Object.keys(v)))];
  return Object.fromEntries(
    terms.map((t) => [t, vectors.reduce((s, v) => s + (v[t] || 0), 0) / vectors.length])
  );
};

const topTerms = (centroid, n = 3) =>
  Object.entries(centroid).sort((a, b) => b[1] - a[1]).slice(0, n).map(([t]) => t);

function kmeansCluster(texts, k = 2, iterations = 20) {
  const vectors = texts.map((t) => vectorizer.vector(t));
  const n = vectors.length;
  k = Math.max(1, Math.min(k, n));

  let centroids = Array.from({ length: k }, (_, i) => ({ ...vectors[Math.floor((i * n) / k)] }));
  let assignments = Array(n).fill(-1);

  for (let iter = 0; iter < iterations; iter++) {
    const newAssignments = vectors.map((v) =>
      centroids.reduce((best, c, ci) => (euclidean(v, c) < euclidean(v, centroids[best]) ? ci : best), 0)
    );
    if (newAssignments.every((a, i) => a === assignments[i])) break;
    assignments = newAssignments;
    centroids = Array.from({ length: k }, (_, c) =>
      meanVector(vectors.filter((_, i) => assignments[i] === c))
    );
  }

  const clusters = centroids.map((c, ci) => ({
    cluster: ci,
    members: vectors.reduce((acc, _, i) => (assignments[i] === ci ? [...acc, i] : acc), []),
    keywords: topTerms(c),
  }));

  return { k, assignments, clusters };
}

// ============================================================
// Routes
// ============================================================

app.get('/', (_req, res) => {
  res.json({ message: 'AI/ML Node.js Backend is running', version: '1.0' });
});

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.post('/api/message', (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'message is required' });
  const analysis = analyzeSentiment(message);
  res.json({
    reply: `AI review: ${analysis.prediction}`,
    original_message: message,
    analysis,
  });
});

app.post('/api/sentiment', (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'message is required' });
  res.json(analyzeSentiment(message));
});

app.post('/api/predict', (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'message is required' });
  res.json(spamClassifier.predict(message));
});

app.post('/api/similarity', (req, res) => {
  const { text_a, text_b } = req.body;
  if (!text_a || !text_b) return res.status(400).json({ error: 'text_a and text_b are required' });
  res.json(textSimilarity(text_a, text_b));
});

app.post('/api/generate', (req, res) => {
  const { seed = '', max_words = 30 } = req.body || {};
  if (max_words < 1 || max_words > 100) return res.status(400).json({ error: 'max_words must be 1-100' });
  res.json(markovGenerator.generate(seed, max_words));
});

app.post('/api/cluster', (req, res) => {
  const { texts, k = 2 } = req.body || {};
  if (!Array.isArray(texts) || texts.length < 2) {
    return res.status(400).json({ error: 'texts must be an array with at least 2 items' });
  }
  if (k < 1 || k > texts.length) {
    return res.status(400).json({ error: `k must be between 1 and ${texts.length}` });
  }
  res.json(kmeansCluster(texts, k));
});

// ============================================================
// Start
// ============================================================

app.listen(PORT, '0.0.0.0', () => {
  console.log(`AI/ML Node.js Backend running on http://0.0.0.0:${PORT}`);
});
