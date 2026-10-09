"""Configuration data for sentiment analysis."""

POSITIVE_WORDS = {
    "good", "great", "excellent", "happy", "love", "amazing", "fast", "smart", "nice",
    "success", "support", "helpful", "smooth", "easy", "positive", "improve"
}
NEGATIVE_WORDS = {
    "bad", "slow", "issue", "problem", "error", "poor", "hate", "worst", "broken",
    "difficult", "confusing", "negative", "fail", "weak"
}

TRAINING_TEXTS = [
    "I love this product and it works great",
    "This is amazing and very helpful",
    "The app is fast and smooth to use",
    "I am happy with the support and service",
    "This is good and easy to understand",
    "The feature is poor and very slow",
    "I have a problem with the login screen",
    "This is bad and confusing",
    "There is an issue with the dashboard",
    "The experience was awful and weak",
    "The interface is clean and better than before",
    "The tool feels excellent and very smart",
]
TRAINING_LABELS = [
    "positive", "positive", "positive", "positive", "positive",
    "negative", "negative", "negative", "negative", "negative",
    "positive", "positive",
]
