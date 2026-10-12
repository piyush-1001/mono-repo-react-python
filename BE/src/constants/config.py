"""Operational constants."""

rate_limiter_config = {"request_limit": 10, "time": 5}

PAYLOAD_TIMEOUT = 5
HTTP_TIMEOUT = 15
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
BULK_IMPORT_LIMIT = 500
LOW_STOCK_ALERT_BATCH = 250

# Background jobs
LOW_STOCK_DIGEST_JOB = "inventory.low_stock_digest"
STOCK_SYNC_JOB = "inventory.stock_sync"
JOB_RETRY_ATTEMPTS = 3
JOB_LOCK_TTL = 300

# Redis key namespaces
USER_SESSION_PREFIX = "session:user"
TOKEN_SESSION_PREFIX = "session:token"
RATE_LIMIT_PREFIX = "ratelimit"
IDEMPOTENCY_PREFIX = "idempotency"
JOB_LOCK_PREFIX = "job:lock"
