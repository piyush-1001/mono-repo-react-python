"""API and exception message constants."""

# --- generic ---
SUCCESS = "SUCCESS"
ERROR = "ERROR"
SOMETHING_WENT_WRONG = "Something went wrong. Please try again later."
INVALID_REQUEST = "Invalid request"
UNAUTHORIZED = "Unauthorized"
FORBIDDEN = "You do not have permission to perform this action"
NOT_FOUND = "Resource not found"
METHOD_NOT_ALLOWED = "Method not allowed"
TOO_MANY_REQUESTS = "Rate limit exceeded. Please slow down."
VALIDATION_FAILED = "Validation failed"
SUCCESSFULLY_CREATED = "Successfully created"
SUCCESSFULLY_UPDATED = "Successfully updated"
SUCCESSFULLY_DELETED = "Successfully deleted"

# --- auth / tokens ---
LOGIN_SUCCESSFUL = "Logged in successfully"
SIGNED_OUT = "Signed out successfully"
INVALID_CREDENTIALS = "Invalid email or password"
INVALID_TOKEN = "Invalid token"
EXPIRED_TOKEN = "Token has expired"
TOKEN_REFRESHED = "Token refreshed successfully"
MISSING_TOKEN = "Authentication credentials were not provided"
SESSION_EXPIRED = "Session has expired, please sign in again"
ACCOUNT_INACTIVE = "This account is deactivated"
RSA_KEY_UNAVAILABLE = "Encryption key is not available"
PAYLOAD_EXPIRED = "Request payload has expired"
PAYLOAD_INVALID = "Request payload could not be decrypted"

# --- user ---
USER_NOT_FOUND = "User not found"
EMAIL_ALREADY_EXISTS = "A user with this email already exists"
PHONE_ALREADY_EXISTS = "A user with this phone number already exists"
EMAIL_FIELD_REQUIRED = "Email is required"
PASSWORD_FIELD_REQUIRED = "Password is required"
PASSWORD_TOO_SHORT = "Password must be at least 8 characters"
SELF_DEACTIVATION_NOT_ALLOWED = "You cannot deactivate your own account"
ROLE_INVALID = "Requested role is not valid"

# --- category ---
CATEGORY_NOT_FOUND = "Category not found"
CATEGORY_CODE_ALREADY_EXISTS = "A category with this code already exists"
CATEGORY_NOT_EMPTY = "Category still has products assigned"

# --- product ---
PRODUCT_NOT_FOUND = "Product not found"
SKU_ALREADY_EXISTS = "A product with this SKU already exists"
STOCK_MOVEMENT_NOT_ALLOWED = "Stock movement would make stock negative"
INSUFFICIENT_STOCK = "Not enough stock available for this movement"
